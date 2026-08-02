use core::fmt;

use crate::{
    CastleSide, CastlingRights, Color, FullmoveNumber, HalfmoveClock, Move, MoveKind, MoveList,
    MoveListOverflow, Piece, PieceKind, PositionMutationError, Square,
};

use super::Position;

/// A fail-loud legal-move generation or perft error.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum LegalMoveError {
    /// Bounded move storage was exhausted.
    MoveListOverflow(MoveListOverflow),
    /// Internal reversible position editing failed.
    Mutation(PositionMutationError),
    /// A generated move contradicted its encoded semantic identity.
    InvalidGeneratedMove { current: Move },
    /// The reversible halfmove clock could not be incremented.
    HalfmoveClockOverflow,
    /// The one-based fullmove number could not be incremented.
    FullmoveNumberOverflow,
    /// Recursive node accumulation exceeded `u64`.
    PerftOverflow,
}

impl fmt::Display for LegalMoveError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::MoveListOverflow(error) => error.fmt(formatter),
            Self::Mutation(error) => error.fmt(formatter),
            Self::InvalidGeneratedMove { current } => write!(
                formatter,
                "generated move {} contradicts position state",
                current.to_uci()
            ),
            Self::HalfmoveClockOverflow => formatter.write_str("halfmove clock overflow"),
            Self::FullmoveNumberOverflow => formatter.write_str("fullmove number overflow"),
            Self::PerftOverflow => formatter.write_str("perft node count overflow"),
        }
    }
}

impl std::error::Error for LegalMoveError {}

impl From<MoveListOverflow> for LegalMoveError {
    fn from(value: MoveListOverflow) -> Self {
        Self::MoveListOverflow(value)
    }
}

impl From<PositionMutationError> for LegalMoveError {
    fn from(value: PositionMutationError) -> Self {
        Self::Mutation(value)
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct Undo {
    captured: Option<(Square, Piece)>,
    previous_castling_rights: CastlingRights,
    previous_en_passant: Option<Square>,
    previous_halfmove_clock: HalfmoveClock,
    previous_fullmove_number: FullmoveNumber,
    previous_side_to_move: Color,
    previous_zobrist: u64,
}

impl Position {
    /// Generates every legal move for the current side to move.
    ///
    /// The position is restored exactly before this method returns, including
    /// on candidates rejected for king safety.
    pub fn legal_moves(&mut self) -> Result<MoveList, LegalMoveError> {
        let pseudo_legal = self.pseudo_legal_moves()?;
        let moving_side = self.side_to_move();
        let mut legal = MoveList::new();

        for current in pseudo_legal.iter() {
            if !self.special_candidate_is_valid(current, moving_side) {
                continue;
            }
            if matches!(current.kind(), MoveKind::KingCastle | MoveKind::QueenCastle)
                && !self.castling_transit_is_safe(current, moving_side)?
            {
                continue;
            }

            let undo = self.make_generated_move(current)?;
            let safe = !self.is_square_attacked(
                self.king_square(moving_side),
                moving_side.opposite(),
            );
            self.unmake_generated_move(current, undo)?;
            if safe {
                legal.push(current)?;
            }
        }

        Ok(legal)
    }

    /// Returns whether `candidate` is one of the exact generated legal moves.
    pub fn is_legal_move(&mut self, candidate: Move) -> Result<bool, LegalMoveError> {
        Ok(self.legal_moves()?.iter().any(|current| current == candidate))
    }

    /// Counts legal leaf nodes at `depth` using reversible make/unmake.
    pub fn perft(&mut self, depth: u8) -> Result<u64, LegalMoveError> {
        if depth == 0 {
            return Ok(1);
        }
        let moves = self.legal_moves()?;
        if depth == 1 {
            return Ok(moves.len() as u64);
        }

        let mut nodes = 0_u64;
        for current in moves.iter() {
            let undo = self.make_generated_move(current)?;
            let child = self.perft(depth - 1);
            self.unmake_generated_move(current, undo)?;
            nodes = nodes
                .checked_add(child?)
                .ok_or(LegalMoveError::PerftOverflow)?;
        }
        Ok(nodes)
    }

    /// Returns root moves and their legal descendant counts.
    pub fn divide(&mut self, depth: u8) -> Result<Vec<(Move, u64)>, LegalMoveError> {
        if depth == 0 {
            return Ok(Vec::new());
        }
        let moves = self.legal_moves()?;
        let mut result = Vec::with_capacity(moves.len());
        for current in moves.iter() {
            let undo = self.make_generated_move(current)?;
            let child = self.perft(depth - 1);
            self.unmake_generated_move(current, undo)?;
            result.push((current, child?));
        }
        Ok(result)
    }

    fn special_candidate_is_valid(&self, current: Move, side: Color) -> bool {
        let source = current.source();
        let destination = current.destination();
        let Some(moving_piece) = self.piece_at(source) else {
            return false;
        };
        if moving_piece.color != side {
            return false;
        }

        if current.promotion().is_some() {
            let promotion_row = match side {
                Color::White => 0,
                Color::Black => 7,
            };
            if moving_piece.kind != PieceKind::Pawn || destination.row() != promotion_row {
                return false;
            }
        }

        match current.kind() {
            MoveKind::EnPassant => self.en_passant_capture_square(current, side).is_some(),
            MoveKind::KingCastle | MoveKind::QueenCastle => moving_piece.kind == PieceKind::King,
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

    fn castling_transit_is_safe(
        &mut self,
        current: Move,
        side: Color,
    ) -> Result<bool, LegalMoveError> {
        let enemy = side.opposite();
        if self.is_square_attacked(current.source(), enemy) {
            return Ok(false);
        }
        let transit_file = match current.kind() {
            MoveKind::KingCastle => 5,
            MoveKind::QueenCastle => 3,
            _ => return Ok(true),
        };
        let transit = Square::from_row_file(current.source().row(), transit_file)
            .expect("castling transit coordinate is valid");
        self.editor().move_piece(current.source(), transit)?;
        let attacked = self.is_square_attacked(transit, enemy);
        self.editor().move_piece(transit, current.source())?;
        Ok(!attacked)
    }

    fn make_generated_move(&mut self, current: Move) -> Result<Undo, LegalMoveError> {
        let source = current.source();
        let destination = current.destination();
        let moving_piece = self
            .piece_at(source)
            .ok_or(LegalMoveError::InvalidGeneratedMove { current })?;
        let moving_side = self.side_to_move();
        if moving_piece.color != moving_side
            || !self.special_candidate_is_valid(current, moving_side)
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
                Square::from_row_file(
                    (source.row() + destination.row()) / 2,
                    source.file(),
                )
                .expect("double-push midpoint is valid"),
            )
        } else {
            None
        };
        let next_castling = updated_castling_rights(
            self.castling_rights(),
            moving_piece,
            source,
            captured,
        );
        let undo = Undo {
            captured,
            previous_castling_rights: self.castling_rights(),
            previous_en_passant: self.en_passant(),
            previous_halfmove_clock: self.halfmove_clock(),
            previous_fullmove_number: self.fullmove_number(),
            previous_side_to_move: moving_side,
            previous_zobrist: self.zobrist(),
        };

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
        Ok(undo)
    }

    fn unmake_generated_move(
        &mut self,
        current: Move,
        undo: Undo,
    ) -> Result<(), LegalMoveError> {
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
        Ok(())
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
#[path = "legal_tests.rs"]
mod tests;
