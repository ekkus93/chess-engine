use chess_core::{
    LegalMoveToken, LegalMoveTokenList, Move, MoveKind, PieceKind, Position, MAX_PSEUDO_LEGAL_MOVES,
};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum MoveOrdering {
    Generation,
    Tactical,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
struct MoveOrderKey {
    transposition_table: u8,
    category: u8,
    promotion: u16,
    victim: u16,
    attacker_preference: u16,
}

impl MoveOrderKey {
    const GENERATION: Self = Self {
        transposition_table: 0,
        category: 0,
        promotion: 0,
        victim: 0,
        attacker_preference: 0,
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
        MoveOrdering::Tactical => transposition_table_move_hook(position),
    };
    order_legal_moves_with_tt_move(position, tokens, ordering, transposition_table_move)
}

const fn transposition_table_move_hook(_position: &Position) -> Option<Move> {
    None
}

fn order_legal_moves_with_tt_move(
    position: &Position,
    tokens: &LegalMoveTokenList,
    ordering: MoveOrdering,
    transposition_table_move: Option<Move>,
) -> OrderedLegalMoves {
    let mut ordered = OrderedLegalMoves::new();

    for token in tokens.iter() {
        let current = token.move_made();
        let key = match ordering {
            MoveOrdering::Generation => MoveOrderKey::GENERATION,
            MoveOrdering::Tactical => tactical_key(position, current, transposition_table_move),
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
) -> MoveOrderKey {
    let promotion = current.promotion();
    let capture = current.kind().is_capture();
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

    MoveOrderKey {
        transposition_table: u8::from(transposition_table_move == Some(current)),
        category,
        promotion: promotion.map_or(0, piece_value),
        victim,
        attacker_preference,
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
        order_legal_moves_with_tt_move, ordered_legal_moves, transposition_table_move_hook,
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
        let ordered: Vec<_> =
            order_legal_moves_with_tt_move(&root, &tokens, MoveOrdering::Tactical, Some(tt_move))
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
