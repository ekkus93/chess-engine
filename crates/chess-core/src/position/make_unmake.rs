use crate::{
    CastleSide, CastlingRights, Color, FullmoveNumber, HalfmoveClock, Move, MoveKind, Piece,
    PieceKind, Square,
};

use super::{
    zobrist::{castling_state_key, piece_square_key, side_to_move_key},
    LegalMoveError, Position,
};

/// Opaque state required to reverse one successfully applied move.
///
/// An undo token is bound to the exact move that produced it and must be
/// consumed in last-in, first-out order against the same position. Callers
/// cannot construct or alter tokens, preventing incomplete restoration state.
#[derive(Debug, Eq, PartialEq)]
pub struct PositionUndo {
    current: Move,
    moving_piece: Piece,
    captured: Option<(Square, Piece)>,
    previous_castling_rights: CastlingRights,
    previous_en_passant: Option<Square>,
    previous_halfmove_clock: HalfmoveClock,
    previous_fullmove_number: FullmoveNumber,
    previous_side_to_move: Color,
    previous_zobrist: u64,
}

impl PositionUndo {
    /// Returns the move bound to this undo token.
    #[must_use]
    pub const fn move_made(&self) -> Move {
        self.current
    }

    /// Returns the captured square and piece, when the move captured.
    #[must_use]
    pub const fn captured(&self) -> Option<(Square, Piece)> {
        self.captured
    }
}

impl Position {
    /// Applies one exact legal move and returns the state needed to reverse it.
    ///
    /// The move must match one of the packed identities returned by
    /// [`Position::legal_moves`]. An illegal move returns an error without
    /// changing any position field.
    pub fn make_move(&mut self, current: Move) -> Result<PositionUndo, LegalMoveError> {
        if !self.is_legal_move(current)? {
            return Err(LegalMoveError::IllegalMove { current });
        }
        self.make_generated_legal_move(current)
    }

    /// Reverses one move using its opaque undo token.
    ///
    /// Tokens must be consumed in last-in, first-out order against the same
    /// position. A token that does not match the current post-move state is
    /// rejected before any mutation occurs.
    pub fn unmake_move(&mut self, undo: PositionUndo) -> Result<(), LegalMoveError> {
        self.unmake_generated_legal_move(undo)
    }

