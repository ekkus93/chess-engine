use crate::{CastlingRights, Color, FullmoveNumber, HalfmoveClock, Piece, Square};

use super::{Position, PositionBuildError};

#[derive(Clone, Debug, Eq, PartialEq)]
pub(super) struct PositionBuilder {
    pub(super) mailbox: [Option<Piece>; 64],
    pub(super) side_to_move: Color,
    pub(super) castling_rights: CastlingRights,
    pub(super) en_passant: Option<Square>,
    pub(super) halfmove_clock: HalfmoveClock,
    pub(super) fullmove_number: FullmoveNumber,
}

impl PositionBuilder {
    pub(super) const fn empty() -> Self {
        Self {
            mailbox: [None; 64],
            side_to_move: Color::White,
            castling_rights: CastlingRights::NONE,
            en_passant: None,
            halfmove_clock: HalfmoveClock::new(0),
            fullmove_number: FullmoveNumber::ONE,
        }
    }

    pub(super) fn place_piece(
        &mut self,
        square: Square,
        piece: Piece,
    ) -> Result<(), PositionBuildError> {
        let slot = &mut self.mailbox[square.index() as usize];
        if slot.is_some() {
            return Err(PositionBuildError::OccupiedSquare { square });
        }
        *slot = Some(piece);
        Ok(())
    }

    pub(super) const fn with_side_to_move(mut self, side_to_move: Color) -> Self {
        self.side_to_move = side_to_move;
        self
    }

    pub(super) const fn with_castling_rights(mut self, castling_rights: CastlingRights) -> Self {
        self.castling_rights = castling_rights;
        self
    }

    pub(super) const fn with_en_passant(mut self, en_passant: Option<Square>) -> Self {
        self.en_passant = en_passant;
        self
    }

    pub(super) const fn with_halfmove_clock(mut self, halfmove_clock: HalfmoveClock) -> Self {
        self.halfmove_clock = halfmove_clock;
        self
    }

    pub(super) const fn with_fullmove_number(mut self, fullmove_number: FullmoveNumber) -> Self {
        self.fullmove_number = fullmove_number;
        self
    }

    pub(super) const fn with_zobrist(self, _zobrist: u64) -> Self {
        self
    }

    pub(super) fn build_playable(self) -> Result<Position, PositionBuildError> {
        Position::from_builder(self)
    }
}
