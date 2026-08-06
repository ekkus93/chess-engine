use core::cmp::Reverse;

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

    pub(crate) fn is_killer(&self, ply: u16, current: Move) -> bool {
        let killers = self.killers(ply);
        killers.primary == Some(current) || killers.secondary == Some(current)
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
    tokens: [Option<LegalMoveToken>; MAX_PSEUDO_LEGAL_MOVES],
    len: usize,
    diagnostics: MoveOrderingDiagnostics,
}

impl OrderedLegalMoves {
    fn new() -> Self {
        Self {
            tokens: [None; MAX_PSEUDO_LEGAL_MOVES],
            len: 0,
            diagnostics: MoveOrderingDiagnostics::default(),
        }
    }

    pub(crate) fn iter(&self) -> impl ExactSizeIterator<Item = LegalMoveToken> + '_ {
        self.tokens[..self.len]
            .iter()
            .copied()
            .map(|token| token.expect("occupied ordered-move prefix contains legal tokens"))
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
        (transposition_table_move, previous_pv_move),
        see_capture_ordering,
    )
}

#[cfg(test)]
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

#[cfg(test)]
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
        (transposition_table_move, previous_pv_move),
        see_capture_ordering,
    )
}

const fn transposition_table_move_hook(_position: &Position) -> Option<Move> {
    None
}

const fn previous_pv_move_hook(_ply: u16) -> Option<Move> {
    None
}

#[cfg(test)]
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
        (transposition_table_move, previous_pv_move),
        false,
    )
    .expect("baseline ordering does not invoke static exchange evaluation")
}

fn try_order_legal_moves_with_hints(
    position: &Position,
    tokens: &LegalMoveTokenList,
    ordering: MoveOrdering,
    ply: u16,
    quiet_state: Option<&QuietOrderingState>,
    priority_moves: (Option<Move>, Option<Move>),
    see_capture_ordering: bool,
) -> Result<OrderedLegalMoves, StaticExchangeError> {
    let (transposition_table_move, previous_pv_move) = priority_moves;
    let mut entries: [Option<OrderedEntry>; MAX_PSEUDO_LEGAL_MOVES] =
        [None; MAX_PSEUDO_LEGAL_MOVES];
    let mut len = 0_usize;
    let mut diagnostics = MoveOrderingDiagnostics::default();
    for token in tokens.iter() {
        let current = token.move_made();
        let see_value = if ordering != MoveOrdering::Generation
            && see_capture_ordering
            && current.kind().is_capture()
        {
            let value = static_exchange_evaluation(position, current)?;
            diagnostics.record_class(value.class());
            Some(value)
        } else {
            None
        };
        let key = match ordering {
            MoveOrdering::Generation => MoveOrderKey::GENERATION,
            MoveOrdering::Tactical => tactical_key(
                position,
                current,
                (transposition_table_move, None),
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
                    (transposition_table_move, previous_pv_move),
                    killers,
                    history,
                    see_value,
                    Some(Reverse(current)),
                )
            }
        };
        let entry = OrderedEntry { token, key };
        let mut insertion = len;
        while insertion > 0 {
            let previous =
                entries[insertion - 1].expect("occupied ordered-move prefix contains entries");
            if previous.key >= entry.key {
                break;
            }
            entries[insertion] = Some(previous);
            insertion -= 1;
        }
        entries[insertion] = Some(entry);
        len += 1;
    }

    let mut ordered = OrderedLegalMoves::new();
    ordered.len = len;
    ordered.diagnostics = diagnostics;
    for (destination, entry) in ordered.tokens[..len].iter_mut().zip(entries[..len].iter()) {
        *destination = Some(
            entry
                .expect("occupied sorted-move prefix contains entries")
                .token,
        );
    }
    Ok(ordered)
}

fn tactical_key(
    position: &Position,
    current: Move,
    priority_moves: (Option<Move>, Option<Move>),
    killers: KillerMoves,
    history: u32,
    see_value: Option<StaticExchangeValue>,
    encoded_tie_break: Option<Reverse<Move>>,
) -> MoveOrderKey {
    let (transposition_table_move, previous_pv_move) = priority_moves;
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
    use core::mem::size_of;

    use chess_core::{
        Move, Position, StaticExchangeError, StaticExchangeMoveStateError, MAX_PSEUDO_LEGAL_MOVES,
    };

    use super::{
        order_legal_moves_with_hints, ordered_legal_moves, ordered_legal_moves_with_see,
        tactical_key, transposition_table_move_hook, try_order_legal_moves_with_hints, KillerMoves,
        MoveOrdering, OrderedEntry, OrderedLegalMoves,
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
    fn recursively_retained_ordering_excludes_temporary_sort_keys() {
        assert!(
            size_of::<OrderedLegalMoves>()
                < size_of::<[Option<OrderedEntry>; MAX_PSEUDO_LEGAL_MOVES]>()
        );
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
        let mut root = position("3r3k/P7/8/8/8/8/8/K2Q4 w - - 0 1");
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
            (Some(tt_move), None),
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
        let mut root = position("4k3/8/2p5/3p4/4P3/8/8/4K3 w - - 0 1");
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
                (None, None),
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
        let mut root = position("7k/8/8/1p2q3/2P1Q3/8/K7/8 w - - 0 1");
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
        let mut root = position("7k/8/8/1p2q3/2P1Q3/8/K7/8 w - - 0 1");
        let tokens = root
            .legal_move_tokens()
            .expect("legal move tokens generate");
        let contradictory = position("7k/8/8/8/8/8/8/K7 w - - 0 1");
        let error = match try_order_legal_moves_with_hints(
            &contradictory,
            &tokens,
            MoveOrdering::Tactical,
            0,
            None,
            (None, None),
            true,
        ) {
            Ok(_) => panic!("contradictory capture source must fail"),
            Err(error) => error,
        };
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
        let mut position = Position::starting();
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
