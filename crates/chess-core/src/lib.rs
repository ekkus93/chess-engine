#![forbid(unsafe_code)]
//! Portable chess rules and position primitives.
//!
//! This crate is the dependency root of the Rust engine and must remain
//! independent of search, protocols, platform adapters, filesystems, and user
//! interfaces.

mod attacks;
mod bitboard;
mod castling;
mod counters;
mod move_encoding;
mod movegen;
mod piece;
mod position;
mod square;
mod uci_move;

pub use attacks::{
    between, bishop_attacks, king_attacks, knight_attacks, line, pawn_attacks, queen_attacks, ray,
    rook_attacks,
};
pub use bitboard::{Bitboard, BitboardIter};
pub use castling::{CastleSide, CastlingRights};
pub use counters::{FullmoveNumber, HalfmoveClock};
pub use move_encoding::{Move, MoveKind};
pub use movegen::{MoveList, MoveListOverflow, MAX_PSEUDO_LEGAL_MOVES};
pub use piece::{Color, Piece, PieceKind};
pub use position::{FenError, Position, PositionBuildError, PositionInvariantError};
#[doc(hidden)]
pub use position::{PositionEditor, PositionMutationError};
pub use square::{ParseSquareError, Square};
pub use uci_move::{MoveParseError, UciMove};
