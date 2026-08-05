//! Versioned, fail-closed complete engine-variant validation.

use core::{fmt, str::FromStr};
use std::{
    collections::HashSet,
    fmt::Write as _,
    fs::{self, OpenOptions},
    io::Write as _,
    path::Path,
    time::Duration,
};

use chess_core::{Color, Game, GameStatus, Position, SearchHistory, UciMove};
use chess_search::{
    iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights,
    EvaluationWeightSet, SearchLimits, SearchPolicySet, TranspositionTable,
};

use crate::{
    engine_variant::{
        EngineVariantIdentity, OptionalCapabilityIdentity, SemanticComponentIdentity,
        ENGINE_VARIANT_SCHEMA_VERSION,
    },
    perft, perft_fixtures,
    self_play::{
        ClaimableDrawPolicy, OpeningLine, OpeningSuite, SelfPlayResult, SelfPlayTermination,
    },
    ToolError,
};

/// Current complete engine-variant validation report schema.
pub const ENGINE_VARIANT_VALIDATION_SCHEMA_VERSION: u16 = 1;
/// Stable semantic identity of the S2-2 complete-variant protocol.
pub const ENGINE_VARIANT_VALIDATION_IDENTIFIER: u64 = 0x5641_5249_5641_4c31;
/// Production minimum: 200 independent color-swapped opening pairs.
pub const MINIMUM_PRODUCTION_VARIANT_PAIRS: u32 = 200;
/// Maximum bounded smoke pair count.
pub const MAXIMUM_SMOKE_VARIANT_PAIRS: u32 = 16;
/// Minimum development pair count.
pub const MINIMUM_DEVELOPMENT_VARIANT_PAIRS: u32 = 8;
/// One-sided 95% normal critical value, intentionally identical to the weight protocol.
pub const VARIANT_ONE_SIDED_95_PERCENT_Z: f64 = 1.644_853_626_951_472_2;
/// Authoritative correctness pre-gate perft depth.
pub const VARIANT_VALIDATION_PERFT_DEPTH: u8 = 4;

const FORMAT_MARKER: &str = "chess-engine-variant-validation-v1";
const MAXIMUM_VALIDATION_PAIRS: u32 = 100_000;
const MAXIMUM_VALIDATION_PLIES: u32 = 4_096;
const MAXIMUM_FIXED_NODES: u64 = 1_000_000_000_000;
const MAXIMUM_CLOCK_MILLISECONDS: u64 = 3_600_000;
const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;

/// Evidence tier and the authority it may carry.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum EngineVariantValidationTier {
    /// Small bounded plumbing and correctness smoke.
    Smoke,
    /// Paired development evidence that cannot authorize activation.
    Development,
    /// Production evidence with at least 200 independent pairs.
    Production,
}

impl fmt::Display for EngineVariantValidationTier {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::Smoke => "smoke",
            Self::Development => "development",
            Self::Production => "production",
        })
    }
}

impl FromStr for EngineVariantValidationTier {
    type Err = ToolError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        match value {
            "smoke" => Ok(Self::Smoke),
            "development" => Ok(Self::Development),
            "production" => Ok(Self::Production),
            _ => Err(ToolError::new(format!(
                "invalid engine-variant validation tier {value:?}"
            ))),
        }
    }
}

/// Equal-resource protocol used by both variants.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum EngineVariantResourceProtocol {
    /// Deterministic workload comparison independent of wall-clock speed.
    FixedNodes(u64),
    /// Release-relevant throughput comparison under an equal wall-clock budget.
    ClockMilliseconds(u64),
}

impl EngineVariantResourceProtocol {
    /// Human-readable reason the protocol exists.
    #[must_use]
    pub const fn purpose(self) -> &'static str {
        match self {
            Self::FixedNodes(_) => {
                "deterministic workload comparison independent of wall-clock speed"
            }
            Self::ClockMilliseconds(_) => {
                "release-relevant throughput comparison under equal wall-clock budgets"
            }
        }
    }

    fn validate(self) -> Result<(), ToolError> {
        match self {
            Self::FixedNodes(nodes) if (1..=MAXIMUM_FIXED_NODES).contains(&nodes) => Ok(()),
            Self::FixedNodes(_) => Err(ToolError::new(format!(
                "fixed-node protocol requires between 1 and {MAXIMUM_FIXED_NODES} nodes"
            ))),
            Self::ClockMilliseconds(milliseconds)
                if (1..=MAXIMUM_CLOCK_MILLISECONDS).contains(&milliseconds) =>
            {
                Ok(())
            }
            Self::ClockMilliseconds(_) => Err(ToolError::new(format!(
                "clock protocol requires between 1 and {MAXIMUM_CLOCK_MILLISECONDS} milliseconds"
            ))),
        }
    }

    fn search_limits(self, check_extension: bool) -> SearchLimits {
        let limits = match self {
            Self::FixedNodes(nodes) => SearchLimits::new().with_nodes(nodes),
            Self::ClockMilliseconds(milliseconds) => {
                SearchLimits::new().with_hard_time(Duration::from_millis(milliseconds))
            }
        };
        if check_extension {
            limits.with_check_extension()
        } else {
            limits
        }
    }
}

impl fmt::Display for EngineVariantResourceProtocol {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::FixedNodes(nodes) => write!(formatter, "fixed_nodes:{nodes}"),
            Self::ClockMilliseconds(milliseconds) => {
                write!(formatter, "clock_ms:{milliseconds}")
            }
        }
    }
}

impl FromStr for EngineVariantResourceProtocol {
    type Err = ToolError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        let (kind, amount) = value
            .split_once(':')
            .ok_or_else(|| ToolError::new(format!("invalid resource protocol {value:?}")))?;
        let amount = amount.parse::<u64>().map_err(|error| {
            ToolError::new(format!(
                "invalid resource protocol amount {amount:?}: {error}"
            ))
        })?;
        let protocol = match kind {
            "fixed_nodes" => Self::FixedNodes(amount),
            "clock_ms" => Self::ClockMilliseconds(amount),
            _ => {
                return Err(ToolError::new(format!(
                    "unsupported resource protocol kind {kind:?}"
                )))
            }
        };
        protocol.validate()?;
        Ok(protocol)
    }
}

/// Complete equal-resource match and acceptance configuration.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct EngineVariantValidationConfig {
    tier: EngineVariantValidationTier,
    pair_count: u32,
    seed: u64,
    protocol: EngineVariantResourceProtocol,
    transposition_table_mebibytes: usize,
    check_extension: bool,
    maximum_plies: u32,
    claimable_draw_policy: ClaimableDrawPolicy,
    minimum_score_margin: f64,
    maximum_unfinished_per_mille: u16,
}

impl EngineVariantValidationConfig {
    /// Creates a tiered variant-validation configuration.
    pub fn new(
        tier: EngineVariantValidationTier,
        pair_count: u32,
        seed: u64,
        protocol: EngineVariantResourceProtocol,
        transposition_table_mebibytes: usize,
    ) -> Result<Self, ToolError> {
        let value = Self {
            tier,
            pair_count,
            seed,
            protocol,
            transposition_table_mebibytes,
            check_extension: false,
            maximum_plies: 256,
            claimable_draw_policy: ClaimableDrawPolicy::Accept,
            minimum_score_margin: 0.0,
            maximum_unfinished_per_mille: 50,
        };
        value.validate()?;
        Ok(value)
    }

    /// Selects whether the shared request limit enables bounded check extension.
    pub fn with_check_extension(mut self, enabled: bool) -> Result<Self, ToolError> {
        self.check_extension = enabled;
        self.validate()?;
        Ok(self)
    }

    /// Selects the complete game-length boundary, including opening plies.
    pub fn with_maximum_plies(mut self, maximum_plies: u32) -> Result<Self, ToolError> {
        self.maximum_plies = maximum_plies;
        self.validate()?;
        Ok(self)
    }

    /// Selects whether claimable draws are accepted immediately.
    #[must_use]
    pub const fn with_claimable_draw_policy(mut self, policy: ClaimableDrawPolicy) -> Self {
        self.claimable_draw_policy = policy;
        self
    }

    /// Requires the lower confidence bound to exceed 50% by this margin.
    pub fn with_minimum_score_margin(mut self, margin: f64) -> Result<Self, ToolError> {
        self.minimum_score_margin = margin;
        self.validate()?;
        Ok(self)
    }

    /// Sets the maximum unfinished-game rate in parts per thousand.
    pub fn with_maximum_unfinished_per_mille(mut self, maximum: u16) -> Result<Self, ToolError> {
        self.maximum_unfinished_per_mille = maximum;
        self.validate()?;
        Ok(self)
    }

    /// Returns the evidence tier.
    #[must_use]
    pub const fn tier(self) -> EngineVariantValidationTier {
        self.tier
    }

    /// Returns the number of independent opening pairs.
    #[must_use]
    pub const fn pair_count(self) -> u32 {
        self.pair_count
    }

    /// Returns the fixed opening-rotation seed.
    #[must_use]
    pub const fn seed(self) -> u64 {
        self.seed
    }

    /// Returns the equal-resource protocol.
    #[must_use]
    pub const fn protocol(self) -> EngineVariantResourceProtocol {
        self.protocol
    }

    /// Returns the TT budget assigned independently to each side.
    #[must_use]
    pub const fn transposition_table_mebibytes(self) -> usize {
        self.transposition_table_mebibytes
    }

    /// Returns whether the shared request limit enables check extension.
    #[must_use]
    pub const fn check_extension_enabled(self) -> bool {
        self.check_extension
    }

    /// Returns the maximum total game length.
    #[must_use]
    pub const fn maximum_plies(self) -> u32 {
        self.maximum_plies
    }

    /// Returns the claimable-draw policy.
    #[must_use]
    pub const fn claimable_draw_policy(self) -> ClaimableDrawPolicy {
        self.claimable_draw_policy
    }

    /// Returns the required score margin above 50%.
    #[must_use]
    pub const fn minimum_score_margin(self) -> f64 {
        self.minimum_score_margin
    }

    /// Returns the unfinished-game ceiling in parts per thousand.
    #[must_use]
    pub const fn maximum_unfinished_per_mille(self) -> u16 {
        self.maximum_unfinished_per_mille
    }

    fn validate(self) -> Result<(), ToolError> {
        match self.tier {
            EngineVariantValidationTier::Smoke
                if !(1..=MAXIMUM_SMOKE_VARIANT_PAIRS).contains(&self.pair_count) =>
            {
                return Err(ToolError::new(format!(
                    "smoke validation requires between 1 and {MAXIMUM_SMOKE_VARIANT_PAIRS} pairs"
                )));
            }
            EngineVariantValidationTier::Development
                if !(MINIMUM_DEVELOPMENT_VARIANT_PAIRS..MINIMUM_PRODUCTION_VARIANT_PAIRS)
                    .contains(&self.pair_count) =>
            {
                return Err(ToolError::new(format!(
                    "development validation requires between {MINIMUM_DEVELOPMENT_VARIANT_PAIRS} and {} pairs",
                    MINIMUM_PRODUCTION_VARIANT_PAIRS - 1
                )));
            }
            EngineVariantValidationTier::Production
                if !(MINIMUM_PRODUCTION_VARIANT_PAIRS..=MAXIMUM_VALIDATION_PAIRS)
                    .contains(&self.pair_count) =>
            {
                return Err(ToolError::new(format!(
                    "production validation requires between {MINIMUM_PRODUCTION_VARIANT_PAIRS} and {MAXIMUM_VALIDATION_PAIRS} pairs"
                )));
            }
            _ => {}
        }
        self.protocol.validate()?;
        if self.transposition_table_mebibytes == 0 {
            return Err(ToolError::new(
                "variant validation TT budget must be at least one MiB",
            ));
        }
        if self.maximum_plies == 0 || self.maximum_plies > MAXIMUM_VALIDATION_PLIES {
            return Err(ToolError::new(format!(
                "variant validation maximum plies must be between 1 and {MAXIMUM_VALIDATION_PLIES}"
            )));
        }
        if !self.minimum_score_margin.is_finite()
            || !(0.0..=0.25).contains(&self.minimum_score_margin)
        {
            return Err(ToolError::new(
                "minimum score margin must be finite and between 0.0 and 0.25",
            ));
        }
        if self.maximum_unfinished_per_mille > 1_000 {
            return Err(ToolError::new(
                "maximum unfinished rate must not exceed 1000 per mille",
            ));
        }
        self.protocol
            .search_limits(self.check_extension)
            .validate()
            .map_err(|error| ToolError::new(error.to_string()))
    }
}

