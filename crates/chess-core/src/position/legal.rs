use core::fmt;

use crate::{
    CastlingRights, Color, FullmoveNumber, HalfmoveClock, Move, MoveKind, MoveList,
    MoveListOverflow, PositionMutationError, Square, MAX_PSEUDO_LEGAL_MOVES,
};

use super::{Position, PositionUndo};

/// A fail-loud legal-move generation, application, restoration, or perft error.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum LegalMoveError {
    /// Bounded move storage was exhausted.
    MoveListOverflow(MoveListOverflow),
    /// Internal reversible position editing failed.
    Mutation(PositionMutationError),
    /// A caller requested a move that is not one of the exact legal identities.
    IllegalMove { current: Move },
    /// A legal-move token was generated for a different source position.
    LegalMoveTokenMismatch { current: Move },
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
            Self::LegalMoveTokenMismatch { current } => write!(
                formatter,
                "legal-move token for {} does not match the current position",
                current.to_uci()
            ),
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

/// Opaque proof that one move was legal in one exact source position.
///
/// Tokens are created only by [`Position::legal_move_tokens`]. They bind the
/// packed move identity to the complete non-board metadata and canonical hash
/// of the source position, allowing search to apply generated legal moves
/// without regenerating the legal move list.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct LegalMoveToken {
    current: Move,
    origin: LegalMoveOrigin,
}

impl LegalMoveToken {
    /// Returns the exact packed move represented by this token.
    #[must_use]
    pub const fn move_made(self) -> Move {
        self.current
    }
}

/// Bounded stack-backed storage for legal-move tokens.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct LegalMoveTokenList {
    tokens: [Option<LegalMoveToken>; MAX_PSEUDO_LEGAL_MOVES],
    len: usize,
}

impl LegalMoveTokenList {
    const fn new() -> Self {
        Self {
            tokens: [None; MAX_PSEUDO_LEGAL_MOVES],
            len: 0,
        }
    }

    /// Returns the number of generated legal-move tokens.
    #[must_use]
    pub const fn len(&self) -> usize {
        self.len
    }

    /// Returns whether no legal-move token was generated.
    #[must_use]
    pub const fn is_empty(&self) -> bool {
        self.len == 0
    }

    /// Returns the token at `index`.
    #[must_use]
    pub fn get(&self, index: usize) -> Option<LegalMoveToken> {
        self.tokens.get(index).copied().flatten()
    }

    /// Iterates in deterministic legal move generation order.
    pub fn iter(&self) -> impl ExactSizeIterator<Item = LegalMoveToken> + '_ {
        self.tokens[..self.len]
            .iter()
            .copied()
            .map(|entry| entry.expect("occupied legal-token prefix contains tokens"))
    }

    fn push(&mut self, token: LegalMoveToken) {
        debug_assert!(self.len < MAX_PSEUDO_LEGAL_MOVES);
        self.tokens[self.len] = Some(token);
        self.len += 1;
    }
}

impl Default for LegalMoveTokenList {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct LegalMoveOrigin {
    zobrist: u64,
    side_to_move: Color,
    castling_rights: CastlingRights,
    en_passant: Option<Square>,
    halfmove_clock: HalfmoveClock,
    fullmove_number: FullmoveNumber,
}

impl LegalMoveOrigin {
    const fn from_position(position: &Position) -> Self {
        Self {
            zobrist: position.zobrist(),
            side_to_move: position.side_to_move(),
            castling_rights: position.castling_rights(),
            en_passant: position.en_passant(),
            halfmove_clock: position.halfmove_clock(),
            fullmove_number: position.fullmove_number(),
        }
    }

    fn matches(self, position: &Position) -> bool {
        self.zobrist == position.zobrist()
            && self.side_to_move == position.side_to_move()
            && self.castling_rights.bits() == position.castling_rights().bits()
            && self.en_passant == position.en_passant()
            && self.halfmove_clock.get() == position.halfmove_clock().get()
            && self.fullmove_number.get() == position.fullmove_number().get()
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

    /// Generates opaque tokens for every legal move in the current position.
    ///
    /// The position is restored exactly before return. Each token records the
    /// source position identity and can later be passed to
    /// [`Position::make_legal_token`] without regenerating the legal move list.
    pub fn legal_move_tokens(&mut self) -> Result<LegalMoveTokenList, LegalMoveError> {
        let origin = LegalMoveOrigin::from_position(self);
        let moves = self.legal_moves()?;
        debug_assert!(origin.matches(self));
        let mut tokens = LegalMoveTokenList::new();
        for current in moves.iter() {
            tokens.push(LegalMoveToken { current, origin });
        }
        Ok(tokens)
    }

    /// Applies one token generated for the exact current position.
    ///
    /// Origin mismatch is rejected before mutation. A valid token uses the
    /// existing generated-legal reversible path and therefore does not
    /// regenerate legal moves.
    pub fn make_legal_token(
        &mut self,
        token: LegalMoveToken,
    ) -> Result<PositionUndo, LegalMoveError> {
        if !token.origin.matches(self) {
            return Err(LegalMoveError::LegalMoveTokenMismatch {
                current: token.current,
            });
        }
        self.make_generated_legal_move(token.current)
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
