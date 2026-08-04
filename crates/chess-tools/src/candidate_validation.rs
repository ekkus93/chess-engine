//! Deterministic, fail-closed candidate-versus-baseline validation.

use core::fmt;
use std::{
    fmt::Write as _,
    fs::{self, OpenOptions},
    io::Write as _,
    path::Path,
};

use chess_core::{Position, SearchHistory};
use chess_search::{
    iterative_deepening_search_with_limits_and_transposition_table_and_weights,
    EvaluationWeightSet, SearchLimits, TranspositionTable,
};
use chess_tune::{NamedWeightArtifact, NamedWeightArtifactError};

use crate::self_play::{
    run_weighted_validation_game, ClaimableDrawPolicy, OpeningSuite, SelfPlayResult,
    SelfPlaySideConfig, SelfPlayTermination, WeightedValidationGameConfig,
};
use crate::{perft, perft_fixtures, ToolError};

/// Current candidate-validation report schema.
pub const CANDIDATE_VALIDATION_SCHEMA_VERSION: u16 = 1;
/// Stable semantic identity of the Task 21.5 validation protocol.
pub const CANDIDATE_VALIDATION_IDENTIFIER: u64 = 0x4341_4e44_5641_4c31;
/// Production minimum: 200 color-balanced opening pairs, or 400 games.
pub const MINIMUM_VALIDATION_PAIRS: u32 = 200;
/// One-sided 95% normal critical value.
pub const ONE_SIDED_95_PERCENT_Z: f64 = 1.644_853_626_951_472_2;

const FORMAT_MARKER: &str = "chess-candidate-validation-v1";
const MAXIMUM_VALIDATION_PAIRS: u32 = 100_000;
const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;

/// Exact engine/source/invocation identity for one validation run.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CandidateValidationProvenance {
    /// Stable caller-selected engine build identity.
    pub engine_identifier: u64,
    /// Semantic engine version.
    pub engine_version: String,
    /// Exact 20-byte source commit.
    pub source_commit: [u8; 20],
    /// Exact command or equivalent invocation.
    pub exact_command: String,
}

impl CandidateValidationProvenance {
    /// Constructs complete non-empty provenance.
    pub fn new(
        engine_identifier: u64,
        engine_version: String,
        source_commit: [u8; 20],
        exact_command: String,
    ) -> Result<Self, ToolError> {
        let value = Self {
            engine_identifier,
            engine_version,
            source_commit,
            exact_command,
        };
        value.validate()?;
        Ok(value)
    }

    fn validate(&self) -> Result<(), ToolError> {
        if self.engine_identifier == 0 {
            return Err(ToolError::new(
                "validation engine identifier must be non-zero",
            ));
        }
        if self.engine_version.is_empty() || self.exact_command.is_empty() {
            return Err(ToolError::new(
                "validation engine version and exact command must not be empty",
            ));
        }
        if self.source_commit.iter().all(|byte| *byte == 0) {
            return Err(ToolError::new("validation source commit must be recorded"));
        }
        Ok(())
    }
}

/// Fixed, color-symmetric match and acceptance configuration.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct CandidateValidationConfig {
    pair_count: u32,
    seed: u64,
    side: SelfPlaySideConfig,
    maximum_plies: u32,
    claimable_draw_policy: ClaimableDrawPolicy,
    minimum_score_margin: f64,
    maximum_unfinished_per_mille: u16,
}

impl CandidateValidationConfig {
    /// Creates a production validation configuration.
    pub fn new(pair_count: u32, seed: u64, side: SelfPlaySideConfig) -> Result<Self, ToolError> {
        let value = Self {
            pair_count,
            seed,
            side,
            maximum_plies: 256,
            claimable_draw_policy: ClaimableDrawPolicy::Accept,
            minimum_score_margin: 0.0,
            maximum_unfinished_per_mille: 50,
        };
        value.validate(MINIMUM_VALIDATION_PAIRS)?;
        Ok(value)
    }

    /// Selects the complete game-length boundary, including opening plies.
    pub fn with_maximum_plies(mut self, maximum_plies: u32) -> Result<Self, ToolError> {
        self.maximum_plies = maximum_plies;
        self.validate(MINIMUM_VALIDATION_PAIRS)?;
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
        self.validate(MINIMUM_VALIDATION_PAIRS)?;
        Ok(self)
    }

