//! Fail-closed evidence protocol for selectively proposed classical terms.
//!
//! Task 22 experiments never mutate the built-in evaluator. Each candidate area
//! is represented by a deterministic overlap probe over existing weights so the
//! protocol can measure symmetry, evaluation cost, fixed-node search behavior,
//! and color-balanced match behavior before any new runtime feature is added.

use core::fmt;
use std::{
    collections::HashSet,
    fmt::Write as _,
    fs::{self, OpenOptions},
    io::Write,
    path::Path,
    time::Instant,
};

use chess_core::{Color, Game, Position, SearchHistory};
use chess_search::{
    evaluate_with_weights,
    iterative_deepening_search_with_limits_and_transposition_table_and_weights, EvaluationWeights,
    PhasedWeight, SearchLimits, TranspositionTable,
};

use crate::{
    self_play::{
        run_weighted_validation_game, ClaimableDrawPolicy, OpeningSuite, SelfPlayResult,
        SelfPlaySideConfig, WeightedValidationGameConfig,
    },
    ToolError,
};

/// Current line-oriented Task 22 evidence schema.
pub const ADVANCED_EVALUATION_REPORT_SCHEMA_VERSION: u16 = 1;
/// Minimum independent color-balanced pairs required before any strength claim.
pub const ADVANCED_EVALUATION_MINIMUM_ACCEPTANCE_PAIRS: u32 = 200;

const FORMAT_MARKER: &str = "CHESS_ADVANCED_EVALUATION_REPORT";
const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;
const ONE_SIDED_95_Z: f64 = 1.644_853_626_951_472_2;

/// Stable Task 22 candidate-area identity.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum AdvancedTermArea {
    /// Pawn majorities and not-yet-passed candidate passers.
    PawnMajorityCandidatePasser,
    /// Attacker-weighted pressure in the enemy king zone.
    KingZoneAttackUnits,
    /// Coordination of pieces defending the king and critical entry squares.
    DefenderCoordination,
    /// Aligned rook-and-queen pressure on a file or rank.
    RookQueenBattery,
    /// Stable minor-piece outposts and bishops restricted by their own pawns.
    MinorOutpostsBadBishops,
    /// King distance and promotion timing in sparse passed-pawn endings.
    EndgameKingPasserRaces,
    /// General exchange preference tied to a durable material advantage.
    SimplificationIncentive,
    /// Additional phase-specific piece-square or material scaling.
    EndgamePhaseSpecificScaling,
}

impl AdvancedTermArea {
    /// Every candidate area in tracker order.
    pub const ALL: [Self; 8] = [
        Self::PawnMajorityCandidatePasser,
        Self::KingZoneAttackUnits,
        Self::DefenderCoordination,
        Self::RookQueenBattery,
        Self::MinorOutpostsBadBishops,
        Self::EndgameKingPasserRaces,
        Self::SimplificationIncentive,
        Self::EndgamePhaseSpecificScaling,
    ];

    /// Stable machine-readable area name.
    #[must_use]
    pub const fn name(self) -> &'static str {
        match self {
            Self::PawnMajorityCandidatePasser => "pawn_majority_candidate_passer",
            Self::KingZoneAttackUnits => "king_zone_attack_units",
            Self::DefenderCoordination => "defender_coordination",
            Self::RookQueenBattery => "rook_queen_battery",
            Self::MinorOutpostsBadBishops => "minor_outposts_bad_bishops",
            Self::EndgameKingPasserRaces => "endgame_king_passer_races",
            Self::SimplificationIncentive => "simplification_incentive",
            Self::EndgamePhaseSpecificScaling => "endgame_phase_specific_scaling",
        }
    }

    /// Concise chess definition used in every evidence record.
    #[must_use]
    pub const fn definition(self) -> &'static str {
        match self {
            Self::PawnMajorityCandidatePasser => {
                "reward a local pawn majority and a pawn that can become passed after favorable exchanges"
            }
            Self::KingZoneAttackUnits => {
                "weight attacks in the enemy king zone by attacker type and coordinated participation"
            }
            Self::DefenderCoordination => {
                "reward mutually supported defenders of the king zone and critical entry squares"
            }
            Self::RookQueenBattery => {
                "reward a rook and queen aligned with useful pressure along one rank or file"
            }
            Self::MinorOutpostsBadBishops => {
                "reward stable advanced minor-piece squares and penalize bishops restricted by own pawns"
            }
            Self::EndgameKingPasserRaces => {
                "compare king distance, pawn tempo, and promotion timing in sparse passed-pawn endings"
            }
            Self::SimplificationIncentive => {
                "prefer exchanges only when a durable material lead survives into the reduced position"
            }
            Self::EndgamePhaseSpecificScaling => {
                "apply additional endgame-specific piece-square tables or material scaling"
            }
        }
    }

    /// Existing compact-baseline coverage that may overlap the proposal.
    #[must_use]
    pub const fn overlap(self) -> &'static str {
        match self {
            Self::PawnMajorityCandidatePasser => {
                "passed-pawn, connected-pawn, advancement, and tapered pawn weights"
            }
            Self::KingZoneAttackUnits => "enemy-attacked king-zone squares and pawn-shield terms",
            Self::DefenderCoordination => {
                "mobility, pawn shield, king-zone pressure, space, and piece-square tables"
            }
            Self::RookQueenBattery => {
                "rook open/semi-open files, rook seventh rank, queen mobility, and space"
            }
            Self::MinorOutpostsBadBishops => {
                "minor-piece mobility, piece-square tables, connected pawns, and bishop pair"
            }
            Self::EndgameKingPasserRaces => "passed-pawn advancement and tapered king activity",
            Self::SimplificationIncentive => {
                "tapered material values and ordinary search evaluation after exchanges"
            }
            Self::EndgamePhaseSpecificScaling => {
                "every material and piece-square value already has middlegame/endgame phases"
            }
        }
    }

    const fn fixture_fens(self) -> [&'static str; 2] {
        match self {
            Self::PawnMajorityCandidatePasser => [
                "4k3/8/2pp4/8/2PPP3/8/8/4K3 w - - 0 1",
                "4k3/8/3p4/2pP4/2P5/8/8/4K3 w - - 0 1",
            ],
            Self::KingZoneAttackUnits => [
                "6k1/5ppp/8/4NQ2/8/8/6PP/6K1 w - - 0 1",
                "6k1/5ppp/8/3B4/6Q1/8/6PP/6K1 w - - 0 1",
            ],
            Self::DefenderCoordination => [
                "6k1/5ppp/8/8/8/5N2/5PPP/5RK1 w - - 0 1",
                "6k1/5ppp/8/8/8/3B1N2/5PPP/5RK1 w - - 0 1",
            ],
            Self::RookQueenBattery => [
                "6k1/5ppp/8/8/8/3R4/5PPP/3Q2K1 w - - 0 1",
                "6k1/5ppp/8/8/3R4/8/5PPP/3Q2K1 w - - 0 1",
            ],
            Self::MinorOutpostsBadBishops => [
                "4k3/2p5/8/3N4/2P5/8/5PPP/4K3 w - - 0 1",
                "4k3/8/8/8/2P1P3/3B4/2P2PPP/4K3 w - - 0 1",
            ],
            Self::EndgameKingPasserRaces => [
                "4k3/8/8/3P4/8/8/4K3/8 w - - 0 1",
                "7k/8/5P2/8/8/8/4K3/8 w - - 0 1",
            ],
            Self::SimplificationIncentive => [
                "7k/8/8/8/8/8/4R3/4K3 w - - 0 1",
                "7k/8/8/8/8/8/3QR3/4K3 w - - 0 1",
            ],
            Self::EndgamePhaseSpecificScaling => [
                "4k3/8/8/8/3N4/8/4p3/4K3 w - - 0 1",
                "4k3/8/8/8/3R4/8/4p3/4K3 w - - 0 1",
            ],
        }
    }

    const fn is_overlap_rejection(self) -> bool {
        matches!(
            self,
            Self::DefenderCoordination | Self::EndgamePhaseSpecificScaling
        )
    }
}

