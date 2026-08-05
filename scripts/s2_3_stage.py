#!/usr/bin/env python3
from pathlib import Path

def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one occurrence, found {count}: {old[:100]!r}")
    p.write_text(text.replace(old, new, 1))

def replace_all(path: str, old: str, new: str, expected: int) -> None:
    p = Path(path)
    text = p.read_text()
    count = text.count(old)
    if count != expected:
        raise SystemExit(f"{path}: expected {expected} occurrences, found {count}: {old[:100]!r}")
    p.write_text(text.replace(old, new))

Path("crates/chess-search/src/diagnostics.rs").write_text(r'''use core::fmt;

const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;

/// One bounded deterministic search counter.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SearchDiagnosticCounter {
    MainNodes,
    QuiescenceNodes,
    BetaCutoffs,
    FirstMoveBetaCutoffs,
    QuiescenceBetaCutoffs,
    QuiescenceFirstMoveBetaCutoffs,
    QuiescenceStandPatCutoffs,
    PvsZeroWindowSearches,
    PvsResearches,
    SeeCalls,
    SeePrunes,
    QuiescenceSeePrunes,
    QuiescenceDeltaPrunes,
    LmrReductions,
    LmrResearches,
    NullMoveAttempts,
    NullMoveCutoffs,
    FrontierFutilityPrunes,
    FrontierRazorAttempts,
    LateMovePrunes,
}

impl fmt::Display for SearchDiagnosticCounter {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::MainNodes => "main_nodes",
            Self::QuiescenceNodes => "quiescence_nodes",
            Self::BetaCutoffs => "beta_cutoffs",
            Self::FirstMoveBetaCutoffs => "first_move_beta_cutoffs",
            Self::QuiescenceBetaCutoffs => "quiescence_beta_cutoffs",
            Self::QuiescenceFirstMoveBetaCutoffs => "quiescence_first_move_beta_cutoffs",
            Self::QuiescenceStandPatCutoffs => "quiescence_stand_pat_cutoffs",
            Self::PvsZeroWindowSearches => "pvs_zero_window_searches",
            Self::PvsResearches => "pvs_researches",
            Self::SeeCalls => "see_calls",
            Self::SeePrunes => "see_prunes",
            Self::QuiescenceSeePrunes => "quiescence_see_prunes",
            Self::QuiescenceDeltaPrunes => "quiescence_delta_prunes",
            Self::LmrReductions => "lmr_reductions",
            Self::LmrResearches => "lmr_researches",
            Self::NullMoveAttempts => "null_move_attempts",
            Self::NullMoveCutoffs => "null_move_cutoffs",
            Self::FrontierFutilityPrunes => "frontier_futility_prunes",
            Self::FrontierRazorAttempts => "frontier_razor_attempts",
            Self::LateMovePrunes => "late_move_prunes",
        })
    }
}

/// Checked diagnostic accumulation overflow.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct SearchDiagnosticOverflow {
    counter: SearchDiagnosticCounter,
}

impl SearchDiagnosticOverflow {
    const fn new(counter: SearchDiagnosticCounter) -> Self {
        Self { counter }
    }

    /// Returns the exact counter that overflowed.
    #[must_use]
    pub const fn counter(self) -> SearchDiagnosticCounter {
        self.counter
    }
}

impl fmt::Display for SearchDiagnosticOverflow {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "search diagnostic counter {} overflowed", self.counter)
    }
}

impl std::error::Error for SearchDiagnosticOverflow {}

/// One allocation-free search event.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SearchDiagnosticEvent {
    MainNode,
    QuiescenceNode,
    BetaCutoff { first_move: bool },
    QuiescenceBetaCutoff { first_move: bool },
    QuiescenceStandPatCutoff,
    PvsZeroWindowSearch,
    PvsResearch,
    SeeCall,
    SeePrune,
    QuiescenceSeePrune,
    QuiescenceDeltaPrune,
    LmrReduction,
    LmrResearch,
    NullMoveAttempt,
    NullMoveCutoff,
    FrontierFutilityPrune,
    FrontierRazorAttempt,
    LateMovePrune,
}

/// Deterministic allocation-free diagnostics for one search scope.
///
/// Completed exact search results use checked accumulation and fail loudly on
/// overflow. Request-wide limit accounting cannot return an error from an
/// observation hook, so it saturates the affected counter and sets
/// [`Self::overflowed`].
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct SearchDiagnostics {
    main_nodes: u64,
    quiescence_nodes: u64,
    beta_cutoffs: u64,
    first_move_beta_cutoffs: u64,
    quiescence_beta_cutoffs: u64,
    quiescence_first_move_beta_cutoffs: u64,
    quiescence_stand_pat_cutoffs: u64,
    pvs_zero_window_searches: u64,
    pvs_researches: u64,
    see_calls: u64,
    see_prunes: u64,
    quiescence_see_prunes: u64,
    quiescence_delta_prunes: u64,
    lmr_reductions: u64,
    lmr_researches: u64,
    null_move_attempts: u64,
    null_move_cutoffs: u64,
    frontier_futility_prunes: u64,
    frontier_razor_attempts: u64,
    late_move_prunes: u64,
    overflowed: bool,
}

impl SearchDiagnostics {
    const EMPTY: Self = Self {
        main_nodes: 0,
        quiescence_nodes: 0,
        beta_cutoffs: 0,
        first_move_beta_cutoffs: 0,
        quiescence_beta_cutoffs: 0,
        quiescence_first_move_beta_cutoffs: 0,
        quiescence_stand_pat_cutoffs: 0,
        pvs_zero_window_searches: 0,
        pvs_researches: 0,
        see_calls: 0,
        see_prunes: 0,
        quiescence_see_prunes: 0,
        quiescence_delta_prunes: 0,
        lmr_reductions: 0,
        lmr_researches: 0,
        null_move_attempts: 0,
        null_move_cutoffs: 0,
        frontier_futility_prunes: 0,
        frontier_razor_attempts: 0,
        late_move_prunes: 0,
        overflowed: false,
    };

    /// Returns a single entered main-search node.
    #[must_use]
    pub const fn main_node() -> Self {
        Self {
            main_nodes: 1,
            ..Self::EMPTY
        }
    }

    /// Returns a single entered quiescence node.
    #[must_use]
    pub const fn quiescence_node() -> Self {
        Self {
            quiescence_nodes: 1,
            ..Self::EMPTY
        }
    }

    /// Checked event recording for completed exact results.
    pub fn record_checked(
        &mut self,
        event: SearchDiagnosticEvent,
    ) -> Result<(), SearchDiagnosticOverflow> {
        match event {
            SearchDiagnosticEvent::MainNode => {
                increment_checked(&mut self.main_nodes, SearchDiagnosticCounter::MainNodes)
            }
            SearchDiagnosticEvent::QuiescenceNode => increment_checked(
                &mut self.quiescence_nodes,
                SearchDiagnosticCounter::QuiescenceNodes,
            ),
            SearchDiagnosticEvent::BetaCutoff { first_move } => {
                increment_checked(
                    &mut self.beta_cutoffs,
                    SearchDiagnosticCounter::BetaCutoffs,
                )?;
                if first_move {
                    increment_checked(
                        &mut self.first_move_beta_cutoffs,
                        SearchDiagnosticCounter::FirstMoveBetaCutoffs,
                    )?;
                }
                Ok(())
            }
            SearchDiagnosticEvent::QuiescenceBetaCutoff { first_move } => {
                increment_checked(
                    &mut self.quiescence_beta_cutoffs,
                    SearchDiagnosticCounter::QuiescenceBetaCutoffs,
                )?;
                if first_move {
                    increment_checked(
                        &mut self.quiescence_first_move_beta_cutoffs,
                        SearchDiagnosticCounter::QuiescenceFirstMoveBetaCutoffs,
                    )?;
                }
                Ok(())
            }
            SearchDiagnosticEvent::QuiescenceStandPatCutoff => increment_checked(
                &mut self.quiescence_stand_pat_cutoffs,
                SearchDiagnosticCounter::QuiescenceStandPatCutoffs,
            ),
            SearchDiagnosticEvent::PvsZeroWindowSearch => increment_checked(
                &mut self.pvs_zero_window_searches,
                SearchDiagnosticCounter::PvsZeroWindowSearches,
            ),
            SearchDiagnosticEvent::PvsResearch => {
                increment_checked(&mut self.pvs_researches, SearchDiagnosticCounter::PvsResearches)
            }
            SearchDiagnosticEvent::SeeCall => {
                increment_checked(&mut self.see_calls, SearchDiagnosticCounter::SeeCalls)
            }
            SearchDiagnosticEvent::SeePrune => {
                increment_checked(&mut self.see_prunes, SearchDiagnosticCounter::SeePrunes)
            }
            SearchDiagnosticEvent::QuiescenceSeePrune => increment_checked(
                &mut self.quiescence_see_prunes,
                SearchDiagnosticCounter::QuiescenceSeePrunes,
            ),
            SearchDiagnosticEvent::QuiescenceDeltaPrune => increment_checked(
                &mut self.quiescence_delta_prunes,
                SearchDiagnosticCounter::QuiescenceDeltaPrunes,
            ),
            SearchDiagnosticEvent::LmrReduction => {
                increment_checked(&mut self.lmr_reductions, SearchDiagnosticCounter::LmrReductions)
            }
            SearchDiagnosticEvent::LmrResearch => {
                increment_checked(&mut self.lmr_researches, SearchDiagnosticCounter::LmrResearches)
            }
            SearchDiagnosticEvent::NullMoveAttempt => increment_checked(
                &mut self.null_move_attempts,
                SearchDiagnosticCounter::NullMoveAttempts,
            ),
            SearchDiagnosticEvent::NullMoveCutoff => increment_checked(
                &mut self.null_move_cutoffs,
                SearchDiagnosticCounter::NullMoveCutoffs,
            ),
            SearchDiagnosticEvent::FrontierFutilityPrune => increment_checked(
                &mut self.frontier_futility_prunes,
                SearchDiagnosticCounter::FrontierFutilityPrunes,
            ),
            SearchDiagnosticEvent::FrontierRazorAttempt => increment_checked(
                &mut self.frontier_razor_attempts,
                SearchDiagnosticCounter::FrontierRazorAttempts,
            ),
            SearchDiagnosticEvent::LateMovePrune => increment_checked(
                &mut self.late_move_prunes,
                SearchDiagnosticCounter::LateMovePrunes,
            ),
        }
    }

    /// Saturating event recording for request-wide observation hooks.
    pub fn saturating_record(&mut self, event: SearchDiagnosticEvent) {
        if self.record_checked(event).is_err() {
            self.overflowed = true;
        }
    }

    /// Checked deterministic addition.
    pub fn checked_add(self, other: Self) -> Result<Self, SearchDiagnosticOverflow> {
        macro_rules! sum {
            ($field:ident, $counter:ident) => {
                self.$field
                    .checked_add(other.$field)
                    .ok_or_else(|| SearchDiagnosticOverflow::new(SearchDiagnosticCounter::$counter))?
            };
        }
        Ok(Self {
            main_nodes: sum!(main_nodes, MainNodes),
            quiescence_nodes: sum!(quiescence_nodes, QuiescenceNodes),
            beta_cutoffs: sum!(beta_cutoffs, BetaCutoffs),
            first_move_beta_cutoffs: sum!(first_move_beta_cutoffs, FirstMoveBetaCutoffs),
            quiescence_beta_cutoffs: sum!(quiescence_beta_cutoffs, QuiescenceBetaCutoffs),
            quiescence_first_move_beta_cutoffs: sum!(
                quiescence_first_move_beta_cutoffs,
                QuiescenceFirstMoveBetaCutoffs
            ),
            quiescence_stand_pat_cutoffs: sum!(
                quiescence_stand_pat_cutoffs,
                QuiescenceStandPatCutoffs
            ),
            pvs_zero_window_searches: sum!(pvs_zero_window_searches, PvsZeroWindowSearches),
            pvs_researches: sum!(pvs_researches, PvsResearches),
            see_calls: sum!(see_calls, SeeCalls),
            see_prunes: sum!(see_prunes, SeePrunes),
            quiescence_see_prunes: sum!(quiescence_see_prunes, QuiescenceSeePrunes),
            quiescence_delta_prunes: sum!(quiescence_delta_prunes, QuiescenceDeltaPrunes),
            lmr_reductions: sum!(lmr_reductions, LmrReductions),
            lmr_researches: sum!(lmr_researches, LmrResearches),
            null_move_attempts: sum!(null_move_attempts, NullMoveAttempts),
            null_move_cutoffs: sum!(null_move_cutoffs, NullMoveCutoffs),
            frontier_futility_prunes: sum!(frontier_futility_prunes, FrontierFutilityPrunes),
            frontier_razor_attempts: sum!(frontier_razor_attempts, FrontierRazorAttempts),
            late_move_prunes: sum!(late_move_prunes, LateMovePrunes),
            overflowed: self.overflowed || other.overflowed,
        })
    }

    #[must_use]
    pub const fn main_nodes(self) -> u64 { self.main_nodes }
    #[must_use]
    pub const fn quiescence_nodes(self) -> u64 { self.quiescence_nodes }
    #[must_use]
    pub const fn beta_cutoffs(self) -> u64 { self.beta_cutoffs }
    #[must_use]
    pub const fn first_move_beta_cutoffs(self) -> u64 { self.first_move_beta_cutoffs }
    #[must_use]
    pub const fn quiescence_beta_cutoffs(self) -> u64 { self.quiescence_beta_cutoffs }
    #[must_use]
    pub const fn quiescence_first_move_beta_cutoffs(self) -> u64 {
        self.quiescence_first_move_beta_cutoffs
    }
    #[must_use]
    pub const fn quiescence_stand_pat_cutoffs(self) -> u64 {
        self.quiescence_stand_pat_cutoffs
    }
    #[must_use]
    pub const fn pvs_zero_window_searches(self) -> u64 { self.pvs_zero_window_searches }
    #[must_use]
    pub const fn pvs_researches(self) -> u64 { self.pvs_researches }
    #[must_use]
    pub const fn see_calls(self) -> u64 { self.see_calls }
    #[must_use]
    pub const fn see_prunes(self) -> u64 { self.see_prunes }
    #[must_use]
    pub const fn quiescence_see_prunes(self) -> u64 { self.quiescence_see_prunes }
    #[must_use]
    pub const fn quiescence_delta_prunes(self) -> u64 { self.quiescence_delta_prunes }
    #[must_use]
    pub const fn lmr_reductions(self) -> u64 { self.lmr_reductions }
    #[must_use]
    pub const fn lmr_researches(self) -> u64 { self.lmr_researches }
    #[must_use]
    pub const fn null_move_attempts(self) -> u64 { self.null_move_attempts }
    #[must_use]
    pub const fn null_move_cutoffs(self) -> u64 { self.null_move_cutoffs }
    #[must_use]
    pub const fn frontier_futility_prunes(self) -> u64 { self.frontier_futility_prunes }
    #[must_use]
    pub const fn frontier_razor_attempts(self) -> u64 { self.frontier_razor_attempts }
    #[must_use]
    pub const fn late_move_prunes(self) -> u64 { self.late_move_prunes }

    /// Whether request-wide saturating observation encountered overflow.
    #[must_use]
    pub const fn overflowed(self) -> bool {
        self.overflowed
    }

    /// Returns whether every reserved future-heuristic counter remains zero.
    #[must_use]
    pub const fn reserved_counters_are_zero(self) -> bool {
        self.pvs_zero_window_searches == 0
            && self.pvs_researches == 0
            && self.see_calls == 0
            && self.see_prunes == 0
            && self.quiescence_see_prunes == 0
            && self.quiescence_delta_prunes == 0
            && self.lmr_reductions == 0
            && self.lmr_researches == 0
            && self.null_move_attempts == 0
            && self.null_move_cutoffs == 0
            && self.frontier_futility_prunes == 0
            && self.frontier_razor_attempts == 0
            && self.late_move_prunes == 0
    }

    /// Deterministic semantic checksum over every counter and overflow state.
    #[must_use]
    pub fn semantic_checksum(self) -> u64 {
        let mut hash = FNV_OFFSET;
        for value in [
            self.main_nodes,
            self.quiescence_nodes,
            self.beta_cutoffs,
            self.first_move_beta_cutoffs,
            self.quiescence_beta_cutoffs,
            self.quiescence_first_move_beta_cutoffs,
            self.quiescence_stand_pat_cutoffs,
            self.pvs_zero_window_searches,
            self.pvs_researches,
            self.see_calls,
            self.see_prunes,
            self.quiescence_see_prunes,
            self.quiescence_delta_prunes,
            self.lmr_reductions,
            self.lmr_researches,
            self.null_move_attempts,
            self.null_move_cutoffs,
            self.frontier_futility_prunes,
            self.frontier_razor_attempts,
            self.late_move_prunes,
        ] {
            hash = hash_bytes(hash, &value.to_le_bytes());
        }
        hash_bytes(hash, &[self.overflowed as u8])
    }
}

fn increment_checked(
    value: &mut u64,
    counter: SearchDiagnosticCounter,
) -> Result<(), SearchDiagnosticOverflow> {
    *value = value
        .checked_add(1)
        .ok_or_else(|| SearchDiagnosticOverflow::new(counter))?;
    Ok(())
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
    use super::{SearchDiagnosticCounter, SearchDiagnosticEvent, SearchDiagnostics};

    #[test]
    fn baseline_reserved_counters_are_zero_and_checksum_is_stable() {
        let first = SearchDiagnostics::default();
        let second = SearchDiagnostics::default();
        assert!(first.reserved_counters_are_zero());
        assert_eq!(first.semantic_checksum(), second.semantic_checksum());
        assert_ne!(first.semantic_checksum(), 0);
    }

    #[test]
    fn checked_add_reports_the_exact_overflowing_counter() {
        let mut maximum = SearchDiagnostics::default();
        maximum.main_nodes = u64::MAX;
        let error = maximum
            .checked_add(SearchDiagnostics::main_node())
            .expect_err("overflow fails loudly");
        assert_eq!(error.counter(), SearchDiagnosticCounter::MainNodes);
    }

    #[test]
    fn saturating_observation_sets_the_overflow_flag() {
        let mut diagnostics = SearchDiagnostics::default();
        diagnostics.main_nodes = u64::MAX;
        diagnostics.saturating_record(SearchDiagnosticEvent::MainNode);
        assert_eq!(diagnostics.main_nodes(), u64::MAX);
        assert!(diagnostics.overflowed());
    }

    #[test]
    fn cutoff_events_are_deterministic_and_future_counters_stay_zero() {
        let mut diagnostics = SearchDiagnostics::main_node();
        diagnostics
            .record_checked(SearchDiagnosticEvent::BetaCutoff { first_move: true })
            .expect("small diagnostic counts fit");
        diagnostics
            .record_checked(SearchDiagnosticEvent::QuiescenceStandPatCutoff)
            .expect("small diagnostic counts fit");
        assert_eq!(diagnostics.beta_cutoffs(), 1);
        assert_eq!(diagnostics.first_move_beta_cutoffs(), 1);
        assert_eq!(diagnostics.quiescence_stand_pat_cutoffs(), 1);
        assert!(diagnostics.reserved_counters_are_zero());
    }
}
''')

