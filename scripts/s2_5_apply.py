#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text()


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)


def replace_once(path: str, old: str, new: str) -> None:
    content = read(path)
    count = content.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement, found {count}: {old[:120]!r}")
    write(path, content.replace(old, new, 1))


# Search-policy identity and validation.
replace_once(
    "crates/chess-search/src/search_policy.rs",
    "/// Canonical checksum of the authoritative v0.1 search policy.\npub const V0_1_SEARCH_POLICY_CHECKSUM: u64 = 0x0c07_69ef_9d03_4770;\n",
    "/// Canonical checksum of the authoritative v0.1 search policy.\npub const V0_1_SEARCH_POLICY_CHECKSUM: u64 = 0x0c07_69ef_9d03_4770;\n"
    "/// Stable identifier for the inactive S2-5 SEE capture-ordering candidate.\n"
    "pub const SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID: u64 = 0x5332_3553_4545_4f31;\n",
)
replace_once(
    "crates/chess-search/src/search_policy.rs",
    "impl ExperimentalSearchFeature {\n    /// Stable machine-readable feature name.\n",
    "impl ExperimentalSearchFeature {\n"
    "    const fn bit(self) -> u64 {\n"
    "        match self {\n"
    "            Self::SeeCaptureOrdering => 1 << 0,\n"
    "            Self::SeeQuiescencePruning => 1 << 1,\n"
    "            Self::DeltaPruning => 1 << 2,\n"
    "            Self::PrincipalVariationSearch => 1 << 3,\n"
    "            Self::LateMoveReductions => 1 << 4,\n"
    "            Self::NullMovePruning => 1 << 5,\n"
    "            Self::FutilityPruning => 1 << 6,\n"
    "            Self::Razoring => 1 << 7,\n"
    "            Self::LateMovePruning => 1 << 8,\n"
    "        }\n"
    "    }\n\n"
    "    /// Stable machine-readable feature name.\n",
)
replace_once(
    "crates/chess-search/src/search_policy.rs",
    "    /// No experimental behavior enabled.\n    pub const NONE: Self = Self { bits: 0 };\n",
    "    /// No experimental behavior enabled.\n"
    "    pub const NONE: Self = Self { bits: 0 };\n"
    "    /// Inactive S2-5 SEE capture-ordering candidate.\n"
    "    pub const SEE_CAPTURE_ORDERING: Self = Self {\n"
    "        bits: ExperimentalSearchFeature::SeeCaptureOrdering.bit(),\n"
    "    };\n",
)
replace_once(
    "crates/chess-search/src/search_policy.rs",
    "    /// Returns whether every experimental feature is disabled.\n    #[must_use]\n    pub const fn is_empty(self) -> bool {\n        self.bits == 0\n    }\n\n    fn first_enabled(self) -> Option<ExperimentalSearchFeature> {\n",
    "    /// Returns whether every experimental feature is disabled.\n"
    "    #[must_use]\n"
    "    pub const fn is_empty(self) -> bool {\n"
    "        self.bits == 0\n"
    "    }\n\n"
    "    /// Returns whether one assigned feature is enabled.\n"
    "    #[must_use]\n"
    "    pub const fn contains(self, feature: ExperimentalSearchFeature) -> bool {\n"
    "        self.bits & feature.bit() != 0\n"
    "    }\n\n"
    "    fn first_unsupported_enabled(self) -> Option<ExperimentalSearchFeature> {\n",
)
replace_once(
    "crates/chess-search/src/search_policy.rs",
    "        FEATURES\n            .into_iter()\n            .find_map(|(bit, feature)| (self.bits & bit != 0).then_some(feature))\n",
    "        FEATURES.into_iter().find_map(|(bit, feature)| {\n"
    "            (self.bits & bit != 0 && feature != ExperimentalSearchFeature::SeeCaptureOrdering)\n"
    "                .then_some(feature)\n"
    "        })\n",
)
replace_once(
    "crates/chess-search/src/search_policy.rs",
    "    pub const V0_1: Self = Self::new(SearchPolicyParameters {\n        alpha_beta: AlphaBetaMode::FullWindowFailSoft,\n        transposition: TranspositionPolicy::ClusteredFullKey,\n        move_ordering: MoveOrderingPolicy::V0_1MvvLvaKillersHistory,\n        quiescence: QuiescencePolicy::CapturesPromotionsAndEvasions,\n        aspiration_windows: true,\n        aspiration_half_width_centipawns: DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS as u16,\n        maximum_quiescence_ply: MAX_QUIESCENCE_PLY,\n        maximum_check_extensions_per_line: MAX_CHECK_EXTENSIONS_PER_LINE,\n        experimental_features: ExperimentalSearchFeatures::NONE,\n    });\n",
    "    pub const V0_1: Self = Self::new(SearchPolicyParameters {\n"
    "        alpha_beta: AlphaBetaMode::FullWindowFailSoft,\n"
    "        transposition: TranspositionPolicy::ClusteredFullKey,\n"
    "        move_ordering: MoveOrderingPolicy::V0_1MvvLvaKillersHistory,\n"
    "        quiescence: QuiescencePolicy::CapturesPromotionsAndEvasions,\n"
    "        aspiration_windows: true,\n"
    "        aspiration_half_width_centipawns: DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS as u16,\n"
    "        maximum_quiescence_ply: MAX_QUIESCENCE_PLY,\n"
    "        maximum_check_extensions_per_line: MAX_CHECK_EXTENSIONS_PER_LINE,\n"
    "        experimental_features: ExperimentalSearchFeatures::NONE,\n"
    "    });\n\n"
    "    /// Inactive S2-5 candidate: v0.1 semantics plus SEE capture ordering.\n"
    "    pub const SEE_CAPTURE_ORDERING: Self = Self::new(SearchPolicyParameters {\n"
    "        alpha_beta: AlphaBetaMode::FullWindowFailSoft,\n"
    "        transposition: TranspositionPolicy::ClusteredFullKey,\n"
    "        move_ordering: MoveOrderingPolicy::V0_1MvvLvaKillersHistory,\n"
    "        quiescence: QuiescencePolicy::CapturesPromotionsAndEvasions,\n"
    "        aspiration_windows: true,\n"
    "        aspiration_half_width_centipawns: DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS as u16,\n"
    "        maximum_quiescence_ply: MAX_QUIESCENCE_PLY,\n"
    "        maximum_check_extensions_per_line: MAX_CHECK_EXTENSIONS_PER_LINE,\n"
    "        experimental_features: ExperimentalSearchFeatures::SEE_CAPTURE_ORDERING,\n"
    "    });\n",
)
replace_once(
    "crates/chess-search/src/search_policy.rs",
    "    /// Returns the configured per-line check-extension budget.\n    #[must_use]\n    pub const fn maximum_check_extensions_per_line(self) -> u16 {\n        self.parameters.maximum_check_extensions_per_line\n    }\n\n    /// Validates supported ranges and rejects not-yet-implemented features.\n",
    "    /// Returns the configured per-line check-extension budget.\n"
    "    #[must_use]\n"
    "    pub const fn maximum_check_extensions_per_line(self) -> u16 {\n"
    "        self.parameters.maximum_check_extensions_per_line\n"
    "    }\n\n"
    "    /// Returns whether the inactive S2-5 SEE ordering candidate is selected.\n"
    "    #[must_use]\n"
    "    pub const fn see_capture_ordering_enabled(self) -> bool {\n"
    "        self.parameters\n"
    "            .experimental_features\n"
    "            .contains(ExperimentalSearchFeature::SeeCaptureOrdering)\n"
    "    }\n\n"
    "    /// Validates supported ranges and rejects not-yet-implemented features.\n",
)
replace_once(
    "crates/chess-search/src/search_policy.rs",
    "        if let Some(feature) = self.parameters.experimental_features.first_enabled() {\n",
    "        if let Some(feature) = self\n"
    "            .parameters\n"
    "            .experimental_features\n"
    "            .first_unsupported_enabled()\n"
    "        {\n",
)
replace_once(
    "crates/chess-search/src/search_policy.rs",
    "    pub fn baseline() -> Self {\n        let set = Self::new(V0_1_SEARCH_POLICY_ID, SearchPolicy::V0_1);\n        debug_assert_eq!(set.checksum, V0_1_SEARCH_POLICY_CHECKSUM);\n        set\n    }\n",
    "    pub fn baseline() -> Self {\n"
    "        let set = Self::new(V0_1_SEARCH_POLICY_ID, SearchPolicy::V0_1);\n"
    "        debug_assert_eq!(set.checksum, V0_1_SEARCH_POLICY_CHECKSUM);\n"
    "        set\n"
    "    }\n\n"
    "    /// Returns the inactive S2-5 SEE capture-ordering candidate.\n"
    "    #[must_use]\n"
    "    pub fn see_capture_ordering_candidate() -> Self {\n"
    "        Self::new(\n"
    "            SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID,\n"
    "            SearchPolicy::SEE_CAPTURE_ORDERING,\n"
    "        )\n"
    "    }\n",
)
replace_once(
    "crates/chess-search/src/search_policy.rs",
    "        SearchPolicyValidationError, V0_1_SEARCH_POLICY_CHECKSUM,\n",
    "        SearchPolicyValidationError, SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID,\n"
    "        V0_1_SEARCH_POLICY_CHECKSUM,\n",
)
replace_once(
    "crates/chess-search/src/search_policy.rs",
    "    #[test]\n    fn semantic_parameter_changes_change_the_checksum() {\n",
    "    #[test]\n"
    "    fn see_capture_ordering_candidate_is_valid_distinct_and_inactive_by_default() {\n"
    "        let baseline = SearchPolicySet::baseline();\n"
    "        let candidate = SearchPolicySet::see_capture_ordering_candidate();\n"
    "        assert_eq!(candidate.identifier, SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID);\n"
    "        assert_eq!(candidate.validate(), Ok(()));\n"
    "        assert!(candidate.policy.see_capture_ordering_enabled());\n"
    "        assert!(!baseline.policy.see_capture_ordering_enabled());\n"
    "        assert_ne!(candidate.identifier, baseline.identifier);\n"
    "        assert_ne!(candidate.checksum, baseline.checksum);\n"
    "    }\n\n"
    "    #[test]\n"
    "    fn semantic_parameter_changes_change_the_checksum() {\n",
)
replace_once(
    "crates/chess-search/src/search_policy.rs",
    "            ExperimentalSearchFeatures::from_bits(1).expect(\"assigned feature bit is recognized\");\n",
    "            ExperimentalSearchFeatures::from_bits(1 << 1)\n"
    "                .expect(\"assigned feature bit is recognized\");\n",
)