    /// Sets the maximum unfinished-game rate in parts per thousand.
    pub fn with_maximum_unfinished_per_mille(mut self, maximum: u16) -> Result<Self, ToolError> {
        self.maximum_unfinished_per_mille = maximum;
        self.validate(MINIMUM_VALIDATION_PAIRS)?;
        Ok(self)
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

    /// Returns the identical search configuration used by both evaluators.
    #[must_use]
    pub const fn side(self) -> SelfPlaySideConfig {
        self.side
    }

    /// Returns the maximum game length.
    #[must_use]
    pub const fn maximum_plies(self) -> u32 {
        self.maximum_plies
    }

    /// Returns the draw-claim policy.
    #[must_use]
    pub const fn claimable_draw_policy(self) -> ClaimableDrawPolicy {
        self.claimable_draw_policy
    }

    /// Returns the required improvement margin above an even score.
    #[must_use]
    pub const fn minimum_score_margin(self) -> f64 {
        self.minimum_score_margin
    }

    /// Returns the unfinished-game ceiling in parts per thousand.
    #[must_use]
    pub const fn maximum_unfinished_per_mille(self) -> u16 {
        self.maximum_unfinished_per_mille
    }

    fn validate(self, minimum_pairs: u32) -> Result<(), ToolError> {
        if self.pair_count < minimum_pairs || self.pair_count > MAXIMUM_VALIDATION_PAIRS {
            return Err(ToolError::new(format!(
                "candidate validation requires between {minimum_pairs} and {MAXIMUM_VALIDATION_PAIRS} opening pairs, found {}",
                self.pair_count
            )));
        }
        WeightedValidationGameConfig::new(
            self.side,
            self.side,
            self.maximum_plies,
            self.claimable_draw_policy,
        )?;
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
        Ok(())
    }
}

/// Color assigned to the candidate in one paired game.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CandidateColor {
    /// Candidate plays White.
    White,
    /// Candidate plays Black.
    Black,
}

impl fmt::Display for CandidateColor {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::White => "white",
            Self::Black => "black",
        })
    }
}

/// Fail-closed outcome of the complete validation protocol.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CandidateValidationDecision {
    /// Tactical, rules, or artifact correctness failed.
    RejectedCorrectness,
    /// Too many games reached the explicit maximum-ply boundary.
    RejectedUnfinishedRate,
    /// The one-sided lower confidence bound did not prove improvement.
    RejectedStrength,
    /// Every correctness and statistical requirement passed.
    Accepted,
}

impl fmt::Display for CandidateValidationDecision {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::RejectedCorrectness => "rejected_correctness",
            Self::RejectedUnfinishedRate => "rejected_unfinished_rate",
            Self::RejectedStrength => "rejected_strength",
            Self::Accepted => "accepted",
        })
    }
}

/// Recorded correctness-suite result.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct CandidateCorrectnessSummary {
    /// Maximum authoritative perft depth rerun.
    pub perft_depth: u8,
    /// Number of exact fixture/depth comparisons.
    pub perft_cases: u32,
    /// Whether every perft count matched.
    pub perft_passed: bool,
    /// Number of weighted tactical fixtures.
    pub tactical_cases: u32,
    /// Whether every tactical move requirement matched.
    pub tactical_passed: bool,
}

impl CandidateCorrectnessSummary {
    /// Returns whether all candidate correctness checks passed.
    #[must_use]
    pub const fn passed(self) -> bool {
        self.perft_passed && self.tactical_passed
    }
}

/// Complete replay payload for one game in an opening pair.
#[derive(Clone, Debug, PartialEq)]
pub struct CandidateValidationGame {
    /// Zero-based independent pair index.
    pub pair_index: u32,
    /// Deterministic pair seed retained as provenance.
    pub pair_seed: u64,
    /// Opening source identifier.
    pub opening_identifier: String,
    /// Candidate color in this game.
    pub candidate_color: CandidateColor,
    /// Absolute game result.
    pub result: SelfPlayResult,
    /// Exact rule or policy termination.
    pub termination: SelfPlayTermination,
    /// Candidate score: 1 win, 0.5 draw/unfinished, 0 loss.
    pub candidate_score: f64,
    /// Complete game move list after the supplied opening.
    pub moves: Vec<String>,
    /// Final canonical FEN.
    pub final_fen: String,
}