/// Runtime policy, evaluator, and checksum-bound complete identity.
#[derive(Clone, Copy, Debug)]
pub struct EngineVariantRuntime<'a> {
    /// Complete variant identity.
    pub identity: &'a EngineVariantIdentity,
    /// Exact search policy used by this variant.
    pub search_policy: &'a SearchPolicySet,
    /// Exact evaluator used by this variant.
    pub evaluation_weights: &'a EvaluationWeightSet,
}

impl<'a> EngineVariantRuntime<'a> {
    /// Constructs and validates a runtime bundle.
    pub fn new(
        identity: &'a EngineVariantIdentity,
        search_policy: &'a SearchPolicySet,
        evaluation_weights: &'a EvaluationWeightSet,
    ) -> Result<Self, ToolError> {
        let value = Self {
            identity,
            search_policy,
            evaluation_weights,
        };
        value.validate()?;
        Ok(value)
    }

    fn validate(self) -> Result<(), ToolError> {
        self.identity.validate()?;
        self.search_policy
            .validate()
            .map_err(|error| ToolError::new(error.to_string()))?;
        self.evaluation_weights
            .validate()
            .map_err(|error| ToolError::new(error.to_string()))?;
        if self.identity.search_policy_identity()
            != (SemanticComponentIdentity {
                schema_version: self.search_policy.schema_version,
                identifier: self.search_policy.identifier,
                checksum: self.search_policy.checksum,
            })
        {
            return Err(ToolError::new(
                "engine-variant runtime policy does not match its identity",
            ));
        }
        if self.identity.evaluation_weight_identity()
            != (SemanticComponentIdentity {
                schema_version: self.evaluation_weights.schema_version,
                identifier: self.evaluation_weights.identifier,
                checksum: self.evaluation_weights.checksum,
            })
        {
            return Err(ToolError::new(
                "engine-variant runtime weights do not match their identity",
            ));
        }
        Ok(())
    }
}

/// Standalone serializable snapshot of a complete variant identity.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RecordedEngineVariantIdentity {
    /// Identity schema.
    pub schema_version: u16,
    /// Complete-variant semantic identifier.
    pub identifier: u64,
    /// Exact source commit.
    pub source_commit: [u8; 20],
    /// Engine/package version.
    pub engine_version: String,
    /// Search-policy identity.
    pub search_policy: SemanticComponentIdentity,
    /// Evaluation-weight identity.
    pub evaluation_weights: SemanticComponentIdentity,
    /// Opening-book state and data identity.
    pub opening_book: OptionalCapabilityIdentity,
    /// Tablebase state and data identity.
    pub tablebase: OptionalCapabilityIdentity,
    /// Exact TT size.
    pub transposition_table_mebibytes: u64,
    /// Target/toolchain/profile/features identity.
    pub build_identity: String,
    /// Exact invocation.
    pub exact_invocation: String,
    /// Complete identity checksum.
    pub checksum: u64,
}

impl RecordedEngineVariantIdentity {
    fn from_identity(identity: &EngineVariantIdentity) -> Self {
        Self {
            schema_version: identity.schema_version(),
            identifier: identity.identifier(),
            source_commit: identity.source_commit(),
            engine_version: identity.engine_version().to_owned(),
            search_policy: identity.search_policy_identity(),
            evaluation_weights: identity.evaluation_weight_identity(),
            opening_book: identity.opening_book_identity(),
            tablebase: identity.tablebase_identity(),
            transposition_table_mebibytes: identity.transposition_table_mebibytes(),
            build_identity: identity.build_identity().to_owned(),
            exact_invocation: identity.exact_invocation().to_owned(),
            checksum: identity.checksum(),
        }
    }

    /// Recomputes the checksum using the engine-variant identity algorithm.
    #[must_use]
    pub fn computed_checksum(&self) -> u64 {
        let mut hash = FNV_OFFSET;
        hash = hash_bytes(hash, &self.schema_version.to_le_bytes());
        hash = hash_bytes(hash, &self.identifier.to_le_bytes());
        hash = hash_bytes(hash, &self.source_commit);
        hash = hash_text(hash, &self.engine_version);
        hash = hash_component(hash, self.search_policy);
        hash = hash_component(hash, self.evaluation_weights);
        hash = hash_optional_capability(hash, self.opening_book);
        hash = hash_optional_capability(hash, self.tablebase);
        hash = hash_bytes(hash, &self.transposition_table_mebibytes.to_le_bytes());
        hash = hash_text(hash, &self.build_identity);
        hash_text(hash, &self.exact_invocation)
    }

    /// Validates all exact identity fields and checksum.
    pub fn validate(&self) -> Result<(), ToolError> {
        if self.schema_version != ENGINE_VARIANT_SCHEMA_VERSION {
            return Err(ToolError::new(format!(
                "unsupported recorded engine-variant schema {}",
                self.schema_version
            )));
        }
        if self.identifier == 0
            || self.source_commit.iter().all(|byte| *byte == 0)
            || self.engine_version.trim().is_empty()
            || self.build_identity.trim().is_empty()
            || self.exact_invocation.trim().is_empty()
            || self.transposition_table_mebibytes == 0
        {
            return Err(ToolError::new(
                "recorded engine-variant identity is incomplete",
            ));
        }
        validate_component(self.search_policy, "search-policy")?;
        validate_component(self.evaluation_weights, "evaluation-weight")?;
        validate_optional_capability(self.opening_book, "opening-book")?;
        validate_optional_capability(self.tablebase, "tablebase")?;
        if self.checksum != self.computed_checksum() {
            return Err(ToolError::new(
                "recorded engine-variant identity checksum mismatch",
            ));
        }
        Ok(())
    }
}

/// Candidate color in one paired game.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum EngineVariantCandidateColor {
    /// Candidate plays White.
    White,
    /// Candidate plays Black.
    Black,
}

impl fmt::Display for EngineVariantCandidateColor {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::White => "white",
            Self::Black => "black",
        })
    }
}

impl FromStr for EngineVariantCandidateColor {
    type Err = ToolError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        match value {
            "white" => Ok(Self::White),
            "black" => Ok(Self::Black),
            _ => Err(ToolError::new(format!("invalid candidate color {value:?}"))),
        }
    }
}

/// Variant blamed by a typed game failure.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum EngineVariantFaultingSide {
    /// Baseline variant failed.
    Baseline,
    /// Candidate variant failed.
    Candidate,
    /// Infrastructure failed before one side could be blamed.
    Infrastructure,
}

impl fmt::Display for EngineVariantFaultingSide {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::Baseline => "baseline",
            Self::Candidate => "candidate",
            Self::Infrastructure => "infrastructure",
        })
    }
}

impl FromStr for EngineVariantFaultingSide {
    type Err = ToolError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        match value {
            "baseline" => Ok(Self::Baseline),
            "candidate" => Ok(Self::Candidate),
            "infrastructure" => Ok(Self::Infrastructure),
            _ => Err(ToolError::new(format!("invalid faulting side {value:?}"))),
        }
    }
}

/// Typed failure that is never silently converted into a chess score.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum EngineVariantGameFailure {
    /// Engine supplied an illegal move.
    IllegalMove {
        /// Variant responsible for the move.
        side: EngineVariantFaultingSide,
        /// Exact diagnostic.
        detail: String,
    },
    /// Engine search aborted or failed as a process-equivalent crash.
    Crash {
        /// Variant responsible for the failure.
        side: EngineVariantFaultingSide,
        /// Exact diagnostic.
        detail: String,
    },
    /// External clock protocol declared a forfeit.
    TimeForfeit {
        /// Variant responsible for the forfeit.
        side: EngineVariantFaultingSide,
        /// Exact diagnostic.
        detail: String,
    },
    /// Harness, allocation, I/O, or other non-chess infrastructure failed.
    Infrastructure {
        /// Exact diagnostic.
        detail: String,
    },
}

impl EngineVariantGameFailure {
    fn kind(&self) -> &'static str {
        match self {
            Self::IllegalMove { .. } => "illegal_move",
            Self::Crash { .. } => "crash",
            Self::TimeForfeit { .. } => "time_forfeit",
            Self::Infrastructure { .. } => "infrastructure_failure",
        }
    }

    fn side(&self) -> EngineVariantFaultingSide {
        match self {
            Self::IllegalMove { side, .. }
            | Self::Crash { side, .. }
            | Self::TimeForfeit { side, .. } => *side,
            Self::Infrastructure { .. } => EngineVariantFaultingSide::Infrastructure,
        }
    }

    fn detail(&self) -> &str {
        match self {
            Self::IllegalMove { detail, .. }
            | Self::Crash { detail, .. }
            | Self::TimeForfeit { detail, .. }
            | Self::Infrastructure { detail } => detail,
        }
    }
}

/// Completed chess result or typed non-chess failure.
#[derive(Clone, Debug, PartialEq)]
pub enum EngineVariantGameOutcome {
    /// Completed, drawn, or maximum-ply chess result.
    Completed {
        /// Absolute result.
        result: SelfPlayResult,
        /// Exact termination reason.
        termination: SelfPlayTermination,
        /// Candidate-relative score.
        candidate_score: f64,
        /// Complete move list after the opening.
        moves: Vec<String>,
        /// Final canonical FEN.
        final_fen: String,
    },
    /// Explicitly classified failure excluded from score statistics.
    Failure(EngineVariantGameFailure),
}

/// Replay and failure evidence for one game.
#[derive(Clone, Debug, PartialEq)]
pub struct EngineVariantValidationGame {
    /// Zero-based independent pair index.
    pub pair_index: u32,
    /// Deterministic pair seed.
    pub pair_seed: u64,
    /// Opening source identifier.
    pub opening_identifier: String,
    /// Candidate color.
    pub candidate_color: EngineVariantCandidateColor,
    /// Completed result or typed failure.
    pub outcome: EngineVariantGameOutcome,
}

/// Complete correctness pre-gate evidence.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct EngineVariantCorrectnessSummary {
    /// Maximum authoritative perft depth.
    pub perft_depth: u8,
    /// Number of perft fixture/depth comparisons.
    pub perft_cases: u32,
    /// Whether every perft count matched.
    pub perft_passed: bool,
    /// Number of forced-mate fixtures.
    pub forced_mate_cases: u32,
    /// Whether all forced-mate fixtures passed.
    pub forced_mate_passed: bool,
    /// Number of longest-survival fixtures.
    pub longest_survival_cases: u32,
    /// Whether all longest-survival fixtures passed.
    pub longest_survival_passed: bool,
    /// Number of candidate tactical/legal-PV fixtures.
    pub tactical_cases: u32,
    /// Whether all tactical/legal-PV fixtures passed.
    pub tactical_passed: bool,
    /// Number of repeated-search equivalence fixtures.
    pub equivalence_cases: u32,
    /// Whether all repeated-search equivalence fixtures passed.
    pub equivalence_passed: bool,
    /// Pre-gate infrastructure failures.
    pub infrastructure_failures: u32,
    /// Exact pre-gate failure diagnostic, or empty on success.
    pub failure_detail: String,
}

impl EngineVariantCorrectnessSummary {
    /// Returns whether all chess correctness checks passed.
    #[must_use]
    pub const fn passed(&self) -> bool {
        self.perft_passed
            && self.forced_mate_passed
            && self.longest_survival_passed
            && self.tactical_passed
            && self.equivalence_passed
            && self.infrastructure_failures == 0
    }
}

/// Fail-closed disposition of one report.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum EngineVariantValidationDecision {
    /// Correctness fixture failed before games.
    RejectedCorrectness,
    /// Harness or other non-chess infrastructure failed.
    InfrastructureFailure,
    /// Illegal move, crash, or time forfeit occurred.
    RejectedGameFailure,
    /// Too many games reached the maximum-ply boundary.
    RejectedUnfinishedRate,
    /// Statistical evidence did not strictly prove the required margin.
    RejectedStrength,
    /// Smoke tier passed but carries no activation authority.
    PassedSmoke,
    /// Development tier passed but carries no activation authority.
    PassedDevelopment,
    /// Production tier alone proved the required margin and may be reviewed for activation.
    AcceptedForActivation,
}

impl fmt::Display for EngineVariantValidationDecision {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::RejectedCorrectness => "rejected_correctness",
            Self::InfrastructureFailure => "infrastructure_failure",
            Self::RejectedGameFailure => "rejected_game_failure",
            Self::RejectedUnfinishedRate => "rejected_unfinished_rate",
            Self::RejectedStrength => "rejected_strength",
            Self::PassedSmoke => "passed_smoke",
            Self::PassedDevelopment => "passed_development",
            Self::AcceptedForActivation => "accepted_for_activation",
        })
    }
}

