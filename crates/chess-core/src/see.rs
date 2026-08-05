use core::fmt;

use crate::{
    bishop_attacks, king_attacks, knight_attacks, pawn_attacks, rook_attacks, Bitboard, Color,
    Move, MoveKind, Piece, PieceKind, Position, Square,
};

/// Version of the stable static-exchange material-value contract.
pub const STATIC_EXCHANGE_SCHEMA_VERSION: u16 = 1;
/// Stable semantic identifier for the initial standalone SEE contract.
pub const STATIC_EXCHANGE_POLICY_ID: u64 = 0x5345_4556_414c_3031;
/// Maximum number of alternating captures admitted by the fixed local recursion.
pub const MAX_STATIC_EXCHANGE_PLIES: u8 = 64;

const STATIC_EXCHANGE_PIECE_VALUES: [i32; 6] = [100, 320, 330, 500, 900, 20_000];
const PROMOTION_ORDER: [PieceKind; 4] = [
    PieceKind::Knight,
    PieceKind::Bishop,
    PieceKind::Rook,
    PieceKind::Queen,
];
const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;

/// Material classification returned by static exchange evaluation.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[repr(i8)]
pub enum StaticExchangeClass {
    /// The initiating exchange loses material under the SEE policy.
    Losing = -1,
    /// The initiating exchange is materially equal under the SEE policy.
    Equal = 0,
    /// The initiating exchange wins material under the SEE policy.
    Winning = 1,
}

/// A bounded material result from the initiating side's perspective.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[repr(transparent)]
pub struct StaticExchangeValue(i32);

impl StaticExchangeValue {
    /// Creates a static-exchange value from centipawns.
    #[must_use]
    pub const fn from_centipawns(centipawns: i32) -> Self {
        Self(centipawns)
    }

    /// Returns the signed material result in stable SEE centipawns.
    #[must_use]
    pub const fn centipawns(self) -> i32 {
        self.0
    }

    /// Classifies the material result without any tolerance band.
    #[must_use]
    pub const fn class(self) -> StaticExchangeClass {
        if self.0 < 0 {
            StaticExchangeClass::Losing
        } else if self.0 > 0 {
            StaticExchangeClass::Winning
        } else {
            StaticExchangeClass::Equal
        }
    }
}

/// Position-state contradiction detected before or during SEE setup.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum StaticExchangeMoveStateError {
    /// The encoded source square is empty.
    MissingSourcePiece { source: Square },
    /// The source piece does not belong to the position's side to move.
    WrongSideToMove {
        source: Square,
        piece_color: Color,
        side_to_move: Color,
    },
    /// Destination occupancy or en-passant state contradicts the move kind.
    InvalidTargetState { destination: Square },
    /// Piece geometry or promotion state contradicts the packed move.
    InvalidGeometry { current: Move },
    /// The supplied move leaves the moving side's king attacked.
    IllegalKingExposure { current: Move },
}

/// A fail-loud static exchange evaluation error.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum StaticExchangeError {
    /// The move is neither a capture nor a promotion exchange event.
    NonExchangeMove { current: Move },
    /// The packed move contradicts the supplied position.
    MoveStateContradiction(StaticExchangeMoveStateError),
    /// Fixed-capacity alternating-capture storage was exhausted.
    ExchangeCapacityExceeded,
    /// Signed material arithmetic exceeded the documented domain.
    ArithmeticOverflow,
}

impl fmt::Display for StaticExchangeMoveStateError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::MissingSourcePiece { source } => {
                write!(formatter, "static exchange source {source} is empty")
            }
            Self::WrongSideToMove {
                source,
                piece_color,
                side_to_move,
            } => write!(
                formatter,
                "static exchange source {source} contains a {piece_color} piece while {side_to_move} is to move"
            ),
            Self::InvalidTargetState { destination } => write!(
                formatter,
                "static exchange target state at {destination} contradicts the move"
            ),
            Self::InvalidGeometry { current } => write!(
                formatter,
                "static exchange move {} contradicts piece geometry or promotion state",
                current.to_uci()
            ),
            Self::IllegalKingExposure { current } => write!(
                formatter,
                "static exchange move {} leaves its king attacked",
                current.to_uci()
            ),
        }
    }
}