# Diagnostics: retain the baseline checksum when the new counters are zero.
path = "crates/chess-search/src/diagnostics.rs"
for old, new in [
    ("    SeeCalls,\n    SeePrunes,\n", "    SeeCalls,\n    SeeWinningCaptures,\n    SeeEqualCaptures,\n    SeeLosingCaptures,\n    SeePrunes,\n"),
    ("            Self::SeeCalls => \"see_calls\",\n            Self::SeePrunes => \"see_prunes\",\n", "            Self::SeeCalls => \"see_calls\",\n            Self::SeeWinningCaptures => \"see_winning_captures\",\n            Self::SeeEqualCaptures => \"see_equal_captures\",\n            Self::SeeLosingCaptures => \"see_losing_captures\",\n            Self::SeePrunes => \"see_prunes\",\n"),
    ("    SeeCall,\n    SeePrune,\n", "    SeeCall,\n    SeeWinningCapture,\n    SeeEqualCapture,\n    SeeLosingCapture,\n    SeePrune,\n"),
    ("    see_calls: u64,\n    see_prunes: u64,\n", "    see_calls: u64,\n    see_winning_captures: u64,\n    see_equal_captures: u64,\n    see_losing_captures: u64,\n    see_prunes: u64,\n"),
    ("        see_calls: 0,\n        see_prunes: 0,\n", "        see_calls: 0,\n        see_winning_captures: 0,\n        see_equal_captures: 0,\n        see_losing_captures: 0,\n        see_prunes: 0,\n"),
    ("            SearchDiagnosticEvent::SeeCall => {\n                increment_checked(&mut self.see_calls, SearchDiagnosticCounter::SeeCalls)\n            }\n            SearchDiagnosticEvent::SeePrune => {\n", "            SearchDiagnosticEvent::SeeCall => {\n                increment_checked(&mut self.see_calls, SearchDiagnosticCounter::SeeCalls)\n            }\n            SearchDiagnosticEvent::SeeWinningCapture => increment_checked(\n                &mut self.see_winning_captures,\n                SearchDiagnosticCounter::SeeWinningCaptures,\n            ),\n            SearchDiagnosticEvent::SeeEqualCapture => increment_checked(\n                &mut self.see_equal_captures,\n                SearchDiagnosticCounter::SeeEqualCaptures,\n            ),\n            SearchDiagnosticEvent::SeeLosingCapture => increment_checked(\n                &mut self.see_losing_captures,\n                SearchDiagnosticCounter::SeeLosingCaptures,\n            ),\n            SearchDiagnosticEvent::SeePrune => {\n"),
    ("            see_calls: sum!(see_calls, SeeCalls),\n            see_prunes: sum!(see_prunes, SeePrunes),\n", "            see_calls: sum!(see_calls, SeeCalls),\n            see_winning_captures: sum!(see_winning_captures, SeeWinningCaptures),\n            see_equal_captures: sum!(see_equal_captures, SeeEqualCaptures),\n            see_losing_captures: sum!(see_losing_captures, SeeLosingCaptures),\n            see_prunes: sum!(see_prunes, SeePrunes),\n"),
    ("    pub const fn see_calls(self) -> u64 {\n        self.see_calls\n    }\n    #[must_use]\n    pub const fn see_prunes(self) -> u64 {\n", "    pub const fn see_calls(self) -> u64 {\n        self.see_calls\n    }\n    #[must_use]\n    pub const fn see_winning_captures(self) -> u64 {\n        self.see_winning_captures\n    }\n    #[must_use]\n    pub const fn see_equal_captures(self) -> u64 {\n        self.see_equal_captures\n    }\n    #[must_use]\n    pub const fn see_losing_captures(self) -> u64 {\n        self.see_losing_captures\n    }\n    #[must_use]\n    pub const fn see_prunes(self) -> u64 {\n"),
    ("            && self.see_calls == 0\n            && self.see_prunes == 0\n", "            && self.see_calls == 0\n            && self.see_winning_captures == 0\n            && self.see_equal_captures == 0\n            && self.see_losing_captures == 0\n            && self.see_prunes == 0\n"),
]:
    replace_once(path, old, new)