impl FromStr for EngineVariantValidationDecision {
    type Err = ToolError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        match value {
            "rejected_correctness" => Ok(Self::RejectedCorrectness),
            "infrastructure_failure" => Ok(Self::InfrastructureFailure),
            "rejected_game_failure" => Ok(Self::RejectedGameFailure),
            "rejected_unfinished_rate" => Ok(Self::RejectedUnfinishedRate),
            "rejected_strength" => Ok(Self::RejectedStrength),
            "passed_smoke" => Ok(Self::PassedSmoke),
            "passed_development" => Ok(Self::PassedDevelopment),
            "accepted_for_activation" => Ok(Self::AcceptedForActivation),
            _ => Err(ToolError::new(format!(
                "invalid engine-variant validation decision {value:?}"
            ))),
        }
    }
}

/// Versioned, checksummed complete engine-variant evidence.
#[derive(Clone, Debug, PartialEq)]
pub struct EngineVariantValidationReport {
    /// Fixed validation configuration.
    pub config: EngineVariantValidationConfig,
    /// Exact baseline identity.
    pub baseline: RecordedEngineVariantIdentity,
    /// Exact candidate identity.
    pub candidate: RecordedEngineVariantIdentity,
    /// Canonical opening-suite checksum.
    pub opening_suite_checksum: u64,
    /// Number of supplied opening lines.
    pub opening_count: u32,
    /// Correctness pre-gate evidence.
    pub correctness: EngineVariantCorrectnessSummary,
    /// Every scheduled paired game.
    pub games: Vec<EngineVariantValidationGame>,
    /// Candidate wins.
    pub candidate_wins: u32,
    /// Completed draws.
    pub draws: u32,
    /// Candidate losses.
    pub candidate_losses: u32,
    /// Maximum-ply unfinished games.
    pub unfinished: u32,
    /// Illegal-move failures.
    pub illegal_moves: u32,
    /// Crash-equivalent failures.
    pub crashes: u32,
    /// Time forfeits.
    pub time_forfeits: u32,
    /// Infrastructure failures.
    pub infrastructure_failures: u32,
    /// Mean candidate score over independent pair scores.
    pub mean_pair_score: f64,
    /// Sample standard error over independent pair scores.
    pub pair_score_standard_error: f64,
    /// One-sided 95% lower confidence bound.
    pub lower_confidence_bound: f64,
    /// Final fail-closed decision.
    pub decision: EngineVariantValidationDecision,
    /// Canonical semantic report checksum.
    pub checksum: u64,
}

impl EngineVariantValidationReport {
    /// Validation evidence never changes runtime defaults.
    #[must_use]
    pub const fn activated(&self) -> bool {
        false
    }

    /// Recomputes the complete semantic checksum.
    #[must_use]
    pub fn computed_checksum(&self) -> u64 {
        let mut hash = FNV_OFFSET;
        for value in [
            u64::from(ENGINE_VARIANT_VALIDATION_SCHEMA_VERSION),
            ENGINE_VARIANT_VALIDATION_IDENTIFIER,
            u64::from(self.config.pair_count),
            self.config.seed,
            self.config.transposition_table_mebibytes as u64,
            u64::from(self.config.maximum_plies),
            self.config.minimum_score_margin.to_bits(),
            u64::from(self.config.maximum_unfinished_per_mille),
            self.baseline.checksum,
            self.candidate.checksum,
            self.opening_suite_checksum,
            u64::from(self.opening_count),
            u64::from(self.correctness.perft_depth),
            u64::from(self.correctness.perft_cases),
            u64::from(self.correctness.forced_mate_cases),
            u64::from(self.correctness.longest_survival_cases),
            u64::from(self.correctness.tactical_cases),
            u64::from(self.correctness.equivalence_cases),
            u64::from(self.correctness.infrastructure_failures),
            u64::from(self.candidate_wins),
            u64::from(self.draws),
            u64::from(self.candidate_losses),
            u64::from(self.unfinished),
            u64::from(self.illegal_moves),
            u64::from(self.crashes),
            u64::from(self.time_forfeits),
            u64::from(self.infrastructure_failures),
            self.mean_pair_score.to_bits(),
            self.pair_score_standard_error.to_bits(),
            self.lower_confidence_bound.to_bits(),
        ] {
            hash = hash_bytes(hash, &value.to_le_bytes());
        }
        hash = hash_text(hash, &self.config.tier.to_string());
        hash = hash_text(hash, &self.config.protocol.to_string());
        hash = hash_text(hash, self.config.protocol.purpose());
        hash = hash_bytes(hash, &[self.config.check_extension as u8]);
        hash = hash_text(hash, &self.config.claimable_draw_policy.to_string());
        for passed in [
            self.correctness.perft_passed,
            self.correctness.forced_mate_passed,
            self.correctness.longest_survival_passed,
            self.correctness.tactical_passed,
            self.correctness.equivalence_passed,
        ] {
            hash = hash_bytes(hash, &[passed as u8]);
        }
        hash = hash_text(hash, &self.correctness.failure_detail);
        hash = hash_text(hash, &self.decision.to_string());
        hash = hash_bytes(hash, &[self.activated() as u8]);
        for game in &self.games {
            hash = hash_bytes(hash, &game.pair_index.to_le_bytes());
            hash = hash_bytes(hash, &game.pair_seed.to_le_bytes());
            hash = hash_text(hash, &game.opening_identifier);
            hash = hash_text(hash, &game.candidate_color.to_string());
            match &game.outcome {
                EngineVariantGameOutcome::Completed {
                    result,
                    termination,
                    candidate_score,
                    moves,
                    final_fen,
                } => {
                    hash = hash_text(hash, "completed");
                    hash = hash_text(hash, &result.to_string());
                    hash = hash_text(hash, &termination.to_string());
                    hash = hash_bytes(hash, &candidate_score.to_bits().to_le_bytes());
                    hash = hash_text(hash, &moves.join(" "));
                    hash = hash_text(hash, final_fen);
                }
                EngineVariantGameOutcome::Failure(failure) => {
                    hash = hash_text(hash, failure.kind());
                    hash = hash_text(hash, &failure.side().to_string());
                    hash = hash_text(hash, failure.detail());
                }
            }
        }
        hash
    }

    /// Validates identities, pairing, counts, statistics, decision, inactivity, and checksum.
    pub fn validate(&self) -> Result<(), ToolError> {
        self.config.validate()?;
        self.baseline.validate()?;
        self.candidate.validate()?;
        if self.baseline.checksum == self.candidate.checksum {
            return Err(ToolError::new(
                "baseline and candidate complete identities must differ",
            ));
        }
        let configured_tt = self.config.transposition_table_mebibytes as u64;
        if self.baseline.transposition_table_mebibytes != configured_tt
            || self.candidate.transposition_table_mebibytes != configured_tt
        {
            return Err(ToolError::new(
                "report TT configuration does not match both engine identities",
            ));
        }
        if self.opening_count == 0 || self.opening_suite_checksum == 0 {
            return Err(ToolError::new("variant opening provenance is empty"));
        }
        let expected_games = self.config.pair_count.saturating_mul(2) as usize;
        if self.correctness.passed() && self.games.len() != expected_games {
            return Err(ToolError::new(
                "successful correctness gate requires every scheduled paired game",
            ));
        }
        if !self.correctness.passed() && !self.games.is_empty() {
            return Err(ToolError::new(
                "games must not run after a failed correctness pre-gate",
            ));
        }
        if self.correctness.passed() {
            for pair_index in 0..self.config.pair_count {
                let pair = self
                    .games
                    .iter()
                    .filter(|game| game.pair_index == pair_index)
                    .collect::<Vec<_>>();
                if pair.len() != 2
                    || pair[0].candidate_color == pair[1].candidate_color
                    || pair[0].opening_identifier != pair[1].opening_identifier
                    || pair[0].pair_seed != pair[1].pair_seed
                {
                    return Err(ToolError::new(
                        "variant-validation pair is not exactly color-balanced",
                    ));
                }
            }
        }
        let counted = self
            .candidate_wins
            .saturating_add(self.draws)
            .saturating_add(self.candidate_losses)
            .saturating_add(self.unfinished)
            .saturating_add(self.illegal_moves)
            .saturating_add(self.crashes)
            .saturating_add(self.time_forfeits)
            .saturating_add(self.infrastructure_failures) as usize;
        if counted != self.games.len() {
            return Err(ToolError::new(
                "variant-validation outcome counts do not match game records",
            ));
        }
        let mut observed_wins = 0_u32;
        let mut observed_draws = 0_u32;
        let mut observed_losses = 0_u32;
        let mut observed_unfinished = 0_u32;
        let mut observed_illegal = 0_u32;
        let mut observed_crashes = 0_u32;
        let mut observed_time_forfeits = 0_u32;
        let mut observed_infrastructure = 0_u32;
        for game in &self.games {
            match &game.outcome {
                EngineVariantGameOutcome::Completed {
                    result,
                    candidate_score: score,
                    final_fen,
                    ..
                } => {
                    if !score.is_finite()
                        || score.to_bits()
                            != candidate_score(*result, game.candidate_color).to_bits()
                        || final_fen.is_empty()
                    {
                        return Err(ToolError::new(
                            "completed variant game has inconsistent score or final FEN",
                        ));
                    }
                    match result {
                        SelfPlayResult::WhiteWin | SelfPlayResult::BlackWin => {
                            let candidate_won = matches!(
                                (result, game.candidate_color),
                                (SelfPlayResult::WhiteWin, EngineVariantCandidateColor::White)
                                    | (
                                        SelfPlayResult::BlackWin,
                                        EngineVariantCandidateColor::Black
                                    )
                            );
                            if candidate_won {
                                observed_wins = observed_wins.saturating_add(1);
                            } else {
                                observed_losses = observed_losses.saturating_add(1);
                            }
                        }
                        SelfPlayResult::Draw => {
                            observed_draws = observed_draws.saturating_add(1);
                        }
                        SelfPlayResult::Unfinished => {
                            observed_unfinished = observed_unfinished.saturating_add(1);
                        }
                    }
                }
                EngineVariantGameOutcome::Failure(failure) => {
                    if failure.detail().is_empty() {
                        return Err(ToolError::new(
                            "variant game failure detail must not be empty",
                        ));
                    }
                    match failure {
                        EngineVariantGameFailure::IllegalMove { .. } => {
                            observed_illegal = observed_illegal.saturating_add(1);
                        }
                        EngineVariantGameFailure::Crash { .. } => {
                            observed_crashes = observed_crashes.saturating_add(1);
                        }
                        EngineVariantGameFailure::TimeForfeit { .. } => {
                            observed_time_forfeits = observed_time_forfeits.saturating_add(1);
                        }
                        EngineVariantGameFailure::Infrastructure { .. } => {
                            observed_infrastructure = observed_infrastructure.saturating_add(1);
                        }
                    }
                }
            }
        }
        if (
            observed_wins,
            observed_draws,
            observed_losses,
            observed_unfinished,
            observed_illegal,
            observed_crashes,
            observed_time_forfeits,
            observed_infrastructure,
        ) != (
            self.candidate_wins,
            self.draws,
            self.candidate_losses,
            self.unfinished,
            self.illegal_moves,
            self.crashes,
            self.time_forfeits,
            self.infrastructure_failures,
        ) {
            return Err(ToolError::new(
                "variant-validation recorded counts disagree with game outcomes",
            ));
        }
        for value in [
            self.mean_pair_score,
            self.pair_score_standard_error,
            self.lower_confidence_bound,
        ] {
            if !value.is_finite() {
                return Err(ToolError::new(
                    "variant-validation statistics must be finite",
                ));
            }
        }
        if self.correctness.passed()
            && self.illegal_moves == 0
            && self.crashes == 0
            && self.time_forfeits == 0
            && self.infrastructure_failures == 0
        {
            let pair_scores = collect_pair_scores(&self.games, self.config.pair_count)?;
            let (mean, standard_error, lower_bound) = summarize_pair_scores(&pair_scores)?;
            if self.mean_pair_score.to_bits() != mean.to_bits()
                || self.pair_score_standard_error.to_bits() != standard_error.to_bits()
                || self.lower_confidence_bound.to_bits() != lower_bound.to_bits()
            {
                return Err(ToolError::new(
                    "variant-validation statistics disagree with independent pair scores",
                ));
            }
        } else if self.mean_pair_score.to_bits() != 0.0_f64.to_bits()
            || self.pair_score_standard_error.to_bits() != 0.0_f64.to_bits()
            || self.lower_confidence_bound.to_bits() != 0.0_f64.to_bits()
        {
            return Err(ToolError::new(
                "failed variant validation must not retain score statistics",
            ));
        }
        if self.decision != self.expected_decision()? {
            return Err(ToolError::new(
                "variant-validation decision does not match fail-closed rules",
            ));
        }
        if self.decision == EngineVariantValidationDecision::AcceptedForActivation
            && self.config.tier != EngineVariantValidationTier::Production
        {
            return Err(ToolError::new(
                "only production reports may be accepted for activation",
            ));
        }
        if self.checksum != self.computed_checksum() {
            return Err(ToolError::new(
                "engine-variant validation checksum mismatch",
            ));
        }
        Ok(())
    }

