use crate::Color;

/// A castling side relative to the king.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum CastleSide {
    /// King-side castling.
    KingSide,
    /// Queen-side castling.
    QueenSide,
}

/// Four independent castling-right bits.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[repr(transparent)]
pub struct CastlingRights(u8);

impl CastlingRights {
    const WHITE_KING: u8 = 1 << 0;
    const WHITE_QUEEN: u8 = 1 << 1;
    const BLACK_KING: u8 = 1 << 2;
    const BLACK_QUEEN: u8 = 1 << 3;
    const ALL_BITS: u8 =
        Self::WHITE_KING | Self::WHITE_QUEEN | Self::BLACK_KING | Self::BLACK_QUEEN;

    /// No castling rights.
    pub const NONE: Self = Self(0);
    /// All four castling rights.
    pub const ALL: Self = Self(Self::ALL_BITS);

    const fn bit(color: Color, side: CastleSide) -> u8 {
        match (color, side) {
            (Color::White, CastleSide::KingSide) => Self::WHITE_KING,
            (Color::White, CastleSide::QueenSide) => Self::WHITE_QUEEN,
            (Color::Black, CastleSide::KingSide) => Self::BLACK_KING,
            (Color::Black, CastleSide::QueenSide) => Self::BLACK_QUEEN,
        }
    }

    /// Returns whether a specific castling right is present.
    #[must_use]
    pub const fn contains(self, color: Color, side: CastleSide) -> bool {
        self.0 & Self::bit(color, side) != 0
    }

    /// Returns a copy with one castling right added.
    #[must_use]
    pub const fn with(self, color: Color, side: CastleSide) -> Self {
        Self(self.0 | Self::bit(color, side))
    }

    /// Removes one castling right.
    pub fn clear(&mut self, color: Color, side: CastleSide) {
        self.0 &= !Self::bit(color, side);
    }

    /// Removes both castling rights for one color.
    pub fn clear_color(&mut self, color: Color) {
        self.clear(color, CastleSide::KingSide);
        self.clear(color, CastleSide::QueenSide);
    }

    /// Returns the underlying four-bit value for diagnostics and hashing.
    #[must_use]
    pub const fn bits(self) -> u8 {
        self.0
    }
}

#[cfg(test)]
mod tests {
    use core::mem::size_of;

    use crate::Color;

    use super::{CastleSide, CastlingRights};

    #[test]
    fn every_right_has_one_independent_bit() {
        let combinations = [
            (Color::White, CastleSide::KingSide),
            (Color::White, CastleSide::QueenSide),
            (Color::Black, CastleSide::KingSide),
            (Color::Black, CastleSide::QueenSide),
        ];
        let mut rights = CastlingRights::NONE;

        for (color, side) in combinations {
            assert!(!rights.contains(color, side));
            rights = rights.with(color, side);
            assert!(rights.contains(color, side));
        }
        assert_eq!(rights, CastlingRights::ALL);
        assert_eq!(rights.bits(), 0x0f);
        assert_eq!(size_of::<CastlingRights>(), 1);
    }

    #[test]
    fn clearing_is_scoped_by_side_and_color() {
        let mut rights = CastlingRights::ALL;
        rights.clear(Color::White, CastleSide::KingSide);
        assert!(!rights.contains(Color::White, CastleSide::KingSide));
        assert!(rights.contains(Color::White, CastleSide::QueenSide));
        assert!(rights.contains(Color::Black, CastleSide::KingSide));

        rights.clear_color(Color::Black);
        assert!(!rights.contains(Color::Black, CastleSide::KingSide));
        assert!(!rights.contains(Color::Black, CastleSide::QueenSide));
        assert!(rights.contains(Color::White, CastleSide::QueenSide));
    }
}
