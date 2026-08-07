mod builder;
mod editor;
mod error;
mod fen;
mod legal;
mod make_unmake;
mod search_null;
#[cfg(test)]
mod tests;
mod zobrist;

use builder::PositionBuilder;
use editor::PositionEditor;
pub use error::{PositionBuildError, PositionInvariantError, PositionMutationError};
pub use fen::FenError;
pub use legal::{LegalMoveError, LegalMoveToken, LegalMoveTokenList};
pub use make_unmake::PositionUndo;
pub use search_null::{SearchNullError, SearchNullUndo};

use crate::{
    Bitboard, CastlingRights, Color, FullmoveNumber, HalfmoveClock, Piece, PieceKind, Square,
};

/// A validated, playable chess position.
///
/// The mailbox, bitboards, occupancies, and cached king squares are redundant
/// by design and remain private. Construction and internal editing validate or
/// update every representation together.
///
/// `Clone` exists for application snapshots and restoration tests. Production
/// recursive search must use make/unmake rather than clone-per-node traversal.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Position {
    mailbox: [Option<Piece>; 64],
    pieces: [[Bitboard; 6]; 2],
    occupancy: [Bitboard; 2],
    all_occupancy: Bitboard,
    king_squares: [Square; 2],
    side_to_move: Color,
    castling_rights: CastlingRights,
    en_passant: Option<Square>,
    halfmove_clock: HalfmoveClock,
    fullmove_number: FullmoveNumber,
    zobrist: u64,
}

impl Position {
    /// Creates the standard chess starting position.
    #[must_use]
    pub fn starting() -> Self {
        Self::try_starting().expect("the hard-coded starting position must satisfy invariants")
    }

    fn try_starting() -> Result<Self, PositionBuildError> {
        let mut builder = PositionBuilder::empty()
            .with_side_to_move(Color::White)
            .with_castling_rights(CastlingRights::ALL)
            .with_en_passant(None)
            .with_halfmove_clock(HalfmoveClock::default())
            .with_fullmove_number(FullmoveNumber::ONE);
        let back_rank = [
            PieceKind::Rook,
            PieceKind::Knight,
            PieceKind::Bishop,
            PieceKind::Queen,
            PieceKind::King,
            PieceKind::Bishop,
            PieceKind::Knight,
            PieceKind::Rook,
        ];

        for (file, kind) in back_rank.into_iter().enumerate() {
            let file = u8::try_from(file).expect("back-rank file is below eight");
            builder.place_piece(
                Square::from_row_file(0, file).expect("black home square is valid"),
                Piece::new(Color::Black, kind),
            )?;
            builder.place_piece(
                Square::from_row_file(7, file).expect("white home square is valid"),
                Piece::new(Color::White, kind),
            )?;
            builder.place_piece(
                Square::from_row_file(1, file).expect("black pawn square is valid"),
                Piece::new(Color::Black, PieceKind::Pawn),
            )?;
            builder.place_piece(
                Square::from_row_file(6, file).expect("white pawn square is valid"),
                Piece::new(Color::White, PieceKind::Pawn),
            )?;
        }

        builder.build_playable()
    }

    /// Returns the piece occupying `square`.
    #[must_use]
    pub const fn piece_at(&self, square: Square) -> Option<Piece> {
        self.mailbox[square.index() as usize]
    }

    /// Returns the piece bitboard for one color and kind.
    #[must_use]
    pub const fn piece_bitboard(&self, color: Color, kind: PieceKind) -> Bitboard {
        self.pieces[color.index()][kind.index()]
    }

    /// Returns all occupied squares for one color.
    #[must_use]
    pub const fn occupancy(&self, color: Color) -> Bitboard {
        self.occupancy[color.index()]
    }

    /// Returns all occupied squares.
    #[must_use]
    pub const fn all_occupancy(&self) -> Bitboard {
        self.all_occupancy
    }

    /// Returns the cached king square for `color`.
    #[must_use]
    pub const fn king_square(&self, color: Color) -> Square {
        self.king_squares[color.index()]
    }

    /// Returns the side to move.
    #[must_use]
    pub const fn side_to_move(&self) -> Color {
        self.side_to_move
    }

    /// Returns the current castling-right bits.
    #[must_use]
    pub const fn castling_rights(&self) -> CastlingRights {
        self.castling_rights
    }

    /// Returns the current FEN en-passant target, when present.
    #[must_use]
    pub const fn en_passant(&self) -> Option<Square> {
        self.en_passant
    }

    /// Returns the reversible halfmove clock.
    #[must_use]
    pub const fn halfmove_clock(&self) -> HalfmoveClock {
        self.halfmove_clock
    }

    /// Returns the one-based fullmove number.
    #[must_use]
    pub const fn fullmove_number(&self) -> FullmoveNumber {
        self.fullmove_number
    }

