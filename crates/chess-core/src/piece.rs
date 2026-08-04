use core::fmt;

/// The side to move or the owner of a piece.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[repr(u8)]
pub enum Color {
    /// White moves toward decreasing row indices.
    White = 0,
    /// Black moves toward increasing row indices.
    Black = 1,
}

impl Color {
    /// Returns the opposing color.
    #[must_use]
    pub const fn opposite(self) -> Self {
        match self {
            Self::White => Self::Black,
            Self::Black => Self::White,
        }
    }

    /// Returns the stable table index for this color.
    #[must_use]
    pub const fn index(self) -> usize {
        self as usize
    }

    /// Returns the signed mailbox delta for a one-square pawn push.
    #[must_use]
    pub const fn pawn_push(self) -> i8 {
        match self {
            Self::White => -8,
            Self::Black => 8,
        }
    }

    /// Returns the zero-based row containing this color's home pieces.
    #[must_use]
    pub const fn home_row(self) -> u8 {
        match self {
            Self::White => 7,
            Self::Black => 0,
        }
    }

    /// Returns the zero-based row from which this color's pawns may double-push.
    #[must_use]
    pub const fn pawn_start_row(self) -> u8 {
        match self {
            Self::White => 6,
            Self::Black => 1,
        }
    }

    /// Returns the zero-based row on which this color promotes.
    #[must_use]
    pub const fn promotion_row(self) -> u8 {
        match self {
            Self::White => 0,
            Self::Black => 7,
        }
    }
}

impl fmt::Display for Color {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::White => "white",
            Self::Black => "black",
        })
    }
}

/// A non-empty chess piece kind.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[repr(u8)]
pub enum PieceKind {
    /// Pawn.
    Pawn = 0,
    /// Knight.
    Knight = 1,
    /// Bishop.
    Bishop = 2,
    /// Rook.
    Rook = 3,
    /// Queen.
    Queen = 4,
    /// King.
    King = 5,
}

impl PieceKind {
    /// All piece kinds in stable table order.
    pub const ALL: [Self; 6] = [
        Self::Pawn,
        Self::Knight,
        Self::Bishop,
        Self::Rook,
        Self::Queen,
        Self::King,
    ];

    /// Returns the stable table index for this piece kind.
    #[must_use]
    pub const fn index(self) -> usize {
        self as usize
    }

    /// Returns the lowercase FEN character for this kind.
    #[must_use]
    pub const fn fen_char(self) -> char {
        match self {
            Self::Pawn => 'p',
            Self::Knight => 'n',
            Self::Bishop => 'b',
            Self::Rook => 'r',
            Self::Queen => 'q',
            Self::King => 'k',
        }
    }
}

impl fmt::Display for PieceKind {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::Pawn => "pawn",
            Self::Knight => "knight",
            Self::Bishop => "bishop",
            Self::Rook => "rook",
            Self::Queen => "queen",
            Self::King => "king",
        })
    }
}

/// A compact chess piece value without a location.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct Piece {
    /// Piece owner.
    pub color: Color,
    /// Piece kind.
    pub kind: PieceKind,
}

impl Piece {
    /// Creates a piece value.
    #[must_use]
    pub const fn new(color: Color, kind: PieceKind) -> Self {
        Self { color, kind }
    }

    /// Parses one FEN piece character.
    #[must_use]
    pub fn from_fen_char(value: char) -> Option<Self> {
        let color = if value.is_ascii_uppercase() {
            Color::White
        } else {
            Color::Black
        };
        let kind = match value.to_ascii_lowercase() {
            'p' => PieceKind::Pawn,
            'n' => PieceKind::Knight,
            'b' => PieceKind::Bishop,
            'r' => PieceKind::Rook,
            'q' => PieceKind::Queen,
            'k' => PieceKind::King,
            _ => return None,
        };
        Some(Self::new(color, kind))
    }

    /// Returns this piece's canonical FEN character.
    #[must_use]
    pub fn fen_char(self) -> char {
        let value = self.kind.fen_char();
        match self.color {
            Color::White => value.to_ascii_uppercase(),
            Color::Black => value,
        }
    }
}

impl fmt::Display for Piece {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "{}", self.fen_char())
    }
}

#[cfg(test)]
mod tests {
    use core::mem::size_of;

    use super::{Color, Piece, PieceKind};

    #[test]
    fn color_contract_is_stable() {
        assert_eq!(Color::White.index(), 0);
        assert_eq!(Color::Black.index(), 1);
        assert_eq!(Color::White.opposite(), Color::Black);
        assert_eq!(Color::Black.opposite(), Color::White);
        assert_eq!(Color::White.pawn_push(), -8);
        assert_eq!(Color::Black.pawn_push(), 8);
        assert_eq!(Color::White.home_row(), 7);
        assert_eq!(Color::Black.home_row(), 0);
        assert_eq!(Color::White.pawn_start_row(), 6);
        assert_eq!(Color::Black.pawn_start_row(), 1);
        assert_eq!(Color::White.promotion_row(), 0);
        assert_eq!(Color::Black.promotion_row(), 7);
        assert_eq!(Color::White.to_string(), "white");
        assert_eq!(Color::Black.to_string(), "black");
        assert_eq!(size_of::<Color>(), 1);
    }

    #[test]
    fn piece_kind_contract_is_stable() {
        let expected = [
            (PieceKind::Pawn, 0, 'p', "pawn"),
            (PieceKind::Knight, 1, 'n', "knight"),
            (PieceKind::Bishop, 2, 'b', "bishop"),
            (PieceKind::Rook, 3, 'r', "rook"),
            (PieceKind::Queen, 4, 'q', "queen"),
            (PieceKind::King, 5, 'k', "king"),
        ];

        for (kind, index, fen, name) in expected {
            assert_eq!(kind.index(), index);
            assert_eq!(kind.fen_char(), fen);
            assert_eq!(kind.to_string(), name);
        }
        assert_eq!(PieceKind::ALL.len(), 6);
        assert_eq!(size_of::<PieceKind>(), 1);
    }

    #[test]
    fn piece_fen_conversion_round_trips() {
        for color in [Color::White, Color::Black] {
            for kind in PieceKind::ALL {
                let piece = Piece::new(color, kind);
                let encoded = piece.fen_char();
                assert_eq!(Piece::from_fen_char(encoded), Some(piece));
                assert_eq!(piece.to_string(), encoded.to_string());
            }
        }
        assert_eq!(Piece::from_fen_char('x'), None);
        assert_eq!(size_of::<Piece>(), 2);
    }
}