    fn expected_decision(&self) -> Result<EngineVariantValidationDecision, ToolError> {
        if self.correctness.infrastructure_failures > 0 || self.infrastructure_failures > 0 {
            return Ok(EngineVariantValidationDecision::InfrastructureFailure);
        }
        if !self.correctness.passed() {
            return Ok(EngineVariantValidationDecision::RejectedCorrectness);
        }
        if self.illegal_moves > 0 || self.crashes > 0 || self.time_forfeits > 0 {
            return Ok(EngineVariantValidationDecision::RejectedGameFailure);
        }
        let unfinished_per_mille = if self.games.is_empty() {
            0
        } else {
            u64::from(self.unfinished) * 1_000 / self.games.len() as u64
        };
        if unfinished_per_mille > u64::from(self.config.maximum_unfinished_per_mille) {
            return Ok(EngineVariantValidationDecision::RejectedUnfinishedRate);
        }
        if self.lower_confidence_bound <= 0.5 + self.config.minimum_score_margin {
            return Ok(EngineVariantValidationDecision::RejectedStrength);
        }
        Ok(match self.config.tier {
            EngineVariantValidationTier::Smoke => EngineVariantValidationDecision::PassedSmoke,
            EngineVariantValidationTier::Development => {
                EngineVariantValidationDecision::PassedDevelopment
            }
            EngineVariantValidationTier::Production => {
                EngineVariantValidationDecision::AcceptedForActivation
            }
        })
    }

    /// Serializes deterministic strict line-oriented evidence.
    pub fn serialize(&self) -> Result<String, ToolError> {
        self.validate()?;
        let mut output = String::new();
        line(&mut output, FORMAT_MARKER);
        field(
            &mut output,
            "schema",
            ENGINE_VARIANT_VALIDATION_SCHEMA_VERSION,
        );
        hex_field(
            &mut output,
            "report_identifier",
            ENGINE_VARIANT_VALIDATION_IDENTIFIER,
        );
        field(&mut output, "tier", self.config.tier);
        field(&mut output, "pair_count", self.config.pair_count);
        field(&mut output, "seed", self.config.seed);
        field(&mut output, "protocol", self.config.protocol);
        text_field(
            &mut output,
            "protocol_purpose",
            self.config.protocol.purpose(),
        );
        field(
            &mut output,
            "transposition_table_mebibytes",
            self.config.transposition_table_mebibytes,
        );
        field(&mut output, "check_extension", self.config.check_extension);
        field(&mut output, "maximum_plies", self.config.maximum_plies);
        field(
            &mut output,
            "claimable_draw_policy",
            self.config.claimable_draw_policy,
        );
        float_bits_field(
            &mut output,
            "minimum_score_margin",
            self.config.minimum_score_margin,
        );
        field(
            &mut output,
            "maximum_unfinished_per_mille",
            self.config.maximum_unfinished_per_mille,
        );
        serialize_identity(&mut output, "baseline", &self.baseline);
        serialize_identity(&mut output, "candidate", &self.candidate);
        hex_field(
            &mut output,
            "opening_suite_checksum",
            self.opening_suite_checksum,
        );
        field(&mut output, "opening_count", self.opening_count);
        field(&mut output, "perft_depth", self.correctness.perft_depth);
        field(&mut output, "perft_cases", self.correctness.perft_cases);
        field(&mut output, "perft_passed", self.correctness.perft_passed);
        field(
            &mut output,
            "forced_mate_cases",
            self.correctness.forced_mate_cases,
        );
        field(
            &mut output,
            "forced_mate_passed",
            self.correctness.forced_mate_passed,
        );
        field(
            &mut output,
            "longest_survival_cases",
            self.correctness.longest_survival_cases,
        );
        field(
            &mut output,
            "longest_survival_passed",
            self.correctness.longest_survival_passed,
        );
        field(
            &mut output,
            "tactical_cases",
            self.correctness.tactical_cases,
        );
        field(
            &mut output,
            "tactical_passed",
            self.correctness.tactical_passed,
        );
        field(
            &mut output,
            "equivalence_cases",
            self.correctness.equivalence_cases,
        );
        field(
            &mut output,
            "equivalence_passed",
            self.correctness.equivalence_passed,
        );
        field(
            &mut output,
            "correctness_infrastructure_failures",
            self.correctness.infrastructure_failures,
        );
        text_field(
            &mut output,
            "correctness_failure_detail",
            &self.correctness.failure_detail,
        );
        field(&mut output, "game_count", self.games.len());
        field(&mut output, "candidate_wins", self.candidate_wins);
        field(&mut output, "draws", self.draws);
        field(&mut output, "candidate_losses", self.candidate_losses);
        field(&mut output, "unfinished", self.unfinished);
        field(&mut output, "illegal_moves", self.illegal_moves);
        field(&mut output, "crashes", self.crashes);
        field(&mut output, "time_forfeits", self.time_forfeits);
        field(
            &mut output,
            "infrastructure_failures",
            self.infrastructure_failures,
        );
        float_bits_field(&mut output, "mean_pair_score", self.mean_pair_score);
        float_bits_field(
            &mut output,
            "pair_score_standard_error",
            self.pair_score_standard_error,
        );
        float_bits_field(
            &mut output,
            "lower_confidence_bound",
            self.lower_confidence_bound,
        );
        field(&mut output, "decision", self.decision);
        field(&mut output, "activated", self.activated());
        for (index, game) in self.games.iter().enumerate() {
            serialize_game(&mut output, index, game);
        }
        hex_field(&mut output, "checksum", self.checksum);
        Ok(output)
    }

    /// Parses and fully validates one strict report.
    pub fn deserialize(text: &str) -> Result<Self, ToolError> {
        let mut reader = ReportReader::new(text);
        reader.expect_line(FORMAT_MARKER)?;
        let schema = reader.parse_field::<u16>("schema")?;
        if schema != ENGINE_VARIANT_VALIDATION_SCHEMA_VERSION {
            return Err(ToolError::new(format!(
                "unsupported engine-variant report schema {schema}"
            )));
        }
        let identifier = reader.parse_hex_field("report_identifier")?;
        if identifier != ENGINE_VARIANT_VALIDATION_IDENTIFIER {
            return Err(ToolError::new("engine-variant report identifier mismatch"));
        }
        let tier = reader.parse_field("tier")?;
        let pair_count = reader.parse_field("pair_count")?;
        let seed = reader.parse_field("seed")?;
        let protocol: EngineVariantResourceProtocol = reader.parse_field("protocol")?;
        let protocol_purpose = reader.parse_text_field("protocol_purpose")?;
        if protocol_purpose != protocol.purpose() {
            return Err(ToolError::new("resource protocol purpose mismatch"));
        }
        let transposition_table_mebibytes = reader.parse_field("transposition_table_mebibytes")?;
        let check_extension = reader.parse_bool_field("check_extension")?;
        let maximum_plies = reader.parse_field("maximum_plies")?;
        let claimable_draw_policy = reader.parse_field("claimable_draw_policy")?;
        let minimum_score_margin = reader.parse_float_bits_field("minimum_score_margin")?;
        let maximum_unfinished_per_mille = reader.parse_field("maximum_unfinished_per_mille")?;
        let config = EngineVariantValidationConfig {
            tier,
            pair_count,
            seed,
            protocol,
            transposition_table_mebibytes,
            check_extension,
            maximum_plies,
            claimable_draw_policy,
            minimum_score_margin,
            maximum_unfinished_per_mille,
        };
        config.validate()?;
        let baseline = deserialize_identity(&mut reader, "baseline")?;
        let candidate = deserialize_identity(&mut reader, "candidate")?;
        let opening_suite_checksum = reader.parse_hex_field("opening_suite_checksum")?;
        let opening_count = reader.parse_field("opening_count")?;
        let correctness = EngineVariantCorrectnessSummary {
            perft_depth: reader.parse_field("perft_depth")?,
            perft_cases: reader.parse_field("perft_cases")?,
            perft_passed: reader.parse_bool_field("perft_passed")?,
            forced_mate_cases: reader.parse_field("forced_mate_cases")?,
            forced_mate_passed: reader.parse_bool_field("forced_mate_passed")?,
            longest_survival_cases: reader.parse_field("longest_survival_cases")?,
            longest_survival_passed: reader.parse_bool_field("longest_survival_passed")?,
            tactical_cases: reader.parse_field("tactical_cases")?,
            tactical_passed: reader.parse_bool_field("tactical_passed")?,
            equivalence_cases: reader.parse_field("equivalence_cases")?,
            equivalence_passed: reader.parse_bool_field("equivalence_passed")?,
            infrastructure_failures: reader.parse_field("correctness_infrastructure_failures")?,
            failure_detail: reader.parse_text_field("correctness_failure_detail")?,
        };
        let game_count = reader.parse_field::<usize>("game_count")?;
        let candidate_wins = reader.parse_field("candidate_wins")?;
        let draws = reader.parse_field("draws")?;
        let candidate_losses = reader.parse_field("candidate_losses")?;
        let unfinished = reader.parse_field("unfinished")?;
        let illegal_moves = reader.parse_field("illegal_moves")?;
        let crashes = reader.parse_field("crashes")?;
        let time_forfeits = reader.parse_field("time_forfeits")?;
        let infrastructure_failures = reader.parse_field("infrastructure_failures")?;
        let mean_pair_score = reader.parse_float_bits_field("mean_pair_score")?;
        let pair_score_standard_error =
            reader.parse_float_bits_field("pair_score_standard_error")?;
        let lower_confidence_bound = reader.parse_float_bits_field("lower_confidence_bound")?;
        let decision = reader.parse_field("decision")?;
        if reader.parse_bool_field("activated")? {
            return Err(ToolError::new(
                "engine-variant validation reports must remain inactive",
            ));
        }
        let mut games = Vec::new();
        games
            .try_reserve_exact(game_count)
            .map_err(|_| ToolError::new("failed to reserve report game records"))?;
        for index in 0..game_count {
            games.push(deserialize_game(&mut reader, index)?);
        }
        let checksum = reader.parse_hex_field("checksum")?;
        reader.finish()?;
        let report = Self {
            config,
            baseline,
            candidate,
            opening_suite_checksum,
            opening_count,
            correctness,
            games,
            candidate_wins,
            draws,
            candidate_losses,
            unfinished,
            illegal_moves,
            crashes,
            time_forfeits,
            infrastructure_failures,
            mean_pair_score,
            pair_score_standard_error,
            lower_confidence_bound,
            decision,
            checksum,
        };
        report.validate()?;
        Ok(report)
    }
}

/// Runs the complete S2-2 protocol with authoritative depth-four perft.
pub fn run_engine_variant_validation(
    config: EngineVariantValidationConfig,
    openings: &OpeningSuite,
    baseline: EngineVariantRuntime<'_>,
    candidate: EngineVariantRuntime<'_>,
) -> Result<EngineVariantValidationReport, ToolError> {
    run_engine_variant_validation_internal(
        config,
        openings,
        baseline,
        candidate,
        VARIANT_VALIDATION_PERFT_DEPTH,
    )
}

