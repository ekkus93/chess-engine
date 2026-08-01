use core::fmt;

use crate::{Color, PieceKind, Square};

/// A fail-loud position construction error.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PositionBuildError {
    /// Two pieces were assigned to one mailbox square.
    OccupiedSquare { square: Square },
    /// A playable position omitted one color's king.
    MissingKing { color: Color },
    /// A playable position contained multiple kings of one color.
    MultipleKings { color: Color, count: u8 },
    /// Internal storage editing failed while materializing the position.
    Mutation(PositionMutationError),
    /// Materialized redundant state failed validation.
    Invariant(PositionInvariantError),
}

impl fmt::Display for PositionBuildError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::OccupiedSquare { square } => write!(formatter, "square {square} is already occupied"),
            Self::MissingKing { color } => write!(formatter, "playable position is missing the {color} king"),
            Self::MultipleKings { color, count } => {
                write!(formatter, "playable position has {count} {color} kings")
            }
            Self::Mutation(error) => error.fmt(formatter),
            Self::Invariant(error) => error.fmt(formatter),
        }
    }
}

impl std::error::Error for PositionBuildError {}

impl From<PositionMutationError> for PositionBuildError {
    fn from(value: PositionMutationError) -> Self {
        Self::Mutation(value)
    }
}

impl From<PositionInvariantError> for PositionBuildError {
    fn from(value: PositionInvariantError) -> Self {
        Self::Invariant(value)
    }
}

/// A detected contradiction between private position representations.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PositionInvariantError {
    /// Mailbox and a color/kind bitboard disagree.
    MailboxBitboardMismatch { color: Color, kind: PieceKind },
    /// A color occupancy does not equal the union of its piece bitboards.
    OccupancyMismatch { color: Color },
    /// White and black occupancies overlap.
    ColorOccupancyOverlap,
    /// All-occupancy does not equal the union of color occupancies.
    AllOccupancyMismatch,
    /// A playable position does not have exactly one king for a color.
    KingCount { color: Color, count: u8 },
    /// A cached king square disagrees with the mailbox.
    CachedKingMismatch {
        color: Color,
        cached: Square,
        actual: Square,
    },
    /// An en-passant target is on the wrong rank for the side to move.
    InvalidEnPassantRank {
        side_to_move: Color,
        square: Square,
    },
    /// An en-passant target square is occupied.
    OccupiedEnPassantSquare { square: Square },
}

impl fmt::Display for PositionInvariantError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::MailboxBitboardMismatch { color, kind } => {
                write!(formatter, "mailbox and {color} {kind} bitboard disagree")
            }
            Self::OccupancyMismatch { color } => {
                write!(formatter, "{color} occupancy disagrees with piece bitboards")
            }
            Self::ColorOccupancyOverlap => formatter.write_str("white and black occupancies overlap"),
            Self::AllOccupancyMismatch => {
                formatter.write_str("all occupancy disagrees with color occupancies")
            }
            Self::KingCount { color, count } => {
                write!(formatter, "expected one {color} king, found {count}")
            }
            Self::CachedKingMismatch {
                color,
                cached,
                actual,
            } => write!(
                formatter,
                "cached {color} king square {cached} disagrees with mailbox square {actual}"
            ),
            Self::InvalidEnPassantRank {
                side_to_move,
                square,
            } => write!(
                formatter,
                "en-passant target {square} is invalid with {side_to_move} to move"
            ),
            Self::OccupiedEnPassantSquare { square } => {
                write!(formatter, "en-passant target {square} is occupied")
            }
        }
    }
}

impl std::error::Error for PositionInvariantError {}

/// An error from the crate-internal position mutation boundary.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PositionMutationError {
    /// A piece already occupies the requested addition square.
    OccupiedSquare { square: Square },
    /// A requested source or removal square is empty.
    EmptySquare { square: Square },
    /// A move destination is occupied.
    DestinationOccupied { square: Square },
    /// A playable king cannot be removed without a replacement.
    CannotRemoveKing { color: Color },
    /// A king of the same color is already present.
    KingAlreadyPresent { color: Color },
    /// Initial king placement disagrees with the prevalidated cache.
    UnexpectedKingSquare { color: Color, square: Square },
}

impl fmt::Display for PositionMutationError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::OccupiedSquare { square } => write!(formatter, "square {square} is already occupied"),
            Self::EmptySquare { square } => write!(formatter, "square {square} is empty"),
            Self::DestinationOccupied { square } => {
                write!(formatter, "destination square {square} is occupied")
            }
            Self::CannotRemoveKing { color } => {
                write!(formatter, "cannot remove the {color} king from a playable position")
            }
            Self::KingAlreadyPresent { color } => write!(formatter, "the {color} king is already present"),
            Self::UnexpectedKingSquare { color, square } => write!(
                formatter,
                "{color} king placement on {square} disagrees with the cached king square"
            ),
        }
    }
}

impl std::error::Error for PositionMutationError {}
