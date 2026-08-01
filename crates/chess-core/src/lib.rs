#![forbid(unsafe_code)]
//! Portable chess rules and position primitives.
//!
//! This crate is the dependency root of the Rust engine and must remain
//! independent of search, protocols, platform adapters, filesystems, and user
//! interfaces.

mod bitboard;
mod castling;
mod counters;
mod move_encoding;
mod piece;
mod position;
mod square;

pub use bitboard::{Bitboard, BitboardIter};
pub use castling::{CastleSide, CastlingRights};
pub use counters::{FullmoveNumber, HalfmoveClock};
pub use move_encoding::{Move, MoveKind};
pub use piece::{Color, Piece, PieceKind};
pub use position::{Position, PositionBuildError, PositionInvariantError};
pub use square::{ParseSquareError, Square};
