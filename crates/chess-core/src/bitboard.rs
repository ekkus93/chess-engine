use core::{fmt, iter::FusedIterator, ops};

use crate::Square;

/// A compact set of chessboard squares.
#[derive(Clone, Copy, Default, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[repr(transparent)]
pub struct Bitboard(u64);

impl Bitboard {
    /// Empty square set.
    pub const EMPTY: Self = Self(0);
    /// All chessboard squares.
    pub const FULL: Self = Self(u64::MAX);
    /// File `a` mask under the `a8 = 0` mapping.
    pub const FILE_A: Self = Self(0x0101_0101_0101_0101);
    /// File `h` mask under the `a8 = 0` mapping.
    pub const FILE_H: Self = Self(0x8080_8080_8080_8080);
    /// Rank eight mask.
    pub const RANK_8: Self = Self(0x0000_0000_0000_00ff);
    /// Rank one mask.
    pub const RANK_1: Self = Self(0xff00_0000_0000_0000);

    /// Creates a bitboard from raw bits.
    #[must_use]
    pub const fn from_bits(bits: u64) -> Self {
        Self(bits)
    }

    /// Returns the raw bit representation.
    #[must_use]
    pub const fn bits(self) -> u64 {
        self.0
    }

    /// Returns whether no square is set.
    #[must_use]
    pub const fn is_empty(self) -> bool {
        self.0 == 0
    }

    /// Returns the number of set squares.
    #[must_use]
    pub const fn count(self) -> u32 {
        self.0.count_ones()
    }

    /// Returns whether a square is present.
    #[must_use]
    pub const fn contains(self, square: Square) -> bool {
        self.0 & (1_u64 << square.index()) != 0
    }

    /// Adds a square.
    pub fn set(&mut self, square: Square) {
        self.0 |= 1_u64 << square.index();
    }

    /// Removes a square.
    pub fn clear(&mut self, square: Square) {
        self.0 &= !(1_u64 << square.index());
    }

    /// Removes and returns the least-significant set square.
    pub fn pop_lsb(&mut self) -> Option<Square> {
        if self.is_empty() {
            return None;
        }
        let index = u8::try_from(self.0.trailing_zeros()).expect("bit index is below 64");
        self.0 &= self.0 - 1;
        Some(Square::from_index_unchecked(index))
    }

    /// Iterates over set squares from least to most significant.
    #[must_use]
    pub const fn iter(self) -> BitboardIter {
        BitboardIter(self)
    }

    /// Shifts squares one rank toward rank eight.
    #[must_use]
    pub const fn north(self) -> Self {
        Self(self.0 >> 8)
    }

    /// Shifts squares one rank toward rank one.
    #[must_use]
    pub const fn south(self) -> Self {
        Self(self.0 << 8)
    }

    /// Shifts squares one file toward file `h` without wrapping.
    #[must_use]
    pub const fn east(self) -> Self {
        Self((self.0 & !Self::FILE_H.0) << 1)
    }

    /// Shifts squares one file toward file `a` without wrapping.
    #[must_use]
    pub const fn west(self) -> Self {
        Self((self.0 & !Self::FILE_A.0) >> 1)
    }

    /// Shifts squares north-east without wrapping.
    #[must_use]
    pub const fn north_east(self) -> Self {
        Self((self.0 & !Self::FILE_H.0) >> 7)
    }

    /// Shifts squares north-west without wrapping.
    #[must_use]
    pub const fn north_west(self) -> Self {
        Self((self.0 & !Self::FILE_A.0) >> 9)
    }

    /// Shifts squares south-east without wrapping.
    #[must_use]
    pub const fn south_east(self) -> Self {
        Self((self.0 & !Self::FILE_H.0) << 9)
    }

    /// Shifts squares south-west without wrapping.
    #[must_use]
    pub const fn south_west(self) -> Self {
        Self((self.0 & !Self::FILE_A.0) << 7)
    }
}

impl From<Square> for Bitboard {
    fn from(square: Square) -> Self {
        Self(1_u64 << square.index())
    }
}

impl fmt::Debug for Bitboard {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "Bitboard({:#018x})", self.0)
    }
}

impl ops::BitAnd for Bitboard {
    type Output = Self;

    fn bitand(self, rhs: Self) -> Self::Output {
        Self(self.0 & rhs.0)
    }
}

impl ops::BitAndAssign for Bitboard {
    fn bitand_assign(&mut self, rhs: Self) {
        self.0 &= rhs.0;
    }
}

impl ops::BitOr for Bitboard {
    type Output = Self;

    fn bitor(self, rhs: Self) -> Self::Output {
        Self(self.0 | rhs.0)
    }
}

