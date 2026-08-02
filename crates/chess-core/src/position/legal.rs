use core::fmt;

use crate::{Color, Move, MoveKind, MoveList, MoveListOverflow, PositionMutationError, Square};

use super::Position;

/// A fail-loud legal-move generation, application, restoration, or perft error.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum LegalMoveError {
    /// Bounded move storage was exhausted.
    MoveListOverflow(MoveListOverflow),
    /// Internal reversible position editing failed.
    Mutation(PositionMutationError),
    /// A caller requested a move that is not one of the exact legal identities.
    IllegalMove { current: Move },
    /// A generated move contradicted its encoded semantic identity.
    InvalidGeneratedMove { current: Move },
    /// An undo token did not match the current post-move position.
    UndoStateMismatch { current: Move },
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
            Self::IllegalMove { current } => {
                write!(formatter, "move {} is not legal", current.to_uci())
            }
            Self::InvalidGeneratedMove { current } => write!(
                formatter,
                "generated move {} contradicts position state",
                current.to_uci()
            ),
            Self::UndoStateMismatch { current } => write!(
                formatter,
                "undo token for {} does not match the current position",
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
            let Some(moving_piece) = self.piece_at(current.source()) else {
                continue;
            };
            if moving_piece.color != moving_side
                || !self.generated_move_matches_state(current, moving_piece)
            {
                continue;
            }
            if matches!(current.kind(), MoveKind::KingCastle | MoveKind::QueenCastle)
                && !self.castling_transit_is_safe(current, moving_side)?
            {
                continue;
            }

            let undo = self.make_generated_legal_move(current)?;
            let safe =
                !self.is_square_attacked(self.king_square(moving_side), moving_side.opposite());
            self.unmake_generated_legal_move(undo)?;
            if safe {
                legal.push(current)?;
            }
        }

        Ok(legal)
    }

    /// Returns whether `candidate` is one of the exact generated legal moves.
    pub fn is_legal_move(&mut self, candidate: Move) -> Result<bool, LegalMoveError> {
        Ok(self
            .legal_moves()?
            .iter()
            .any(|current| current == candidate))
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
            let undo = self.make_generated_legal_move(current)?;
            let child = self.perft(depth - 1);
            self.unmake_generated_legal_move(undo)?;
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
            let undo = self.make_generated_legal_move(current)?;
            let child = self.perft(depth - 1);
            self.unmake_generated_legal_move(undo)?;
            result.push((current, child?));
        }
        Ok(result)
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
}

#[cfg(test)]
#[path = "legal_tests.rs"]
mod tests;
