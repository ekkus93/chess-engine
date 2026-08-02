use core::{fmt, str::FromStr};

use crate::{Move, PieceKind, Square};

/// A structured UCI coordinate-move syntax error.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum MoveParseError {
    /// UCI coordinate moves contain exactly four or five ASCII characters.
    InvalidLength { found: usize },
    /// UCI coordinate moves are ASCII-only.
    NonAscii,
    /// The source coordinate is invalid.
    InvalidSource { value: String },
    /// The destination coordinate is invalid.
    InvalidDestination { value: String },
    /// Promotion suffix must be one of `n`, `b`, `r`, or `q`.
    InvalidPromotion { value: char },
}

impl fmt::Display for MoveParseError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InvalidLength { found } => write!(
                formatter,
                "UCI move must contain four or five characters, found {found}"
            ),
            Self::NonAscii => formatter.write_str("UCI move must contain only ASCII characters"),
            Self::InvalidSource { value } => {
                write!(formatter, "invalid UCI source square {value:?}")
            }
            Self::InvalidDestination { value } => {
                write!(formatter, "invalid UCI destination square {value:?}")
            }
            Self::InvalidPromotion { value } => {
                write!(formatter, "invalid UCI promotion suffix {value:?}")
            }
        }
    }
}

impl std::error::Error for MoveParseError {}

/// Parsed UCI coordinate syntax that has not yet been resolved for legality.
///
/// This adapter value never synthesizes an unchecked internal [`Move`]. A later
/// legal-move resolver compares it against generated legal moves and requires
/// exactly one match.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct UciMove {
    source: Square,
    destination: Square,
    promotion: Option<PieceKind>,
}

impl UciMove {
    /// Creates a syntax value from validated coordinates and promotion identity.
    ///
    /// Pawn, king, and queenless invalid promotion identities are rejected by
    /// parsing; this constructor is deliberately private until legal resolution
    /// is implemented.
    const fn new(
        source: Square,
        destination: Square,
        promotion: Option<PieceKind>,
    ) -> Self {
        Self {
            source,
            destination,
            promotion,
        }
    }

    /// Returns the source coordinate.
    #[must_use]
    pub const fn source(self) -> Square {
        self.source
    }

    /// Returns the destination coordinate.
    #[must_use]
    pub const fn destination(self) -> Square {
        self.destination
    }

    /// Returns the optional promotion identity.
    #[must_use]
    pub const fn promotion(self) -> Option<PieceKind> {
        self.promotion
    }

    /// Returns whether this syntax value identifies an internal legal move.
    #[must_use]
    pub const fn matches(self, candidate: Move) -> bool {
        self.source == candidate.source()
            && self.destination == candidate.destination()
            && match (self.promotion, candidate.promotion()) {
                (Some(expected), Some(actual)) => expected as u8 == actual as u8,
                (None, None) => true,
                _ => false,
            }
    }
}

impl FromStr for UciMove {
    type Err = MoveParseError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        if !value.is_ascii() {
            return Err(MoveParseError::NonAscii);
        }
        let length = value.len();
        if !(4..=5).contains(&length) {
            return Err(MoveParseError::InvalidLength { found: length });
        }

        let source_text = &value[0..2];
        let destination_text = &value[2..4];
        let source = source_text
            .parse::<Square>()
            .map_err(|_| MoveParseError::InvalidSource {
                value: source_text.to_owned(),
            })?;
        let destination = destination_text
            .parse::<Square>()
            .map_err(|_| MoveParseError::InvalidDestination {
                value: destination_text.to_owned(),
            })?;
        let promotion = if length == 5 {
            let suffix = char::from(value.as_bytes()[4]);
            Some(match suffix {
                'n' => PieceKind::Knight,
                'b' => PieceKind::Bishop,
                'r' => PieceKind::Rook,
                'q' => PieceKind::Queen,
                _ => return Err(MoveParseError::InvalidPromotion { value: suffix }),
            })
        } else {
            None
        };

        Ok(Self::new(source, destination, promotion))
    }
}

impl fmt::Display for UciMove {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "{}{}", self.source, self.destination)?;
        if let Some(promotion) = self.promotion {
            write!(formatter, "{}", promotion.fen_char())?;
        }
        Ok(())
    }
}

impl Move {
    /// Formats this internal move as UCI coordinate notation.
    #[must_use]
    pub fn to_uci(self) -> String {
        self.to_string()
    }
}

impl fmt::Display for Move {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "{}{}", self.source(), self.destination())?;
        if let Some(promotion) = self.promotion() {
            write!(formatter, "{}", promotion.fen_char())?;
        }
        Ok(())
    }
}

#[cfg(test)]
#[path = "uci_move_tests.rs"]
mod tests;