fn run_engine_variant_validation_internal(
    config: EngineVariantValidationConfig,
    openings: &OpeningSuite,
    baseline: EngineVariantRuntime<'_>,
    candidate: EngineVariantRuntime<'_>,
    perft_depth: u8,
) -> Result<EngineVariantValidationReport, ToolError> {
    config.validate()?;
    baseline.validate()?;
    candidate.validate()?;
    if baseline.identity.checksum() == candidate.identity.checksum() {
        return Err(ToolError::new(
            "baseline and candidate complete identities must differ",
        ));
    }
    let configured_tt = config.transposition_table_mebibytes as u64;
    if baseline.identity.transposition_table_mebibytes() != configured_tt
        || candidate.identity.transposition_table_mebibytes() != configured_tt
    {
        return Err(ToolError::new(
            "configured TT size must match both complete variant identities",
        ));
    }
    validate_openings(config, openings)?;
    let opening_suite_checksum = opening_suite_checksum(openings);
    let opening_count = u32::try_from(openings.lines().len())
        .map_err(|_| ToolError::new("opening count exceeds u32"))?;
    let correctness = run_correctness_suite(candidate, config, perft_depth);
    let mut report = EngineVariantValidationReport {
        config,
        baseline: RecordedEngineVariantIdentity::from_identity(baseline.identity),
        candidate: RecordedEngineVariantIdentity::from_identity(candidate.identity),
        opening_suite_checksum,
        opening_count,
        correctness,
        games: Vec::new(),
        candidate_wins: 0,
        draws: 0,
        candidate_losses: 0,
        unfinished: 0,
        illegal_moves: 0,
        crashes: 0,
        time_forfeits: 0,
        infrastructure_failures: 0,
        mean_pair_score: 0.0,
        pair_score_standard_error: 0.0,
        lower_confidence_bound: 0.0,
        decision: EngineVariantValidationDecision::RejectedCorrectness,
        checksum: 0,
    };
    if !report.correctness.passed() {
        report.decision = report.expected_decision()?;
        report.checksum = report.computed_checksum();
        report.validate()?;
        return Ok(report);
    }

    let opening_offset = (splitmix64(config.seed) % openings.lines().len() as u64) as usize;
    report
        .games
        .try_reserve_exact(config.pair_count.saturating_mul(2) as usize)
        .map_err(|_| ToolError::new("failed to reserve variant match game records"))?;
    for pair_index in 0..config.pair_count {
        let opening =
            &openings.lines()[(opening_offset + pair_index as usize) % openings.lines().len()];
        let pair_seed = splitmix64(config.seed ^ u64::from(pair_index));
        let white = play_variant_game(
            opening,
            config,
            baseline,
            candidate,
            EngineVariantCandidateColor::White,
        );
        let black = play_variant_game(
            opening,
            config,
            baseline,
            candidate,
            EngineVariantCandidateColor::Black,
        );
        append_game(
            &mut report,
            pair_index,
            pair_seed,
            opening.identifier(),
            EngineVariantCandidateColor::White,
            white,
        )?;
        append_game(
            &mut report,
            pair_index,
            pair_seed,
            opening.identifier(),
            EngineVariantCandidateColor::Black,
            black,
        )?;
    }
    let pair_scores = collect_pair_scores(&report.games, config.pair_count)?;
    if pair_scores.len() == config.pair_count as usize {
        let (mean, standard_error, lower_bound) = summarize_pair_scores(&pair_scores)?;
        report.mean_pair_score = mean;
        report.pair_score_standard_error = standard_error;
        report.lower_confidence_bound = lower_bound;
    }
    report.decision = report.expected_decision()?;
    report.checksum = report.computed_checksum();
    report.validate()?;
    Ok(report)
}

/// Writes evidence atomically through caller-selected same-directory paths.
pub fn write_engine_variant_validation_report_atomic(
    destination: &Path,
    temporary: &Path,
    report: &EngineVariantValidationReport,
) -> Result<(), ToolError> {
    if destination == temporary
        || destination.parent().unwrap_or_else(|| Path::new("."))
            != temporary.parent().unwrap_or_else(|| Path::new("."))
    {
        return Err(ToolError::new(
            "variant report destination and temporary paths must differ and share one directory",
        ));
    }
    let text = report.serialize()?;
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(temporary)
        .map_err(|error| {
            ToolError::new(format!(
                "failed to create temporary variant report {}: {error}",
                temporary.display()
            ))
        })?;
    if let Err(error) = file
        .write_all(text.as_bytes())
        .and_then(|()| file.flush())
        .and_then(|()| file.sync_all())
    {
        drop(file);
        let _ = fs::remove_file(temporary);
        return Err(ToolError::new(format!(
            "failed to write temporary variant report {}: {error}",
            temporary.display()
        )));
    }
    drop(file);
    if let Err(error) = fs::rename(temporary, destination) {
        let _ = fs::remove_file(temporary);
        return Err(ToolError::new(format!(
            "failed to rename variant report {}: {error}",
            destination.display()
        )));
    }
    Ok(())
}

fn validate_openings(
    config: EngineVariantValidationConfig,
    openings: &OpeningSuite,
) -> Result<(), ToolError> {
    if openings.lines().is_empty() {
        return Err(ToolError::new("variant validation opening suite is empty"));
    }
    let required = usize::try_from(config.pair_count)
        .map_err(|_| ToolError::new("variant pair count exceeds usize"))?;
    if openings.lines().len() < required {
        return Err(ToolError::new(format!(
            "variant validation requires at least one distinct opening per pair: {} pairs but only {} openings",
            config.pair_count,
            openings.lines().len()
        )));
    }
    let mut semantic = HashSet::with_capacity(openings.lines().len());
    for opening in openings.lines() {
        let key = (opening.initial_fen().to_owned(), opening.moves().to_vec());
        if !semantic.insert(key) {
            return Err(ToolError::new(
                "variant validation opening suite contains duplicate semantic openings",
            ));
        }
        if opening.moves().len() as u32 >= config.maximum_plies {
            return Err(ToolError::new(format!(
                "opening {:?} reaches the maximum-ply boundary",
                opening.identifier()
            )));
        }
    }
    Ok(())
}

fn run_correctness_suite(
    candidate: EngineVariantRuntime<'_>,
    config: EngineVariantValidationConfig,
    perft_depth: u8,
) -> EngineVariantCorrectnessSummary {
    let mut summary = EngineVariantCorrectnessSummary {
        perft_depth,
        perft_cases: 0,
        perft_passed: true,
        forced_mate_cases: 1,
        forced_mate_passed: false,
        longest_survival_cases: 1,
        longest_survival_passed: false,
        tactical_cases: 1,
        tactical_passed: false,
        equivalence_cases: 1,
        equivalence_passed: false,
        infrastructure_failures: 0,
        failure_detail: String::new(),
    };
    let result = (|| -> Result<(), ToolError> {
        if !(1..=5).contains(&perft_depth) {
            return Err(ToolError::new(
                "variant perft depth must be between one and five",
            ));
        }
        for fixture in perft_fixtures()? {
            for depth in 1..=perft_depth {
                let expected = fixture.expected[usize::from(depth - 1)];
                let actual = perft(fixture.fen, depth)?;
                summary.perft_cases = summary
                    .perft_cases
                    .checked_add(1)
                    .ok_or_else(|| ToolError::new("variant perft case count overflow"))?;
                summary.perft_passed &= actual == expected;
            }
        }
        summary.forced_mate_passed = fixture_selects_one_of(
            "7k/5Q2/6K1/8/8/8/8/8 w - - 0 1",
            3,
            &["f7e8", "f7f8", "f7g7", "f7h7"],
            candidate,
            config,
        )?;
        summary.longest_survival_passed = fixture_selects_one_of(
            "4Q2k/8/4K3/8/8/8/8/8 b - - 0 1",
            6,
            &["h8g7"],
            candidate,
            config,
        )?;
        summary.tactical_passed =
            fixture_produces_legal_pv("7k/P7/6K1/8/8/8/8/8 w - - 0 1", 2, candidate, config)?;
        summary.equivalence_passed = repeated_search_is_equivalent(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            2,
            candidate,
            config,
        )?;
        Ok(())
    })();
    if let Err(error) = result {
        summary.infrastructure_failures = 1;
        summary.failure_detail = error.to_string();
    }
    summary
}

fn fixture_selects_one_of(
    fen: &str,
    depth: u16,
    acceptable: &[&str],
    runtime: EngineVariantRuntime<'_>,
    config: EngineVariantValidationConfig,
) -> Result<bool, ToolError> {
    let result = search_fixture(fen, depth, runtime, config)?;
    Ok(result
        .best_move()
        .map(|current| current.to_uci())
        .as_deref()
        .is_some_and(|value| acceptable.contains(&value)))
}

fn fixture_produces_legal_pv(
    fen: &str,
    depth: u16,
    runtime: EngineVariantRuntime<'_>,
    config: EngineVariantValidationConfig,
) -> Result<bool, ToolError> {
    let mut position =
        Position::from_fen(fen).map_err(|error| ToolError::new(error.to_string()))?;
    let original = position.clone();
    let result = search_fixture(fen, depth, runtime, config)?;
    let Some(current) = result.best_move() else {
        return Ok(false);
    };
    let legal = position
        .legal_moves()
        .map_err(|error| ToolError::new(error.to_string()))?;
    let is_legal = legal.iter().any(|candidate| candidate == current);
    Ok(is_legal && position == original)
}

fn repeated_search_is_equivalent(
    fen: &str,
    depth: u16,
    runtime: EngineVariantRuntime<'_>,
    config: EngineVariantValidationConfig,
) -> Result<bool, ToolError> {
    let first = search_fixture(fen, depth, runtime, config)?;
    let second = search_fixture(fen, depth, runtime, config)?;
    Ok(first.best_move() == second.best_move()
        && first.score() == second.score()
        && first.completed_depth() == second.completed_depth()
        && first.nodes() == second.nodes()
        && first.qnodes() == second.qnodes()
        && first.selective_depth() == second.selective_depth())
}

fn search_fixture(
    fen: &str,
    depth: u16,
    runtime: EngineVariantRuntime<'_>,
    config: EngineVariantValidationConfig,
) -> Result<chess_search::SearchResult, ToolError> {
    let mut position =
        Position::from_fen(fen).map_err(|error| ToolError::new(error.to_string()))?;
    let mut history = SearchHistory::from_position(&position);
    let mut table = TranspositionTable::new(config.transposition_table_mebibytes)
        .map_err(|error| ToolError::new(error.to_string()))?;
    iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights(
        &mut position,
        &mut history,
        SearchLimits::new().with_depth(depth),
        &mut table,
        runtime.search_policy,
        &runtime.evaluation_weights.weights,
    )
    .map_err(|error| ToolError::new(error.to_string()))
}

fn play_variant_game(
    opening: &OpeningLine,
    config: EngineVariantValidationConfig,
    baseline: EngineVariantRuntime<'_>,
    candidate: EngineVariantRuntime<'_>,
    candidate_color: EngineVariantCandidateColor,
) -> EngineVariantGameOutcome {
    match play_variant_game_internal(opening, config, baseline, candidate, candidate_color) {
        Ok(outcome) => outcome,
        Err(failure) => EngineVariantGameOutcome::Failure(failure),
    }
}

fn play_variant_game_internal(
    opening: &OpeningLine,
    config: EngineVariantValidationConfig,
    baseline: EngineVariantRuntime<'_>,
    candidate: EngineVariantRuntime<'_>,
    candidate_color: EngineVariantCandidateColor,
) -> Result<EngineVariantGameOutcome, EngineVariantGameFailure> {
    let mut game =
        instantiate_opening(opening).map_err(|error| EngineVariantGameFailure::Infrastructure {
            detail: error.to_string(),
        })?;
    let mut white_table =
        TranspositionTable::new(config.transposition_table_mebibytes).map_err(|error| {
            EngineVariantGameFailure::Infrastructure {
                detail: error.to_string(),
            }
        })?;
    let mut black_table =
        TranspositionTable::new(config.transposition_table_mebibytes).map_err(|error| {
            EngineVariantGameFailure::Infrastructure {
                detail: error.to_string(),
            }
        })?;
    let (result, termination) = loop {
        let status = game
            .status()
            .map_err(|error| EngineVariantGameFailure::Infrastructure {
                detail: error.to_string(),
            })?;
        if let Some(completed) = completed_status(status, config.claimable_draw_policy) {
            break completed;
        }
        let ply_count = u32::try_from(game.ply_count()).map_err(|_| {
            EngineVariantGameFailure::Infrastructure {
                detail: "game ply count exceeds u32".to_owned(),
            }
        })?;
        if ply_count >= config.maximum_plies {
            break (
                SelfPlayResult::Unfinished,
                SelfPlayTermination::MaximumPly(config.maximum_plies),
            );
        }
        let color = game.position().side_to_move();
        let candidate_to_move = matches!(
            (candidate_color, color),
            (EngineVariantCandidateColor::White, Color::White)
                | (EngineVariantCandidateColor::Black, Color::Black)
        );
        let runtime = if candidate_to_move {
            candidate
        } else {
            baseline
        };
        let faulting_side = if candidate_to_move {
            EngineVariantFaultingSide::Candidate
        } else {
            EngineVariantFaultingSide::Baseline
        };
        let table = match color {
            Color::White => &mut white_table,
            Color::Black => &mut black_table,
        };
        let mut position = game.position().clone();
        let mut history = game.search_history();
        let search =
            iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights(
                &mut position,
                &mut history,
                config.protocol.search_limits(config.check_extension),
                table,
                runtime.search_policy,
                &runtime.evaluation_weights.weights,
            )
            .map_err(|error| EngineVariantGameFailure::Crash {
                side: faulting_side,
                detail: error.to_string(),
            })?;
        let current = search
            .best_move()
            .ok_or_else(|| EngineVariantGameFailure::Crash {
                side: faulting_side,
                detail: format!("nonterminal position at ply {ply_count} produced no move"),
            })?;
        game.make_move(current)
            .map_err(|error| EngineVariantGameFailure::IllegalMove {
                side: faulting_side,
                detail: error.to_string(),
            })?;
    };
    let candidate_score = candidate_score(result, candidate_color);
    Ok(EngineVariantGameOutcome::Completed {
        result,
        termination,
        candidate_score,
        moves: game
            .moves()
            .iter()
            .map(|current| current.to_uci())
            .collect(),
        final_fen: game.position().to_fen(),
    })
}

