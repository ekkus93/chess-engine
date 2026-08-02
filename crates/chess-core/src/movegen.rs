use core::fmt;

use crate::{
    bishop_attacks, king_attacks, knight_attacks, queen_attacks, rook_attacks, CastleSide, Color,
    Move, MoveKind, Piece, PieceKind, Position, Square,
};

/// Maximum number of pseudo-legal moves retained without heap allocation.
pub const MAX_PSEUDO_LEGAL_MOVES: usize = 256;

const QUIET_PROMOTIONS: [MoveKind; 4] = [
    MoveKind::KnightPromotion,
    MoveKind::BishopPromotion,
    MoveKind::RookPromotion,
    MoveKind::QueenPromotion,
];
const CAPTURE_PROMOTIONS: [MoveKind; 4] = [
    MoveKind::KnightPromotionCapture,
    MoveKind::BishopPromotionCapture,
    MoveKind::RookPromotionCapture,
    MoveKind::QueenPromotionCapture,
];

/// Fail-loud pseudo-legal move-generation error.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct MoveListOverflow {
    capacity: usize,
}

impl MoveListOverflow {
    /// Returns the fixed move-list capacity that was exceeded.
    #[must_use]
    pub const fn capacity(self) -> usize {
        self.capacity
    }
}

impl fmt::Display for MoveListOverflow {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            formatter,
            "pseudo-legal move list exceeded fixed capacity {}",
            self.capacity
        )
    }
}

impl std::error::Error for MoveListOverflow {}

/// Bounded stack-backed pseudo-legal move storage.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct MoveList {
    moves: [Option<Move>; MAX_PSEUDO_LEGAL_MOVES],
    len: usize,
}

impl MoveList {
    /// Creates an empty move list.
    #[must_use]
    pub const fn new() -> Self {
        Self {
            moves: [None; MAX_PSEUDO_LEGAL_MOVES],
            len: 0,
        }
    }

    /// Returns the number of stored moves.
    #[must_use]
    pub const fn len(&self) -> usize {
        self.len
    }

    /// Returns whether the list contains no moves.
    #[must_use]
    pub const fn is_empty(&self) -> bool {
        self.len == 0
    }

    /// Returns the move at `index`.
    #[must_use]
    pub fn get(&self, index: usize) -> Option<Move> {
        self.moves.get(index).copied().flatten()
    }

    /// Iterates in deterministic generation order.
    pub fn iter(&self) -> impl ExactSizeIterator<Item = Move> + '_ {
        self.moves[..self.len]
            .iter()
            .copied()
            .map(|entry| entry.expect("occupied move-list prefix contains moves"))
    }

    fn push(&mut self, current: Move) -> Result<(), MoveListOverflow> {
        let slot = self.moves.get_mut(self.len).ok_or(MoveListOverflow {
            capacity: MAX_PSEUDO_LEGAL_MOVES,
        })?;
        *slot = Some(current);
        self.len += 1;
        Ok(())
    }
}

impl Default for MoveList {
    fn default() -> Self {
        Self::new()
    }
}

impl Position {
    /// Generates every pseudo-legal move for the current side to move.
    ///
    /// This layer enforces piece geometry, ownership, occupancy, promotion
    /// identity, en-passant target geometry, and basic castling rights/path
    /// conditions. It does not reject moves that expose the moving king, king
    /// moves into attack, castling through attack, or invalid en-passant capture
    /// state; those checks belong to Task 7's legal layer.
    pub fn pseudo_legal_moves(&self) -> Result<MoveList, MoveListOverflow> {
        let mut moves = MoveList::new();
        let side = self.side_to_move();

        self.generate_pawn_moves(side, &mut moves)?;
        self.generate_piece_moves(side, PieceKind::Knight, &mut moves)?;
        self.generate_piece_moves(side, PieceKind::Bishop, &mut moves)?;
        self.generate_piece_moves(side, PieceKind::Rook, &mut moves)?;
        self.generate_piece_moves(side, PieceKind::Queen, &mut moves)?;
        self.generate_piece_moves(side, PieceKind::King, &mut moves)?;
        self.generate_castling_candidates(side, &mut moves)?;

        Ok(moves)
    }