/// Versioned, checksummed candidate-validation evidence.
#[derive(Clone, Debug, PartialEq)]
pub struct CandidateValidationReport {
    /// Exact source and command identity.
    pub provenance: CandidateValidationProvenance,
    /// Complete fixed protocol configuration.
    pub config: CandidateValidationConfig,
    /// Baseline weight identity.
    pub baseline_identifier: u64,
    /// Baseline semantic checksum.
    pub baseline_checksum: u64,
    /// Candidate weight identity.
    pub candidate_identifier: u64,
    /// Candidate runtime-weight checksum.
    pub candidate_checksum: u64,
    /// Candidate named-artifact checksum.
    pub candidate_artifact_checksum: u64,
    /// Canonical opening-suite checksum.
    pub opening_suite_checksum: u64,
    /// Number of source opening lines.
    pub opening_count: u32,
    /// Candidate correctness results.
    pub correctness: CandidateCorrectnessSummary,
    /// Every paired game, in pair then candidate-color order.
    pub games: Vec<CandidateValidationGame>,
    /// Candidate wins across individual games.
    pub candidate_wins: u32,
    /// Completed draws across individual games.
    pub draws: u32,
    /// Candidate losses across individual games.
    pub candidate_losses: u32,
    /// Maximum-ply unfinished games.
    pub unfinished: u32,
    /// Mean candidate score over independent color-swapped pair scores.
    pub mean_pair_score: f64,
    /// Sample standard error over independent pair scores.
    pub pair_score_standard_error: f64,
    /// One-sided 95% lower confidence bound.
    pub lower_confidence_bound: f64,
    /// Final fail-closed decision.
    pub decision: CandidateValidationDecision,
    /// Canonical semantic report checksum.
    pub checksum: u64,
}

impl CandidateValidationReport {
    /// Candidate outputs are evidence only and are never activated by this protocol.
    #[must_use]
    pub const fn activated(&self) -> bool {
        false
    }

    /// Recomputes the complete semantic checksum.
    #[must_use]
    pub fn computed_checksum(&self) -> u64 {
        let mut hash = FNV_OFFSET;
        for value in [
            u64::from(CANDIDATE_VALIDATION_SCHEMA_VERSION),
            CANDIDATE_VALIDATION_IDENTIFIER,
            self.provenance.engine_identifier,
        ] {
            hash = hash_bytes(hash, &value.to_le_bytes());
        }
        hash = hash_text(hash, &self.provenance.engine_version);
        hash = hash_bytes(hash, &self.provenance.source_commit);
        hash = hash_text(hash, &self.provenance.exact_command);
        for value in [
            u64::from(self.config.pair_count),
            self.config.seed,
            self.config.maximum_plies.into(),
            self.config.minimum_score_margin.to_bits(),
            u64::from(self.config.maximum_unfinished_per_mille),
            self.baseline_identifier,
            self.baseline_checksum,
            self.candidate_identifier,
            self.candidate_checksum,
            self.candidate_artifact_checksum,
            self.opening_suite_checksum,
            u64::from(self.opening_count),
            u64::from(self.correctness.perft_depth),
            u64::from(self.correctness.perft_cases),
            u64::from(self.correctness.tactical_cases),
            u64::from(self.candidate_wins),
            u64::from(self.draws),
            u64::from(self.candidate_losses),
            u64::from(self.unfinished),
            self.mean_pair_score.to_bits(),
            self.pair_score_standard_error.to_bits(),
            self.lower_confidence_bound.to_bits(),
        ] {
            hash = hash_bytes(hash, &value.to_le_bytes());
        }
        hash = hash_bytes(hash, &[self.config.claimable_draw_policy as u8]);
        hash = hash_bytes(hash, &[self.config.side.check_extension_enabled() as u8]);
        hash = hash_text(hash, &self.config.side.limit().to_string());
        hash = hash_bytes(
            hash,
            &(self.config.side.transposition_table_mebibytes() as u64).to_le_bytes(),
        );
        hash = hash_bytes(hash, &[self.correctness.perft_passed as u8]);
        hash = hash_bytes(hash, &[self.correctness.tactical_passed as u8]);
        hash = hash_text(hash, &self.decision.to_string());
        hash = hash_bytes(hash, &[self.activated() as u8]);
        for game in &self.games {
            hash = hash_bytes(hash, &game.pair_index.to_le_bytes());
            hash = hash_bytes(hash, &game.pair_seed.to_le_bytes());
            hash = hash_text(hash, &game.opening_identifier);
            hash = hash_text(hash, &game.candidate_color.to_string());
            hash = hash_text(hash, &game.result.to_string());
            hash = hash_text(hash, &game.termination.to_string());
            hash = hash_bytes(hash, &game.candidate_score.to_bits().to_le_bytes());
            hash = hash_text(hash, &game.moves.join(" "));
            hash = hash_text(hash, &game.final_fen);
        }
        hash
    }