    pub(crate) fn make_generated_legal_move(
        &mut self,
        current: Move,
    ) -> Result<PositionUndo, LegalMoveError> {
        let source = current.source();
        let destination = current.destination();
        let moving_piece = self
            .piece_at(source)
            .ok_or(LegalMoveError::InvalidGeneratedMove { current })?;
        let moving_side = self.side_to_move();
        if moving_piece.color != moving_side
            || !self.generated_move_matches_state(current, moving_piece)
        {
            return Err(LegalMoveError::InvalidGeneratedMove { current });
        }

        let captured = self.capture_for_move(current, moving_side)?;
        let mut next_halfmove = self.halfmove_clock();
        if moving_piece.kind == PieceKind::Pawn || captured.is_some() {
            next_halfmove.reset();
        } else {
            next_halfmove
                .checked_increment()
                .ok_or(LegalMoveError::HalfmoveClockOverflow)?;
        }
        let mut next_fullmove = self.fullmove_number();
        if moving_side == Color::Black {
            next_fullmove
                .checked_increment()
                .ok_or(LegalMoveError::FullmoveNumberOverflow)?;
        }
        let next_en_passant = if current.kind() == MoveKind::DoublePawnPush {
            Some(
                Square::from_row_file((source.row() + destination.row()) / 2, source.file())
                    .expect("double-push midpoint is valid"),
            )
        } else {
            None
        };
        let next_castling =
            updated_castling_rights(self.castling_rights(), moving_piece, source, captured);
        let undo = PositionUndo {
            current,
            moving_piece,
            captured,
            previous_castling_rights: self.castling_rights(),
            previous_en_passant: self.en_passant(),
            previous_halfmove_clock: self.halfmove_clock(),
            previous_fullmove_number: self.fullmove_number(),
            previous_side_to_move: moving_side,
            previous_zobrist: self.zobrist(),
        };
        let mut next_zobrist = self.zobrist()
            ^ self.canonical_en_passant_key()
            ^ castling_state_key(self.castling_rights())
            ^ move_hash_delta(current, moving_piece, captured, moving_side);

        if let Some((capture_square, _)) = captured {
            self.editor().remove_piece(capture_square)?;
        }

        match current.kind() {
            MoveKind::KingCastle | MoveKind::QueenCastle => {
                self.editor().move_piece(source, destination)?;
                let (rook_source, rook_destination) = castle_rook_squares(current, moving_side);
                self.editor().move_piece(rook_source, rook_destination)?;
            }
            MoveKind::KnightPromotion
            | MoveKind::BishopPromotion
            | MoveKind::RookPromotion
            | MoveKind::QueenPromotion
            | MoveKind::KnightPromotionCapture
            | MoveKind::BishopPromotionCapture
            | MoveKind::RookPromotionCapture
            | MoveKind::QueenPromotionCapture => {
                self.editor().remove_piece(source)?;
                self.editor().add_piece(
                    destination,
                    Piece::new(
                        moving_side,
                        current
                            .promotion()
                            .expect("promotion kinds carry promotion identity"),
                    ),
                )?;
            }
            MoveKind::Quiet
            | MoveKind::DoublePawnPush
            | MoveKind::Capture
            | MoveKind::EnPassant => {
                self.editor().move_piece(source, destination)?;
            }
        }

        self.castling_rights = next_castling;
        self.en_passant = next_en_passant;
        self.halfmove_clock = next_halfmove;
        self.fullmove_number = next_fullmove;
        self.side_to_move = moving_side.opposite();
        next_zobrist ^= castling_state_key(self.castling_rights());
        next_zobrist ^= side_to_move_key();
        next_zobrist ^= self.canonical_en_passant_key();
        self.zobrist = next_zobrist;
        debug_assert_eq!(self.zobrist(), self.recomputed_zobrist());
        Ok(undo)
    }

    pub(crate) fn unmake_generated_legal_move(
        &mut self,
        undo: PositionUndo,
    ) -> Result<(), LegalMoveError> {
        if !self.undo_matches_position(&undo) {
            return Err(LegalMoveError::UndoStateMismatch {
                current: undo.current,
            });
        }

        let current = undo.current;
        let source = current.source();
        let destination = current.destination();
        let moving_side = undo.previous_side_to_move;

        match current.kind() {
            MoveKind::KingCastle | MoveKind::QueenCastle => {
                let (rook_source, rook_destination) = castle_rook_squares(current, moving_side);
                self.editor().move_piece(rook_destination, rook_source)?;
                self.editor().move_piece(destination, source)?;
            }
            MoveKind::KnightPromotion
            | MoveKind::BishopPromotion
            | MoveKind::RookPromotion
            | MoveKind::QueenPromotion
            | MoveKind::KnightPromotionCapture
            | MoveKind::BishopPromotionCapture
            | MoveKind::RookPromotionCapture
            | MoveKind::QueenPromotionCapture => {
                self.editor().remove_piece(destination)?;
                self.editor()
                    .add_piece(source, Piece::new(moving_side, PieceKind::Pawn))?;
            }
            MoveKind::Quiet
            | MoveKind::DoublePawnPush
            | MoveKind::Capture
            | MoveKind::EnPassant => {
                self.editor().move_piece(destination, source)?;
            }
        }

        if let Some((capture_square, captured_piece)) = undo.captured {
            self.editor().add_piece(capture_square, captured_piece)?;
        }

        self.castling_rights = undo.previous_castling_rights;
        self.en_passant = undo.previous_en_passant;
        self.halfmove_clock = undo.previous_halfmove_clock;
        self.fullmove_number = undo.previous_fullmove_number;
        self.side_to_move = undo.previous_side_to_move;
        self.zobrist = undo.previous_zobrist;
        debug_assert_eq!(self.zobrist(), self.recomputed_zobrist());
        Ok(())
    }

