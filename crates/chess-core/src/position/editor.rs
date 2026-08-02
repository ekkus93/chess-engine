use crate::{Piece, PieceKind, Square};

use super::{Position, PositionMutationError};

/// Capability that atomically updates every private position representation.
///
/// Only `Position` can construct an editor, so adapters cannot mutate mailbox
/// or bitboard state directly.
pub struct PositionEditor<'a> {
    pub(super) position: &'a mut Position,
}

impl PositionEditor<'_> {
    /// Adds a piece to an empty square.
    pub fn add_piece(&mut self, square: Square, piece: Piece) -> Result<(), PositionMutationError> {
        if self.position.piece_at(square).is_some() {
            return Err(PositionMutationError::OccupiedSquare { square });
        }
        if piece.kind == PieceKind::King {
            if !self
                .position
                .piece_bitboard(piece.color, PieceKind::King)
                .is_empty()
            {
                return Err(PositionMutationError::KingAlreadyPresent { color: piece.color });
            }
            if self.position.king_squares[piece.color.index()] != square {
                return Err(PositionMutationError::UnexpectedKingSquare {
                    color: piece.color,
                    square,
                });
            }
        }
        self.set_piece_unchecked(square, piece);
        Ok(())
    }

    /// Removes a non-king piece.
    pub fn remove_piece(&mut self, square: Square) -> Result<Piece, PositionMutationError> {
        let piece = self
            .position
            .piece_at(square)
            .ok_or(PositionMutationError::EmptySquare { square })?;
        if piece.kind == PieceKind::King {
            return Err(PositionMutationError::CannotRemoveKing { color: piece.color });
        }
        self.clear_piece_unchecked(square, piece);
        Ok(piece)
    }

    /// Moves a piece to an empty destination in one operation.
    pub fn move_piece(
        &mut self,
        source: Square,
        destination: Square,
    ) -> Result<Piece, PositionMutationError> {
        let piece = self
            .position
            .piece_at(source)
            .ok_or(PositionMutationError::EmptySquare { square: source })?;
        if self.position.piece_at(destination).is_some() {
            return Err(PositionMutationError::DestinationOccupied {
                square: destination,
            });
        }
        self.clear_piece_unchecked(source, piece);
        if piece.kind == PieceKind::King {
            self.position.king_squares[piece.color.index()] = destination;
        }
        self.set_piece_unchecked(destination, piece);
        Ok(piece)
    }

    fn set_piece_unchecked(&mut self, square: Square, piece: Piece) {
        self.position.mailbox[square.index() as usize] = Some(piece);
        self.position.pieces[piece.color.index()][piece.kind.index()].set(square);
        self.position.occupancy[piece.color.index()].set(square);
        self.position.all_occupancy.set(square);
    }

    fn clear_piece_unchecked(&mut self, square: Square, piece: Piece) {
        self.position.mailbox[square.index() as usize] = None;
        self.position.pieces[piece.color.index()][piece.kind.index()].clear(square);
        self.position.occupancy[piece.color.index()].clear(square);
        self.position.all_occupancy.clear(square);
    }
}