    /// Validates counts, finite statistics, color balance, inactivity, and checksum.
    pub fn validate(&self) -> Result<(), ToolError> {
        self.provenance.validate()?;
        self.config.validate(1)?;
        if self.opening_count == 0 || self.opening_suite_checksum == 0 {
            return Err(ToolError::new("validation opening provenance is empty"));
        }
        let expected_games = self.config.pair_count.saturating_mul(2) as usize;
        if self.correctness.passed() && self.games.len() != expected_games {
            return Err(ToolError::new(
                "successful correctness gate requires every paired game",
            ));
        }
        if !self.correctness.passed() && !self.games.is_empty() {
            return Err(ToolError::new(
                "match games must not run after a correctness failure",
            ));
        }
        for pair in 0..self.config.pair_count {
            let games = self
                .games
                .iter()
                .filter(|game| game.pair_index == pair)
                .collect::<Vec<_>>();
            if self.correctness.passed()
                && (games.len() != 2
                    || games[0].candidate_color == games[1].candidate_color
                    || games[0].opening_identifier != games[1].opening_identifier
                    || games[0].pair_seed != games[1].pair_seed)
            {
                return Err(ToolError::new(
                    "validation pair is not exactly color-balanced",
                ));
            }
        }
        let counted = self
            .candidate_wins
            .saturating_add(self.draws)
            .saturating_add(self.candidate_losses)
            .saturating_add(self.unfinished) as usize;
        if counted != self.games.len() {
            return Err(ToolError::new(
                "validation result counts do not match games",
            ));
        }
        for value in [
            self.mean_pair_score,
            self.pair_score_standard_error,
            self.lower_confidence_bound,
        ] {
            if !value.is_finite() {
                return Err(ToolError::new("validation statistics must be finite"));
            }
        }
        if self.checksum != self.computed_checksum() {
            return Err(ToolError::new("candidate-validation checksum mismatch"));
        }
        Ok(())
    }