impl fmt::Display for StaticExchangeError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NonExchangeMove { current } => write!(
                formatter,
                "move {} is not a capture or promotion exchange event",
                current.to_uci()
            ),
            Self::MoveStateContradiction(error) => error.fmt(formatter),
            Self::ExchangeCapacityExceeded => {
                formatter.write_str("static exchange capture capacity exceeded")
            }
            Self::ArithmeticOverflow => formatter.write_str("static exchange arithmetic overflow"),
        }
    }
}

impl std::error::Error for StaticExchangeMoveStateError {}
impl std::error::Error for StaticExchangeError {}

impl From<StaticExchangeMoveStateError> for StaticExchangeError {
    fn from(value: StaticExchangeMoveStateError) -> Self {
        Self::MoveStateContradiction(value)
    }
}

/// Returns the stable untuned material value used exclusively by SEE.
#[must_use]
pub const fn static_exchange_piece_value(kind: PieceKind) -> i32 {
    STATIC_EXCHANGE_PIECE_VALUES[kind.index()]
}

/// Returns a deterministic checksum for the complete SEE semantic contract.
#[must_use]
pub fn static_exchange_semantic_checksum() -> u64 {
    let mut hash = FNV_OFFSET;
    hash = hash_bytes(hash, &STATIC_EXCHANGE_SCHEMA_VERSION.to_le_bytes());
    hash = hash_bytes(hash, &STATIC_EXCHANGE_POLICY_ID.to_le_bytes());
    hash = hash_bytes(hash, &[MAX_STATIC_EXCHANGE_PLIES]);
    for value in STATIC_EXCHANGE_PIECE_VALUES {
        hash = hash_bytes(hash, &value.to_le_bytes());
    }
    for promotion in PROMOTION_ORDER {
        hash = hash_bytes(hash, &[promotion as u8]);
    }
    hash = hash_bytes(
        hash,
        b"mandatory-initial;optional-recapture;lva-kind-source;legal-king;local-board",
    );
    hash
}

/// Evaluates one capture or promotion exchange event without mutating `position`.
///
/// The initiating move is mandatory. Later recaptures alternate by side and may
/// be declined whenever continuing would lose material. Each side uses the
/// least valuable legal attacker, with stable source-square tie breaking.
/// Promotion continuations from the selected pawn are evaluated independently.
///
/// This is a material-ordering primitive. It is not a replacement for legal
/// search and does not read tuned evaluation weights.
pub fn static_exchange_evaluation(
    position: &Position,
    current: Move,
) -> Result<StaticExchangeValue, StaticExchangeError> {
    let validated = validate_initial_exchange(position, current)?;
    let mut board = SeeBoard::from_position(position);
    board.apply_exchange(
        validated.source,
        validated.destination,
        validated.capture_square,
        validated.resulting_kind,
        validated.moving_side,
    );
    if board.king_is_attacked(validated.moving_side) {
        return Err(StaticExchangeMoveStateError::IllegalKingExposure { current }.into());
    }

    let response = exchange_gain(
        &board,
        validated.destination,
        validated.moving_side.opposite(),
        validated.resulting_kind,
        0,
    )?;
    let result = validated
        .immediate_gain
        .checked_sub(response)
        .ok_or(StaticExchangeError::ArithmeticOverflow)?;
    Ok(StaticExchangeValue::from_centipawns(result))
}

#[derive(Clone, Copy)]
struct ValidatedInitialExchange {
    source: Square,
    destination: Square,
    capture_square: Option<Square>,
    moving_side: Color,
    resulting_kind: PieceKind,
    immediate_gain: i32,
}