replace_once(
    path,
    "        hash_bytes(hash, &[self.overflowed as u8])\n",
    "        if self.see_winning_captures != 0\n"
    "            || self.see_equal_captures != 0\n"
    "            || self.see_losing_captures != 0\n"
    "        {\n"
    "            hash = hash_bytes(hash, b\"see-capture-classification-v1\");\n"
    "            for value in [\n"
    "                self.see_winning_captures,\n"
    "                self.see_equal_captures,\n"
    "                self.see_losing_captures,\n"
    "            ] {\n"
    "                hash = hash_bytes(hash, &value.to_le_bytes());\n"
    "            }\n"
    "        }\n"
    "        hash_bytes(hash, &[self.overflowed as u8])\n",
)
replace_once(
    path,
    "    #[test]\n    fn cutoff_events_are_deterministic_and_future_counters_stay_zero() {\n",
    "    #[test]\n"
    "    fn see_classification_events_are_exact_and_checksum_visible() {\n"
    "        let baseline_checksum = SearchDiagnostics::default().semantic_checksum();\n"
    "        let mut diagnostics = SearchDiagnostics::default();\n"
    "        for event in [\n"
    "            SearchDiagnosticEvent::SeeCall,\n"
    "            SearchDiagnosticEvent::SeeWinningCapture,\n"
    "        ] {\n"
    "            diagnostics\n"
    "                .record_checked(event)\n"
    "                .expect(\"small diagnostic counts fit\");\n"
    "        }\n"
    "        assert_eq!(diagnostics.see_calls(), 1);\n"
    "        assert_eq!(diagnostics.see_winning_captures(), 1);\n"
    "        assert_eq!(diagnostics.see_equal_captures(), 0);\n"
    "        assert_eq!(diagnostics.see_losing_captures(), 0);\n"
    "        assert_ne!(diagnostics.semantic_checksum(), baseline_checksum);\n"
    "    }\n\n"
    "    #[test]\n"
    "    fn cutoff_events_are_deterministic_and_future_counters_stay_zero() {\n",
)