    /// Returns the canonical repetition Zobrist key for this position.
    ///
    /// The key includes pieces, side to move, castling rights, and only a
    /// legally capturable en-passant file. Move counters are excluded.
    #[must_use]
    pub const fn zobrist(&self) -> u64 {
        self.zobrist
    }

    /// Validates every currently enforceable redundant-state invariant.
    pub fn validate_invariants(&self) -> Result<(), PositionInvariantError> {
        let mut expected_pieces = [[Bitboard::EMPTY; 6]; 2];
        let mut expected_occupancy = [Bitboard::EMPTY; 2];
        let mut expected_kings = [None; 2];
        let mut king_counts = [0_u8; 2];

        for index in 0..Square::COUNT {
            let square = Square::new(index).expect("iteration index is a valid square");
            let Some(piece) = self.mailbox[index as usize] else {
                continue;
            };
            expected_pieces[piece.color.index()][piece.kind.index()].set(square);
            expected_occupancy[piece.color.index()].set(square);
            if piece.kind == PieceKind::King {
                king_counts[piece.color.index()] += 1;
                expected_kings[piece.color.index()] = Some(square);
            }
        }

        for color in [Color::White, Color::Black] {
            for kind in PieceKind::ALL {
                if self.pieces[color.index()][kind.index()]
                    != expected_pieces[color.index()][kind.index()]
                {
                    return Err(PositionInvariantError::MailboxBitboardMismatch { color, kind });
                }
            }
            if self.occupancy[color.index()] != expected_occupancy[color.index()] {
                return Err(PositionInvariantError::OccupancyMismatch { color });
            }
            if king_counts[color.index()] != 1 {
                return Err(PositionInvariantError::KingCount {
                    color,
                    count: king_counts[color.index()],
                });
            }
            let actual = expected_kings[color.index()]
                .expect("a king count of one always has a recorded square");
            let cached = self.king_squares[color.index()];
            if cached != actual {
                return Err(PositionInvariantError::CachedKingMismatch {
                    color,
                    cached,
                    actual,
                });
            }
        }

        if !(self.occupancy(Color::White) & self.occupancy(Color::Black)).is_empty() {
            return Err(PositionInvariantError::ColorOccupancyOverlap);
        }
        let expected_all = self.occupancy(Color::White) | self.occupancy(Color::Black);
        if self.all_occupancy != expected_all {
            return Err(PositionInvariantError::AllOccupancyMismatch);
        }

        if let Some(square) = self.en_passant {
            let expected_rank = match self.side_to_move {
                Color::White => 6,
                Color::Black => 3,
            };
            if square.rank() != expected_rank {
                return Err(PositionInvariantError::InvalidEnPassantRank {
                    side_to_move: self.side_to_move,
                    square,
                });
            }
            if self.piece_at(square).is_some() {
                return Err(PositionInvariantError::OccupiedEnPassantSquare { square });
            }
        }

        Ok(())
    }

    fn editor(&mut self) -> PositionEditor<'_> {
        PositionEditor { position: self }
    }

    fn from_builder(builder: PositionBuilder) -> Result<Self, PositionBuildError> {
        let mut king_squares = [None; 2];
        let mut king_counts = [0_u8; 2];
        for (index, piece) in builder.mailbox.iter().copied().enumerate() {
            let Some(piece) = piece else {
                continue;
            };
            if piece.kind == PieceKind::King {
                king_counts[piece.color.index()] += 1;
                king_squares[piece.color.index()] = Some(
                    Square::new(u8::try_from(index).expect("mailbox index is below 64"))
                        .expect("mailbox index is a valid square"),
                );
            }
        }

        let resolved_kings =
            [Color::White, Color::Black].map(|color| match king_counts[color.index()] {
                0 => Err(PositionBuildError::MissingKing { color }),
                1 => {
                    Ok(king_squares[color.index()]
                        .expect("one counted king has one recorded square"))
                }
                count => Err(PositionBuildError::MultipleKings { color, count }),
            });
        let [white_king, black_king] = resolved_kings;

        let mut position = Self {
            mailbox: [None; 64],
            pieces: [[Bitboard::EMPTY; 6]; 2],
            occupancy: [Bitboard::EMPTY; 2],
            all_occupancy: Bitboard::EMPTY,
            king_squares: [white_king?, black_king?],
            side_to_move: builder.side_to_move,
            castling_rights: builder.castling_rights,
            en_passant: builder.en_passant,
            halfmove_clock: builder.halfmove_clock,
            fullmove_number: builder.fullmove_number,
            zobrist: 0,
        };

        for (index, piece) in builder.mailbox.into_iter().enumerate() {
            if let Some(piece) = piece {
                let square = Square::new(u8::try_from(index).expect("mailbox index is below 64"))
                    .expect("mailbox index is a valid square");
                position.editor().add_piece(square, piece)?;
            }
        }
        position.zobrist = position.recomputed_zobrist();
        position.validate_invariants()?;
        Ok(position)
    }
}

impl Default for Position {
    fn default() -> Self {
        Self::starting()
    }
}