impl fmt::Display for AdvancedTermArea {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(self.name())
    }
}

/// Fail-closed outcome for one proposed area.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum AdvancedTermDecision {
    /// A separate term would duplicate the compact evaluator without an independent signal.
    RejectedOverlap,
    /// The deterministic overlap probe did not establish a strength benefit.
    RejectedNoStrengthEvidence,
    /// The probe warrants a dedicated implementation and a new production validation run.
    ReviseDedicatedImplementation,
}

impl fmt::Display for AdvancedTermDecision {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::RejectedOverlap => "rejected_overlap",
            Self::RejectedNoStrengthEvidence => "rejected_no_strength_evidence",
            Self::ReviseDedicatedImplementation => "revise_dedicated_implementation",
        })
    }
}

/// Fixed configuration for a Task 22 evidence run.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct AdvancedEvaluationConfig {
    pair_count: u32,
    seed: u64,
    side: SelfPlaySideConfig,
    maximum_plies: u32,
    benchmark_iterations: u64,
    fixed_nodes: u64,
}

impl AdvancedEvaluationConfig {
    /// Creates a deterministic evidence configuration.
    #[must_use]
    pub const fn new(
        pair_count: u32,
        seed: u64,
        side: SelfPlaySideConfig,
        benchmark_iterations: u64,
        fixed_nodes: u64,
    ) -> Self {
        Self {
            pair_count,
            seed,
            side,
            maximum_plies: 64,
            benchmark_iterations,
            fixed_nodes,
        }
    }

    /// Sets the maximum game length without turning unfinished games into draws.
    #[must_use]
    pub const fn with_maximum_plies(mut self, maximum_plies: u32) -> Self {
        self.maximum_plies = maximum_plies;
        self
    }

    /// Returns the independent opening-pair count.
    #[must_use]
    pub const fn pair_count(self) -> u32 {
        self.pair_count
    }

    fn validate(self, openings: &OpeningSuite) -> Result<(), ToolError> {
        if self.pair_count == 0 {
            return Err(ToolError::new(
                "advanced-evaluation protocol requires at least one opening pair",
            ));
        }
        if self.benchmark_iterations == 0 || self.fixed_nodes == 0 {
            return Err(ToolError::new(
                "advanced-evaluation benchmark iterations and fixed nodes must be nonzero",
            ));
        }
        let required = usize::try_from(self.pair_count)
            .map_err(|_| ToolError::new("advanced-evaluation pair count exceeds usize"))?;
        if openings.lines().len() < required {
            return Err(ToolError::new(format!(
                "advanced-evaluation protocol requires {required} distinct openings, found {}",
                openings.lines().len()
            )));
        }
        let mut semantic = HashSet::with_capacity(openings.lines().len());
        for opening in openings.lines() {
            if !semantic.insert((opening.initial_fen().to_owned(), opening.moves().to_vec())) {
                return Err(ToolError::new(
                    "advanced-evaluation opening suite contains duplicate semantic openings",
                ));
            }
        }
        WeightedValidationGameConfig::new(
            self.side,
            self.side,
            self.maximum_plies,
            ClaimableDrawPolicy::Accept,
        )?;
        Ok(())
    }
}