    /// Serializes deterministic line-oriented evidence with exact float bits.
    pub fn serialize(&self) -> Result<String, ToolError> {
        self.validate()?;
        let mut output = String::new();
        line(&mut output, FORMAT_MARKER);
        field(&mut output, "schema", CANDIDATE_VALIDATION_SCHEMA_VERSION);
        hex_field(
            &mut output,
            "report_identifier",
            CANDIDATE_VALIDATION_IDENTIFIER,
        );
        hex_field(
            &mut output,
            "engine_identifier",
            self.provenance.engine_identifier,
        );
        text_field(
            &mut output,
            "engine_version",
            &self.provenance.engine_version,
        );
        field(
            &mut output,
            "source_commit",
            encode_hex(&self.provenance.source_commit),
        );
        text_field(&mut output, "exact_command", &self.provenance.exact_command);
        field(&mut output, "pair_count", self.config.pair_count);
        field(&mut output, "game_count", self.games.len());
        field(&mut output, "seed", self.config.seed);
        field(
            &mut output,
            "minimum_required_pairs",
            MINIMUM_VALIDATION_PAIRS,
        );
        field(&mut output, "search_limit", self.config.side.limit());
        field(
            &mut output,
            "transposition_table_mebibytes",
            self.config.side.transposition_table_mebibytes(),
        );
        field(
            &mut output,
            "check_extension",
            self.config.side.check_extension_enabled(),
        );
        field(&mut output, "maximum_plies", self.config.maximum_plies);
        field(
            &mut output,
            "claimable_draw_policy",
            self.config.claimable_draw_policy,
        );
        float_field(
            &mut output,
            "minimum_score_margin",
            self.config.minimum_score_margin,
        );
        field(
            &mut output,
            "maximum_unfinished_per_mille",
            self.config.maximum_unfinished_per_mille,
        );
        hex_field(&mut output, "baseline_identifier", self.baseline_identifier);
        hex_field(&mut output, "baseline_checksum", self.baseline_checksum);
        hex_field(
            &mut output,
            "candidate_identifier",
            self.candidate_identifier,
        );
        hex_field(&mut output, "candidate_checksum", self.candidate_checksum);
        hex_field(
            &mut output,
            "candidate_artifact_checksum",
            self.candidate_artifact_checksum,
        );
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
            "tactical_cases",
            self.correctness.tactical_cases,
        );
        field(
            &mut output,
            "tactical_passed",
            self.correctness.tactical_passed,
        );
        field(&mut output, "candidate_wins", self.candidate_wins);
        field(&mut output, "draws", self.draws);
        field(&mut output, "candidate_losses", self.candidate_losses);
        field(&mut output, "unfinished", self.unfinished);
        float_field(&mut output, "mean_pair_score", self.mean_pair_score);
        float_field(
            &mut output,
            "pair_score_standard_error",
            self.pair_score_standard_error,
        );
        float_field(
            &mut output,
            "lower_confidence_bound",
            self.lower_confidence_bound,
        );
        field(&mut output, "decision", self.decision);
        field(&mut output, "activated", self.activated());
        for (index, game) in self.games.iter().enumerate() {
            let prefix = format!("game.{index}");
            field(
                &mut output,
                &format!("{prefix}.pair_index"),
                game.pair_index,
            );
            field(&mut output, &format!("{prefix}.pair_seed"), game.pair_seed);
            text_field(
                &mut output,
                &format!("{prefix}.opening"),
                &game.opening_identifier,
            );
            field(
                &mut output,
                &format!("{prefix}.candidate_color"),
                game.candidate_color,
            );
            field(&mut output, &format!("{prefix}.result"), game.result);
            text_field(
                &mut output,
                &format!("{prefix}.termination"),
                &game.termination.to_string(),
            );
            float_field(
                &mut output,
                &format!("{prefix}.candidate_score"),
                game.candidate_score,
            );
            text_field(
                &mut output,
                &format!("{prefix}.moves"),
                &game.moves.join(" "),
            );
            text_field(&mut output, &format!("{prefix}.final_fen"), &game.final_fen);
        }
        hex_field(&mut output, "checksum", self.checksum);
        Ok(output)
    }
}

/// Runs the complete production Task 21.5 protocol.
pub fn run_candidate_validation(
    provenance: CandidateValidationProvenance,
    config: CandidateValidationConfig,
    openings: &OpeningSuite,
    candidate_artifact: &NamedWeightArtifact,
) -> Result<CandidateValidationReport, ToolError> {
    run_candidate_validation_internal(
        provenance,
        config,
        openings,
        candidate_artifact,
        MINIMUM_VALIDATION_PAIRS,
        4,
    )
}