replace_once("crates/chess-search/src/lib.rs", "mod check_extension;\nmod evaluation;", "mod check_extension;\nmod diagnostics;\nmod evaluation;")
replace_once(
    "crates/chess-search/src/lib.rs",
    "pub use check_extension::{\n    CheckExtensionDiagnostics, CheckExtensionEvent, MAX_CHECK_EXTENSIONS_PER_LINE,\n};\n",
    "pub use check_extension::{\n    CheckExtensionDiagnostics, CheckExtensionEvent, MAX_CHECK_EXTENSIONS_PER_LINE,\n};\npub use diagnostics::{\n    SearchDiagnosticCounter, SearchDiagnosticEvent, SearchDiagnosticOverflow, SearchDiagnostics,\n};\n",
)

replace_once("crates/chess-search/src/cancellation.rs", "use crate::CheckExtensionEvent;", "use crate::{CheckExtensionEvent, SearchDiagnosticEvent};")
replace_once(
    "crates/chess-search/src/cancellation.rs",
    "    fn on_check_extension(&mut self, _event: CheckExtensionEvent) {}\n}",
    "    fn on_check_extension(&mut self, _event: CheckExtensionEvent) {}\n\n    /// Records one allocation-free deterministic search diagnostic event.\n    ///\n    /// The default is observationally inert. Limit-aware controllers override\n    /// this hook so interrupted work remains visible without affecting search.\n    fn on_search_diagnostic(&mut self, _event: SearchDiagnosticEvent) {}\n}",
)