fn instantiate_opening(opening: &OpeningLine) -> Result<Game, ToolError> {
    let position = Position::from_fen(opening.initial_fen())
        .map_err(|error| ToolError::new(error.to_string()))?;
    let mut game = Game::new(position);
    for value in opening.moves() {
        let syntax = value
            .parse::<UciMove>()
            .map_err(|error| ToolError::new(error.to_string()))?;
        let mut position = game.position().clone();
        let legal = position
            .legal_moves()
            .map_err(|error| ToolError::new(error.to_string()))?;
        let mut matches = legal.iter().filter(|current| syntax.matches(*current));
        let current = matches
            .next()
            .ok_or_else(|| ToolError::new(format!("opening move {value} is not legal")))?;
        if matches.next().is_some() {
            return Err(ToolError::new(format!(
                "opening move {value} resolved ambiguously"
            )));
        }
        game.make_move(current)
            .map_err(|error| ToolError::new(error.to_string()))?;
    }
    Ok(game)
}

fn append_game(
    report: &mut EngineVariantValidationReport,
    pair_index: u32,
    pair_seed: u64,
    opening_identifier: &str,
    candidate_color: EngineVariantCandidateColor,
    outcome: EngineVariantGameOutcome,
) -> Result<(), ToolError> {
    match &outcome {
        EngineVariantGameOutcome::Completed { result, .. } => match result {
            SelfPlayResult::WhiteWin | SelfPlayResult::BlackWin => {
                let candidate_won = matches!(
                    (result, candidate_color),
                    (SelfPlayResult::WhiteWin, EngineVariantCandidateColor::White)
                        | (SelfPlayResult::BlackWin, EngineVariantCandidateColor::Black)
                );
                if candidate_won {
                    increment(&mut report.candidate_wins, "candidate win")?;
                } else {
                    increment(&mut report.candidate_losses, "candidate loss")?;
                }
            }
            SelfPlayResult::Draw => increment(&mut report.draws, "draw")?,
            SelfPlayResult::Unfinished => increment(&mut report.unfinished, "unfinished")?,
        },
        EngineVariantGameOutcome::Failure(failure) => match failure {
            EngineVariantGameFailure::IllegalMove { .. } => {
                increment(&mut report.illegal_moves, "illegal move")?
            }
            EngineVariantGameFailure::Crash { .. } => increment(&mut report.crashes, "crash")?,
            EngineVariantGameFailure::TimeForfeit { .. } => {
                increment(&mut report.time_forfeits, "time forfeit")?
            }
            EngineVariantGameFailure::Infrastructure { .. } => increment(
                &mut report.infrastructure_failures,
                "infrastructure failure",
            )?,
        },
    }
    report.games.push(EngineVariantValidationGame {
        pair_index,
        pair_seed,
        opening_identifier: opening_identifier.to_owned(),
        candidate_color,
        outcome,
    });
    Ok(())
}

fn increment(value: &mut u32, label: &str) -> Result<(), ToolError> {
    *value = value
        .checked_add(1)
        .ok_or_else(|| ToolError::new(format!("{label} count overflow")))?;
    Ok(())
}

fn collect_pair_scores(
    games: &[EngineVariantValidationGame],
    pair_count: u32,
) -> Result<Vec<f64>, ToolError> {
    let mut scores = Vec::with_capacity(pair_count as usize);
    for pair_index in 0..pair_count {
        let pair = games
            .iter()
            .filter(|game| game.pair_index == pair_index)
            .collect::<Vec<_>>();
        if pair.len() != 2 {
            return Err(ToolError::new("variant pair does not contain two games"));
        }
        let mut total = 0.0;
        for game in pair {
            let EngineVariantGameOutcome::Completed {
                candidate_score, ..
            } = &game.outcome
            else {
                return Ok(Vec::new());
            };
            total += candidate_score;
        }
        scores.push(total * 0.5);
    }
    Ok(scores)
}

fn summarize_pair_scores(scores: &[f64]) -> Result<(f64, f64, f64), ToolError> {
    if scores.is_empty() || scores.iter().any(|score| !score.is_finite()) {
        return Err(ToolError::new("pair scores must be finite and non-empty"));
    }
    let mean = scores.iter().sum::<f64>() / scores.len() as f64;
    let standard_error = if scores.len() <= 1 {
        0.0
    } else {
        let squared = scores
            .iter()
            .map(|score| {
                let difference = *score - mean;
                difference * difference
            })
            .sum::<f64>();
        let sample_variance = squared / (scores.len() - 1) as f64;
        (sample_variance / scores.len() as f64).sqrt()
    };
    Ok((
        mean,
        standard_error,
        mean - VARIANT_ONE_SIDED_95_PERCENT_Z * standard_error,
    ))
}

fn candidate_score(result: SelfPlayResult, candidate_color: EngineVariantCandidateColor) -> f64 {
    match result {
        SelfPlayResult::WhiteWin => {
            if candidate_color == EngineVariantCandidateColor::White {
                1.0
            } else {
                0.0
            }
        }
        SelfPlayResult::BlackWin => {
            if candidate_color == EngineVariantCandidateColor::Black {
                1.0
            } else {
                0.0
            }
        }
        SelfPlayResult::Draw | SelfPlayResult::Unfinished => 0.5,
    }
}

fn completed_status(
    status: GameStatus,
    policy: ClaimableDrawPolicy,
) -> Option<(SelfPlayResult, SelfPlayTermination)> {
    match status {
        GameStatus::Ongoing => None,
        GameStatus::Checkmate { winner } => Some((
            result_for_winner(winner),
            SelfPlayTermination::Checkmate(winner),
        )),
        GameStatus::Stalemate => Some((SelfPlayResult::Draw, SelfPlayTermination::Stalemate)),
        GameStatus::AutomaticDraw(reason) => Some((
            SelfPlayResult::Draw,
            SelfPlayTermination::AutomaticDraw(reason),
        )),
        GameStatus::ClaimableDraw(reason) => match policy {
            ClaimableDrawPolicy::Accept => Some((
                SelfPlayResult::Draw,
                SelfPlayTermination::ClaimedDraw(reason),
            )),
            ClaimableDrawPolicy::Continue => None,
        },
    }
}

fn result_for_winner(winner: Color) -> SelfPlayResult {
    match winner {
        Color::White => SelfPlayResult::WhiteWin,
        Color::Black => SelfPlayResult::BlackWin,
    }
}

fn opening_suite_checksum(openings: &OpeningSuite) -> u64 {
    let mut hash = FNV_OFFSET;
    for opening in openings.lines() {
        hash = hash_text(hash, opening.identifier());
        hash = hash_text(hash, opening.initial_fen());
        for current in opening.moves() {
            hash = hash_text(hash, current);
        }
    }
    hash
}