fn run_candidate_validation_internal(
    provenance: CandidateValidationProvenance,
    config: CandidateValidationConfig,
    openings: &OpeningSuite,
    candidate_artifact: &NamedWeightArtifact,
    minimum_pairs: u32,
    perft_depth: u8,
) -> Result<CandidateValidationReport, ToolError> {
    provenance.validate()?;
    config.validate(minimum_pairs)?;
    candidate_artifact
        .validate()
        .map_err(named_artifact_error)?;
    if openings.lines().is_empty() {
        return Err(ToolError::new(
            "candidate validation opening suite is empty",
        ));
    }

    let baseline = EvaluationWeightSet::baseline();
    baseline
        .validate()
        .map_err(|error| ToolError::new(error.to_string()))?;
    let candidate =
        EvaluationWeightSet::new(candidate_artifact.identifier, candidate_artifact.weights);
    candidate
        .validate()
        .map_err(|error| ToolError::new(error.to_string()))?;
    if candidate.identifier == baseline.identifier {
        return Err(ToolError::new(
            "candidate identifier must differ from the built-in baseline identifier",
        ));
    }

    let correctness = run_correctness_suite(&candidate, perft_depth)?;
    let opening_suite_checksum = opening_suite_checksum(openings);
    let opening_count = u32::try_from(openings.lines().len())
        .map_err(|_| ToolError::new("opening count exceeds u32"))?;
    let mut report = CandidateValidationReport {
        provenance,
        config,
        baseline_identifier: baseline.identifier,
        baseline_checksum: baseline.checksum,
        candidate_identifier: candidate.identifier,
        candidate_checksum: candidate.checksum,
        candidate_artifact_checksum: candidate_artifact.checksum,
        opening_suite_checksum,
        opening_count,
        correctness,
        games: Vec::new(),
        candidate_wins: 0,
        draws: 0,
        candidate_losses: 0,
        unfinished: 0,
        mean_pair_score: 0.0,
        pair_score_standard_error: 0.0,
        lower_confidence_bound: 0.0,
        decision: CandidateValidationDecision::RejectedCorrectness,
        checksum: 0,
    };
    if !correctness.passed() {
        report.checksum = report.computed_checksum();
        report.validate()?;
        return Ok(report);
    }

    let match_config = WeightedValidationGameConfig::new(
        config.side,
        config.side,
        config.maximum_plies,
        config.claimable_draw_policy,
    )?;
    let opening_offset = (splitmix64(config.seed) % openings.lines().len() as u64) as usize;
    let mut pair_scores = Vec::with_capacity(config.pair_count as usize);
    report
        .games
        .reserve(config.pair_count.saturating_mul(2) as usize);

    for pair_index in 0..config.pair_count {
        let opening =
            &openings.lines()[(opening_offset + pair_index as usize) % openings.lines().len()];
        let pair_seed = splitmix64(config.seed ^ u64::from(pair_index));
        let candidate_white = run_weighted_validation_game(
            opening,
            match_config,
            &candidate.weights,
            &baseline.weights,
        )?;
        let candidate_black = run_weighted_validation_game(
            opening,
            match_config,
            &baseline.weights,
            &candidate.weights,
        )?;
        let white_score = candidate_score(candidate_white.result(), CandidateColor::White);
        let black_score = candidate_score(candidate_black.result(), CandidateColor::Black);
        pair_scores.push((white_score + black_score) * 0.5);
        append_game(
            &mut report,
            pair_index,
            pair_seed,
            opening.identifier(),
            CandidateColor::White,
            candidate_white,
            white_score,
        )?;
        append_game(
            &mut report,
            pair_index,
            pair_seed,
            opening.identifier(),
            CandidateColor::Black,
            candidate_black,
            black_score,
        )?;
    }

    let (mean, standard_error, lower_bound) = summarize_pair_scores(&pair_scores)?;
    report.mean_pair_score = mean;
    report.pair_score_standard_error = standard_error;
    report.lower_confidence_bound = lower_bound;
    let unfinished_per_mille = if report.games.is_empty() {
        0
    } else {
        u64::from(report.unfinished) * 1_000 / report.games.len() as u64
    };
    report.decision = if unfinished_per_mille > u64::from(config.maximum_unfinished_per_mille) {
        CandidateValidationDecision::RejectedUnfinishedRate
    } else if lower_bound > 0.5 + config.minimum_score_margin {
        CandidateValidationDecision::Accepted
    } else {
        CandidateValidationDecision::RejectedStrength
    };
    report.checksum = report.computed_checksum();
    report.validate()?;
    Ok(report)
}

/// Writes validation evidence through a caller-selected same-directory temporary file.
pub fn write_candidate_validation_report_atomic(
    destination: &Path,
    temporary: &Path,
    report: &CandidateValidationReport,
) -> Result<(), ToolError> {
    if destination == temporary
        || destination.parent().unwrap_or_else(|| Path::new("."))
            != temporary.parent().unwrap_or_else(|| Path::new("."))
    {
        return Err(ToolError::new(
            "validation destination and temporary paths must differ and share one directory",
        ));
    }
    let text = report.serialize()?;
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(temporary)
        .map_err(|error| {
            ToolError::new(format!(
                "failed to create temporary validation report {}: {error}",
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
            "failed to write temporary validation report {}: {error}",
            temporary.display()
        )));
    }
    drop(file);
    if let Err(error) = fs::rename(temporary, destination) {
        let _ = fs::remove_file(temporary);
        return Err(ToolError::new(format!(
            "failed to rename candidate-validation report {}: {error}",
            destination.display()
        )));
    }
    Ok(())
}