replace_once(
    "crates/chess-search/src/limits.rs",
    "    CheckExtensionDiagnostics, CheckExtensionEvent, SearchCancellationProbe, MAX_MATE_PLY,\n",
    "    CheckExtensionDiagnostics, CheckExtensionEvent, SearchCancellationProbe,\n    SearchDiagnosticEvent, SearchDiagnostics, MAX_MATE_PLY,\n",
)
replace_once("crates/chess-search/src/limits.rs", "    check_extension_diagnostics: CheckExtensionDiagnostics,\n    termination: Option<SearchLimitTermination>,", "    check_extension_diagnostics: CheckExtensionDiagnostics,\n    search_diagnostics: SearchDiagnostics,\n    termination: Option<SearchLimitTermination>,")
replace_once("crates/chess-search/src/limits.rs", "            check_extension_diagnostics: CheckExtensionDiagnostics::default(),\n            termination: None,", "            check_extension_diagnostics: CheckExtensionDiagnostics::default(),\n            search_diagnostics: SearchDiagnostics::default(),\n            termination: None,")
replace_once(
    "crates/chess-search/src/limits.rs",
    "    pub(crate) const fn check_extension_diagnostics(&self) -> CheckExtensionDiagnostics {\n        self.check_extension_diagnostics\n    }\n",
    "    pub(crate) const fn check_extension_diagnostics(&self) -> CheckExtensionDiagnostics {\n        self.check_extension_diagnostics\n    }\n\n    pub(crate) const fn search_diagnostics(&self) -> SearchDiagnostics {\n        self.search_diagnostics\n    }\n",
)
replace_once(
    "crates/chess-search/src/limits.rs",
    "        self.visited_nodes = self.visited_nodes.saturating_add(1);\n        if quiescence {\n            self.visited_qnodes = self.visited_qnodes.saturating_add(1);\n        }\n",
    "        self.visited_nodes = self.visited_nodes.saturating_add(1);\n        if quiescence {\n            self.visited_qnodes = self.visited_qnodes.saturating_add(1);\n            self.search_diagnostics\n                .saturating_record(SearchDiagnosticEvent::QuiescenceNode);\n        } else {\n            self.search_diagnostics\n                .saturating_record(SearchDiagnosticEvent::MainNode);\n        }\n",
)
replace_once(
    "crates/chess-search/src/limits.rs",
    "    fn on_check_extension(&mut self, event: CheckExtensionEvent) {\n        self.check_extension_diagnostics.record(event);\n    }\n}",
    "    fn on_check_extension(&mut self, event: CheckExtensionEvent) {\n        self.check_extension_diagnostics.record(event);\n    }\n\n    fn on_search_diagnostic(&mut self, event: SearchDiagnosticEvent) {\n        self.search_diagnostics.saturating_record(event);\n    }\n}",
)