# Replace move ordering with an explicit fixed-capacity SEE-aware implementation.
write(
    "crates/chess-search/src/move_ordering.rs",
    r'''use core::cmp::Reverse;

use chess_core::{
    static_exchange_evaluation, Color, LegalMoveToken, LegalMoveTokenList, Move, MoveKind,
    PieceKind, Position, StaticExchangeClass, StaticExchangeError, StaticExchangeValue,
    MAX_PSEUDO_LEGAL_MOVES,
};

use crate::{
    SearchCancellationProbe, SearchDiagnosticEvent, SearchDiagnosticOverflow, SearchDiagnostics,
    MAX_MATE_PLY,
};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum MoveOrdering {
    Generation,
    Tactical,
    Quiet,
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub(crate) struct MoveOrderingDiagnostics {
    see_calls: u16,
    winning: u16,
    equal: u16,
    losing: u16,
}

impl MoveOrderingDiagnostics {
    fn record_class(&mut self, class: StaticExchangeClass) {
        self.see_calls += 1;
        match class {
            StaticExchangeClass::Winning => self.winning += 1,
            StaticExchangeClass::Equal => self.equal += 1,
            StaticExchangeClass::Losing => self.losing += 1,
        }
    }

    pub(crate) fn record_into<Probe>(
        self,
        diagnostics: &mut SearchDiagnostics,
        cancellation: &mut Probe,
    ) -> Result<(), SearchDiagnosticOverflow>
    where
        Probe: SearchCancellationProbe + ?Sized,
    {
        record_repeated(
            self.see_calls,
            SearchDiagnosticEvent::SeeCall,
            diagnostics,
            cancellation,
        )?;
        record_repeated(
            self.winning,
            SearchDiagnosticEvent::SeeWinningCapture,
            diagnostics,
            cancellation,
        )?;
        record_repeated(
            self.equal,
            SearchDiagnosticEvent::SeeEqualCapture,
            diagnostics,
            cancellation,
        )?;
        record_repeated(
            self.losing,
            SearchDiagnosticEvent::SeeLosingCapture,
            diagnostics,
            cancellation,
        )
    }

    #[cfg(test)]
    const fn see_calls(self) -> u16 {
        self.see_calls
    }

    #[cfg(test)]
    const fn winning(self) -> u16 {
        self.winning
    }

    #[cfg(test)]
    const fn equal(self) -> u16 {
        self.equal
    }

    #[cfg(test)]
    const fn losing(self) -> u16 {
        self.losing
    }
}

fn record_repeated<Probe>(
    count: u16,
    event: SearchDiagnosticEvent,
    diagnostics: &mut SearchDiagnostics,
    cancellation: &mut Probe,
) -> Result<(), SearchDiagnosticOverflow>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    for _ in 0..count {
        diagnostics.record_checked(event)?;
        cancellation.on_search_diagnostic(event);
    }
    Ok(())
}

const ORDERING_PLY_COUNT: usize = MAX_MATE_PLY as usize + 1;
const HISTORY_SCORE_MAXIMUM: u32 = 1_000_000;

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
struct KillerMoves {
    primary: Option<Move>,
    secondary: Option<Move>,
}

pub(crate) struct QuietOrderingState {
    killers: [KillerMoves; ORDERING_PLY_COUNT],
    history: [[[u32; 64]; 64]; 2],
}

impl QuietOrderingState {
    pub(crate) const fn new() -> Self {
        Self {
            killers: [KillerMoves {
                primary: None,
                secondary: None,
            }; ORDERING_PLY_COUNT],
            history: [[[0; 64]; 64]; 2],
        }
    }

    pub(crate) fn record_quiet_cutoff(
        &mut self,
        color: Color,
        current: Move,
        depth: u16,
        ply: u16,
    ) {
        if !is_quiet(current) {
            return;
        }
        if let Some(killers) = self.killers.get_mut(usize::from(ply)) {
            if killers.primary != Some(current) {
                killers.secondary = killers.primary;
                killers.primary = Some(current);
            }
        }
        let depth = u32::from(depth);
        let bonus = depth.saturating_mul(depth).max(1);
        let entry = &mut self.history[color.index()][usize::from(current.source().index())]
            [usize::from(current.destination().index())];
        *entry = entry.saturating_add(bonus).min(HISTORY_SCORE_MAXIMUM);
    }

    fn killers(&self, ply: u16) -> KillerMoves {
        self.killers
            .get(usize::from(ply))
            .copied()
            .unwrap_or_default()
    }

    fn history_score(&self, color: Color, current: Move) -> u32 {
        self.history[color.index()][usize::from(current.source().index())]
            [usize::from(current.destination().index())]
    }
}

impl Default for QuietOrderingState {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
struct MoveOrderKey {
    transposition_table: u8,
    previous_principal_variation: u8,
    category: u8,
    promotion: u16,
    see_class: u8,
    see_value: i32,
    victim: u16,
    attacker_preference: u16,
    killer: u8,
    history: u32,
    encoded_tie_break: Option<Reverse<Move>>,
}

impl MoveOrderKey {
    const GENERATION: Self = Self {
        transposition_table: 0,
        previous_principal_variation: 0,
        category: 0,
        promotion: 0,
        see_class: 0,
        see_value: 0,
        victim: 0,
        attacker_preference: 0,
        killer: 0,
        history: 0,
        encoded_tie_break: None,
    };
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct OrderedEntry {
    token: LegalMoveToken,
    key: MoveOrderKey,
}

pub(crate) struct OrderedLegalMoves {
    entries: [Option<OrderedEntry>; MAX_PSEUDO_LEGAL_MOVES],
    len: usize,
    diagnostics: MoveOrderingDiagnostics,
}

impl OrderedLegalMoves {
    fn new() -> Self {
        Self {
            entries: [None; MAX_PSEUDO_LEGAL_MOVES],
            len: 0,
            diagnostics: MoveOrderingDiagnostics::default(),
        }
    }

    pub(crate) fn iter(&self) -> impl ExactSizeIterator<Item = LegalMoveToken> + '_ {
        self.entries[..self.len].iter().copied().map(|entry| {
            entry
                .expect("occupied ordered-move prefix contains entries")
                .token
        })
    }

    pub(crate) const fn diagnostics(&self) -> MoveOrderingDiagnostics {
        self.diagnostics
    }
}

pub(crate) fn ordered_legal_moves(
    position: &Position,
    tokens: &LegalMoveTokenList,
    ordering: MoveOrdering,
) -> OrderedLegalMoves {
    ordered_legal_moves_with_see(position, tokens, ordering, false)
        .expect("baseline ordering does not invoke static exchange evaluation")
}

pub(crate) fn ordered_legal_moves_with_see(
    position: &Position,
    tokens: &LegalMoveTokenList,
    ordering: MoveOrdering,
    see_capture_ordering: bool,
) -> Result<OrderedLegalMoves, StaticExchangeError> {
    let transposition_table_move = match ordering {
        MoveOrdering::Generation => None,
        MoveOrdering::Tactical | MoveOrdering::Quiet => transposition_table_move_hook(position),
    };
    let previous_pv_move = match ordering {
        MoveOrdering::Quiet => previous_pv_move_hook(0),
        MoveOrdering::Generation | MoveOrdering::Tactical => None,
    };
    try_order_legal_moves_with_hints(
        position,
        tokens,
        ordering,
        0,
        None,
        transposition_table_move,
        previous_pv_move,
        see_capture_ordering,
    )
}

pub(crate) fn ordered_legal_moves_with_state(
    position: &Position,
    tokens: &LegalMoveTokenList,
    ordering: MoveOrdering,
    ply: u16,
    quiet_state: &QuietOrderingState,
) -> OrderedLegalMoves {
    try_order_legal_moves_with_state(
        position,
        tokens,
        ordering,
        ply,
        quiet_state,
        transposition_table_move_hook(position),
        false,
    )
    .expect("baseline ordering does not invoke static exchange evaluation")
}

pub(crate) fn ordered_legal_moves_with_state_and_tt_move(
    position: &Position,
    tokens: &LegalMoveTokenList,
    ordering: MoveOrdering,
    ply: u16,
    quiet_state: &QuietOrderingState,
    transposition_table_move: Option<Move>,
) -> OrderedLegalMoves {
    ordered_legal_moves_with_state_and_tt_move_and_see(
        position,
        tokens,
        ordering,
        ply,
        quiet_state,
        transposition_table_move,
        false,
    )
    .expect("baseline ordering does not invoke static exchange evaluation")
}

pub(crate) fn ordered_legal_moves_with_state_and_tt_move_and_see(
    position: &Position,
    tokens: &LegalMoveTokenList,
    ordering: MoveOrdering,
    ply: u16,
    quiet_state: &QuietOrderingState,
    transposition_table_move: Option<Move>,
    see_capture_ordering: bool,
) -> Result<OrderedLegalMoves, StaticExchangeError> {
    try_order_legal_moves_with_state(
        position,
        tokens,
        ordering,
        ply,
        quiet_state,
        transposition_table_move,
        see_capture_ordering,
    )
}

fn try_order_legal_moves_with_state(
    position: &Position,
    tokens: &LegalMoveTokenList,
    ordering: MoveOrdering,
    ply: u16,
    quiet_state: &QuietOrderingState,
    transposition_table_move: Option<Move>,
    see_capture_ordering: bool,
) -> Result<OrderedLegalMoves, StaticExchangeError> {
    let previous_pv_move = match ordering {
        MoveOrdering::Quiet => previous_pv_move_hook(ply),
        MoveOrdering::Generation | MoveOrdering::Tactical => None,
    };
    try_order_legal_moves_with_hints(
        position,
        tokens,
        ordering,
        ply,
        Some(quiet_state),
        transposition_table_move,
        previous_pv_move,
        see_capture_ordering,
    )
}

const fn transposition_table_move_hook(_position: &Position) -> Option<Move> {
    None
}

const fn previous_pv_move_hook(_ply: u16) -> Option<Move> {
    None
}

fn order_legal_moves_with_hints(
    position: &Position,
    tokens: &LegalMoveTokenList,
    ordering: MoveOrdering,
    ply: u16,
    quiet_state: Option<&QuietOrderingState>,
    transposition_table_move: Option<Move>,
    previous_pv_move: Option<Move>,
) -> OrderedLegalMoves {
    try_order_legal_moves_with_hints(
        position,
        tokens,
        ordering,
        ply,
        quiet_state,
        transposition_table_move,
        previous_pv_move,
        false,
    )
    .expect("baseline ordering does not invoke static exchange evaluation")
}

#[allow(clippy::too_many_arguments)]
fn try_order_legal_moves_with_hints(
    position: &Position,
    tokens: &LegalMoveTokenList,
    ordering: MoveOrdering,
    ply: u16,
    quiet_state: Option<&QuietOrderingState>,
    transposition_table_move: Option<Move>,
    previous_pv_move: Option<Move>,
    see_capture_ordering: bool,
) -> Result<OrderedLegalMoves, StaticExchangeError> {
    let mut ordered = OrderedLegalMoves::new();
    for token in tokens.iter() {
        let current = token.move_made();
        let see_value = if ordering != MoveOrdering::Generation
            && see_capture_ordering
            && current.kind().is_capture()
        {
            let value = static_exchange_evaluation(position, current)?;
            ordered.diagnostics.record_class(value.class());
            Some(value)
        } else {
            None
        };
        let key = match ordering {
            MoveOrdering::Generation => MoveOrderKey::GENERATION,
            MoveOrdering::Tactical => tactical_key(
                position,
                current,
                transposition_table_move,
                None,
                KillerMoves::default(),
                0,
                see_value,
                see_value.map(|_| Reverse(current)),
            ),
            MoveOrdering::Quiet => {
                let killers =
                    quiet_state.map_or_else(KillerMoves::default, |state| state.killers(ply));
                let history = quiet_state.map_or(0, |state| {
                    state.history_score(position.side_to_move(), current)
                });
                tactical_key(
                    position,
                    current,
                    transposition_table_move,
                    previous_pv_move,
                    killers,
                    history,
                    see_value,
                    Some(Reverse(current)),
                )
            }
        };
        let entry = OrderedEntry { token, key };
        let mut insertion = ordered.len;
        while insertion > 0 {
            let previous = ordered.entries[insertion - 1]
                .expect("occupied ordered-move prefix contains entries");
            if previous.key >= entry.key {
                break;
            }
            ordered.entries[insertion] = Some(previous);
            insertion -= 1;
        }
        ordered.entries[insertion] = Some(entry);
        ordered.len += 1;
    }
    Ok(ordered)
}

#[allow(clippy::too_many_arguments)]
fn tactical_key(
    position: &Position,
    current: Move,
    transposition_table_move: Option<Move>,
    previous_pv_move: Option<Move>,
    killers: KillerMoves,
    history: u32,
    see_value: Option<StaticExchangeValue>,
    encoded_tie_break: Option<Reverse<Move>>,
) -> MoveOrderKey {
    let promotion = current.promotion();
    let capture = current.kind().is_capture();
    let quiet = is_quiet(current);
    let category = if promotion.is_some() {
        2
    } else if capture {
        1
    } else {
        0
    };
    let victim = if capture {
        captured_piece_kind(position, current).map_or(0, piece_value)
    } else {
        0
    };
    let attacker_preference = if capture {
        let attacker = position
            .piece_at(current.source())
            .expect("a legal move source is occupied")
            .kind;
        piece_value(PieceKind::King) - piece_value(attacker)
    } else {
        0
    };
    let killer = if quiet && killers.primary == Some(current) {
        2
    } else if quiet && killers.secondary == Some(current) {
        1
    } else {
        0
    };
    let see_class = see_value.map_or(0, |value| match value.class() {
        StaticExchangeClass::Losing => 1,
        StaticExchangeClass::Equal => 2,
        StaticExchangeClass::Winning => 3,
    });
    MoveOrderKey {
        transposition_table: u8::from(transposition_table_move == Some(current)),
        previous_principal_variation: u8::from(previous_pv_move == Some(current)),
        category,
        promotion: promotion.map_or(0, piece_value),
        see_class,
        see_value: see_value.map_or(0, StaticExchangeValue::centipawns),
        victim,
        attacker_preference,
        killer,
        history: if quiet { history } else { 0 },
        encoded_tie_break: if quiet || see_value.is_some() {
            encoded_tie_break
        } else {
            None
        },
    }
}

fn captured_piece_kind(position: &Position, current: Move) -> Option<PieceKind> {
    if current.kind() == MoveKind::EnPassant {
        Some(PieceKind::Pawn)
    } else {
        position
            .piece_at(current.destination())
            .map(|piece| piece.kind)
    }
}

const fn is_quiet(current: Move) -> bool {
    !current.kind().is_capture() && current.promotion().is_none()
}

const fn piece_value(kind: PieceKind) -> u16 {
    match kind {
        PieceKind::Pawn => 100,
        PieceKind::Knight => 320,
        PieceKind::Bishop => 330,
        PieceKind::Rook => 500,
        PieceKind::Queen => 900,
        PieceKind::King => 20_000,
    }
}

#[cfg(test)]
mod tests {
    use chess_core::{Move, Position, StaticExchangeError, StaticExchangeMoveStateError};

    use super::{
        order_legal_moves_with_hints, ordered_legal_moves, ordered_legal_moves_with_see,
        tactical_key, transposition_table_move_hook, try_order_legal_moves_with_hints,
        KillerMoves, MoveOrdering,
    };

    fn position(fen: &str) -> Position {
        fen.parse().expect("move-ordering fixture FEN is valid")
    }

    fn ordered_moves(root: &mut Position, ordering: MoveOrdering) -> Vec<Move> {
        let tokens = root
            .legal_move_tokens()
            .expect("legal move tokens generate");
        ordered_legal_moves(root, &tokens, ordering)
            .iter()
            .map(|token| token.move_made())
            .collect()
    }

    #[test]
    fn transposition_table_hook_is_an_explicit_no_op() {
        let root = Position::starting();
        assert_eq!(transposition_table_move_hook(&root), None);
    }

    #[test]
    fn generation_policy_preserves_exact_legal_token_order() {
        let mut root = Position::starting();
        let expected: Vec<_> = root
            .legal_move_tokens()
            .expect("legal move tokens generate")
            .iter()
            .map(|token| token.move_made())
            .collect();
        let actual = ordered_moves(&mut root, MoveOrdering::Generation);
        assert_eq!(actual, expected);
    }

    #[test]
    fn tt_move_and_promotions_precede_captures_and_quiets() {
        let mut root = position("3r3k/P7/8/8/8/8/8/K2Q4 w - - 0 1");
        let tokens = root
            .legal_move_tokens()
            .expect("legal move tokens generate");
        let tt_move = tokens
            .iter()
            .map(|token| token.move_made())
            .find(|current| current.to_uci() == "a1b1")
            .expect("fixture quiet TT move exists");
        let ordered: Vec<_> = order_legal_moves_with_hints(
            &root,
            &tokens,
            MoveOrdering::Tactical,
            0,
            None,
            Some(tt_move),
            None,
        )
        .iter()
        .map(|token| token.move_made())
        .collect();

        assert_eq!(ordered[0], tt_move);
        let promotions: Vec<_> = ordered
            .iter()
            .copied()
            .filter(|current| current.promotion().is_some())
            .map(Move::to_uci)
            .collect();
        assert_eq!(promotions, ["a7a8q", "a7a8r", "a7a8b", "a7a8n"]);
        let last_promotion = ordered
            .iter()
            .rposition(|current| current.promotion().is_some())
            .expect("fixture promotions exist");
        let capture = ordered
            .iter()
            .position(|current| current.to_uci() == "d1d8")
            .expect("fixture capture exists");
        assert!(last_promotion < capture);
    }

    #[test]
    fn see_candidate_preserves_tt_and_promotion_precedence() {
        let root = position("3r3k/P7/8/8/8/8/8/K2Q4 w - - 0 1");
        let tokens = root
            .legal_move_tokens()
            .expect("legal move tokens generate");
        let tt_move = tokens
            .iter()
            .map(|token| token.move_made())
            .find(|current| current.to_uci() == "a1b1")
            .expect("fixture quiet TT move exists");
        let ordered: Vec<_> = try_order_legal_moves_with_hints(
            &root,
            &tokens,
            MoveOrdering::Tactical,
            0,
            None,
            Some(tt_move),
            None,
            true,
        )
        .expect("legal captures are valid SEE inputs")
        .iter()
        .map(|token| token.move_made())
        .collect();
        assert_eq!(ordered[0], tt_move);
        let last_promotion = ordered
            .iter()
            .rposition(|current| current.promotion().is_some())
            .expect("fixture promotions exist");
        let first_non_promotion_capture = ordered
            .iter()
            .position(|current| current.kind().is_capture() && current.promotion().is_none())
            .expect("fixture capture exists");
        assert!(last_promotion < first_non_promotion_capture);
    }

    #[test]
    fn see_classes_and_signed_values_order_exactly() {
        let root = position("4k3/8/2p5/3p4/4P3/8/8/4K3 w - - 0 1");
        let current = root
            .legal_moves()
            .expect("legal moves generate")
            .iter()
            .find(|candidate| candidate.to_uci() == "e4d5")
            .expect("capture exists");
        let key = |value| {
            tactical_key(
                &root,
                current,
                None,
                None,
                KillerMoves::default(),
                0,
                Some(value),
                Some(core::cmp::Reverse(current)),
            )
        };
        assert!(
            key(chess_core::StaticExchangeValue::from_centipawns(100))
                > key(chess_core::StaticExchangeValue::from_centipawns(0))
        );
        assert!(
            key(chess_core::StaticExchangeValue::from_centipawns(0))
                > key(chess_core::StaticExchangeValue::from_centipawns(-1))
        );
        assert!(
            key(chess_core::StaticExchangeValue::from_centipawns(200))
                > key(chess_core::StaticExchangeValue::from_centipawns(100))
        );
    }

    #[test]
    fn see_is_computed_once_per_capture_and_classified() {
        let root = position("7k/8/8/1p2q3/2P1Q3/8/K7/8 w - - 0 1");
        let tokens = root
            .legal_move_tokens()
            .expect("legal move tokens generate");
        let capture_count = tokens
            .iter()
            .filter(|token| token.move_made().kind().is_capture())
            .count() as u16;
        let ordered = ordered_legal_moves_with_see(&root, &tokens, MoveOrdering::Tactical, true)
            .expect("legal captures are valid SEE inputs");
        let diagnostics = ordered.diagnostics();
        assert_eq!(diagnostics.see_calls(), capture_count);
        assert_eq!(
            diagnostics.see_calls(),
            diagnostics.winning() + diagnostics.equal() + diagnostics.losing()
        );
    }

    #[test]
    fn contradictory_internal_see_input_fails_loudly() {
        let root = position("7k/8/8/1p2q3/2P1Q3/8/K7/8 w - - 0 1");
        let tokens = root
            .legal_move_tokens()
            .expect("legal move tokens generate");
        let contradictory = position("7k/8/8/8/8/8/8/K7 w - - 0 1");
        let error = try_order_legal_moves_with_hints(
            &contradictory,
            &tokens,
            MoveOrdering::Tactical,
            0,
            None,
            None,
            None,
            true,
        )
        .expect_err("contradictory capture source must fail");
        assert!(matches!(
            error,
            StaticExchangeError::MoveStateContradiction(
                StaticExchangeMoveStateError::MissingSourcePiece { .. }
            )
        ));
    }

    #[test]
    fn captures_use_mvv_lva_with_stable_equal_keys() {
        let mut victim_root = position("7k/8/8/1p2q3/2P1Q3/8/K7/8 w - - 0 1");
        let victim_order: Vec<_> = ordered_moves(&mut victim_root, MoveOrdering::Tactical)
            .into_iter()
            .filter(|current| current.kind().is_capture())
            .map(Move::to_uci)
            .collect();
        assert_eq!(&victim_order[..2], ["e4e5", "c4b5"]);

        let mut attacker_root = position("7k/8/8/3q4/2P5/8/8/K2R4 w - - 0 1");
        let attacker_order: Vec<_> = ordered_moves(&mut attacker_root, MoveOrdering::Tactical)
            .into_iter()
            .filter(|current| current.kind().is_capture())
            .map(Move::to_uci)
            .collect();
        assert_eq!(&attacker_order[..2], ["c4d5", "d1d5"]);
    }
}

#[cfg(test)]
mod quiet_tests {
    use chess_core::{Color, Move, Position};

    use super::{
        ordered_legal_moves_with_state, ordered_legal_moves_with_state_and_tt_move,
        previous_pv_move_hook, MoveOrdering, QuietOrderingState,
    };

    fn legal_move(position: &mut Position, uci: &str) -> Move {
        position
            .legal_move_tokens()
            .expect("legal tokens generate")
            .iter()
            .map(|token| token.move_made())
            .find(|current| current.to_uci() == uci)
            .expect("fixture move is legal")
    }

    #[test]
    fn previous_pv_hook_is_an_explicit_no_op() {
        assert_eq!(previous_pv_move_hook(0), None);
    }

    #[test]
    fn quiet_ties_use_packed_move_order() {
        let position = Position::starting();
        let tokens = position.legal_move_tokens().expect("legal tokens generate");
        let mut expected: Vec<_> = tokens.iter().map(|token| token.move_made()).collect();
        expected.sort_unstable();
        let state = QuietOrderingState::new();
        let actual: Vec<_> =
            ordered_legal_moves_with_state(&position, &tokens, MoveOrdering::Quiet, 0, &state)
                .iter()
                .map(|token| token.move_made())
                .collect();
        assert_eq!(actual, expected);
    }

    #[test]
    fn explicit_tt_move_precedes_quiet_heuristics() {
        let mut position = Position::starting();
        let hint = legal_move(&mut position, "h2h4");
        let tokens = position.legal_move_tokens().expect("legal tokens generate");
        let state = QuietOrderingState::new();
        let ordered: Vec<_> = ordered_legal_moves_with_state_and_tt_move(
            &position,
            &tokens,
            MoveOrdering::Quiet,
            0,
            &state,
            Some(hint),
        )
        .iter()
        .map(|token| token.move_made())
        .collect();
        assert_eq!(ordered.first().copied(), Some(hint));
    }

    #[test]
    fn killers_precede_history_and_captures_are_not_recorded() {
        let mut position = Position::starting();
        let secondary = legal_move(&mut position, "g1f3");
        let primary = legal_move(&mut position, "b1c3");
        let history_move = legal_move(&mut position, "e2e4");
        let mut state = QuietOrderingState::new();
        state.record_quiet_cutoff(Color::White, secondary, 2, 4);
        state.record_quiet_cutoff(Color::White, primary, 3, 4);
        for _ in 0..8 {
            state.record_quiet_cutoff(Color::White, history_move, 8, 5);
        }
        let tokens = position.legal_move_tokens().expect("legal tokens generate");
        let ordered: Vec<_> =
            ordered_legal_moves_with_state(&position, &tokens, MoveOrdering::Quiet, 4, &state)
                .iter()
                .map(|token| token.move_made())
                .collect();
        assert_eq!(&ordered[..3], [primary, secondary, history_move]);

        let mut capture_position: Position = "7k/8/8/3q4/2P5/8/8/K7 w - - 0 1"
            .parse()
            .expect("capture fixture is valid");
        let capture = legal_move(&mut capture_position, "c4d5");
        state.record_quiet_cutoff(Color::White, capture, 12, 3);
        assert_eq!(state.killers(3), Default::default());
        assert_eq!(state.history_score(Color::White, capture), 0);
    }
}
''',
)