fn run_correctness_suite(
    candidate: &EvaluationWeightSet,
    perft_depth: u8,
) -> Result<CandidateCorrectnessSummary, ToolError> {
    if !(1..=5).contains(&perft_depth) {
        return Err(ToolError::new(
            "candidate perft depth must be between one and five",
        ));
    }
    let fixtures = perft_fixtures()?;
    let mut perft_cases = 0_u32;
    let mut perft_passed = true;
    for fixture in fixtures {
        for depth in 1..=perft_depth {
            let expected = fixture.expected[usize::from(depth - 1)];
            let actual = perft(fixture.fen, depth)?;
            perft_cases = perft_cases
                .checked_add(1)
                .ok_or_else(|| ToolError::new("perft case count overflow"))?;
            perft_passed &= actual == expected;
        }
    }

    let tactical = [
        (
            "7k/5Q2/6K1/8/8/8/8/8 w - - 0 1",
            3_u16,
            &["f7e8", "f7f8", "f7g7", "f7h7"][..],
        ),
        ("4Q2k/8/4K3/8/8/8/8/8 b - - 0 1", 6_u16, &["h8g7"][..]),
    ];
    let mut tactical_passed = true;
    for (fen, depth, acceptable) in tactical {
        let mut position =
            Position::from_fen(fen).map_err(|error| ToolError::new(error.to_string()))?;
        let mut history = SearchHistory::from_position(&position);
        let mut table =
            TranspositionTable::new(8).map_err(|error| ToolError::new(error.to_string()))?;
        let search = iterative_deepening_search_with_limits_and_transposition_table_and_weights(
            &mut position,
            &mut history,
            SearchLimits::new().with_depth(depth),
            &mut table,
            &candidate.weights,
        )
        .map_err(|error| ToolError::new(error.to_string()))?;
        let selected = search.best_move().map(|current| current.to_uci());
        tactical_passed &= selected
            .as_deref()
            .is_some_and(|value| acceptable.contains(&value));
    }

    Ok(CandidateCorrectnessSummary {
        perft_depth,
        perft_cases,
        perft_passed,
        tactical_cases: 2,
        tactical_passed,
    })
}

fn append_game(
    report: &mut CandidateValidationReport,
    pair_index: u32,
    pair_seed: u64,
    opening_identifier: &str,
    candidate_color: CandidateColor,
    game: crate::self_play::WeightedValidationGame,
    score: f64,
) -> Result<(), ToolError> {
    match game.result() {
        SelfPlayResult::WhiteWin | SelfPlayResult::BlackWin => {
            let candidate_won = matches!(
                (game.result(), candidate_color),
                (SelfPlayResult::WhiteWin, CandidateColor::White)
                    | (SelfPlayResult::BlackWin, CandidateColor::Black)
            );
            if candidate_won {
                report.candidate_wins = report
                    .candidate_wins
                    .checked_add(1)
                    .ok_or_else(|| ToolError::new("candidate win count overflow"))?;
            } else {
                report.candidate_losses = report
                    .candidate_losses
                    .checked_add(1)
                    .ok_or_else(|| ToolError::new("candidate loss count overflow"))?;
            }
        }
        SelfPlayResult::Draw => {
            report.draws = report
                .draws
                .checked_add(1)
                .ok_or_else(|| ToolError::new("draw count overflow"))?;
        }
        SelfPlayResult::Unfinished => {
            report.unfinished = report
                .unfinished
                .checked_add(1)
                .ok_or_else(|| ToolError::new("unfinished count overflow"))?;
        }
    }
    report.games.push(CandidateValidationGame {
        pair_index,
        pair_seed,
        opening_identifier: opening_identifier.to_owned(),
        candidate_color,
        result: game.result(),
        termination: game.termination(),
        candidate_score: score,
        moves: game.moves().to_vec(),
        final_fen: game.final_fen().to_owned(),
    });
    Ok(())
}

fn candidate_score(result: SelfPlayResult, candidate_color: CandidateColor) -> f64 {
    match result {
        SelfPlayResult::WhiteWin => {
            if candidate_color == CandidateColor::White {
                1.0
            } else {
                0.0
            }
        }
        SelfPlayResult::BlackWin => {
            if candidate_color == CandidateColor::Black {
                1.0
            } else {
                0.0
            }
        }
        SelfPlayResult::Draw | SelfPlayResult::Unfinished => 0.5,
    }
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
        mean - ONE_SIDED_95_PERCENT_Z * standard_error,
    ))
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