    pub(super) fn generated_move_matches_state(&self, current: Move, moving_piece: Piece) -> bool {
        let side = moving_piece.color;
        let destination = current.destination();
        let promotion_row = match side {
            Color::White => 0,
            Color::Black => 7,
        };

        if current.promotion().is_some()
            && (moving_piece.kind != PieceKind::Pawn || destination.row() != promotion_row)
        {
            return false;
        }
        if current.promotion().is_none()
            && moving_piece.kind == PieceKind::Pawn
            && destination.row() == promotion_row
        {
            return false;
        }

        match current.kind() {
            MoveKind::EnPassant => self.en_passant_capture_square(current, side).is_some(),
            MoveKind::KingCastle | MoveKind::QueenCastle => {
                self.castling_move_matches_state(current, moving_piece)
            }
            MoveKind::KnightPromotion
            | MoveKind::BishopPromotion
            | MoveKind::RookPromotion
            | MoveKind::QueenPromotion => self.piece_at(destination).is_none(),
            MoveKind::KnightPromotionCapture
            | MoveKind::BishopPromotionCapture
            | MoveKind::RookPromotionCapture
            | MoveKind::QueenPromotionCapture
            | MoveKind::Capture => self
                .piece_at(destination)
                .is_some_and(|piece| piece.color != side && piece.kind != PieceKind::King),
            MoveKind::Quiet | MoveKind::DoublePawnPush => self.piece_at(destination).is_none(),
        }
    }

    fn undo_matches_position(&self, undo: &PositionUndo) -> bool {
        let current = undo.current;
        let source = current.source();
        let destination = current.destination();
        let moving_side = undo.previous_side_to_move;
        if self.side_to_move() != moving_side.opposite() || self.piece_at(source).is_some() {
            return false;
        }

        let destination_piece = match current.promotion() {
            Some(kind) => Piece::new(moving_side, kind),
            None => undo.moving_piece,
        };
        if self.piece_at(destination) != Some(destination_piece) {
            return false;
        }

        if matches!(current.kind(), MoveKind::KingCastle | MoveKind::QueenCastle) {
            let (rook_source, rook_destination) = castle_rook_squares(current, moving_side);
            if self.piece_at(rook_source).is_some()
                || self.piece_at(rook_destination) != Some(Piece::new(moving_side, PieceKind::Rook))
            {
                return false;
            }
        }

        if let Some((capture_square, _)) = undo.captured {
            if capture_square != destination && self.piece_at(capture_square).is_some() {
                return false;
            }
        }
        true
    }

    fn castling_move_matches_state(&self, current: Move, moving_piece: Piece) -> bool {
        if moving_piece.kind != PieceKind::King {
            return false;
        }
        let side = moving_piece.color;
        let row = match side {
            Color::White => 7,
            Color::Black => 0,
        };
        let (castle_side, destination_file) = match current.kind() {
            MoveKind::KingCastle => (CastleSide::KingSide, 6),
            MoveKind::QueenCastle => (CastleSide::QueenSide, 2),
            _ => return false,
        };
        let source = home_square(row, 4);
        let destination = home_square(row, destination_file);
        let (rook_source, _) = castle_rook_squares(current, side);
        current.source() == source
            && current.destination() == destination
            && self.castling_rights().contains(side, castle_side)
            && self.piece_at(rook_source) == Some(Piece::new(side, PieceKind::Rook))
            && self.piece_at(destination).is_none()
    }

    fn capture_for_move(
        &self,
        current: Move,
        side: Color,
    ) -> Result<Option<(Square, Piece)>, LegalMoveError> {
        if current.kind() == MoveKind::EnPassant {
            return self
                .en_passant_capture_square(current, side)
                .map(|square| {
                    (
                        square,
                        self.piece_at(square)
                            .expect("validated en-passant capture square contains a pawn"),
                    )
                })
                .map(Some)
                .ok_or(LegalMoveError::InvalidGeneratedMove { current });
        }
        if current.kind().is_capture() {
            return self
                .piece_at(current.destination())
                .filter(|piece| piece.color != side && piece.kind != PieceKind::King)
                .map(|piece| Some((current.destination(), piece)))
                .ok_or(LegalMoveError::InvalidGeneratedMove { current });
        }
        Ok(None)
    }