/// Measured evidence for one candidate area.
#[derive(Clone, Debug, PartialEq)]
pub struct AdvancedTermEvidence {
    /// Stable area identity.
    pub area: AdvancedTermArea,
    /// Number of isolated white-perspective fixtures; every fixture is mirrored.
    pub fixture_count: u32,
    /// Whether baseline and probe evaluations passed exact mirror/color symmetry.
    pub symmetry_passed: bool,
    /// Informational baseline static-evaluation time.
    pub baseline_evaluation_nanos: u128,
    /// Informational overlap-probe static-evaluation time.
    pub probe_evaluation_nanos: u128,
    /// Number of fixed-node positions, including mirrors.
    pub fixed_node_positions: u32,
    /// Positions where the probe changed the deterministic best move.
    pub best_move_changes: u32,
    /// Sum of absolute centipawn differences where both searches completed a score.
    pub absolute_score_delta_sum: i64,
    /// Total baseline production nodes entered.
    pub baseline_nodes: u64,
    /// Total overlap-probe production nodes entered.
    pub probe_nodes: u64,
    /// Candidate wins in the color-balanced match.
    pub candidate_wins: u32,
    /// Completed draws in the color-balanced match.
    pub draws: u32,
    /// Candidate losses in the color-balanced match.
    pub candidate_losses: u32,
    /// Explicit maximum-ply unfinished games.
    pub unfinished: u32,
    /// Mean independent pair score from the candidate perspective.
    pub mean_pair_score: f64,
    /// Sample standard error across independent pair scores.
    pub pair_score_standard_error: f64,
    /// One-sided 95% lower confidence bound.
    pub lower_confidence_bound: f64,
    /// Fail-closed disposition.
    pub decision: AdvancedTermDecision,
}

/// Complete versioned Task 22 evidence record.
#[derive(Clone, Debug, PartialEq)]
pub struct AdvancedEvaluationReport {
    /// Exact evidence-run configuration.
    pub config: AdvancedEvaluationConfig,
    /// Evidence in stable tracker order.
    pub terms: Vec<AdvancedTermEvidence>,
    /// Canonical semantic checksum.
    pub checksum: u64,
}

impl AdvancedEvaluationReport {
    /// Reports are evidence only and can never activate evaluator behavior.
    #[must_use]
    pub const fn activated(&self) -> bool {
        false
    }

    /// Computes the canonical FNV-1a checksum.
    #[must_use]
    pub fn computed_checksum(&self) -> u64 {
        let mut hash = FNV_OFFSET;
        hash = hash_bytes(
            hash,
            &ADVANCED_EVALUATION_REPORT_SCHEMA_VERSION.to_le_bytes(),
        );
        hash = hash_bytes(hash, &self.config.pair_count.to_le_bytes());
        hash = hash_bytes(hash, &self.config.seed.to_le_bytes());
        hash = hash_bytes(hash, &self.config.maximum_plies.to_le_bytes());
        hash = hash_bytes(
            hash,
            &(self.config.side.transposition_table_mebibytes() as u64).to_le_bytes(),
        );
        hash = hash_text(hash, &self.config.side.limit().to_string());
        hash = hash_bytes(
            hash,
            &[u8::from(self.config.side.check_extension_enabled())],
        );
        hash = hash_bytes(hash, &self.config.benchmark_iterations.to_le_bytes());
        hash = hash_bytes(hash, &self.config.fixed_nodes.to_le_bytes());
        for term in &self.terms {
            hash = hash_text(hash, term.area.name());
            hash = hash_text(hash, term.area.definition());
            hash = hash_text(hash, term.area.overlap());
            hash = hash_bytes(hash, &term.fixture_count.to_le_bytes());
            hash = hash_bytes(hash, &[u8::from(term.symmetry_passed)]);
            hash = hash_bytes(hash, &term.baseline_evaluation_nanos.to_le_bytes());
            hash = hash_bytes(hash, &term.probe_evaluation_nanos.to_le_bytes());
            hash = hash_bytes(hash, &term.fixed_node_positions.to_le_bytes());
            hash = hash_bytes(hash, &term.best_move_changes.to_le_bytes());
            hash = hash_bytes(hash, &term.absolute_score_delta_sum.to_le_bytes());
            hash = hash_bytes(hash, &term.baseline_nodes.to_le_bytes());
            hash = hash_bytes(hash, &term.probe_nodes.to_le_bytes());
            hash = hash_bytes(hash, &term.candidate_wins.to_le_bytes());
            hash = hash_bytes(hash, &term.draws.to_le_bytes());
            hash = hash_bytes(hash, &term.candidate_losses.to_le_bytes());
            hash = hash_bytes(hash, &term.unfinished.to_le_bytes());
            hash = hash_bytes(hash, &term.mean_pair_score.to_bits().to_le_bytes());
            hash = hash_bytes(
                hash,
                &term.pair_score_standard_error.to_bits().to_le_bytes(),
            );
            hash = hash_bytes(hash, &term.lower_confidence_bound.to_bits().to_le_bytes());
            hash = hash_text(hash, &term.decision.to_string());
        }
        hash
    }

