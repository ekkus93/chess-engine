use core::fmt;

use crate::{Color, FullmoveNumber, HalfmoveClock, Square};

use super::{zobrist::side_to_move_key, Position};

/// A fail-loud search-only null-transition error.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SearchNullError {
    /// The side to move is checked and therefore cannot pass synthetically.
    InCheck {
        /// Checked side that would otherwise have been toggled.
        side_to_move: Color,
    },
    /// The supplied opaque undo token does not match the current synthetic state.
    UndoStateMismatch,
}

impl fmt::Display for SearchNullError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InCheck { side_to_move } => write!(
                formatter,
                "cannot apply a search-only null transition while {side_to_move} is in check"
            ),
            Self::UndoStateMismatch => formatter
                .write_str("search-only null undo token does not match the current position state"),
        }
    }
}

impl std::error::Error for SearchNullError {}

/// Opaque state required to reverse one search-only null transition.
///
/// This token is deliberately separate from legal-move undo state. It cannot
/// be constructed or altered by callers and must be consumed in LIFO order
/// against the exact synthetic position that produced it.
#[derive(Debug, Eq, PartialEq)]
pub struct SearchNullUndo {
    previous_side_to_move: Color,
    previous_en_passant: Option<Square>,
    previous_halfmove_clock: HalfmoveClock,
    previous_fullmove_number: FullmoveNumber,
    previous_zobrist: u64,
    resulting_zobrist: u64,
}

impl Position {
    /// Applies one reversible search-only null transition.
    ///
    /// The board, castling rights, and legal clocks remain unchanged. The side
    /// to move toggles, en-passant is cleared, and the canonical incremental
    /// hash removes the prior en-passant contribution before toggling its side
    /// key. Checked positions fail before any field is changed.
    pub fn make_search_null(&mut self) -> Result<SearchNullUndo, SearchNullError> {
        let side_to_move = self.side_to_move();
        if self.is_in_check(side_to_move) {
            return Err(SearchNullError::InCheck { side_to_move });
        }

        let undo = SearchNullUndo {
            previous_side_to_move: side_to_move,
            previous_en_passant: self.en_passant(),
            previous_halfmove_clock: self.halfmove_clock(),
            previous_fullmove_number: self.fullmove_number(),
            previous_zobrist: self.zobrist(),
            resulting_zobrist: self.zobrist()
                ^ self.canonical_en_passant_key()
                ^ side_to_move_key(),
        };

        self.en_passant = None;
        self.side_to_move = side_to_move.opposite();
        self.zobrist = undo.resulting_zobrist;
        debug_assert_eq!(self.zobrist(), self.recomputed_zobrist());
        Ok(undo)
    }