impl ops::BitOrAssign for Bitboard {
    fn bitor_assign(&mut self, rhs: Self) {
        self.0 |= rhs.0;
    }
}

impl ops::BitXor for Bitboard {
    type Output = Self;

    fn bitxor(self, rhs: Self) -> Self::Output {
        Self(self.0 ^ rhs.0)
    }
}

impl ops::BitXorAssign for Bitboard {
    fn bitxor_assign(&mut self, rhs: Self) {
        self.0 ^= rhs.0;
    }
}

impl ops::Not for Bitboard {
    type Output = Self;

    fn not(self) -> Self::Output {
        Self(!self.0)
    }
}

impl IntoIterator for Bitboard {
    type Item = Square;
    type IntoIter = BitboardIter;

    fn into_iter(self) -> Self::IntoIter {
        self.iter()
    }
}

/// Iterator over the set squares in a bitboard.
#[derive(Clone, Debug)]
pub struct BitboardIter(Bitboard);

impl Iterator for BitboardIter {
    type Item = Square;

    fn next(&mut self) -> Option<Self::Item> {
        self.0.pop_lsb()
    }

    fn size_hint(&self) -> (usize, Option<usize>) {
        let count = usize::try_from(self.0.count()).expect("bit count fits usize");
        (count, Some(count))
    }
}

impl ExactSizeIterator for BitboardIter {}
impl FusedIterator for BitboardIter {}

#[cfg(test)]
mod tests {
    use core::mem::size_of;

    use crate::Square;

    use super::Bitboard;

    fn square(value: &str) -> Square {
        value.parse().expect("test square is valid")
    }

    #[test]
    fn set_clear_contains_count_and_pop_are_consistent() {
        let a8 = square("a8");
        let d4 = square("d4");
        let h1 = square("h1");
        let mut board = Bitboard::EMPTY;
        assert!(board.is_empty());

        for current in [a8, d4, h1] {
            board.set(current);
            assert!(board.contains(current));
        }
        assert_eq!(board.count(), 3);
        assert_eq!(board.iter().collect::<Vec<_>>(), vec![a8, d4, h1]);
        assert_eq!(board.pop_lsb(), Some(a8));
        assert_eq!(board.pop_lsb(), Some(d4));
        assert_eq!(board.pop_lsb(), Some(h1));
        assert_eq!(board.pop_lsb(), None);

        board.set(d4);
        board.clear(d4);
        assert!(!board.contains(d4));
        assert_eq!(size_of::<Bitboard>(), 8);
    }

    #[test]
    fn shifts_follow_board_geometry_without_file_wrapping() {
        assert_eq!(
            Bitboard::from(square("d4")).north(),
            Bitboard::from(square("d5"))
        );
        assert_eq!(
            Bitboard::from(square("d4")).south(),
            Bitboard::from(square("d3"))
        );
        assert_eq!(
            Bitboard::from(square("d4")).east(),
            Bitboard::from(square("e4"))
        );
        assert_eq!(
            Bitboard::from(square("d4")).west(),
            Bitboard::from(square("c4"))
        );
        assert_eq!(
            Bitboard::from(square("d4")).north_east(),
            Bitboard::from(square("e5"))
        );
        assert_eq!(
            Bitboard::from(square("d4")).north_west(),
            Bitboard::from(square("c5"))
        );
        assert_eq!(
            Bitboard::from(square("d4")).south_east(),
            Bitboard::from(square("e3"))
        );
        assert_eq!(
            Bitboard::from(square("d4")).south_west(),
            Bitboard::from(square("c3"))
        );

        assert_eq!(Bitboard::from(square("h4")).east(), Bitboard::EMPTY);
        assert_eq!(Bitboard::from(square("a4")).west(), Bitboard::EMPTY);
        assert_eq!(Bitboard::from(square("h8")).north_east(), Bitboard::EMPTY);
        assert_eq!(Bitboard::from(square("a1")).south_west(), Bitboard::EMPTY);
        assert_eq!(Bitboard::RANK_8.north(), Bitboard::EMPTY);
        assert_eq!(Bitboard::RANK_1.south(), Bitboard::EMPTY);
    }

    #[test]
    fn bitwise_operations_preserve_exact_sets() {
        let a = Bitboard::from(square("a1"));
        let b = Bitboard::from(square("b1"));
        assert_eq!((a | b).count(), 2);
        assert_eq!((a | b) & a, a);
        assert_eq!((a | b) ^ a, b);
        assert_eq!((!Bitboard::EMPTY).bits(), Bitboard::FULL.bits());
    }
}