    /// Validates completeness, ordering, finite statistics, symmetry, and checksum.
    pub fn validate(&self) -> Result<(), ToolError> {
        if self.terms.len() != AdvancedTermArea::ALL.len() {
            return Err(ToolError::new(
                "advanced-evaluation report does not contain every Task 22 area",
            ));
        }
        for (expected, term) in AdvancedTermArea::ALL.into_iter().zip(&self.terms) {
            if term.area != expected {
                return Err(ToolError::new(
                    "advanced-evaluation report term order is not canonical",
                ));
            }
            if !term.symmetry_passed || term.fixture_count < 2 {
                return Err(ToolError::new(format!(
                    "advanced-evaluation area {} lacks isolated symmetric fixtures",
                    term.area
                )));
            }
            for value in [
                term.mean_pair_score,
                term.pair_score_standard_error,
                term.lower_confidence_bound,
            ] {
                if !value.is_finite() {
                    return Err(ToolError::new(
                        "advanced-evaluation match statistics must be finite",
                    ));
                }
            }
            let game_count = term
                .candidate_wins
                .saturating_add(term.draws)
                .saturating_add(term.candidate_losses)
                .saturating_add(term.unfinished);
            if game_count != self.config.pair_count.saturating_mul(2) {
                return Err(ToolError::new(format!(
                    "advanced-evaluation area {} has inconsistent match counts",
                    term.area
                )));
            }
        }
        if self.checksum != self.computed_checksum() {
            return Err(ToolError::new(
                "advanced-evaluation report checksum mismatch",
            ));
        }
        Ok(())
    }

    /// Serializes deterministic line-oriented evidence with exact float bits.
    pub fn serialize(&self) -> Result<String, ToolError> {
        self.validate()?;
        let mut output = String::new();
        writeln!(
            output,
            "{FORMAT_MARKER}\t{ADVANCED_EVALUATION_REPORT_SCHEMA_VERSION}"
        )
        .expect("writing to String cannot fail");
        writeln!(output, "pair_count={}", self.config.pair_count)
            .expect("writing to String cannot fail");
        writeln!(output, "seed={}", self.config.seed).expect("writing to String cannot fail");
        writeln!(output, "maximum_plies={}", self.config.maximum_plies)
            .expect("writing to String cannot fail");
        writeln!(
            output,
            "transposition_table_mebibytes={}",
            self.config.side.transposition_table_mebibytes()
        )
        .expect("writing to String cannot fail");
        writeln!(output, "search_limit={}", self.config.side.limit())
            .expect("writing to String cannot fail");
        writeln!(
            output,
            "check_extension={}",
            self.config.side.check_extension_enabled()
        )
        .expect("writing to String cannot fail");
        writeln!(
            output,
            "benchmark_iterations={}",
            self.config.benchmark_iterations
        )
        .expect("writing to String cannot fail");
        writeln!(output, "fixed_nodes={}", self.config.fixed_nodes)
            .expect("writing to String cannot fail");
        writeln!(
            output,
            "minimum_acceptance_pairs={ADVANCED_EVALUATION_MINIMUM_ACCEPTANCE_PAIRS}"
        )
        .expect("writing to String cannot fail");
        writeln!(output, "activated={}", self.activated()).expect("writing to String cannot fail");
        for (index, term) in self.terms.iter().enumerate() {
            let prefix = format!("term.{index}");
            writeln!(output, "{prefix}.area={}", term.area).expect("writing to String cannot fail");
            writeln!(output, "{prefix}.definition={}", term.area.definition())
                .expect("writing to String cannot fail");
            writeln!(output, "{prefix}.overlap={}", term.area.overlap())
                .expect("writing to String cannot fail");
            writeln!(output, "{prefix}.fixture_count={}", term.fixture_count)
                .expect("writing to String cannot fail");
            writeln!(output, "{prefix}.symmetry_passed={}", term.symmetry_passed)
                .expect("writing to String cannot fail");
            writeln!(
                output,
                "{prefix}.baseline_evaluation_nanos={}",
                term.baseline_evaluation_nanos
            )
            .expect("writing to String cannot fail");
            writeln!(
                output,
                "{prefix}.probe_evaluation_nanos={}",
                term.probe_evaluation_nanos
            )
            .expect("writing to String cannot fail");
            writeln!(
                output,
                "{prefix}.fixed_node_positions={}",
                term.fixed_node_positions
            )
            .expect("writing to String cannot fail");
            writeln!(
                output,
                "{prefix}.best_move_changes={}",
                term.best_move_changes
            )
            .expect("writing to String cannot fail");
            writeln!(
                output,
                "{prefix}.absolute_score_delta_sum={}",
                term.absolute_score_delta_sum
            )
            .expect("writing to String cannot fail");
            writeln!(output, "{prefix}.baseline_nodes={}", term.baseline_nodes)
                .expect("writing to String cannot fail");
            writeln!(output, "{prefix}.probe_nodes={}", term.probe_nodes)
                .expect("writing to String cannot fail");
            writeln!(output, "{prefix}.candidate_wins={}", term.candidate_wins)
                .expect("writing to String cannot fail");
            writeln!(output, "{prefix}.draws={}", term.draws)
                .expect("writing to String cannot fail");
            writeln!(
                output,
                "{prefix}.candidate_losses={}",
                term.candidate_losses
            )
            .expect("writing to String cannot fail");
            writeln!(output, "{prefix}.unfinished={}", term.unfinished)
                .expect("writing to String cannot fail");
            writeln!(
                output,
                "{prefix}.mean_pair_score_bits={:016x}",
                term.mean_pair_score.to_bits()
            )
            .expect("writing to String cannot fail");
            writeln!(
                output,
                "{prefix}.standard_error_bits={:016x}",
                term.pair_score_standard_error.to_bits()
            )
            .expect("writing to String cannot fail");
            writeln!(
                output,
                "{prefix}.lower_bound_bits={:016x}",
                term.lower_confidence_bound.to_bits()
            )
            .expect("writing to String cannot fail");
            writeln!(output, "{prefix}.decision={}", term.decision)
                .expect("writing to String cannot fail");
        }
        writeln!(output, "checksum={:016x}", self.checksum).expect("writing to String cannot fail");
        Ok(output)
    }
}