    /// Reverses one search-only null transition exactly.
    ///
    /// A token from another position or a non-LIFO restoration attempt fails
    /// before any field is changed.
    pub fn unmake_search_null(&mut self, undo: SearchNullUndo) -> Result<(), SearchNullError> {
        if self.side_to_move() != undo.previous_side_to_move.opposite()
            || self.en_passant().is_some()
            || self.halfmove_clock() != undo.previous_halfmove_clock
            || self.fullmove_number() != undo.previous_fullmove_number
            || self.zobrist() != undo.resulting_zobrist
        {
            return Err(SearchNullError::UndoStateMismatch);
        }

        self.side_to_move = undo.previous_side_to_move;
        self.en_passant = undo.previous_en_passant;
        self.halfmove_clock = undo.previous_halfmove_clock;
        self.fullmove_number = undo.previous_fullmove_number;
        self.zobrist = undo.previous_zobrist;
        debug_assert_eq!(self.zobrist(), self.recomputed_zobrist());
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use crate::{Color, Position, SearchHistory};

    use super::SearchNullError;

    fn position(fen: &str) -> Position {
        Position::from_fen(fen).expect("search-null fixture FEN is valid")
    }

    fn assert_board_and_rule_state_unchanged(actual: &Position, expected: &Position) {
        for index in 0..crate::Square::COUNT {
            let square = crate::Square::new(index).expect("board index is valid");
            assert_eq!(actual.piece_at(square), expected.piece_at(square));
        }
        for color in [Color::White, Color::Black] {
            assert_eq!(actual.occupancy(color), expected.occupancy(color));
            assert_eq!(actual.king_square(color), expected.king_square(color));
            for kind in crate::PieceKind::ALL {
                assert_eq!(
                    actual.piece_bitboard(color, kind),
                    expected.piece_bitboard(color, kind)
                );
            }
        }
        assert_eq!(actual.all_occupancy(), expected.all_occupancy());
        assert_eq!(actual.castling_rights(), expected.castling_rights());
        assert_eq!(actual.halfmove_clock(), expected.halfmove_clock());
        assert_eq!(actual.fullmove_number(), expected.fullmove_number());
    }

    #[test]
    fn search_null_round_trip_clears_en_passant_and_restores_exactly() {
        let mut current = position("r3k2r/8/8/3pP3/8/8/8/R3K2R w KQkq d6 99 42");
        let snapshot = current.clone();
        let previous_zobrist = current.zobrist();

        let undo = current
            .make_search_null()
            .expect("eligible position accepts a search-only null transition");

        assert_eq!(current.side_to_move(), Color::Black);
        assert_eq!(current.en_passant(), None);
        assert_board_and_rule_state_unchanged(&current, &snapshot);
        assert_ne!(current.zobrist(), previous_zobrist);
        assert_eq!(current.zobrist(), current.recomputed_zobrist());

        current
            .unmake_search_null(undo)
            .expect("matching search-null token restores exactly");
        assert_eq!(current, snapshot);
        assert_eq!(current.zobrist(), previous_zobrist);
        assert_eq!(current.zobrist(), current.recomputed_zobrist());
    }

    #[test]
    fn search_null_preserves_maximum_clocks_without_arithmetic() {
        let mut current = position("7k/8/8/8/8/8/8/K7 b - - 65535 65535");
        let snapshot = current.clone();

        let undo = current
            .make_search_null()
            .expect("maximum counters do not overflow because null does not advance them");
        assert_eq!(current.halfmove_clock(), snapshot.halfmove_clock());
        assert_eq!(current.fullmove_number(), snapshot.fullmove_number());
        assert_eq!(current.zobrist(), current.recomputed_zobrist());

        current
            .unmake_search_null(undo)
            .expect("maximum-counter position restores");
        assert_eq!(current, snapshot);
    }

    #[test]
    fn search_null_rejects_checked_side_before_mutation() {
        let mut current = position("4k3/8/8/8/8/8/4R3/4K3 b - - 17 9");
        let snapshot = current.clone();

        assert_eq!(
            current.make_search_null(),
            Err(SearchNullError::InCheck {
                side_to_move: Color::Black
            })
        );
        assert_eq!(current, snapshot);
        assert_eq!(current.zobrist(), current.recomputed_zobrist());
    }

    #[test]
    fn search_null_rejects_mismatched_undo_before_mutation() {
        let mut source = Position::starting();
        let source_undo = source
            .make_search_null()
            .expect("source transition succeeds");

        let mut target = position("7k/8/8/8/8/8/8/K7 w - - 0 1");
        let _target_undo = target
            .make_search_null()
            .expect("target transition succeeds");
        let target_snapshot = target.clone();

        assert_eq!(
            target.unmake_search_null(source_undo),
            Err(SearchNullError::UndoStateMismatch)
        );
        assert_eq!(target, target_snapshot);
        assert_eq!(target.zobrist(), target.recomputed_zobrist());
    }

    #[test]
    fn search_null_keeps_search_history_on_the_legal_parent() {
        let mut current = position("7k/8/8/3pP3/8/8/8/7K w - d6 73 20");
        let history = SearchHistory::from_position(&current);
        let history_snapshot = history.clone();
        let legal_parent_zobrist = current.zobrist();

        let undo = current
            .make_search_null()
            .expect("search-only null transition succeeds");

        assert_eq!(history, history_snapshot);
        assert_eq!(history.current_zobrist(), Some(legal_parent_zobrist));
        assert_ne!(history.current_zobrist(), Some(current.zobrist()));
        assert_eq!(history.line_len(), 0);

        current
            .unmake_search_null(undo)
            .expect("history-independent transition restores");
        assert_eq!(history.current_zobrist(), Some(current.zobrist()));
    }

    #[test]
    fn search_null_repeated_round_trips_remain_exact() {
        let mut current = position("r3k2r/8/8/3pP3/8/8/8/R3K2R w KQkq d6 12 34");
        let snapshot = current.clone();

        for _ in 0..32 {
            let undo = current
                .make_search_null()
                .expect("repeated transition succeeds");
            assert_eq!(current.zobrist(), current.recomputed_zobrist());
            current
                .unmake_search_null(undo)
                .expect("repeated restoration succeeds");
            assert_eq!(current, snapshot);
            assert_eq!(current.zobrist(), current.recomputed_zobrist());
        }
    }
}