fn named_artifact_error(error: NamedWeightArtifactError) -> ToolError {
    ToolError::new(format!("invalid candidate artifact: {error}"))
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

fn float_field(output: &mut String, name: &str, value: f64) {
    writeln!(output, "{name}={value:.17e}\tbits={:016x}", value.to_bits())
        .expect("writing to String cannot fail");
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
    use chess_search::EvaluationWeights;

    use crate::self_play::SelfPlayLimit;
    use chess_tune::{
        NamedWeightArtifact, TrainingDatasetProvenance, TrainingMetadata, TrainingRunProvenance,
    };

    use super::*;

    fn artifact() -> NamedWeightArtifact {
        NamedWeightArtifact::new(
            0x4341_4e44_4944_3031,
            TrainingMetadata::new(
                TrainingRunProvenance::new(1, [7; 20], 9, 1, 1),
                TrainingDatasetProvenance::new(1, 2, 1, 1),
            ),
            EvaluationWeights::DEFAULT,
        )
        .expect("candidate artifact")
    }

    fn openings() -> OpeningSuite {
        OpeningSuite::from_text(concat!(
            "CHESS_SELF_PLAY_OPENINGS\t1\n",
            "king-pawn\trnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\te2e4 e7e5\n",
        ))
        .expect("opening suite")
    }

    #[test]
    fn production_configuration_enforces_four_hundred_games() {
        let side = SelfPlaySideConfig::new(1, SelfPlayLimit::Depth(1));
        assert!(CandidateValidationConfig::new(199, 1, side).is_err());
        assert!(CandidateValidationConfig::new(200, 1, side).is_ok());
    }

    #[test]
    fn candidate_score_is_color_relative_and_unfinished_is_separate() {
        assert_eq!(
            candidate_score(SelfPlayResult::WhiteWin, CandidateColor::White),
            1.0
        );
        assert_eq!(
            candidate_score(SelfPlayResult::WhiteWin, CandidateColor::Black),
            0.0
        );
        assert_eq!(
            candidate_score(SelfPlayResult::Draw, CandidateColor::White),
            0.5
        );
        assert_eq!(
            candidate_score(SelfPlayResult::Unfinished, CandidateColor::Black),
            0.5
        );
    }

    #[test]
    fn confidence_summary_uses_independent_pair_scores() {
        let (mean, standard_error, lower) =
            summarize_pair_scores(&[0.25, 0.5, 0.75, 1.0]).expect("summary");
        assert_eq!(mean, 0.625);
        assert!(standard_error > 0.0);
        assert!(lower < mean);
    }

    #[test]
    fn small_internal_run_is_color_balanced_deterministic_and_inactive() {
        let side = SelfPlaySideConfig::new(1, SelfPlayLimit::Depth(1));
        let config = CandidateValidationConfig {
            pair_count: 1,
            seed: 42,
            side,
            maximum_plies: 6,
            claimable_draw_policy: ClaimableDrawPolicy::Accept,
            minimum_score_margin: 0.0,
            maximum_unfinished_per_mille: 1_000,
        };
        let provenance = CandidateValidationProvenance::new(
            1,
            "test".to_owned(),
            [1; 20],
            "candidate-test".to_owned(),
        )
        .expect("provenance");
        let first = run_candidate_validation_internal(
            provenance.clone(),
            config,
            &openings(),
            &artifact(),
            1,
            1,
        )
        .expect("first run");
        let second =
            run_candidate_validation_internal(provenance, config, &openings(), &artifact(), 1, 1)
                .expect("second run");
        assert_eq!(first, second);
        assert_eq!(first.games.len(), 2);
        assert_ne!(
            first.games[0].candidate_color,
            first.games[1].candidate_color
        );
        assert_eq!(
            first.games[0].opening_identifier,
            first.games[1].opening_identifier
        );
        assert!(!first.activated());
        assert_eq!(first.checksum, first.computed_checksum());
        assert!(first
            .serialize()
            .expect("serialize")
            .contains("activated=false"));
    }
}