fn splitmix64(seed: u64) -> u64 {
    let mut value = seed.wrapping_add(0x9e37_79b9_7f4a_7c15);
    value = (value ^ (value >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
    value = (value ^ (value >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
    value ^ (value >> 31)
}

fn validate_component(identity: SemanticComponentIdentity, name: &str) -> Result<(), ToolError> {
    if identity.schema_version == 0 || identity.identifier == 0 || identity.checksum == 0 {
        return Err(ToolError::new(format!(
            "recorded {name} identity is incomplete"
        )));
    }
    Ok(())
}

fn validate_optional_capability(
    identity: OptionalCapabilityIdentity,
    name: &str,
) -> Result<(), ToolError> {
    match identity {
        OptionalCapabilityIdentity::Disabled => Ok(()),
        OptionalCapabilityIdentity::Enabled {
            implementation_identifier,
            data_identifier,
            checksum,
        } if implementation_identifier != 0 && data_identifier != 0 && checksum != 0 => Ok(()),
        OptionalCapabilityIdentity::Enabled { .. } => Err(ToolError::new(format!(
            "recorded enabled {name} identity is incomplete"
        ))),
    }
}

fn hash_component(mut hash: u64, identity: SemanticComponentIdentity) -> u64 {
    hash = hash_bytes(hash, &identity.schema_version.to_le_bytes());
    hash = hash_bytes(hash, &identity.identifier.to_le_bytes());
    hash_bytes(hash, &identity.checksum.to_le_bytes())
}

fn hash_optional_capability(mut hash: u64, identity: OptionalCapabilityIdentity) -> u64 {
    match identity {
        OptionalCapabilityIdentity::Disabled => hash_bytes(hash, &[0]),
        OptionalCapabilityIdentity::Enabled {
            implementation_identifier,
            data_identifier,
            checksum,
        } => {
            hash = hash_bytes(hash, &[1]);
            hash = hash_bytes(hash, &implementation_identifier.to_le_bytes());
            hash = hash_bytes(hash, &data_identifier.to_le_bytes());
            hash_bytes(hash, &checksum.to_le_bytes())
        }
    }
}

fn serialize_identity(output: &mut String, prefix: &str, identity: &RecordedEngineVariantIdentity) {
    field(output, &format!("{prefix}.schema"), identity.schema_version);
    hex_field(output, &format!("{prefix}.identifier"), identity.identifier);
    field(
        output,
        &format!("{prefix}.source_commit"),
        encode_hex(&identity.source_commit),
    );
    text_field(
        output,
        &format!("{prefix}.engine_version"),
        &identity.engine_version,
    );
    serialize_component(output, &format!("{prefix}.policy"), identity.search_policy);
    serialize_component(
        output,
        &format!("{prefix}.weights"),
        identity.evaluation_weights,
    );
    field(
        output,
        &format!("{prefix}.opening_book"),
        capability_token(identity.opening_book),
    );
    field(
        output,
        &format!("{prefix}.tablebase"),
        capability_token(identity.tablebase),
    );
    field(
        output,
        &format!("{prefix}.transposition_table_mebibytes"),
        identity.transposition_table_mebibytes,
    );
    text_field(
        output,
        &format!("{prefix}.build_identity"),
        &identity.build_identity,
    );
    text_field(
        output,
        &format!("{prefix}.exact_invocation"),
        &identity.exact_invocation,
    );
    hex_field(output, &format!("{prefix}.checksum"), identity.checksum);
}

fn deserialize_identity(
    reader: &mut ReportReader<'_>,
    prefix: &str,
) -> Result<RecordedEngineVariantIdentity, ToolError> {
    let identity = RecordedEngineVariantIdentity {
        schema_version: reader.parse_field(&format!("{prefix}.schema"))?,
        identifier: reader.parse_hex_field(&format!("{prefix}.identifier"))?,
        source_commit: decode_commit(&reader.take(&format!("{prefix}.source_commit"))?)?,
        engine_version: reader.parse_text_field(&format!("{prefix}.engine_version"))?,
        search_policy: deserialize_component(reader, &format!("{prefix}.policy"))?,
        evaluation_weights: deserialize_component(reader, &format!("{prefix}.weights"))?,
        opening_book: parse_capability(&reader.take(&format!("{prefix}.opening_book"))?)?,
        tablebase: parse_capability(&reader.take(&format!("{prefix}.tablebase"))?)?,
        transposition_table_mebibytes: reader
            .parse_field(&format!("{prefix}.transposition_table_mebibytes"))?,
        build_identity: reader.parse_text_field(&format!("{prefix}.build_identity"))?,
        exact_invocation: reader.parse_text_field(&format!("{prefix}.exact_invocation"))?,
        checksum: reader.parse_hex_field(&format!("{prefix}.checksum"))?,
    };
    identity.validate()?;
    Ok(identity)
}

fn serialize_component(output: &mut String, prefix: &str, identity: SemanticComponentIdentity) {
    field(output, &format!("{prefix}.schema"), identity.schema_version);
    hex_field(output, &format!("{prefix}.identifier"), identity.identifier);
    hex_field(output, &format!("{prefix}.checksum"), identity.checksum);
}

fn deserialize_component(
    reader: &mut ReportReader<'_>,
    prefix: &str,
) -> Result<SemanticComponentIdentity, ToolError> {
    let identity = SemanticComponentIdentity {
        schema_version: reader.parse_field(&format!("{prefix}.schema"))?,
        identifier: reader.parse_hex_field(&format!("{prefix}.identifier"))?,
        checksum: reader.parse_hex_field(&format!("{prefix}.checksum"))?,
    };
    validate_component(identity, prefix)?;
    Ok(identity)
}

fn capability_token(identity: OptionalCapabilityIdentity) -> String {
    match identity {
        OptionalCapabilityIdentity::Disabled => "disabled".to_owned(),
        OptionalCapabilityIdentity::Enabled {
            implementation_identifier,
            data_identifier,
            checksum,
        } => format!(
            "enabled:{implementation_identifier:016x}:{data_identifier:016x}:{checksum:016x}"
        ),
    }
}

fn parse_capability(value: &str) -> Result<OptionalCapabilityIdentity, ToolError> {
    if value == "disabled" {
        return Ok(OptionalCapabilityIdentity::Disabled);
    }
    let fields = value.split(':').collect::<Vec<_>>();
    if fields.len() != 4 || fields[0] != "enabled" {
        return Err(ToolError::new(format!(
            "invalid optional capability token {value:?}"
        )));
    }
    let identity = OptionalCapabilityIdentity::Enabled {
        implementation_identifier: parse_hex(fields[1], "capability implementation")?,
        data_identifier: parse_hex(fields[2], "capability data")?,
        checksum: parse_hex(fields[3], "capability checksum")?,
    };
    validate_optional_capability(identity, "capability")?;
    Ok(identity)
}

fn serialize_game(output: &mut String, index: usize, game: &EngineVariantValidationGame) {
    let prefix = format!("game.{index}");
    field(output, &format!("{prefix}.pair_index"), game.pair_index);
    field(output, &format!("{prefix}.pair_seed"), game.pair_seed);
    text_field(
        output,
        &format!("{prefix}.opening"),
        &game.opening_identifier,
    );
    field(
        output,
        &format!("{prefix}.candidate_color"),
        game.candidate_color,
    );
    match &game.outcome {
        EngineVariantGameOutcome::Completed {
            result,
            termination,
            candidate_score,
            moves,
            final_fen,
        } => {
            field(output, &format!("{prefix}.kind"), "completed");
            field(output, &format!("{prefix}.result"), result);
            text_field(
                output,
                &format!("{prefix}.termination"),
                &termination.to_string(),
            );
            float_bits_field(
                output,
                &format!("{prefix}.candidate_score"),
                *candidate_score,
            );
            text_field(output, &format!("{prefix}.moves"), &moves.join(" "));
            text_field(output, &format!("{prefix}.final_fen"), final_fen);
            field(output, &format!("{prefix}.faulting_side"), "-");
            text_field(output, &format!("{prefix}.failure_detail"), "");
        }
        EngineVariantGameOutcome::Failure(failure) => {
            field(output, &format!("{prefix}.kind"), failure.kind());
            field(output, &format!("{prefix}.result"), "-");
            text_field(output, &format!("{prefix}.termination"), "");
            field(output, &format!("{prefix}.candidate_score_bits"), "-");
            text_field(output, &format!("{prefix}.moves"), "");
            text_field(output, &format!("{prefix}.final_fen"), "");
            field(output, &format!("{prefix}.faulting_side"), failure.side());
            text_field(
                output,
                &format!("{prefix}.failure_detail"),
                failure.detail(),
            );
        }
    }
}

fn deserialize_game(
    reader: &mut ReportReader<'_>,
    index: usize,
) -> Result<EngineVariantValidationGame, ToolError> {
    let prefix = format!("game.{index}");
    let pair_index = reader.parse_field(&format!("{prefix}.pair_index"))?;
    let pair_seed = reader.parse_field(&format!("{prefix}.pair_seed"))?;
    let opening_identifier = reader.parse_text_field(&format!("{prefix}.opening"))?;
    let candidate_color = reader.parse_field(&format!("{prefix}.candidate_color"))?;
    let kind = reader.take(&format!("{prefix}.kind"))?;
    let result_token = reader.take(&format!("{prefix}.result"))?;
    let termination = reader.parse_text_field(&format!("{prefix}.termination"))?;
    let score_token = reader.take(&format!("{prefix}.candidate_score_bits"))?;
    let moves = reader.parse_text_field(&format!("{prefix}.moves"))?;
    let final_fen = reader.parse_text_field(&format!("{prefix}.final_fen"))?;
    let side_token = reader.take(&format!("{prefix}.faulting_side"))?;
    let failure_detail = reader.parse_text_field(&format!("{prefix}.failure_detail"))?;
    let outcome = if kind == "completed" {
        if side_token != "-" || !failure_detail.is_empty() || score_token == "-" {
            return Err(ToolError::new("malformed completed game record"));
        }
        EngineVariantGameOutcome::Completed {
            result: result_token.parse()?,
            termination: termination.parse()?,
            candidate_score: f64::from_bits(parse_hex(&score_token, "candidate score bits")?),
            moves: split_moves(&moves),
            final_fen,
        }
    } else {
        if result_token != "-"
            || !termination.is_empty()
            || score_token != "-"
            || !moves.is_empty()
            || !final_fen.is_empty()
            || failure_detail.is_empty()
        {
            return Err(ToolError::new("malformed failed game record"));
        }
        let side = side_token.parse()?;
        EngineVariantGameOutcome::Failure(match kind.as_str() {
            "illegal_move" => EngineVariantGameFailure::IllegalMove {
                side,
                detail: failure_detail,
            },
            "crash" => EngineVariantGameFailure::Crash {
                side,
                detail: failure_detail,
            },
            "time_forfeit" => EngineVariantGameFailure::TimeForfeit {
                side,
                detail: failure_detail,
            },
            "infrastructure_failure" => EngineVariantGameFailure::Infrastructure {
                detail: failure_detail,
            },
            _ => {
                return Err(ToolError::new(format!(
                    "invalid game outcome kind {kind:?}"
                )))
            }
        })
    };
    Ok(EngineVariantValidationGame {
        pair_index,
        pair_seed,
        opening_identifier,
        candidate_color,
        outcome,
    })
}

fn split_moves(value: &str) -> Vec<String> {
    if value.is_empty() {
        Vec::new()
    } else {
        value.split_ascii_whitespace().map(str::to_owned).collect()
    }
}

struct ReportReader<'a> {
    lines: std::str::Lines<'a>,
}

impl<'a> ReportReader<'a> {
    fn new(text: &'a str) -> Self {
        Self {
            lines: text.lines(),
        }
    }

    fn expect_line(&mut self, expected: &str) -> Result<(), ToolError> {
        let actual = self
            .lines
            .next()
            .ok_or_else(|| ToolError::new("truncated variant report"))?;
        if actual != expected {
            return Err(ToolError::new(format!(
                "expected report line {expected:?}, found {actual:?}"
            )));
        }
        Ok(())
    }

    fn take(&mut self, name: &str) -> Result<String, ToolError> {
        let line = self
            .lines
            .next()
            .ok_or_else(|| ToolError::new(format!("missing report field {name}")))?;
        let prefix = format!("{name}=");
        line.strip_prefix(&prefix)
            .map(str::to_owned)
            .ok_or_else(|| ToolError::new(format!("expected report field {name}")))
    }

    fn parse_field<T>(&mut self, name: &str) -> Result<T, ToolError>
    where
        T: FromStr,
        T::Err: fmt::Display,
    {
        let value = self.take(name)?;
        value.parse().map_err(|error| {
            ToolError::new(format!("invalid report field {name}={value:?}: {error}"))
        })
    }

    fn parse_bool_field(&mut self, name: &str) -> Result<bool, ToolError> {
        match self.take(name)?.as_str() {
            "true" => Ok(true),
            "false" => Ok(false),
            value => Err(ToolError::new(format!(
                "invalid boolean report field {name}={value:?}"
            ))),
        }
    }

    fn parse_hex_field(&mut self, name: &str) -> Result<u64, ToolError> {
        parse_hex(&self.take(name)?, name)
    }

    fn parse_float_bits_field(&mut self, name: &str) -> Result<f64, ToolError> {
        Ok(f64::from_bits(
            self.parse_hex_field(&format!("{name}_bits"))?,
        ))
    }

    fn parse_text_field(&mut self, name: &str) -> Result<String, ToolError> {
        let bytes = decode_hex(&self.take(&format!("{name}.utf8_hex"))?)?;
        String::from_utf8(bytes)
            .map_err(|error| ToolError::new(format!("invalid UTF-8 field {name}: {error}")))
    }

    fn finish(&mut self) -> Result<(), ToolError> {
        if self.lines.next().is_some() {
            return Err(ToolError::new("variant report contains trailing data"));
        }
        Ok(())
    }
}

fn line(output: &mut String, value: &str) {
    writeln!(output, "{value}").expect("writing to String cannot fail");
}

fn field(output: &mut String, name: &str, value: impl fmt::Display) {
    writeln!(output, "{name}={value}").expect("writing to String cannot fail");
}

fn hex_field(output: &mut String, name: &str, value: u64) {
    writeln!(output, "{name}={value:016x}").expect("writing to String cannot fail");
}

fn float_bits_field(output: &mut String, name: &str, value: f64) {
    hex_field(output, &format!("{name}_bits"), value.to_bits());
}

fn text_field(output: &mut String, name: &str, value: &str) {
    field(
        output,
        &format!("{name}.utf8_hex"),
        encode_hex(value.as_bytes()),
    );
}

fn encode_hex(bytes: &[u8]) -> String {
    let mut output = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        write!(output, "{byte:02x}").expect("writing to String cannot fail");
    }
    output
}

fn decode_hex(value: &str) -> Result<Vec<u8>, ToolError> {
    if value.len() % 2 != 0 {
        return Err(ToolError::new("hex field has odd length"));
    }
    let mut bytes = Vec::with_capacity(value.len() / 2);
    for index in (0..value.len()).step_by(2) {
        let byte = u8::from_str_radix(&value[index..index + 2], 16)
            .map_err(|error| ToolError::new(format!("invalid hex field: {error}")))?;
        bytes.push(byte);
    }
    Ok(bytes)
}

fn decode_commit(value: &str) -> Result<[u8; 20], ToolError> {
    let bytes = decode_hex(value)?;
    bytes
        .try_into()
        .map_err(|_| ToolError::new("source commit must contain exactly 20 bytes"))
}

fn parse_hex(value: &str, name: &str) -> Result<u64, ToolError> {
    u64::from_str_radix(value, 16)
        .map_err(|error| ToolError::new(format!("invalid hex {name} {value:?}: {error}")))
}

fn hash_text(mut hash: u64, text: &str) -> u64 {
    hash = hash_bytes(hash, &(text.len() as u64).to_le_bytes());
    hash_bytes(hash, text.as_bytes())
}

fn hash_bytes(mut hash: u64, bytes: &[u8]) -> u64 {
    for byte in bytes {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    hash
}

#[cfg(test)]
mod tests {
    use chess_search::{EvaluationWeightSet, EvaluationWeights, SearchPolicy, SearchPolicySet};

    use crate::engine_variant::{EngineVariantDescriptor, OptionalCapabilityIdentity};

    use super::*;

    fn descriptor(identifier: u64, invocation: &str) -> EngineVariantDescriptor {
        EngineVariantDescriptor {
            identifier,
            source_commit: [0x22; 20],
            engine_version: "0.1.0".to_owned(),
            opening_book: OptionalCapabilityIdentity::Disabled,
            tablebase: OptionalCapabilityIdentity::Disabled,
            transposition_table_mebibytes: 1,
            build_identity: "rustc-test|x86_64-unknown-linux-gnu|release|default".to_owned(),
            exact_invocation: invocation.to_owned(),
        }
    }

    fn runtimes() -> (
        EngineVariantIdentity,
        SearchPolicySet,
        EvaluationWeightSet,
        EngineVariantIdentity,
        SearchPolicySet,
        EvaluationWeightSet,
    ) {
        let baseline_policy = SearchPolicySet::baseline();
        let baseline_weights = EvaluationWeightSet::baseline();
        let baseline_identity = EngineVariantIdentity::new(
            descriptor(0x4241_5345_4c49_4e45, "variant baseline"),
            &baseline_policy,
            &baseline_weights,
        )
        .expect("baseline identity");
        let mut parameters = SearchPolicy::V0_1.parameters();
        parameters.aspiration_half_width_centipawns += 1;
        let candidate_policy =
            SearchPolicySet::new(0x4341_4e44_504f_4c31, SearchPolicy::new(parameters));
        candidate_policy.validate().expect("candidate policy");
        let candidate_weights =
            EvaluationWeightSet::new(0x4341_4e44_5745_4931, EvaluationWeights::DEFAULT);
        candidate_weights.validate().expect("candidate weights");
        let candidate_identity = EngineVariantIdentity::new(
            descriptor(0x4341_4e44_4944_3031, "variant candidate"),
            &candidate_policy,
            &candidate_weights,
        )
        .expect("candidate identity");
        (
            baseline_identity,
            baseline_policy,
            baseline_weights,
            candidate_identity,
            candidate_policy,
            candidate_weights,
        )
    }

    fn openings(count: usize) -> OpeningSuite {
        let mut text = String::from("CHESS_SELF_PLAY_OPENINGS\t1\n");
        for index in 0..count {
            let first = if index % 2 == 0 { "e2e4" } else { "d2d4" };
            let second = if index % 3 == 0 { "e7e5" } else { "d7d5" };
            writeln!(
                text,
                "opening-{index:03}\trnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\t{first} {second}"
            )
            .expect("write opening");
        }
        OpeningSuite::from_text(&text).expect("openings")
    }

    #[test]
    fn tiers_are_bounded_and_only_production_reaches_two_hundred_pairs() {
        let protocol = EngineVariantResourceProtocol::FixedNodes(1);
        assert!(EngineVariantValidationConfig::new(
            EngineVariantValidationTier::Smoke,
            16,
            1,
            protocol,
            1,
        )
        .is_ok());
        assert!(EngineVariantValidationConfig::new(
            EngineVariantValidationTier::Smoke,
            17,
            1,
            protocol,
            1,
        )
        .is_err());
        assert!(EngineVariantValidationConfig::new(
            EngineVariantValidationTier::Development,
            8,
            1,
            protocol,
            1,
        )
        .is_ok());
        assert!(EngineVariantValidationConfig::new(
            EngineVariantValidationTier::Production,
            199,
            1,
            protocol,
            1,
        )
        .is_err());
        assert!(EngineVariantValidationConfig::new(
            EngineVariantValidationTier::Production,
            200,
            1,
            protocol,
            1,
        )
        .is_ok());
    }

    #[test]
    fn fixed_node_and_clock_protocols_are_explicit_and_equal_resource() {
        let fixed = EngineVariantResourceProtocol::FixedNodes(10_000);
        let clock = EngineVariantResourceProtocol::ClockMilliseconds(25);
        assert_eq!(fixed.to_string(), "fixed_nodes:10000");
        assert_eq!(clock.to_string(), "clock_ms:25");
        assert_ne!(fixed.purpose(), clock.purpose());
        assert_eq!(fixed.to_string().parse(), Ok(fixed));
        assert_eq!(clock.to_string().parse(), Ok(clock));
    }

    #[test]
    fn runtime_identity_mismatch_fails_before_match_allocation() {
        let (baseline_identity, _, baseline_weights, _, candidate_policy, _) = runtimes();
        let error =
            EngineVariantRuntime::new(&baseline_identity, &candidate_policy, &baseline_weights)
                .expect_err("policy mismatch");
        assert!(error.to_string().contains("policy does not match"));
    }

    #[test]
    fn one_pair_smoke_is_color_balanced_inactive_and_round_trips() {
        let (
            baseline_identity,
            baseline_policy,
            baseline_weights,
            candidate_identity,
            candidate_policy,
            candidate_weights,
        ) = runtimes();
        let baseline =
            EngineVariantRuntime::new(&baseline_identity, &baseline_policy, &baseline_weights)
                .expect("baseline runtime");
        let candidate =
            EngineVariantRuntime::new(&candidate_identity, &candidate_policy, &candidate_weights)
                .expect("candidate runtime");
        let config = EngineVariantValidationConfig::new(
            EngineVariantValidationTier::Smoke,
            1,
            42,
            EngineVariantResourceProtocol::FixedNodes(1),
            1,
        )
        .expect("smoke config")
        .with_maximum_plies(4)
        .expect("short games")
        .with_maximum_unfinished_per_mille(1_000)
        .expect("unfinished accepted");
        let report =
            run_engine_variant_validation_internal(config, &openings(1), baseline, candidate, 1)
                .expect("smoke report");
        assert_eq!(report.games.len(), 2);
        assert_ne!(
            report.games[0].candidate_color,
            report.games[1].candidate_color
        );
        assert!(!report.activated());
        assert_ne!(
            report.decision,
            EngineVariantValidationDecision::AcceptedForActivation
        );
        let text = report.serialize().expect("serialize");
        assert_eq!(
            EngineVariantValidationReport::deserialize(&text).expect("deserialize"),
            report
        );
        let truncated = text
            .lines()
            .take(text.lines().count() - 1)
            .collect::<Vec<_>>()
            .join("\n");
        assert!(EngineVariantValidationReport::deserialize(&truncated).is_err());
        let corrupted = text.replacen("checksum=", "checksum=ff", 1);
        assert!(EngineVariantValidationReport::deserialize(&corrupted).is_err());
    }

    #[test]
    fn duplicate_semantic_openings_are_rejected() {
        let duplicate = OpeningSuite::from_text(concat!(
            "CHESS_SELF_PLAY_OPENINGS\t1\n",
            "one\trnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\te2e4 e7e5\n",
            "two\trnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\te2e4 e7e5\n",
        ))
        .expect("syntactically valid duplicate suite");
        let config = EngineVariantValidationConfig::new(
            EngineVariantValidationTier::Smoke,
            2,
            1,
            EngineVariantResourceProtocol::FixedNodes(1),
            1,
        )
        .expect("config");
        assert!(validate_openings(config, &duplicate)
            .expect_err("duplicates fail")
            .to_string()
            .contains("duplicate semantic"));
    }

    #[test]
    fn failure_kinds_are_counted_without_becoming_chess_scores() {
        let failures = [
            EngineVariantGameFailure::IllegalMove {
                side: EngineVariantFaultingSide::Candidate,
                detail: "illegal".to_owned(),
            },
            EngineVariantGameFailure::Crash {
                side: EngineVariantFaultingSide::Baseline,
                detail: "crash".to_owned(),
            },
            EngineVariantGameFailure::TimeForfeit {
                side: EngineVariantFaultingSide::Candidate,
                detail: "flag".to_owned(),
            },
            EngineVariantGameFailure::Infrastructure {
                detail: "runner".to_owned(),
            },
        ];
        assert_eq!(failures[0].kind(), "illegal_move");
        assert_eq!(failures[1].kind(), "crash");
        assert_eq!(failures[2].kind(), "time_forfeit");
        assert_eq!(failures[3].kind(), "infrastructure_failure");
        assert!(failures.iter().all(|failure| !failure.detail().is_empty()));
    }

    #[test]
    fn only_production_success_maps_to_accepted_for_activation() {
        let protocol = EngineVariantResourceProtocol::FixedNodes(1);
        for (tier, expected) in [
            (
                EngineVariantValidationTier::Smoke,
                EngineVariantValidationDecision::PassedSmoke,
            ),
            (
                EngineVariantValidationTier::Development,
                EngineVariantValidationDecision::PassedDevelopment,
            ),
            (
                EngineVariantValidationTier::Production,
                EngineVariantValidationDecision::AcceptedForActivation,
            ),
        ] {
            let pair_count = match tier {
                EngineVariantValidationTier::Smoke => 1,
                EngineVariantValidationTier::Development => 8,
                EngineVariantValidationTier::Production => 200,
            };
            let config = EngineVariantValidationConfig::new(tier, pair_count, 1, protocol, 1)
                .expect("tier config")
                .with_maximum_unfinished_per_mille(1_000)
                .expect("ceiling");
            let correctness = EngineVariantCorrectnessSummary {
                perft_depth: 1,
                perft_cases: 1,
                perft_passed: true,
                forced_mate_cases: 1,
                forced_mate_passed: true,
                longest_survival_cases: 1,
                longest_survival_passed: true,
                tactical_cases: 1,
                tactical_passed: true,
                equivalence_cases: 1,
                equivalence_passed: true,
                infrastructure_failures: 0,
                failure_detail: String::new(),
            };
            let (baseline_identity, _, _, candidate_identity, _, _) = runtimes();
            let mut report = EngineVariantValidationReport {
                config,
                baseline: RecordedEngineVariantIdentity::from_identity(&baseline_identity),
                candidate: RecordedEngineVariantIdentity::from_identity(&candidate_identity),
                opening_suite_checksum: 1,
                opening_count: pair_count,
                correctness,
                games: Vec::new(),
                candidate_wins: pair_count * 2,
                draws: 0,
                candidate_losses: 0,
                unfinished: 0,
                illegal_moves: 0,
                crashes: 0,
                time_forfeits: 0,
                infrastructure_failures: 0,
                mean_pair_score: 1.0,
                pair_score_standard_error: 0.0,
                lower_confidence_bound: 1.0,
                decision: expected,
                checksum: 0,
            };
            for pair_index in 0..pair_count {
                for candidate_color in [
                    EngineVariantCandidateColor::White,
                    EngineVariantCandidateColor::Black,
                ] {
                    report.games.push(EngineVariantValidationGame {
                        pair_index,
                        pair_seed: u64::from(pair_index),
                        opening_identifier: format!("opening-{pair_index}"),
                        candidate_color,
                        outcome: EngineVariantGameOutcome::Completed {
                            result: match candidate_color {
                                EngineVariantCandidateColor::White => SelfPlayResult::WhiteWin,
                                EngineVariantCandidateColor::Black => SelfPlayResult::BlackWin,
                            },
                            termination: SelfPlayTermination::MaximumPly(1),
                            candidate_score: 1.0,
                            moves: Vec::new(),
                            final_fen: "test".to_owned(),
                        },
                    });
                }
            }
            report.checksum = report.computed_checksum();
            assert_eq!(report.expected_decision(), Ok(expected));
            assert_eq!(report.validate(), Ok(()));
        }
    }

    #[test]
    fn atomic_report_write_uses_caller_selected_paths() {
        let (
            baseline_identity,
            baseline_policy,
            baseline_weights,
            candidate_identity,
            candidate_policy,
            candidate_weights,
        ) = runtimes();
        let baseline =
            EngineVariantRuntime::new(&baseline_identity, &baseline_policy, &baseline_weights)
                .expect("baseline runtime");
        let candidate =
            EngineVariantRuntime::new(&candidate_identity, &candidate_policy, &candidate_weights)
                .expect("candidate runtime");
        let config = EngineVariantValidationConfig::new(
            EngineVariantValidationTier::Smoke,
            1,
            7,
            EngineVariantResourceProtocol::FixedNodes(1),
            1,
        )
        .expect("config")
        .with_maximum_plies(4)
        .expect("short")
        .with_maximum_unfinished_per_mille(1_000)
        .expect("ceiling");
        let report =
            run_engine_variant_validation_internal(config, &openings(1), baseline, candidate, 1)
                .expect("report");
        let destination = std::env::temp_dir().join(format!(
            "engine-variant-report-{}-{:016x}.txt",
            std::process::id(),
            report.checksum
        ));
        let temporary = destination.with_extension("tmp");
        let _ = fs::remove_file(&destination);
        let _ = fs::remove_file(&temporary);
        write_engine_variant_validation_report_atomic(&destination, &temporary, &report)
            .expect("atomic write");
        let text = fs::read_to_string(&destination).expect("read report");
        assert_eq!(
            EngineVariantValidationReport::deserialize(&text).expect("parse written report"),
            report
        );
        assert!(!temporary.exists());
        fs::remove_file(destination).expect("remove report");
    }
}