/// Runs the complete Task 22 evidence protocol without modifying runtime defaults.
pub fn run_advanced_evaluation_protocol(
    config: AdvancedEvaluationConfig,
    openings: &OpeningSuite,
) -> Result<AdvancedEvaluationReport, ToolError> {
    config.validate(openings)?;
    let baseline = EvaluationWeights::DEFAULT;
    let mut terms = Vec::with_capacity(AdvancedTermArea::ALL.len());
    for (area_index, area) in AdvancedTermArea::ALL.into_iter().enumerate() {
        let probe = overlap_probe(area);
        let fixtures = fixture_positions(area)?;
        verify_symmetry(&fixtures, &baseline, &probe)?;
        let (baseline_evaluation_nanos, probe_evaluation_nanos) =
            benchmark_weights(&fixtures, config.benchmark_iterations, &baseline, &probe);
        let search = fixed_node_comparison(&fixtures, config.fixed_nodes, &baseline, &probe)?;
        let match_evidence = run_controlled_match(
            config,
            openings,
            u64::try_from(area_index).expect("Task 22 area index fits u64"),
            &baseline,
            &probe,
        )?;
        let decision = decide(
            area,
            config.pair_count,
            match_evidence.lower_confidence_bound,
        );
        terms.push(AdvancedTermEvidence {
            area,
            fixture_count: u32::try_from(fixtures.len() / 2)
                .expect("Task 22 fixture count fits u32"),
            symmetry_passed: true,
            baseline_evaluation_nanos,
            probe_evaluation_nanos,
            fixed_node_positions: u32::try_from(fixtures.len())
                .expect("Task 22 fixed-node fixture count fits u32"),
            best_move_changes: search.best_move_changes,
            absolute_score_delta_sum: search.absolute_score_delta_sum,
            baseline_nodes: search.baseline_nodes,
            probe_nodes: search.probe_nodes,
            candidate_wins: match_evidence.candidate_wins,
            draws: match_evidence.draws,
            candidate_losses: match_evidence.candidate_losses,
            unfinished: match_evidence.unfinished,
            mean_pair_score: match_evidence.mean_pair_score,
            pair_score_standard_error: match_evidence.standard_error,
            lower_confidence_bound: match_evidence.lower_confidence_bound,
            decision,
        });
    }
    let mut report = AdvancedEvaluationReport {
        config,
        terms,
        checksum: 0,
    };
    report.checksum = report.computed_checksum();
    report.validate()?;
    Ok(report)
}

