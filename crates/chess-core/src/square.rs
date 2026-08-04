use core::{fmt, str::FromStr};

/// An error returned when algebraic square text is invalid.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ParseSquareError;

impl fmt::Display for ParseSquareError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("square must contain a file a-h followed by a rank 1-8")
    }
}

impl std::error::Error for ParseSquareError {}

/// A validated square using the canonical `a8 = 0` mapping.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[repr(transparent)]
pub struct Square(u8);

impl Square {
    /// Number of squares on a chessboard.
    pub const COUNT: u8 = 64;

    /// Creates a square from a validated zero-based index.
    #[must_use]
    pub const fn new(index: u8) -> Option<Self> {
        if index < Self::COUNT {
            Some(Self(index))
        } else {
            None
        }
    }

    /// Creates a square from zero-based row and file coordinates.
    #[must_use]
    pub const fn from_row_file(row: u8, file: u8) -> Option<Self> {
        if row < 8 && file < 8 {
            Some(Self(row * 8 + file))
        } else {
            None
        }
    }

    /// Returns the canonical zero-based square index.
    #[must_use]
    pub const fn index(self) -> u8 {
        self.0
    }

    /// Returns the zero-based row, where row zero is rank eight.
    #[must_use]
    pub const fn row(self) -> u8 {
        self.0 / 8
    }

    /// Returns the zero-based file, where file zero is file `a`.
    #[must_use]
    pub const fn file(self) -> u8 {
        self.0 % 8
    }

    /// Returns the human rank number in the range 1 through 8.
    #[must_use]
    pub const fn rank(self) -> u8 {
        8 - self.row()
    }

    /// Returns the algebraic file character.
    #[must_use]
    pub const fn file_char(self) -> char {
        (b'a' + self.file()) as char
    }

    pub(crate) const fn from_index_unchecked(index: u8) -> Self {
        debug_assert!(index < Self::COUNT);
        Self(index)
    }
}

impl fmt::Display for Square {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "{}{}", self.file_char(), self.rank())
    }
}

impl FromStr for Square {
    type Err = ParseSquareError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        let bytes = value.as_bytes();
        if bytes.len() != 2 {
            return Err(ParseSquareError);
        }
        let file = bytes[0];
        let rank = bytes[1];
        if !(b'a'..=b'h').contains(&file) || !(b'1'..=b'8').contains(&rank) {
            return Err(ParseSquareError);
        }
        let file_index = file - b'a';
        let row = b'8' - rank;
        Self::from_row_file(row, file_index).ok_or(ParseSquareError)
    }
}

#[cfg(test)]
mod tests {
    use core::mem::size_of;

    use super::Square;

    #[test]
    fn canonical_mapping_is_retained() {
        assert_eq!(Square::new(0).expect("a8").to_string(), "a8");
        assert_eq!(Square::new(7).expect("h8").to_string(), "h8");
        assert_eq!(Square::new(56).expect("a1").to_string(), "a1");
        assert_eq!(Square::new(63).expect("h1").to_string(), "h1");
        assert_eq!(Square::new(64), None);
        assert_eq!(Square::from_row_file(8, 0), None);
        assert_eq!(Square::from_row_file(0, 8), None);
        assert_eq!(size_of::<Square>(), 1);
    }

    #[test]
    fn every_square_round_trips() {
        for index in 0..Square::COUNT {
            let square = Square::new(index).expect("index is in range");
            let parsed: Square = square.to_string().parse().expect("formatted square parses");
            assert_eq!(parsed, square);
            assert_eq!(square.index(), index);
            assert_eq!(square.row() * 8 + square.file(), index);
            assert!((1..=8).contains(&square.rank()));
        }
    }

    #[test]
    fn invalid_algebraic_text_is_rejected() {
        for value in ["", "a", "a9", "i1", "A1", "a10", "11"] {
            assert!(value.parse::<Square>().is_err(), "{value} must be invalid");
        }
    }
}