    fn generate_pawn_moves(
        &self,
        side: Color,
        moves: &mut MoveList,
    ) -> Result<(), MoveListOverflow> {
        let direction = match side {
            Color::White => -1_i8,
            Color::Black => 1_i8,
        };
        let start_row = match side {
            Color::White => 6,
            Color::Black => 1,
        };
        let promotion_row = match side {
            Color::White => 0,
            Color::Black => 7,
        };

        for source in self.piece_bitboard(side, PieceKind::Pawn) {
            let next_row = source.row() as i8 + direction;
            if let Some(destination) = checked_square(next_row, source.file() as i8) {
                if self.piece_at(destination).is_none() {
                    if destination.row() == promotion_row {
                        push_promotions(moves, source, destination, QUIET_PROMOTIONS)?;
                    } else {
                        moves.push(Move::new(source, destination, MoveKind::Quiet))?;
                        if source.row() == start_row {
                            let double_row = source.row() as i8 + direction * 2;
                            let double_destination =
                                checked_square(double_row, source.file() as i8)
                                    .expect("double-push destination remains on board");
                            if self.piece_at(double_destination).is_none() {
                                moves.push(Move::new(
                                    source,
                                    double_destination,
                                    MoveKind::DoublePawnPush,
                                ))?;
                            }
                        }
                    }
                }
            }

            for destination in crate::pawn_attacks(side, source) {
                if let Some(target) = self.piece_at(destination) {
                    if target.color == side || target.kind == PieceKind::King {
                        continue;
                    }
                    if destination.row() == promotion_row {
                        push_promotions(moves, source, destination, CAPTURE_PROMOTIONS)?;
                    } else {
                        moves.push(Move::new(source, destination, MoveKind::Capture))?;
                    }
                } else if self.en_passant() == Some(destination) {
                    moves.push(Move::new(source, destination, MoveKind::EnPassant))?;
                }
            }
        }
        Ok(())
    }

    fn generate_piece_moves(
        &self,
        side: Color,
        kind: PieceKind,
        moves: &mut MoveList,
    ) -> Result<(), MoveListOverflow> {
        let own_occupancy = self.occupancy(side);
        for source in self.piece_bitboard(side, kind) {
            let attacks = match kind {
                PieceKind::Knight => knight_attacks(source),
                PieceKind::Bishop => bishop_attacks(source, self.all_occupancy()),
                PieceKind::Rook => rook_attacks(source, self.all_occupancy()),
                PieceKind::Queen => queen_attacks(source, self.all_occupancy()),
                PieceKind::King => king_attacks(source),
                PieceKind::Pawn => unreachable!("pawns use dedicated generation"),
            } & !own_occupancy;

            for destination in attacks {
                let move_kind = match self.piece_at(destination) {
                    Some(target) if target.kind == PieceKind::King => continue,
                    Some(_) => MoveKind::Capture,
                    None => MoveKind::Quiet,
                };
                moves.push(Move::new(source, destination, move_kind))?;
            }
        }
        Ok(())
    }

    fn generate_castling_candidates(
        &self,
        side: Color,
        moves: &mut MoveList,
    ) -> Result<(), MoveListOverflow> {
        let home_row = match side {
            Color::White => 7,
            Color::Black => 0,
        };
        let king_source = home_square(home_row, 4);
        if self.piece_at(king_source) != Some(Piece::new(side, PieceKind::King)) {
            return Ok(());
        }

        if self.castling_rights().contains(side, CastleSide::KingSide)
            && self.piece_at(home_square(home_row, 7)) == Some(Piece::new(side, PieceKind::Rook))
            && self.piece_at(home_square(home_row, 5)).is_none()
            && self.piece_at(home_square(home_row, 6)).is_none()
        {
            moves.push(Move::new(
                king_source,
                home_square(home_row, 6),
                MoveKind::KingCastle,
            ))?;
        }

        if self.castling_rights().contains(side, CastleSide::QueenSide)
            && self.piece_at(home_square(home_row, 0)) == Some(Piece::new(side, PieceKind::Rook))
            && self.piece_at(home_square(home_row, 1)).is_none()
            && self.piece_at(home_square(home_row, 2)).is_none()
            && self.piece_at(home_square(home_row, 3)).is_none()
        {
            moves.push(Move::new(
                king_source,
                home_square(home_row, 2),
                MoveKind::QueenCastle,
            ))?;
        }

        Ok(())
    }
}

fn push_promotions(
    moves: &mut MoveList,
    source: Square,
    destination: Square,
    kinds: [MoveKind; 4],
) -> Result<(), MoveListOverflow> {
    for kind in kinds {
        moves.push(Move::new(source, destination, kind))?;
    }
    Ok(())
}

fn home_square(row: u8, file: u8) -> Square {
    Square::from_row_file(row, file).expect("home-board coordinate is valid")
}

fn checked_square(row: i8, file: i8) -> Option<Square> {
    let row = u8::try_from(row).ok()?;
    let file = u8::try_from(file).ok()?;
    Square::from_row_file(row, file)
}

#[cfg(test)]
#[path = "movegen_tests.rs"]
mod tests;
