use core::cmp::Reverse;

use chess_core::{
    Color, LegalMoveToken, LegalMoveTokenList, Move, MoveKind, PieceKind, Position,
    MAX_PSEUDO_LEGAL_MOVES,
};

use crate::MAX_MATE_PLY;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum MoveOrdering {
    Generation,
    Tactical,
    Quiet,
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
}

impl OrderedLegalMoves {
    fn new() -> Self {
        Self {
            entries: [None; MAX_PSEUDO_LEGAL_MOVES],
            len: 0,
        }
    }

    pub(crate) fn iter(&self) -> impl ExactSizeIterator<Item = LegalMoveToken> + '_ {
        self.entries[..self.len].iter().copied().map(|entry| {
            entry
                .expect("occupied ordered-move prefix contains entries")
                .token
        })
    }
}

pub(crate) fn ordered_legal_moves(
    position: &Position,
    tokens: &LegalMoveTokenList,
    ordering: MoveOrdering,
) -> OrderedLegalMoves {
    let transposition_table_move = match ordering {
        MoveOrdering::Generation => None,
        MoveOrdering::Tactical | MoveOrdering::Quiet => transposition_table_move_hook(position),
    };
    let previous_pv_move = match ordering {
        MoveOrdering::Quiet => previous_pv_move_hook(0),
        MoveOrdering::Generation | MoveOrdering::Tactical => None,
    };
    order_legal_moves_with_hints(
        position,
        tokens,
        ordering,
        0,
        None,
        transposition_table_move,
        previous_pv_move,
    )
}

pub(crate) fn ordered_legal_moves_with_state(
    position: &Position,
    tokens: &LegalMoveTokenList,
    ordering: MoveOrdering,
    ply: u16,
    quiet_state: &QuietOrderingState,
) -> OrderedLegalMoves {
    let previous_pv_move = match ordering {
        MoveOrdering::Quiet => previous_pv_move_hook(ply),
        MoveOrdering::Generation | MoveOrdering::Tactical => None,
    };
    order_legal_moves_with_hints(
        position,
        tokens,
        ordering,
        ply,
        Some(quiet_state),
        transposition_table_move_hook(position),
        previous_pv_move,
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
    let mut ordered = OrderedLegalMoves::new();
    for token in tokens.iter() {
        let current = token.move_made();
        let key = match ordering {
            MoveOrdering::Generation => MoveOrderKey::GENERATION,
            MoveOrdering::Tactical => tactical_key(
                position,
                current,
                transposition_table_move,
                None,
                KillerMoves::default(),
                0,
                None,
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
    ordered
}

fn tactical_key(
    position: &Position,
    current: Move,
    transposition_table_move: Option<Move>,
    previous_pv_move: Option<Move>,
    killers: KillerMoves,
    history: u32,
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
    MoveOrderKey {
        transposition_table: u8::from(transposition_table_move == Some(current)),
        previous_principal_variation: u8::from(previous_pv_move == Some(current)),
        category,
        promotion: promotion.map_or(0, piece_value),
        victim,
        attacker_preference,
        killer,
        history: if quiet { history } else { 0 },
        encoded_tie_break: if quiet { encoded_tie_break } else { None },
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
    use chess_core::{Move, Position};

    use super::{
        order_legal_moves_with_hints, ordered_legal_moves, transposition_table_move_hook,
        MoveOrdering,
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
        ordered_legal_moves_with_state, previous_pv_move_hook, MoveOrdering, QuietOrderingState,
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