fn validate_initial_exchange(
    position: &Position,
    current: Move,
) -> Result<ValidatedInitialExchange, StaticExchangeError> {
    if !current.kind().is_capture() && current.promotion().is_none() {
        return Err(StaticExchangeError::NonExchangeMove { current });
    }

    let source = current.source();
    let destination = current.destination();
    let moving_piece = position
        .piece_at(source)
        .ok_or(StaticExchangeMoveStateError::MissingSourcePiece { source })?;
    let moving_side = position.side_to_move();
    if moving_piece.color != moving_side {
        return Err(StaticExchangeMoveStateError::WrongSideToMove {
            source,
            piece_color: moving_piece.color,
            side_to_move: moving_side,
        }
        .into());
    }

    let (capture_square, captured_kind) = match current.kind() {
        MoveKind::Capture
        | MoveKind::KnightPromotionCapture
        | MoveKind::BishopPromotionCapture
        | MoveKind::RookPromotionCapture
        | MoveKind::QueenPromotionCapture => {
            let captured = position
                .piece_at(destination)
                .filter(|piece| {
                    piece.color == moving_side.opposite() && piece.kind != PieceKind::King
                })
                .ok_or(StaticExchangeMoveStateError::InvalidTargetState { destination })?;
            (Some(destination), Some(captured.kind))
        }
        MoveKind::EnPassant => {
            let captured_square =
                validated_en_passant_capture_square(position, current, moving_piece)?;
            (Some(captured_square), Some(PieceKind::Pawn))
        }
        MoveKind::KnightPromotion
        | MoveKind::BishopPromotion
        | MoveKind::RookPromotion
        | MoveKind::QueenPromotion => {
            if position.piece_at(destination).is_some() {
                return Err(
                    StaticExchangeMoveStateError::InvalidTargetState { destination }.into(),
                );
            }
            (None, None)
        }
        MoveKind::Quiet
        | MoveKind::DoublePawnPush
        | MoveKind::KingCastle
        | MoveKind::QueenCastle => return Err(StaticExchangeError::NonExchangeMove { current }),
    };

    if !piece_attacks_target(
        moving_piece,
        source,
        destination,
        position.all_occupancy(),
        current.kind(),
    ) {
        return Err(StaticExchangeMoveStateError::InvalidGeometry { current }.into());
    }

    let resulting_kind = validate_promotion(current, moving_piece)?;
    let capture_gain = captured_kind.map_or(0, static_exchange_piece_value);
    let promotion_gain = promotion_delta(moving_piece.kind, resulting_kind)?;
    let immediate_gain = capture_gain
        .checked_add(promotion_gain)
        .ok_or(StaticExchangeError::ArithmeticOverflow)?;

    Ok(ValidatedInitialExchange {
        source,
        destination,
        capture_square,
        moving_side,
        resulting_kind,
        immediate_gain,
    })
}

fn validate_promotion(
    current: Move,
    moving_piece: Piece,
) -> Result<PieceKind, StaticExchangeError> {
    let destination = current.destination();
    match current.promotion() {
        Some(promoted) => {
            if moving_piece.kind != PieceKind::Pawn
                || destination.row() != moving_piece.color.promotion_row()
            {
                return Err(StaticExchangeMoveStateError::InvalidGeometry { current }.into());
            }
            Ok(promoted)
        }
        None => {
            if moving_piece.kind == PieceKind::Pawn
                && destination.row() == moving_piece.color.promotion_row()
            {
                return Err(StaticExchangeMoveStateError::InvalidGeometry { current }.into());
            }
            Ok(moving_piece.kind)
        }
    }
}

fn validated_en_passant_capture_square(
    position: &Position,
    current: Move,
    moving_piece: Piece,
) -> Result<Square, StaticExchangeError> {
    let destination = current.destination();
    if moving_piece.kind != PieceKind::Pawn
        || position.en_passant() != Some(destination)
        || position.piece_at(destination).is_some()
    {
        return Err(StaticExchangeMoveStateError::InvalidTargetState { destination }.into());
    }
    let capture_row = match moving_piece.color {
        Color::White => destination.row().checked_add(1),
        Color::Black => destination.row().checked_sub(1),
    }
    .ok_or(StaticExchangeMoveStateError::InvalidTargetState { destination })?;
    let captured = Square::from_row_file(capture_row, destination.file())
        .ok_or(StaticExchangeMoveStateError::InvalidTargetState { destination })?;
    if position.piece_at(captured)
        != Some(Piece::new(moving_piece.color.opposite(), PieceKind::Pawn))
    {
        return Err(StaticExchangeMoveStateError::InvalidTargetState { destination }.into());
    }
    Ok(captured)
}