/// Atomically persists one Task 22 evidence record through an explicit temp path.
pub fn write_advanced_evaluation_report_atomic(
    destination: &Path,
    temporary: &Path,
    report: &AdvancedEvaluationReport,
) -> Result<(), ToolError> {
    if destination == temporary
        || destination.parent().unwrap_or_else(|| Path::new("."))
            != temporary.parent().unwrap_or_else(|| Path::new("."))
    {
        return Err(ToolError::new(
            "advanced-evaluation destination and temporary paths must differ and share one directory",
        ));
    }
    let text = report.serialize()?;
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(temporary)
        .map_err(|error| {
            ToolError::new(format!(
                "failed to create temporary advanced-evaluation report {}: {error}",
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
            "failed to write temporary advanced-evaluation report {}: {error}",
            temporary.display()
        )));
    }
    drop(file);
    if let Err(error) = fs::rename(temporary, destination) {
        let _ = fs::remove_file(temporary);
        return Err(ToolError::new(format!(
            "failed to rename advanced-evaluation report {}: {error}",
            destination.display()
        )));
    }
    if let Some(parent) = destination.parent() {
        OpenOptions::new()
            .read(true)
            .open(parent)
            .and_then(|directory| directory.sync_all())
            .map_err(|error| {
                ToolError::new(format!(
                    "failed to synchronize advanced-evaluation report directory {}: {error}",
                    parent.display()
                ))
            })?;
    }
    Ok(())
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
struct FixedNodeEvidence {
    best_move_changes: u32,
    absolute_score_delta_sum: i64,
    baseline_nodes: u64,
    probe_nodes: u64,
}

#[derive(Clone, Copy, Debug, Default, PartialEq)]
struct MatchEvidence {
    candidate_wins: u32,
    draws: u32,
    candidate_losses: u32,
    unfinished: u32,
    mean_pair_score: f64,
    standard_error: f64,
    lower_confidence_bound: f64,
}

fn fixture_positions(area: AdvancedTermArea) -> Result<Vec<Position>, ToolError> {
    let mut positions = Vec::with_capacity(4);
    for fen in area.fixture_fens() {
        let original = Position::from_fen(fen).map_err(|error| {
            ToolError::new(format!("invalid Task 22 fixture for {area}: {error}"))
        })?;
        let mirrored_fen = mirror_and_swap_fen(fen)?;
        let mirrored = Position::from_fen(&mirrored_fen).map_err(|error| {
            ToolError::new(format!(
                "invalid mirrored Task 22 fixture for {area}: {error}"
            ))
        })?;
        positions.push(original);
        positions.push(mirrored);
    }
    Ok(positions)
}

fn mirror_and_swap_fen(fen: &str) -> Result<String, ToolError> {
    let fields: Vec<_> = fen.split_ascii_whitespace().collect();
    if fields.len() != 6 || fields[3] != "-" {
        return Err(ToolError::new(
            "Task 22 mirror helper requires a six-field FEN without en passant",
        ));
    }
    let ranks: Vec<_> = fields[0].split('/').collect();
    if ranks.len() != 8 {
        return Err(ToolError::new(
            "Task 22 fixture board must contain eight ranks",
        ));
    }
    let board = ranks
        .into_iter()
        .rev()
        .map(|rank| {
            rank.chars()
                .map(|character| {
                    if character.is_ascii_lowercase() {
                        character.to_ascii_uppercase()
                    } else if character.is_ascii_uppercase() {
                        character.to_ascii_lowercase()
                    } else {
                        character
                    }
                })
                .collect::<String>()
        })
        .collect::<Vec<_>>()
        .join("/");
    let side = match fields[1] {
        "w" => "b",
        "b" => "w",
        _ => return Err(ToolError::new("Task 22 fixture has invalid side to move")),
    };
    if fields[2] != "-" {
        return Err(ToolError::new(
            "Task 22 mirror helper requires fixtures without castling rights",
        ));
    }
    Ok(format!("{board} {side} - - {} {}", fields[4], fields[5]))
}

fn verify_symmetry(
    fixtures: &[Position],
    baseline: &EvaluationWeights,
    probe: &EvaluationWeights,
) -> Result<(), ToolError> {
    for pair in fixtures.chunks_exact(2) {
        let baseline_original = evaluate_with_weights(&pair[0], baseline);
        let baseline_mirror = evaluate_with_weights(&pair[1], baseline);
        let probe_original = evaluate_with_weights(&pair[0], probe);
        let probe_mirror = evaluate_with_weights(&pair[1], probe);
        if baseline_original != baseline_mirror || probe_original != probe_mirror {
            return Err(ToolError::new(
                "Task 22 fixture failed exact color-and-vertical-mirror symmetry",
            ));
        }
    }
    Ok(())
}

fn benchmark_weights(
    fixtures: &[Position],
    iterations: u64,
    baseline: &EvaluationWeights,
    probe: &EvaluationWeights,
) -> (u128, u128) {
    let baseline_started = Instant::now();
    let mut baseline_checksum = 0_i64;
    for _ in 0..iterations {
        for position in fixtures {
            baseline_checksum = baseline_checksum.wrapping_add(i64::from(
                evaluate_with_weights(position, baseline).centipawns(),
            ));
        }
    }
    let baseline_nanos = baseline_started.elapsed().as_nanos();

    let probe_started = Instant::now();
    let mut probe_checksum = 0_i64;
    for _ in 0..iterations {
        for position in fixtures {
            probe_checksum = probe_checksum.wrapping_add(i64::from(
                evaluate_with_weights(position, probe).centipawns(),
            ));
        }
    }
    let probe_nanos = probe_started.elapsed().as_nanos();
    std::hint::black_box((baseline_checksum, probe_checksum));
    (baseline_nanos, probe_nanos)
}

fn fixed_node_comparison(
    fixtures: &[Position],
    fixed_nodes: u64,
    baseline: &EvaluationWeights,
    probe: &EvaluationWeights,
) -> Result<FixedNodeEvidence, ToolError> {
    let mut evidence = FixedNodeEvidence::default();
    for fixture in fixtures {
        let baseline_result = search_fixture(fixture, fixed_nodes, baseline)?;
        let probe_result = search_fixture(fixture, fixed_nodes, probe)?;
        evidence.baseline_nodes = evidence
            .baseline_nodes
            .checked_add(baseline_result.nodes())
            .ok_or_else(|| ToolError::new("Task 22 baseline node total overflow"))?;
        evidence.probe_nodes = evidence
            .probe_nodes
            .checked_add(probe_result.nodes())
            .ok_or_else(|| ToolError::new("Task 22 probe node total overflow"))?;
        if baseline_result.best_move() != probe_result.best_move() {
            evidence.best_move_changes = evidence.best_move_changes.saturating_add(1);
        }
        if let (Some(baseline_score), Some(probe_score)) =
            (baseline_result.score(), probe_result.score())
        {
            evidence.absolute_score_delta_sum =
                evidence.absolute_score_delta_sum.saturating_add(i64::from(
                    baseline_score
                        .centipawns()
                        .abs_diff(probe_score.centipawns()),
                ));
        }
    }
    Ok(evidence)
}

fn search_fixture(
    fixture: &Position,
    fixed_nodes: u64,
    weights: &EvaluationWeights,
) -> Result<chess_search::SearchResult, ToolError> {
    let mut position = fixture.clone();
    let mut history = SearchHistory::from_position(&position);
    let mut table = TranspositionTable::new(1)
        .map_err(|error| ToolError::new(format!("Task 22 TT allocation failed: {error}")))?;
    iterative_deepening_search_with_limits_and_transposition_table_and_weights(
        &mut position,
        &mut history,
        SearchLimits::new().with_nodes(fixed_nodes),
        &mut table,
        weights,
    )
    .map_err(|error| ToolError::new(format!("Task 22 fixed-node search failed: {error}")))
}

fn run_controlled_match(
    config: AdvancedEvaluationConfig,
    openings: &OpeningSuite,
    area_index: u64,
    baseline: &EvaluationWeights,
    probe: &EvaluationWeights,
) -> Result<MatchEvidence, ToolError> {
    let match_config = WeightedValidationGameConfig::new(
        config.side,
        config.side,
        config.maximum_plies,
        ClaimableDrawPolicy::Accept,
    )?;
    let opening_offset =
        (splitmix64(config.seed ^ area_index) % openings.lines().len() as u64) as usize;
    let mut evidence = MatchEvidence::default();
    let mut pair_scores = Vec::with_capacity(config.pair_count as usize);
    for pair_index in 0..config.pair_count {
        let opening =
            &openings.lines()[(opening_offset + pair_index as usize) % openings.lines().len()];
        let candidate_white = run_weighted_validation_game(opening, match_config, probe, baseline)?;
        let candidate_black = run_weighted_validation_game(opening, match_config, baseline, probe)?;
        let white_score = record_result(&mut evidence, candidate_white.result(), Color::White);
        let black_score = record_result(&mut evidence, candidate_black.result(), Color::Black);
        pair_scores.push((white_score + black_score) * 0.5);
    }
    let (mean, standard_error, lower_bound) = summarize_pair_scores(&pair_scores)?;
    evidence.mean_pair_score = mean;
    evidence.standard_error = standard_error;
    evidence.lower_confidence_bound = lower_bound;
    Ok(evidence)
}

fn record_result(evidence: &mut MatchEvidence, result: SelfPlayResult, candidate: Color) -> f64 {
    match (result, candidate) {
        (SelfPlayResult::WhiteWin, Color::White) | (SelfPlayResult::BlackWin, Color::Black) => {
            evidence.candidate_wins = evidence.candidate_wins.saturating_add(1);
            1.0
        }
        (SelfPlayResult::WhiteWin, Color::Black) | (SelfPlayResult::BlackWin, Color::White) => {
            evidence.candidate_losses = evidence.candidate_losses.saturating_add(1);
            0.0
        }
        (SelfPlayResult::Draw, _) => {
            evidence.draws = evidence.draws.saturating_add(1);
            0.5
        }
        (SelfPlayResult::Unfinished, _) => {
            evidence.unfinished = evidence.unfinished.saturating_add(1);
            0.5
        }
    }
}

fn summarize_pair_scores(scores: &[f64]) -> Result<(f64, f64, f64), ToolError> {
    if scores.is_empty() {
        return Err(ToolError::new(
            "Task 22 controlled match produced no pair scores",
        ));
    }
    let count = scores.len() as f64;
    let mean = scores.iter().sum::<f64>() / count;
    let variance = if scores.len() > 1 {
        scores
            .iter()
            .map(|score| {
                let difference = score - mean;
                difference * difference
            })
            .sum::<f64>()
            / (count - 1.0)
    } else {
        0.0
    };
    let standard_error = (variance / count).sqrt();
    let lower_bound = mean - ONE_SIDED_95_Z * standard_error;
    Ok((mean, standard_error, lower_bound))
}

fn decide(
    area: AdvancedTermArea,
    pair_count: u32,
    lower_confidence_bound: f64,
) -> AdvancedTermDecision {
    if area.is_overlap_rejection() {
        return AdvancedTermDecision::RejectedOverlap;
    }
    if pair_count >= ADVANCED_EVALUATION_MINIMUM_ACCEPTANCE_PAIRS && lower_confidence_bound > 0.5 {
        AdvancedTermDecision::ReviseDedicatedImplementation
    } else {
        AdvancedTermDecision::RejectedNoStrengthEvidence
    }
}

fn overlap_probe(area: AdvancedTermArea) -> EvaluationWeights {
    let mut weights = EvaluationWeights::DEFAULT;
    match area {
        AdvancedTermArea::PawnMajorityCandidatePasser => {
            add_weight(&mut weights.passed_pawn, 4, 8);
            add_weight(&mut weights.connected_pawn, 2, 4);
        }
        AdvancedTermArea::KingZoneAttackUnits => {
            add_weight(&mut weights.king_zone_attack, -2, -1);
        }
        AdvancedTermArea::DefenderCoordination => {
            add_weight(&mut weights.king_shield, 2, 0);
            add_weight(
                &mut weights.mobility[chess_core::PieceKind::Knight.index()],
                1,
                1,
            );
            add_weight(
                &mut weights.mobility[chess_core::PieceKind::Bishop.index()],
                1,
                1,
            );
        }
        AdvancedTermArea::RookQueenBattery => {
            add_weight(&mut weights.rook_open_file, 4, 2);
            add_weight(&mut weights.rook_semi_open_file, 2, 1);
            add_weight(
                &mut weights.mobility[chess_core::PieceKind::Queen.index()],
                1,
                1,
            );
        }
        AdvancedTermArea::MinorOutpostsBadBishops => {
            add_weight(
                &mut weights.mobility[chess_core::PieceKind::Knight.index()],
                1,
                1,
            );
            add_weight(
                &mut weights.mobility[chess_core::PieceKind::Bishop.index()],
                1,
                1,
            );
            add_weight(&mut weights.bishop_pair, 4, 4);
        }
        AdvancedTermArea::EndgameKingPasserRaces => {
            add_weight(&mut weights.passed_pawn, 0, 12);
            add_weight(&mut weights.king_activity, 0, 4);
        }
        AdvancedTermArea::SimplificationIncentive => {
            add_weight(
                &mut weights.material[chess_core::PieceKind::Knight.index()],
                0,
                -4,
            );
            add_weight(
                &mut weights.material[chess_core::PieceKind::Bishop.index()],
                0,
                -4,
            );
            add_weight(
                &mut weights.material[chess_core::PieceKind::Rook.index()],
                0,
                -6,
            );
            add_weight(
                &mut weights.material[chess_core::PieceKind::Queen.index()],
                0,
                -8,
            );
        }
        AdvancedTermArea::EndgamePhaseSpecificScaling => {}
    }
    weights
}

fn add_weight(weight: &mut PhasedWeight, middlegame: i16, endgame: i16) {
    weight.middlegame = weight
        .middlegame
        .checked_add(middlegame)
        .expect("Task 22 overlap probe stays within i16");
    weight.endgame = weight
        .endgame
        .checked_add(endgame)
        .expect("Task 22 overlap probe stays within i16");
}

fn splitmix64(mut value: u64) -> u64 {
    value = value.wrapping_add(0x9e37_79b9_7f4a_7c15);
    let mut mixed = value;
    mixed = (mixed ^ (mixed >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
    mixed = (mixed ^ (mixed >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
    mixed ^ (mixed >> 31)
}

fn hash_bytes(mut hash: u64, bytes: &[u8]) -> u64 {
    for byte in bytes {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    hash
}

fn hash_text(hash: u64, value: &str) -> u64 {
    let hash = hash_bytes(hash, &(value.len() as u64).to_le_bytes());
    hash_bytes(hash, value.as_bytes())
}

#[cfg(test)]
mod tests {
    use std::{env, fs};

    use chess_core::Game;

    use crate::{
        self_play::{SelfPlayLimit, SelfPlaySideConfig},
        STARTING_FEN,
    };

    use super::*;

    fn openings(count: usize) -> OpeningSuite {
        let starting = Game::starting();
        let mut starting_position = starting.position().clone();
        let white_moves = starting_position
            .legal_moves()
            .expect("starting legal moves");
        let mut text = String::from("CHESS_SELF_PLAY_OPENINGS\t1\n");
        let mut generated = 0_usize;
        for white in white_moves.iter() {
            let mut after_white = starting.clone();
            after_white
                .make_move(white)
                .expect("generated White move is legal");
            let mut black_position = after_white.position().clone();
            let black_moves = black_position.legal_moves().expect("Black legal replies");
            for black in black_moves.iter() {
                writeln!(
                    text,
                    "task22-{generated:03}\t{STARTING_FEN}\t{} {}",
                    white.to_uci(),
                    black.to_uci()
                )
                .expect("writing opening text cannot fail");
                generated += 1;
                if generated == count {
                    return OpeningSuite::from_text(&text)
                        .expect("generated Task 22 opening suite");
                }
            }
        }
        panic!("starting two-ply tree did not contain enough Task 22 openings");
    }

    #[test]
    fn task22_area_contract_is_complete_unique_and_stable() {
        let names: HashSet<_> = AdvancedTermArea::ALL
            .into_iter()
            .map(AdvancedTermArea::name)
            .collect();
        assert_eq!(names.len(), AdvancedTermArea::ALL.len());
        assert_eq!(
            AdvancedTermArea::ALL[0].name(),
            "pawn_majority_candidate_passer"
        );
        assert_eq!(
            AdvancedTermArea::ALL[7].name(),
            "endgame_phase_specific_scaling"
        );
    }

    #[test]
    fn every_isolated_fixture_and_probe_is_exactly_symmetric() {
        for area in AdvancedTermArea::ALL {
            let fixtures = fixture_positions(area).expect("fixtures parse");
            assert_eq!(fixtures.len(), 4);
            verify_symmetry(&fixtures, &EvaluationWeights::DEFAULT, &overlap_probe(area))
                .expect("fixture symmetry");
        }
    }

    #[test]
    fn small_protocol_is_complete_checksummed_and_inactive() {
        let side = SelfPlaySideConfig::new(1, SelfPlayLimit::Depth(1));
        let config = AdvancedEvaluationConfig::new(1, 0x2201, side, 1, 8).with_maximum_plies(4);
        let report =
            run_advanced_evaluation_protocol(config, &openings(1)).expect("small Task 22 protocol");
        assert_eq!(report.terms.len(), AdvancedTermArea::ALL.len());
        assert_eq!(report.checksum, report.computed_checksum());
        assert!(!report.activated());
        assert!(report
            .terms
            .iter()
            .all(|term| term.decision != AdvancedTermDecision::ReviseDedicatedImplementation));
        assert!(report
            .serialize()
            .expect("serializes")
            .contains("activated=false"));
    }

    #[test]
    fn atomic_report_write_uses_explicit_same_directory_temp_path() {
        let side = SelfPlaySideConfig::new(1, SelfPlayLimit::Depth(1));
        let config = AdvancedEvaluationConfig::new(1, 0x2202, side, 1, 8).with_maximum_plies(4);
        let report =
            run_advanced_evaluation_protocol(config, &openings(1)).expect("small Task 22 protocol");
        let directory = env::temp_dir().join(format!(
            "chess-task22-{}-{}",
            std::process::id(),
            report.checksum
        ));
        fs::create_dir_all(&directory).expect("temp directory");
        let destination = directory.join("report.txt");
        let temporary = directory.join("report.tmp");
        write_advanced_evaluation_report_atomic(&destination, &temporary, &report)
            .expect("atomic report write");
        assert_eq!(
            fs::read_to_string(&destination).expect("persisted report"),
            report.serialize().expect("serialized report")
        );
        assert!(!temporary.exists());
        fs::remove_dir_all(directory).expect("remove temp directory");
    }

    #[test]
    #[ignore = "Task 22 controlled evidence run"]
    fn task22_controlled_evidence_run() {
        let pair_count = 32;
        let side = SelfPlaySideConfig::new(1, SelfPlayLimit::Depth(1));
        let config = AdvancedEvaluationConfig::new(pair_count, 0x2200_0022, side, 2_000, 512)
            .with_maximum_plies(8);
        let report = run_advanced_evaluation_protocol(config, &openings(pair_count as usize))
            .expect("Task 22 controlled evidence");
        println!(
            "{}",
            report.serialize().expect("Task 22 report serialization")
        );
        assert_eq!(report.terms.len(), 8);
        assert!(!report.activated());
        assert!(report.terms.iter().all(|term| {
            matches!(
                term.decision,
                AdvancedTermDecision::RejectedOverlap
                    | AdvancedTermDecision::RejectedNoStrengthEvidence
            )
        }));
    }
}