replace_once("crates/chess-search/src/alpha_beta.rs", "    SearchCancellationProbe, SearchPolicy, TranspositionBound,\n", "    SearchCancellationProbe, SearchDiagnosticEvent, SearchDiagnosticOverflow,\n    SearchDiagnostics, SearchPolicy, TranspositionBound,\n")
replace_once("crates/chess-search/src/alpha_beta.rs", "    pub(crate) selective_depth: u16,\n}", "    pub(crate) selective_depth: u16,\n    pub(crate) diagnostics: SearchDiagnostics,\n}")
replace_once(
    "crates/chess-search/src/alpha_beta.rs",
    "    pub const fn selective_depth(self) -> u16 {\n        self.selective_depth\n    }\n}",
    "    pub const fn selective_depth(self) -> u16 {\n        self.selective_depth\n    }\n\n    /// Returns deterministic allocation-free search diagnostics.\n    #[must_use]\n    pub const fn diagnostics(self) -> SearchDiagnostics {\n        self.diagnostics\n    }\n}",
)
replace_once("crates/chess-search/src/alpha_beta.rs", "    /// Recursive node accumulation exceeded `u64`.\n    NodeCountOverflow,\n", "    /// Recursive node accumulation exceeded `u64`.\n    NodeCountOverflow,\n    /// Deterministic search diagnostic accumulation exceeded `u64`.\n    DiagnosticCountOverflow(SearchDiagnosticOverflow),\n")
replace_once("crates/chess-search/src/alpha_beta.rs", "            Self::NodeCountOverflow => formatter.write_str(\"alpha-beta node count overflow\"),\n", "            Self::NodeCountOverflow => formatter.write_str(\"alpha-beta node count overflow\"),\n            Self::DiagnosticCountOverflow(error) => error.fmt(formatter),\n")
replace_once(
    "crates/chess-search/src/alpha_beta.rs",
    "impl From<TranspositionScoreConversionError> for AlphaBetaSearchError {\n    fn from(value: TranspositionScoreConversionError) -> Self {\n        Self::TranspositionScoreConversion(value)\n    }\n}\n",
    "impl From<TranspositionScoreConversionError> for AlphaBetaSearchError {\n    fn from(value: TranspositionScoreConversionError) -> Self {\n        Self::TranspositionScoreConversion(value)\n    }\n}\n\nimpl From<SearchDiagnosticOverflow> for AlphaBetaSearchError {\n    fn from(value: SearchDiagnosticOverflow) -> Self {\n        Self::DiagnosticCountOverflow(value)\n    }\n}\n",
)
replace_once("crates/chess-search/src/alpha_beta.rs", "            selective_depth: ply,\n        });", "            selective_depth: ply,\n            diagnostics: SearchDiagnostics::main_node(),\n        });")
replace_once("crates/chess-search/src/alpha_beta.rs", "                        selective_depth: ply,\n                    });", "                        selective_depth: ply,\n                        diagnostics: SearchDiagnostics::main_node(),\n                    });")
replace_once("crates/chess-search/src/alpha_beta.rs", "    let mut selective_depth = ply;\n    let mut best_score = None;", "    let mut selective_depth = ply;\n    let mut diagnostics = SearchDiagnostics::main_node();\n    let mut best_score = None;")
replace_once("crates/chess-search/src/alpha_beta.rs", "    for token in ordered_tokens.iter() {", "    for (move_index, token) in ordered_tokens.iter().enumerate() {")
replace_once("crates/chess-search/src/alpha_beta.rs", "        selective_depth = selective_depth.max(child.selective_depth);\n        let score = -child.score;", "        selective_depth = selective_depth.max(child.selective_depth);\n        diagnostics = diagnostics.checked_add(child.diagnostics)?;\n        let score = -child.score;")
replace_once(
    "crates/chess-search/src/alpha_beta.rs",
    "        if alpha >= beta {\n            if context.ordering == MoveOrdering::Quiet {",
    "        if alpha >= beta {\n            let event = SearchDiagnosticEvent::BetaCutoff {\n                first_move: move_index == 0,\n            };\n            diagnostics.record_checked(event)?;\n            context.cancellation.on_search_diagnostic(event);\n            if context.ordering == MoveOrdering::Quiet {",
)
replace_once("crates/chess-search/src/alpha_beta.rs", "            qnodes,\n            selective_depth,\n        },", "            qnodes,\n            selective_depth,\n            diagnostics,\n        },")