# Alpha-beta typed error, policy propagation, ordering diagnostics.
path = "crates/chess-search/src/alpha_beta.rs"
replace_once(
    path,
    "use chess_core::{LegalMoveError, Move, Position, SearchHistory, SearchHistoryError};\n",
    "use chess_core::{\n"
    "    LegalMoveError, Move, Position, SearchHistory, SearchHistoryError, StaticExchangeError,\n"
    "};\n",
)
replace_once(
    path,
    "    move_ordering::{ordered_legal_moves_with_state_and_tt_move, MoveOrdering, QuietOrderingState},\n",
    "    move_ordering::{\n"
    "        ordered_legal_moves_with_state_and_tt_move_and_see, MoveOrdering, QuietOrderingState,\n"
    "    },\n",
)
replace_once(
    path,
    "    /// Reversible search-line history processing failed.\n    History(SearchHistoryError),\n",
    "    /// Reversible search-line history processing failed.\n"
    "    History(SearchHistoryError),\n"
    "    /// SEE capture ordering found contradictory internal move state.\n"
    "    StaticExchange(StaticExchangeError),\n",
)
replace_once(
    path,
    "            Self::History(error) => error.fmt(formatter),\n            Self::TranspositionTableAllocation(error) => error.fmt(formatter),\n",
    "            Self::History(error) => error.fmt(formatter),\n"
    "            Self::StaticExchange(error) => error.fmt(formatter),\n"
    "            Self::TranspositionTableAllocation(error) => error.fmt(formatter),\n",
)
replace_once(
    path,
    "impl From<SearchHistoryError> for AlphaBetaSearchError {\n    fn from(value: SearchHistoryError) -> Self {\n        Self::History(value)\n    }\n}\n",
    "impl From<SearchHistoryError> for AlphaBetaSearchError {\n"
    "    fn from(value: SearchHistoryError) -> Self {\n"
    "        Self::History(value)\n"
    "    }\n"
    "}\n\n"
    "impl From<StaticExchangeError> for AlphaBetaSearchError {\n"
    "    fn from(value: StaticExchangeError) -> Self {\n"
    "        Self::StaticExchange(value)\n"
    "    }\n"
    "}\n",
)
replace_once(
    path,
    "        maximum_quiescence_ply: policy.search_policy.maximum_quiescence_ply(),\n        weights: policy.weights,\n",
    "        maximum_quiescence_ply: policy.search_policy.maximum_quiescence_ply(),\n"
    "        see_capture_ordering: policy.search_policy.see_capture_ordering_enabled(),\n"
    "        weights: policy.weights,\n",
)
replace_once(
    path,
    "    maximum_quiescence_ply: u16,\n    weights: &'a EvaluationWeights,\n",
    "    maximum_quiescence_ply: u16,\n"
    "    see_capture_ordering: bool,\n"
    "    weights: &'a EvaluationWeights,\n",
)
replace_once(
    path,
    "            QuiescenceSearchPolicy::new(alpha, beta, context.ordering, context.weights),\n",
    "            QuiescenceSearchPolicy::new(\n"
    "                alpha,\n"
    "                beta,\n"
    "                context.ordering,\n"
    "                context.see_capture_ordering,\n"
    "                context.weights,\n"
    "            ),\n",
)
replace_once(
    path,
    "    let ordered_tokens = ordered_legal_moves_with_state_and_tt_move(\n        position,\n        &tokens,\n        context.ordering,\n        ply,\n        context.quiet_ordering,\n        transposition_table_move,\n    );\n    let mut nodes = 1_u64;\n",
    "    let ordered_tokens = ordered_legal_moves_with_state_and_tt_move_and_see(\n"
    "        position,\n"
    "        &tokens,\n"
    "        context.ordering,\n"
    "        ply,\n"
    "        context.quiet_ordering,\n"
    "        transposition_table_move,\n"
    "        context.see_capture_ordering,\n"
    "    )?;\n"
    "    let mut nodes = 1_u64;\n",
)
replace_once(
    path,
    "    let mut diagnostics = SearchDiagnostics::main_node();\n    let mut best_score = None;\n",
    "    let mut diagnostics = SearchDiagnostics::main_node();\n"
    "    ordered_tokens\n"
    "        .diagnostics()\n"
    "        .record_into(&mut diagnostics, &mut *context.cancellation)?;\n"
    "    let mut best_score = None;\n",
)

