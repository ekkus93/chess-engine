use core::{fmt, str::FromStr};

use crate::{
    CastleSide, CastlingRights, Color, FullmoveNumber, HalfmoveClock, Piece, PieceKind, Square,
};

use super::{Position, PositionBuildError, PositionBuilder};

/// A structured strict-FEN parsing error.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum FenError {
    /// FEN must contain exactly six whitespace-separated fields.
    FieldCount { found: usize },
    /// Piece placement must contain exactly eight ranks.
    RankCount { found: usize },
    /// One placement rank did not expand to exactly eight files.
    RankWidth { rank: u8, files: u8 },
    /// A placement character was neither a piece nor a digit from one through eight.
    InvalidPlacementCharacter { rank: u8, file: u8, value: char },
    /// Strict playable FEN does not permit pawns on rank one or rank eight.
    PawnOnPromotionRank { square: Square, color: Color },
    /// Active color must be exactly `w` or `b`.
    InvalidActiveColor { value: String },
    /// Castling field must be `-` or contain only unique `KQkq` tokens.
    InvalidCastlingField { value: String },
    /// A castling token occurred more than once.
    DuplicateCastlingRight { value: char },
    /// En-passant field was not `-` or a valid lowercase square.
    InvalidEnPassantSquare { value: String },
    /// En-passant target rank is inconsistent with the active color.
    InvalidEnPassantRank { side_to_move: Color, square: Square },
    /// Halfmove clock must be an unsigned 16-bit integer.
    InvalidHalfmoveClock { value: String },
    /// Fullmove number must be an unsigned nonzero 16-bit integer.
    InvalidFullmoveNumber { value: String },
    /// Materialized position failed playable-position validation.
    Position(PositionBuildError),
}

impl fmt::Display for FenError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::FieldCount { found } => {
                write!(formatter, "FEN must contain six fields, found {found}")
            }
            Self::RankCount { found } => {
                write!(
                    formatter,
                    "FEN placement must contain eight ranks, found {found}"
                )
            }
            Self::RankWidth { rank, files } => {
                write!(
                    formatter,
                    "FEN rank {rank} expands to {files} files instead of eight"
                )
            }
            Self::InvalidPlacementCharacter { rank, file, value } => write!(
                formatter,
                "invalid FEN placement character {value:?} at rank {rank}, file {file}"
            ),
            Self::PawnOnPromotionRank { square, color } => {
                write!(
                    formatter,
                    "{color} pawn is not allowed on promotion-rank square {square}"
                )
            }
            Self::InvalidActiveColor { value } => {
                write!(formatter, "invalid FEN active-color field {value:?}")
            }
            Self::InvalidCastlingField { value } => {
                write!(formatter, "invalid FEN castling field {value:?}")
            }
            Self::DuplicateCastlingRight { value } => {
                write!(formatter, "duplicate FEN castling right {value}")
            }
            Self::InvalidEnPassantSquare { value } => {
                write!(formatter, "invalid FEN en-passant field {value:?}")
            }
            Self::InvalidEnPassantRank {
                side_to_move,
                square,
            } => write!(
                formatter,
                "en-passant target {square} is inconsistent with {side_to_move} to move"
            ),
            Self::InvalidHalfmoveClock { value } => {
                write!(formatter, "invalid FEN halfmove clock {value:?}")
            }
            Self::InvalidFullmoveNumber { value } => {
                write!(formatter, "invalid FEN fullmove number {value:?}")
            }
            Self::Position(error) => error.fmt(formatter),
        }
    }
}

impl std::error::Error for FenError {}

impl From<PositionBuildError> for FenError {
    fn from(value: PositionBuildError) -> Self {
        Self::Position(value)
    }
}

impl Position {
    /// Parses a strict, playable six-field FEN.
    pub fn from_fen(value: &str) -> Result<Self, FenError> {
        value.parse()
    }

    /// Serializes this position as canonical six-field FEN.
    #[must_use]
    pub fn to_fen(&self) -> String {
        let mut placement = String::new();
        for row in 0..8 {
            if row > 0 {
                placement.push('/');
            }
            let mut empty = 0_u8;
            for file in 0..8 {
                let square =
                    Square::from_row_file(row, file).expect("row and file are in board range");
                match self.piece_at(square) {
                    Some(piece) => {
                        if empty > 0 {
                            placement.push(char::from(b'0' + empty));
                            empty = 0;
                        }
                        placement.push(piece.fen_char());
                    }
                    None => empty += 1,
                }
            }
            if empty > 0 {
                placement.push(char::from(b'0' + empty));
            }
        }

        let active = match self.side_to_move() {
            Color::White => "w",
            Color::Black => "b",
        };
        let castling = canonical_castling(self.castling_rights());
        let en_passant = self
            .en_passant()
            .map_or_else(|| "-".to_owned(), |square| square.to_string());

        format!(
            "{placement} {active} {castling} {en_passant} {} {}",
            self.halfmove_clock(),
            self.fullmove_number()
        )
    }
}

impl FromStr for Position {
    type Err = FenError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        let field_count = value.split_whitespace().count();
        if field_count != 6 {
            return Err(FenError::FieldCount { found: field_count });
        }
        let mut fields = value.split_whitespace();
        let placement = fields.next().expect("field count was checked");
        let active_color = fields.next().expect("field count was checked");
        let castling = fields.next().expect("field count was checked");
        let en_passant = fields.next().expect("field count was checked");
        let halfmove = fields.next().expect("field count was checked");
        let fullmove = fields.next().expect("field count was checked");

