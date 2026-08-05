use core::fmt;

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
    SeeWinningCaptures,
    SeeEqualCaptures,
    SeeLosingCaptures,
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
            Self::SeeWinningCaptures => "see_winning_captures",
            Self::SeeEqualCaptures => "see_equal_captures",
            Self::SeeLosingCaptures => "see_losing_captures",
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
        write!(
            formatter,
            "search diagnostic counter {} overflowed",
            self.counter
        )
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
    SeeWinningCapture,
    SeeEqualCapture,
    SeeLosingCapture,
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
    see_winning_captures: u64,
    see_equal_captures: u64,
    see_losing_captures: u64,
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
        see_winning_captures: 0,
        see_equal_captures: 0,
        see_losing_captures: 0,
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
                increment_checked(&mut self.beta_cutoffs, SearchDiagnosticCounter::BetaCutoffs)?;
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
            SearchDiagnosticEvent::PvsResearch => increment_checked(
                &mut self.pvs_researches,
                SearchDiagnosticCounter::PvsResearches,
            ),
            SearchDiagnosticEvent::SeeCall => {
                increment_checked(&mut self.see_calls, SearchDiagnosticCounter::SeeCalls)
            }
            SearchDiagnosticEvent::SeeWinningCapture => increment_checked(
                &mut self.see_winning_captures,
                SearchDiagnosticCounter::SeeWinningCaptures,
            ),
            SearchDiagnosticEvent::SeeEqualCapture => increment_checked(
                &mut self.see_equal_captures,
                SearchDiagnosticCounter::SeeEqualCaptures,
            ),
            SearchDiagnosticEvent::SeeLosingCapture => increment_checked(
                &mut self.see_losing_captures,
                SearchDiagnosticCounter::SeeLosingCaptures,
            ),
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
            SearchDiagnosticEvent::LmrReduction => increment_checked(
                &mut self.lmr_reductions,
                SearchDiagnosticCounter::LmrReductions,
            ),
            SearchDiagnosticEvent::LmrResearch => increment_checked(
                &mut self.lmr_researches,
                SearchDiagnosticCounter::LmrResearches,
            ),
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
                self.$field.checked_add(other.$field).ok_or_else(|| {
                    SearchDiagnosticOverflow::new(SearchDiagnosticCounter::$counter)
                })?
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
            see_winning_captures: sum!(see_winning_captures, SeeWinningCaptures),
            see_equal_captures: sum!(see_equal_captures, SeeEqualCaptures),
            see_losing_captures: sum!(see_losing_captures, SeeLosingCaptures),
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
    pub const fn main_nodes(self) -> u64 {
        self.main_nodes
    }
    #[must_use]
    pub const fn quiescence_nodes(self) -> u64 {
        self.quiescence_nodes
    }
    #[must_use]
    pub const fn beta_cutoffs(self) -> u64 {
        self.beta_cutoffs
    }
    #[must_use]
    pub const fn first_move_beta_cutoffs(self) -> u64 {
        self.first_move_beta_cutoffs
    }
    #[must_use]
    pub const fn quiescence_beta_cutoffs(self) -> u64 {
        self.quiescence_beta_cutoffs
    }
    #[must_use]
    pub const fn quiescence_first_move_beta_cutoffs(self) -> u64 {
        self.quiescence_first_move_beta_cutoffs
    }
    #[must_use]
    pub const fn quiescence_stand_pat_cutoffs(self) -> u64 {
        self.quiescence_stand_pat_cutoffs
    }
    #[must_use]
    pub const fn pvs_zero_window_searches(self) -> u64 {
        self.pvs_zero_window_searches
    }
    #[must_use]
    pub const fn pvs_researches(self) -> u64 {
        self.pvs_researches
    }
    #[must_use]
    pub const fn see_calls(self) -> u64 {
        self.see_calls
    }
    #[must_use]
    pub const fn see_winning_captures(self) -> u64 {
        self.see_winning_captures
    }
    #[must_use]
    pub const fn see_equal_captures(self) -> u64 {
        self.see_equal_captures
    }
    #[must_use]
    pub const fn see_losing_captures(self) -> u64 {
        self.see_losing_captures
    }
    #[must_use]
    pub const fn see_prunes(self) -> u64 {
        self.see_prunes
    }
    #[must_use]
    pub const fn quiescence_see_prunes(self) -> u64 {
        self.quiescence_see_prunes
    }
    #[must_use]
    pub const fn quiescence_delta_prunes(self) -> u64 {
        self.quiescence_delta_prunes
    }
    #[must_use]
    pub const fn lmr_reductions(self) -> u64 {
        self.lmr_reductions
    }
    #[must_use]
    pub const fn lmr_researches(self) -> u64 {
        self.lmr_researches
    }
    #[must_use]
    pub const fn null_move_attempts(self) -> u64 {
        self.null_move_attempts
    }
    #[must_use]
    pub const fn null_move_cutoffs(self) -> u64 {
        self.null_move_cutoffs
    }
    #[must_use]
    pub const fn frontier_futility_prunes(self) -> u64 {
        self.frontier_futility_prunes
    }
    #[must_use]
    pub const fn frontier_razor_attempts(self) -> u64 {
        self.frontier_razor_attempts
    }
    #[must_use]
    pub const fn late_move_prunes(self) -> u64 {
        self.late_move_prunes
    }

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
            && self.see_winning_captures == 0
            && self.see_equal_captures == 0
            && self.see_losing_captures == 0
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
        if self.see_winning_captures != 0
            || self.see_equal_captures != 0
            || self.see_losing_captures != 0
        {
            hash = hash_bytes(hash, b"see-capture-classification-v1");
            for value in [
                self.see_winning_captures,
                self.see_equal_captures,
                self.see_losing_captures,
            ] {
                hash = hash_bytes(hash, &value.to_le_bytes());
            }
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
        let maximum = SearchDiagnostics {
            main_nodes: u64::MAX,
            ..SearchDiagnostics::default()
        };
        let error = maximum
            .checked_add(SearchDiagnostics::main_node())
            .expect_err("overflow fails loudly");
        assert_eq!(error.counter(), SearchDiagnosticCounter::MainNodes);
    }

    #[test]
    fn saturating_observation_sets_the_overflow_flag() {
        let mut diagnostics = SearchDiagnostics {
            main_nodes: u64::MAX,
            ..SearchDiagnostics::default()
        };
        diagnostics.saturating_record(SearchDiagnosticEvent::MainNode);
        assert_eq!(diagnostics.main_nodes(), u64::MAX);
        assert!(diagnostics.overflowed());
    }

    #[test]
    fn see_classification_events_are_exact_and_checksum_visible() {
        let baseline_checksum = SearchDiagnostics::default().semantic_checksum();
        let mut diagnostics = SearchDiagnostics::default();
        for event in [
            SearchDiagnosticEvent::SeeCall,
            SearchDiagnosticEvent::SeeWinningCapture,
        ] {
            diagnostics
                .record_checked(event)
                .expect("small diagnostic counts fit");
        }
        assert_eq!(diagnostics.see_calls(), 1);
        assert_eq!(diagnostics.see_winning_captures(), 1);
        assert_eq!(diagnostics.see_equal_captures(), 0);
        assert_eq!(diagnostics.see_losing_captures(), 0);
        assert_ne!(diagnostics.semantic_checksum(), baseline_checksum);
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