fn piece_attacks_target(
    piece: Piece,
    source: Square,
    destination: Square,
    occupancy: Bitboard,
    kind: MoveKind,
) -> bool {
    if matches!(
        kind,
        MoveKind::KnightPromotion
            | MoveKind::BishopPromotion
            | MoveKind::RookPromotion
            | MoveKind::QueenPromotion
    ) {
        let expected_row = match piece.color {
            Color::White => source.row().checked_sub(1),
            Color::Black => source.row().checked_add(1),
        };
        return piece.kind == PieceKind::Pawn
            && expected_row == Some(destination.row())
            && source.file() == destination.file();
    }
    match piece.kind {
        PieceKind::Pawn => pawn_attacks(piece.color, source).contains(destination),
        PieceKind::Knight => knight_attacks(source).contains(destination),
        PieceKind::Bishop => bishop_attacks(source, occupancy).contains(destination),
        PieceKind::Rook => rook_attacks(source, occupancy).contains(destination),
        PieceKind::Queen => (bishop_attacks(source, occupancy) | rook_attacks(source, occupancy))
            .contains(destination),
        PieceKind::King => king_attacks(source).contains(destination),
    }
}

fn promotion_delta(
    original_kind: PieceKind,
    resulting_kind: PieceKind,
) -> Result<i32, StaticExchangeError> {
    static_exchange_piece_value(resulting_kind)
        .checked_sub(static_exchange_piece_value(original_kind))
        .ok_or(StaticExchangeError::ArithmeticOverflow)
}

fn exchange_gain(
    board: &SeeBoard,
    target: Square,
    side: Color,
    target_kind: PieceKind,
    ply: u8,
) -> Result<i32, StaticExchangeError> {
    if target_kind == PieceKind::King {
        return Ok(0);
    }
    if ply >= MAX_STATIC_EXCHANGE_PLIES {
        return Err(StaticExchangeError::ExchangeCapacityExceeded);
    }

    let Some(source) = board.least_valuable_legal_attacker(target, side) else {
        return Ok(0);
    };
    let attacker = board
        .piece_at(source)
        .expect("selected attacker square contains a piece");
    let mut best = None;

    if attacker.kind == PieceKind::Pawn && target.row() == side.promotion_row() {
        for promoted in PROMOTION_ORDER {
            let current = recapture_gain(board, source, target, side, target_kind, promoted, ply)?;
            best = Some(best.map_or(current, |previous: i32| previous.max(current)));
        }
    } else {
        best = Some(recapture_gain(
            board,
            source,
            target,
            side,
            target_kind,
            attacker.kind,
            ply,
        )?);
    }

    Ok(best.unwrap_or_default().max(0))
}

fn recapture_gain(
    board: &SeeBoard,
    source: Square,
    target: Square,
    side: Color,
    target_kind: PieceKind,
    resulting_kind: PieceKind,
    ply: u8,
) -> Result<i32, StaticExchangeError> {
    let attacker = board
        .piece_at(source)
        .expect("selected attacker square contains a piece");
    let mut next = *board;
    next.apply_exchange(source, target, Some(target), resulting_kind, side);
    debug_assert!(!next.king_is_attacked(side));

    let promotion_gain = promotion_delta(attacker.kind, resulting_kind)?;
    let immediate = static_exchange_piece_value(target_kind)
        .checked_add(promotion_gain)
        .ok_or(StaticExchangeError::ArithmeticOverflow)?;
    let response = exchange_gain(&next, target, side.opposite(), resulting_kind, ply + 1)?;
    immediate
        .checked_sub(response)
        .ok_or(StaticExchangeError::ArithmeticOverflow)
}

#[derive(Clone, Copy)]
struct SeeBoard {
    pieces: [[Bitboard; 6]; 2],
    occupancy: [Bitboard; 2],
    all_occupancy: Bitboard,
    king_squares: [Square; 2],
}