replace_once("crates/chess-search/src/quiescence.rs", "    EvaluationWeights, Score, SearchCancellationProbe, MAX_MATE_PLY,\n", "    EvaluationWeights, Score, SearchCancellationProbe, SearchDiagnosticEvent,\n    SearchDiagnostics, MAX_MATE_PLY,\n")
replace_once("crates/chess-search/src/quiescence.rs", "            selective_depth: context.ply,\n        });", "            selective_depth: context.ply,\n            diagnostics: SearchDiagnostics::quiescence_node(),\n        });")
replace_once(
    "crates/chess-search/src/quiescence.rs",
    "        if stand_pat >= beta {\n            return Ok(AlphaBetaSearchResult {\n                score: stand_pat,\n                best_move: None,\n                nodes: 1,\n                qnodes: 1,\n                selective_depth: context.ply,\n            });\n        }",
    "        if stand_pat >= beta {\n            let event = SearchDiagnosticEvent::QuiescenceStandPatCutoff;\n            let mut diagnostics = SearchDiagnostics::quiescence_node();\n            diagnostics.record_checked(event)?;\n            cancellation.on_search_diagnostic(event);\n            return Ok(AlphaBetaSearchResult {\n                score: stand_pat,\n                best_move: None,\n                nodes: 1,\n                qnodes: 1,\n                selective_depth: context.ply,\n                diagnostics,\n            });\n        }",
)
replace_once("crates/chess-search/src/quiescence.rs", "                selective_depth: context.ply,\n            });", "                selective_depth: context.ply,\n                diagnostics: SearchDiagnostics::quiescence_node(),\n            });")
replace_once("crates/chess-search/src/quiescence.rs", "    let mut selective_depth = context.ply;\n    for token in ordered_tokens.iter() {", "    let mut selective_depth = context.ply;\n    let mut diagnostics = SearchDiagnostics::quiescence_node();\n    let mut searched_moves = 0_usize;\n    for token in ordered_tokens.iter() {")
replace_once("crates/chess-search/src/quiescence.rs", "        selective_depth = selective_depth.max(child.selective_depth);\n        let score = -child.score;", "        selective_depth = selective_depth.max(child.selective_depth);\n        diagnostics = diagnostics.checked_add(child.diagnostics)?;\n        let score = -child.score;")
replace_once(
    "crates/chess-search/src/quiescence.rs",
    "        if alpha >= beta {\n            break;\n        }\n",
    "        if alpha >= beta {\n            let event = SearchDiagnosticEvent::QuiescenceBetaCutoff {\n                first_move: searched_moves == 0,\n            };\n            diagnostics.record_checked(event)?;\n            cancellation.on_search_diagnostic(event);\n            break;\n        }\n        searched_moves = searched_moves.saturating_add(1);\n",
)
replace_once("crates/chess-search/src/quiescence.rs", "            qnodes,\n            selective_depth,\n        }),", "            qnodes,\n            selective_depth,\n            diagnostics,\n        }),")