        let side_to_move = parse_active_color(active_color)?;
        let builder = parse_placement(placement)?
            .with_side_to_move(side_to_move)
            .with_castling_rights(parse_castling(castling)?)
            .with_en_passant(parse_en_passant(en_passant, side_to_move)?)
            .with_halfmove_clock(parse_halfmove(halfmove)?)
            .with_fullmove_number(parse_fullmove(fullmove)?);
        builder.build_playable().map_err(FenError::from)
    }
}

fn parse_placement(value: &str) -> Result<PositionBuilder, FenError> {
    let rank_count = value.split('/').count();
    if rank_count != 8 {
        return Err(FenError::RankCount { found: rank_count });
    }

    let mut builder = PositionBuilder::empty();
    for (row, rank_text) in value.split('/').enumerate() {
        let row = u8::try_from(row).expect("rank index is below eight");
        let rank_number = 8 - row;
        let mut file = 0_u8;
        for token in rank_text.chars() {
            if ('1'..='8').contains(&token) {
                file = file
                    .checked_add(token.to_digit(10).expect("validated digit") as u8)
                    .ok_or(FenError::RankWidth {
                        rank: rank_number,
                        files: u8::MAX,
                    })?;
                if file > 8 {
                    return Err(FenError::RankWidth {
                        rank: rank_number,
                        files: file,
                    });
                }
                continue;
            }

            let piece = Piece::from_fen_char(token).ok_or(FenError::InvalidPlacementCharacter {
                rank: rank_number,
                file: file.saturating_add(1),
                value: token,
            })?;
            if file >= 8 {
                return Err(FenError::RankWidth {
                    rank: rank_number,
                    files: file.saturating_add(1),
                });
            }
            let square = Square::from_row_file(row, file).expect("row and file are valid");
            if piece.kind == PieceKind::Pawn && (row == 0 || row == 7) {
                return Err(FenError::PawnOnPromotionRank {
                    square,
                    color: piece.color,
                });
            }
            builder.place_piece(square, piece)?;
            file += 1;
        }
        if file != 8 {
            return Err(FenError::RankWidth {
                rank: rank_number,
                files: file,
            });
        }
    }
    Ok(builder)
}

fn parse_active_color(value: &str) -> Result<Color, FenError> {
    match value {
        "w" => Ok(Color::White),
        "b" => Ok(Color::Black),
        _ => Err(FenError::InvalidActiveColor {
            value: value.to_owned(),
        }),
    }
}

fn parse_castling(value: &str) -> Result<CastlingRights, FenError> {
    if value == "-" {
        return Ok(CastlingRights::NONE);
    }
    if value.is_empty() || value.contains('-') {
        return Err(FenError::InvalidCastlingField {
            value: value.to_owned(),
        });
    }

    let mut rights = CastlingRights::NONE;
    for token in value.chars() {
        let (color, side) = match token {
            'K' => (Color::White, CastleSide::KingSide),
            'Q' => (Color::White, CastleSide::QueenSide),
            'k' => (Color::Black, CastleSide::KingSide),
            'q' => (Color::Black, CastleSide::QueenSide),
            _ => {
                return Err(FenError::InvalidCastlingField {
                    value: value.to_owned(),
                });
            }
        };
        if rights.contains(color, side) {
            return Err(FenError::DuplicateCastlingRight { value: token });
        }
        rights = rights.with(color, side);
    }
    Ok(rights)
}

fn parse_en_passant(value: &str, side_to_move: Color) -> Result<Option<Square>, FenError> {
    if value == "-" {
        return Ok(None);
    }
    let square = value
        .parse::<Square>()
        .map_err(|_| FenError::InvalidEnPassantSquare {
            value: value.to_owned(),
        })?;
    let expected_rank = match side_to_move {
        Color::White => 6,
        Color::Black => 3,
    };
    if square.rank() != expected_rank {
        return Err(FenError::InvalidEnPassantRank {
            side_to_move,
            square,
        });
    }
    Ok(Some(square))
}

fn parse_halfmove(value: &str) -> Result<HalfmoveClock, FenError> {
    if value.is_empty() || !value.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(FenError::InvalidHalfmoveClock {
            value: value.to_owned(),
        });
    }
    value
        .parse::<u16>()
        .map(HalfmoveClock::new)
        .map_err(|_| FenError::InvalidHalfmoveClock {
            value: value.to_owned(),
        })
}

fn parse_fullmove(value: &str) -> Result<FullmoveNumber, FenError> {
    if value.is_empty() || !value.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(FenError::InvalidFullmoveNumber {
            value: value.to_owned(),
        });
    }
    let parsed = value
        .parse::<u16>()
        .map_err(|_| FenError::InvalidFullmoveNumber {
            value: value.to_owned(),
        })?;
    FullmoveNumber::new(parsed).ok_or_else(|| FenError::InvalidFullmoveNumber {
        value: value.to_owned(),
    })
}

fn canonical_castling(rights: CastlingRights) -> String {
    let mut value = String::new();
    for (token, color, side) in [
        ('K', Color::White, CastleSide::KingSide),
        ('Q', Color::White, CastleSide::QueenSide),
        ('k', Color::Black, CastleSide::KingSide),
        ('q', Color::Black, CastleSide::QueenSide),
    ] {
        if rights.contains(color, side) {
            value.push(token);
        }
    }
    if value.is_empty() {
        value.push('-');
    }
    value
}

#[cfg(test)]
#[path = "fen_tests.rs"]
mod tests;