impl SeeBoard {
    fn from_position(position: &Position) -> Self {
        let mut pieces = [[Bitboard::EMPTY; 6]; 2];
        for color in [Color::White, Color::Black] {
            for kind in PieceKind::ALL {
                pieces[color.index()][kind.index()] = position.piece_bitboard(color, kind);
            }
        }
        Self {
            pieces,
            occupancy: [
                position.occupancy(Color::White),
                position.occupancy(Color::Black),
            ],
            all_occupancy: position.all_occupancy(),
            king_squares: [
                position.king_square(Color::White),
                position.king_square(Color::Black),
            ],
        }
    }

    fn piece_at(&self, square: Square) -> Option<Piece> {
        for color in [Color::White, Color::Black] {
            if !self.occupancy[color.index()].contains(square) {
                continue;
            }
            for kind in PieceKind::ALL {
                if self.pieces[color.index()][kind.index()].contains(square) {
                    return Some(Piece::new(color, kind));
                }
            }
        }
        None
    }

    fn remove_piece(&mut self, square: Square, piece: Piece) {
        self.pieces[piece.color.index()][piece.kind.index()].clear(square);
        self.occupancy[piece.color.index()].clear(square);
        self.all_occupancy.clear(square);
    }

    fn add_piece(&mut self, square: Square, piece: Piece) {
        self.pieces[piece.color.index()][piece.kind.index()].set(square);
        self.occupancy[piece.color.index()].set(square);
        self.all_occupancy.set(square);
        if piece.kind == PieceKind::King {
            self.king_squares[piece.color.index()] = square;
        }
    }

    fn apply_exchange(
        &mut self,
        source: Square,
        target: Square,
        capture_square: Option<Square>,
        resulting_kind: PieceKind,
        side: Color,
    ) {
        let moving = self
            .piece_at(source)
            .expect("validated exchange source contains a piece");
        if let Some(captured_square) = capture_square {
            let captured = self
                .piece_at(captured_square)
                .expect("validated exchange capture square contains a piece");
            self.remove_piece(captured_square, captured);
        }
        self.remove_piece(source, moving);
        self.add_piece(target, Piece::new(side, resulting_kind));
    }

    fn attackers_to(&self, target: Square, by_color: Color) -> Bitboard {
        let pawns = pawn_attacks(by_color.opposite(), target)
            & self.pieces[by_color.index()][PieceKind::Pawn.index()];
        let knights =
            knight_attacks(target) & self.pieces[by_color.index()][PieceKind::Knight.index()];
        let kings = king_attacks(target) & self.pieces[by_color.index()][PieceKind::King.index()];
        let diagonal = bishop_attacks(target, self.all_occupancy)
            & (self.pieces[by_color.index()][PieceKind::Bishop.index()]
                | self.pieces[by_color.index()][PieceKind::Queen.index()]);
        let orthogonal = rook_attacks(target, self.all_occupancy)
            & (self.pieces[by_color.index()][PieceKind::Rook.index()]
                | self.pieces[by_color.index()][PieceKind::Queen.index()]);
        pawns | knights | kings | diagonal | orthogonal
    }

    fn square_is_attacked(&self, target: Square, by_color: Color) -> bool {
        !self.attackers_to(target, by_color).is_empty()
    }

    fn king_is_attacked(&self, color: Color) -> bool {
        self.square_is_attacked(self.king_squares[color.index()], color.opposite())
    }

    fn least_valuable_legal_attacker(&self, target: Square, side: Color) -> Option<Square> {
        let target_piece = self.piece_at(target)?;
        if target_piece.color == side || target_piece.kind == PieceKind::King {
            return None;
        }
        let attackers = self.attackers_to(target, side);
        for kind in PieceKind::ALL {
            let mut candidates = attackers & self.pieces[side.index()][kind.index()];
            while let Some(source) = candidates.pop_lsb() {
                let resulting_kind =
                    if kind == PieceKind::Pawn && target.row() == side.promotion_row() {
                        PieceKind::Knight
                    } else {
                        kind
                    };
                let mut next = *self;
                next.apply_exchange(source, target, Some(target), resulting_kind, side);
                if !next.king_is_attacked(side) {
                    return Some(source);
                }
            }
        }
        None
    }
}

fn hash_bytes(mut hash: u64, bytes: &[u8]) -> u64 {
    for byte in bytes {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    hash
}

#[cfg(test)]
#[path = "see_tests.rs"]
mod tests;