replace_once("crates/chess-search/src/iterative_deepening.rs", "    EvaluationWeights, PrincipalVariation, Score, SearchCancellationProbe, SearchPolicy,\n", "    EvaluationWeights, PrincipalVariation, Score, SearchCancellationProbe,\n    SearchDiagnosticOverflow, SearchDiagnostics, SearchPolicy,\n")
replace_once("crates/chess-search/src/iterative_deepening.rs", "    selective_depth: u16,\n    principal_variation: PrincipalVariation,", "    selective_depth: u16,\n    search_diagnostics: SearchDiagnostics,\n    principal_variation: PrincipalVariation,")
replace_once(
    "crates/chess-search/src/iterative_deepening.rs",
    "    pub const fn selective_depth(&self) -> u16 {\n        self.selective_depth\n    }\n\n    /// Returns aspiration-window",
    "    pub const fn selective_depth(&self) -> u16 {\n        self.selective_depth\n    }\n\n    /// Returns deterministic diagnostics aggregated across all attempts.\n    #[must_use]\n    pub const fn search_diagnostics(&self) -> SearchDiagnostics {\n        self.search_diagnostics\n    }\n\n    /// Returns aspiration-window",
)
replace_once("crates/chess-search/src/iterative_deepening.rs", "    selective_depth: u16,\n}\n\nimpl<'a> SearchProgress", "    selective_depth: u16,\n    search_diagnostics: SearchDiagnostics,\n}\n\nimpl<'a> SearchProgress")
replace_once(
    "crates/chess-search/src/iterative_deepening.rs",
    "    pub const fn selective_depth(self) -> u16 {\n        self.selective_depth\n    }\n}\n\n/// Completed",
    "    pub const fn selective_depth(self) -> u16 {\n        self.selective_depth\n    }\n\n    /// Returns request-wide diagnostics through this exact completed depth.\n    #[must_use]\n    pub const fn search_diagnostics(self) -> SearchDiagnostics {\n        self.search_diagnostics\n    }\n}\n\n/// Completed",
)
replace_once("crates/chess-search/src/iterative_deepening.rs", "    total_qnodes: u64,\n    selective_depth: u16,\n}", "    total_qnodes: u64,\n    selective_depth: u16,\n    search_diagnostics: SearchDiagnostics,\n}")
replace_once(
    "crates/chess-search/src/iterative_deepening.rs",
    "    pub const fn selective_depth(&self) -> u16 {\n        self.selective_depth\n    }\n}\n\n/// Deterministic",
    "    pub const fn selective_depth(&self) -> u16 {\n        self.selective_depth\n    }\n\n    /// Returns checked diagnostics from every completed attempt and depth.\n    #[must_use]\n    pub const fn search_diagnostics(&self) -> SearchDiagnostics {\n        self.search_diagnostics\n    }\n}\n\n/// Deterministic",
)
replace_once("crates/chess-search/src/iterative_deepening.rs", "    check_extension_diagnostics: CheckExtensionDiagnostics,\n    fallback: Option<SearchCancellationFallback>,", "    check_extension_diagnostics: CheckExtensionDiagnostics,\n    search_diagnostics: SearchDiagnostics,\n    fallback: Option<SearchCancellationFallback>,")
replace_once(
    "crates/chess-search/src/iterative_deepening.rs",
    "    pub const fn check_extension_diagnostics(&self) -> CheckExtensionDiagnostics {\n        self.check_extension_diagnostics\n    }\n",
    "    pub const fn check_extension_diagnostics(&self) -> CheckExtensionDiagnostics {\n        self.check_extension_diagnostics\n    }\n\n    /// Returns request-wide deterministic diagnostics, including partial work.\n    #[must_use]\n    pub const fn search_diagnostics(&self) -> SearchDiagnostics {\n        self.search_diagnostics\n    }\n",
)
replace_once("crates/chess-search/src/iterative_deepening.rs", "    NodeCountOverflow {\n        /// Last depth completed before overflow was detected.\n        completed_depth: u16,\n    },\n}", "    NodeCountOverflow {\n        /// Last depth completed before overflow was detected.\n        completed_depth: u16,\n    },\n    /// Checked deterministic diagnostic aggregation overflowed.\n    DiagnosticCountOverflow(SearchDiagnosticOverflow),\n}")
replace_once("crates/chess-search/src/iterative_deepening.rs", "            Self::NodeCountOverflow { completed_depth } => write!(\n                formatter,\n                \"iterative-deepening node total overflowed after completing depth {completed_depth}\"\n            ),\n", "            Self::NodeCountOverflow { completed_depth } => write!(\n                formatter,\n                \"iterative-deepening node total overflowed after completing depth {completed_depth}\"\n            ),\n            Self::DiagnosticCountOverflow(error) => error.fmt(formatter),\n")
replace_once("crates/chess-search/src/iterative_deepening.rs", "impl std::error::Error for IterativeDeepeningSearchError {}\n", "impl std::error::Error for IterativeDeepeningSearchError {}\n\nimpl From<SearchDiagnosticOverflow> for IterativeDeepeningSearchError {\n    fn from(value: SearchDiagnosticOverflow) -> Self {\n        Self::DiagnosticCountOverflow(value)\n    }\n}\n")
replace_all("crates/chess-search/src/iterative_deepening.rs", "    let mut selective_depth = 0_u16;\n", "    let mut selective_depth = 0_u16;\n    let mut search_diagnostics = SearchDiagnostics::default();\n", 2)
replace_once("crates/chess-search/src/iterative_deepening.rs", "        selective_depth = selective_depth.max(iteration.selective_depth());\n        iterations.push(iteration);", "        selective_depth = selective_depth.max(iteration.selective_depth());\n        search_diagnostics = search_diagnostics.checked_add(iteration.search_diagnostics())?;\n        iterations.push(iteration);")
replace_once("crates/chess-search/src/iterative_deepening.rs", "        total_qnodes,\n        selective_depth,\n    ))", "        total_qnodes,\n        selective_depth,\n        search_diagnostics,\n    ))")
replace_once("crates/chess-search/src/iterative_deepening.rs", "completed_result(iterations, total_nodes, total_qnodes, selective_depth)", "completed_result(\n                    iterations,\n                    total_nodes,\n                    total_qnodes,\n                    selective_depth,\n                    search_diagnostics,\n                )")
replace_once("crates/chess-search/src/iterative_deepening.rs", "                                total_qnodes,\n                                selective_depth,\n                            ),", "                                total_qnodes,\n                                selective_depth,\n                                search_diagnostics,\n                            ),")
replace_once("crates/chess-search/src/iterative_deepening.rs", "        selective_depth = selective_depth.max(iteration.selective_depth());\n        observer(SearchProgress {", "        selective_depth = selective_depth.max(iteration.selective_depth());\n        search_diagnostics = search_diagnostics.checked_add(iteration.search_diagnostics())?;\n        observer(SearchProgress {")
replace_once("crates/chess-search/src/iterative_deepening.rs", "            selective_depth: controller.selective_depth(),\n        });", "            selective_depth: controller.selective_depth(),\n            search_diagnostics: controller.search_diagnostics(),\n        });")
replace_once("crates/chess-search/src/iterative_deepening.rs", "    selective_depth: u16,\n) -> IterativeDeepeningSearchResult {", "    selective_depth: u16,\n    search_diagnostics: SearchDiagnostics,\n) -> IterativeDeepeningSearchResult {")
replace_once("crates/chess-search/src/iterative_deepening.rs", "        total_qnodes,\n        selective_depth,\n    }\n}", "        total_qnodes,\n        selective_depth,\n        search_diagnostics,\n    }\n}")
replace_once("crates/chess-search/src/iterative_deepening.rs", "        check_extension_diagnostics: controller.check_extension_diagnostics(),\n        fallback,", "        check_extension_diagnostics: controller.check_extension_diagnostics(),\n        search_diagnostics: controller.search_diagnostics(),\n        fallback,")
replace_once("crates/chess-search/src/iterative_deepening.rs", "    let mut transposition_diagnostics = initial_attempt.transposition_diagnostics();\n", "    let mut transposition_diagnostics = initial_attempt.transposition_diagnostics();\n    let mut search_diagnostics = initial_result.result().diagnostics();\n")
replace_once("crates/chess-search/src/iterative_deepening.rs", "            transposition_diagnostics =\n                transposition_diagnostics.saturating_add(retry_attempt.transposition_diagnostics());", "            transposition_diagnostics =\n                transposition_diagnostics.saturating_add(retry_attempt.transposition_diagnostics());\n            search_diagnostics =\n                search_diagnostics.checked_add(retry_result.result().diagnostics())?;")
replace_once("crates/chess-search/src/iterative_deepening.rs", "        selective_depth,\n        principal_variation,", "        selective_depth,\n        search_diagnostics,\n        principal_variation,")