# Quiescence propagation and diagnostics.
path = "crates/chess-search/src/quiescence.rs"
replace_once(
    path,
    "    move_ordering::{ordered_legal_moves, MoveOrdering},\n",
    "    move_ordering::{ordered_legal_moves_with_see, MoveOrdering},\n",
)
replace_once(
    path,
    "    ordering: MoveOrdering,\n    weights: &'a EvaluationWeights,\n",
    "    ordering: MoveOrdering,\n"
    "    see_capture_ordering: bool,\n"
    "    weights: &'a EvaluationWeights,\n",
)
replace_once(
    path,
    "        ordering: MoveOrdering,\n        weights: &'a EvaluationWeights,\n    ) -> Self {\n        Self {\n            alpha,\n            beta,\n            ordering,\n            weights,\n        }\n",
    "        ordering: MoveOrdering,\n"
    "        see_capture_ordering: bool,\n"
    "        weights: &'a EvaluationWeights,\n"
    "    ) -> Self {\n"
    "        Self {\n"
    "            alpha,\n"
    "            beta,\n"
    "            ordering,\n"
    "            see_capture_ordering,\n"
    "            weights,\n"
    "        }\n",
)
replace_once(
    path,
    "        QuiescenceSearchPolicy::new(alpha, beta, ordering, &EvaluationWeights::DEFAULT),\n",
    "        QuiescenceSearchPolicy::new(\n"
    "            alpha,\n"
    "            beta,\n"
    "            ordering,\n"
    "            false,\n"
    "            &EvaluationWeights::DEFAULT,\n"
    "        ),\n",
)
replace_once(
    path,
    "        ordering,\n        weights,\n    } = policy;\n",
    "        ordering,\n"
    "        see_capture_ordering,\n"
    "        weights,\n"
    "    } = policy;\n",
)
replace_once(
    path,
    "    let ordered_tokens = ordered_legal_moves(position, &tokens, ordering);\n    let mut nodes = 1_u64;\n",
    "    let ordered_tokens =\n"
    "        ordered_legal_moves_with_see(position, &tokens, ordering, see_capture_ordering)?;\n"
    "    let mut nodes = 1_u64;\n",
)
replace_once(
    path,
    "    let mut diagnostics = SearchDiagnostics::quiescence_node();\n    let mut searched_moves = 0_usize;\n",
    "    let mut diagnostics = SearchDiagnostics::quiescence_node();\n"
    "    ordered_tokens\n"
    "        .diagnostics()\n"
    "        .record_into(&mut diagnostics, cancellation)?;\n"
    "    let mut searched_moves = 0_usize;\n",
)
replace_once(
    path,
    "            QuiescenceSearchPolicy::new(-beta, -alpha, ordering, weights),\n",
    "            QuiescenceSearchPolicy::new(\n"
    "                -beta,\n"
    "                -alpha,\n"
    "                ordering,\n"
    "                see_capture_ordering,\n"
    "                weights,\n"
    "            ),\n",
)