    fn en_passant_capture_square(&self, current: Move, side: Color) -> Option<Square> {
        if current.kind() != MoveKind::EnPassant
            || self.en_passant() != Some(current.destination())
            || self.piece_at(current.destination()).is_some()
        {
            return None;
        }
        let row = match side {
            Color::White => current.destination().row().checked_add(1)?,
            Color::Black => current.destination().row().checked_sub(1)?,
        };
        let captured = Square::from_row_file(row, current.destination().file())?;
        (self.piece_at(captured) == Some(Piece::new(side.opposite(), PieceKind::Pawn)))
            .then_some(captured)
    }
}

fn move_hash_delta(
    current: Move,
    moving_piece: Piece,
    captured: Option<(Square, Piece)>,
    moving_side: Color,
) -> u64 {
    let mut delta = piece_square_key(moving_piece, current.source());
    if let Some((capture_square, captured_piece)) = captured {
        delta ^= piece_square_key(captured_piece, capture_square);
    }

    match current.kind() {
        MoveKind::KingCastle | MoveKind::QueenCastle => {
            delta ^= piece_square_key(moving_piece, current.destination());
            let rook = Piece::new(moving_side, PieceKind::Rook);
            let (rook_source, rook_destination) = castle_rook_squares(current, moving_side);
            delta ^= piece_square_key(rook, rook_source);
            delta ^= piece_square_key(rook, rook_destination);
        }
        MoveKind::KnightPromotion
        | MoveKind::BishopPromotion
        | MoveKind::RookPromotion
        | MoveKind::QueenPromotion
        | MoveKind::KnightPromotionCapture
        | MoveKind::BishopPromotionCapture
        | MoveKind::RookPromotionCapture
        | MoveKind::QueenPromotionCapture => {
            let promoted = Piece::new(
                moving_side,
                current
                    .promotion()
                    .expect("promotion kinds carry promotion identity"),
            );
            delta ^= piece_square_key(promoted, current.destination());
        }
        MoveKind::Quiet | MoveKind::DoublePawnPush | MoveKind::Capture | MoveKind::EnPassant => {
            delta ^= piece_square_key(moving_piece, current.destination());
        }
    }
    delta
}

fn updated_castling_rights(
    mut rights: CastlingRights,
    moving_piece: Piece,
    source: Square,
    captured: Option<(Square, Piece)>,
) -> CastlingRights {
    if moving_piece.kind == PieceKind::King {
        rights.clear_color(moving_piece.color);
    } else if moving_piece.kind == PieceKind::Rook {
        clear_rook_home_right(&mut rights, moving_piece.color, source);
    }
    if let Some((capture_square, captured_piece)) = captured {
        if captured_piece.kind == PieceKind::Rook {
            clear_rook_home_right(&mut rights, captured_piece.color, capture_square);
        }
    }
    rights
}

fn clear_rook_home_right(rights: &mut CastlingRights, color: Color, square: Square) {
    let row = match color {
        Color::White => 7,
        Color::Black => 0,
    };
    if square == home_square(row, 0) {
        rights.clear(color, CastleSide::QueenSide);
    } else if square == home_square(row, 7) {
        rights.clear(color, CastleSide::KingSide);
    }
}

fn castle_rook_squares(current: Move, side: Color) -> (Square, Square) {
    let row = match side {
        Color::White => 7,
        Color::Black => 0,
    };
    match current.kind() {
        MoveKind::KingCastle => (home_square(row, 7), home_square(row, 5)),
        MoveKind::QueenCastle => (home_square(row, 0), home_square(row, 3)),
        _ => unreachable!("only castling moves have rook squares"),
    }
}

fn home_square(row: u8, file: u8) -> Square {
    Square::from_row_file(row, file).expect("home-board coordinate is valid")
}

#[cfg(test)]
#[path = "make_unmake_tests.rs"]
mod tests;