replace_once(
    "crates/chess-search/src/alpha_beta.rs",
    "    #[test]\n    fn equal_scores_keep_deterministic_first_best_move() {",
    "    #[test]\n    fn diagnostics_are_consistent_and_observationally_inert() {\n        let mut first_position = Position::starting();\n        let mut first_history = SearchHistory::from_position(&first_position);\n        let first = alpha_beta_search(&mut first_position, &mut first_history, 3)\n            .expect(\"diagnostic search succeeds\");\n\n        let mut second_position = Position::starting();\n        let mut second_history = SearchHistory::from_position(&second_position);\n        let second = alpha_beta_search(&mut second_position, &mut second_history, 3)\n            .expect(\"repeated diagnostic search succeeds\");\n\n        let diagnostics = first.diagnostics();\n        assert_eq!(first.score(), second.score());\n        assert_eq!(first.best_move(), second.best_move());\n        assert_eq!(first.nodes(), diagnostics.main_nodes() + diagnostics.quiescence_nodes());\n        assert_eq!(first.qnodes(), diagnostics.quiescence_nodes());\n        assert!(diagnostics.beta_cutoffs() > 0);\n        assert!(diagnostics.first_move_beta_cutoffs() <= diagnostics.beta_cutoffs());\n        assert!(diagnostics.reserved_counters_are_zero());\n        assert!(!diagnostics.overflowed());\n        assert_eq!(diagnostics, second.diagnostics());\n    }\n\n    #[test]\n    fn equal_scores_keep_deterministic_first_best_move() {",
)
replace_once(
    "crates/chess-search/src/iterative_deepening.rs",
    "        assert_eq!(result.completed_depth(), 3);\n        assert_eq!(",
    "        assert_eq!(result.completed_depth(), 3);\n        assert_eq!(\n            result.nodes(),\n            result.search_diagnostics().main_nodes()\n                + result.search_diagnostics().quiescence_nodes()\n        );\n        assert_eq!(result.qnodes(), result.search_diagnostics().quiescence_nodes());\n        assert!(result.search_diagnostics().reserved_counters_are_zero());\n        assert_eq!(",
)

print("S2-3 diagnostics source staged")