# Export the candidate identity constant.
replace_once(
    "crates/chess-search/src/lib.rs",
    "    MAXIMUM_CHECK_EXTENSIONS_PER_LINE, SEARCH_POLICY_SCHEMA_VERSION, V0_1_SEARCH_POLICY_CHECKSUM,\n    V0_1_SEARCH_POLICY_ID,\n",
    "    MAXIMUM_CHECK_EXTENSIONS_PER_LINE, SEARCH_POLICY_SCHEMA_VERSION,\n"
    "    SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID, V0_1_SEARCH_POLICY_CHECKSUM,\n"
    "    V0_1_SEARCH_POLICY_ID,\n",
)

# Public integration parity and restoration tests.
write(
    "crates/chess-search/tests/s2_5_see_ordering.rs",
    r'''use chess_core::{Move, Position, SearchHistory};
use chess_search::{
    iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights,
    EvaluationWeights, SearchLimits, SearchPolicySet, TranspositionTable,
    SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID,
};

const TT_MEBIBYTES: usize = 1;

fn run(
    fen: &str,
    depth: u16,
    policy: &SearchPolicySet,
) -> chess_search::SearchResult {
    let mut position = Position::from_fen(fen).expect("fixture FEN parses");
    let root = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_root = history.clone();
    let mut table = TranspositionTable::new(TT_MEBIBYTES).expect("small TT allocates");
    let result =
        iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights(
            &mut position,
            &mut history,
            SearchLimits::new().with_depth(depth),
            &mut table,
            policy,
            &EvaluationWeights::DEFAULT,
        )
        .expect("controlled search succeeds");
    assert_eq!(position, root);
    assert_eq!(history, history_root);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
    replay_pv(&root, result.principal_variation().map(|pv| pv.moves()).unwrap_or(&[]));
    result
}

fn replay_pv(root: &Position, moves: &[Move]) {
    let mut position = root.clone();
    for current in moves {
        let token = position
            .legal_move_tokens()
            .expect("PV legal tokens generate")
            .iter()
            .find(|token| token.move_made() == *current)
            .expect("PV move is legal");
        position
            .make_legal_token(token)
            .expect("PV legal token applies");
    }
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
}

#[test]
fn candidate_identity_is_explicit_valid_and_default_remains_inactive() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::see_capture_ordering_candidate();
    baseline.validate().expect("baseline policy validates");
    candidate.validate().expect("candidate policy validates");
    assert_eq!(candidate.identifier, SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID);
    assert!(!baseline.policy.see_capture_ordering_enabled());
    assert!(candidate.policy.see_capture_ordering_enabled());
    assert_ne!(baseline.checksum, candidate.checksum);
}

#[test]
fn candidate_preserves_exact_scores_mate_distance_and_legal_pvs() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::see_capture_ordering_candidate();
    for (fen, depth) in [
        ("7k/5Q2/6K1/8/8/8/8/8 w - - 0 1", 3),
        ("4Q2k/8/4K3/8/8/8/8/8 b - - 0 1", 6),
        ("7k/P7/6K1/8/8/8/8/8 w - - 0 1", 3),
        ("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1", 3),
        ("3rk3/8/8/8/8/8/8/K2Q4 w - - 0 1", 3),
        ("r1bq1rk1/ppp2ppp/2np1n2/4p3/2B1P3/2N2N2/PPPP1PPP/R1BQ1RK1 w - - 4 7", 4),
    ] {
        let baseline_result = run(fen, depth, &baseline);
        let candidate_result = run(fen, depth, &candidate);
        assert_eq!(candidate_result.score(), baseline_result.score(), "{fen}");
        assert_eq!(
            candidate_result.completed_depth(),
            baseline_result.completed_depth(),
            "{fen}"
        );
    }
}

#[test]
fn candidate_records_exact_capture_classes_without_pruning() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::see_capture_ordering_candidate();
    let fen = "7k/8/8/1p2q3/2P1Q3/8/K7/8 w - - 0 1";
    let baseline_result = run(fen, 3, &baseline);
    let candidate_result = run(fen, 3, &candidate);
    let baseline_diagnostics = baseline_result.search_diagnostics();
    let diagnostics = candidate_result.search_diagnostics();
    assert_eq!(baseline_diagnostics.see_calls(), 0);
    assert!(diagnostics.see_calls() > 0);
    assert_eq!(
        diagnostics.see_calls(),
        diagnostics.see_winning_captures()
            + diagnostics.see_equal_captures()
            + diagnostics.see_losing_captures()
    );
    assert_eq!(diagnostics.see_prunes(), 0);
    assert_eq!(diagnostics.quiescence_see_prunes(), 0);
    assert_eq!(candidate_result.score(), baseline_result.score());
}
''',
)

print("S2-5 core patch applied")
