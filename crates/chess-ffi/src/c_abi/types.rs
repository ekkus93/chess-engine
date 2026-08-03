use core::{mem::size_of, ptr};

use crate::EngineConfig;

/// Stable C ABI version implemented by this crate.
pub const CHESS_ENGINE_ABI_VERSION: u32 = 1;

/// Null opaque engine handle.
pub const CHESS_ENGINE_NULL_HANDLE: u64 = 0;
/// Null opaque cancellation handle.
pub const CHESS_ENGINE_NULL_CANCELLATION_HANDLE: u64 = 0;

/// Search request includes a depth limit.
pub const CHESS_ENGINE_SEARCH_FLAG_DEPTH: u32 = 1 << 0;
/// Search request includes a node limit.
pub const CHESS_ENGINE_SEARCH_FLAG_NODES: u32 = 1 << 1;
/// Search request includes a soft time limit.
pub const CHESS_ENGINE_SEARCH_FLAG_SOFT_TIME: u32 = 1 << 2;
/// Search request includes a hard time limit.
pub const CHESS_ENGINE_SEARCH_FLAG_HARD_TIME: u32 = 1 << 3;
/// Search request selects explicit infinite mode.
pub const CHESS_ENGINE_SEARCH_FLAG_INFINITE: u32 = 1 << 4;
/// Search request enables the bounded check extension.
pub const CHESS_ENGINE_SEARCH_FLAG_CHECK_EXTENSION: u32 = 1 << 5;
/// Search request includes an explicit cancellation handle.
pub const CHESS_ENGINE_SEARCH_FLAG_CANCELLATION: u32 = 1 << 6;

pub(crate) const CHESS_ENGINE_SEARCH_KNOWN_FLAGS: u32 = CHESS_ENGINE_SEARCH_FLAG_DEPTH
    | CHESS_ENGINE_SEARCH_FLAG_NODES
    | CHESS_ENGINE_SEARCH_FLAG_SOFT_TIME
    | CHESS_ENGINE_SEARCH_FLAG_HARD_TIME
    | CHESS_ENGINE_SEARCH_FLAG_INFINITE
    | CHESS_ENGINE_SEARCH_FLAG_CHECK_EXTENSION
    | CHESS_ENGINE_SEARCH_FLAG_CANCELLATION;

/// Opaque engine token. Zero is never valid.
pub type ChessEngineHandle = u64;
/// Opaque cancellation token. Zero is never valid.
pub type ChessEngineCancellationHandle = u64;

/// Structured result code returned by every fallible C ABI operation.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(i32)]
pub enum ChessEngineResultCode {
    /// Operation completed successfully.
    Ok = 0,
    /// A required pointer or opaque token was null.
    NullPointer = 1,
    /// An opaque token was unknown, destroyed, or of the wrong type.
    InvalidHandle = 2,
    /// A length-delimited byte range was not valid UTF-8.
    InvalidUtf8 = 3,
    /// A scalar, flag, or argument combination was invalid.
    InvalidArgument = 4,
    /// A versioned C record had an unsupported ABI version or size.
    AbiMismatch = 5,
    /// Strict playable FEN validation failed.
    InvalidFen = 10,
    /// UCI move syntax was malformed.
    InvalidMoveSyntax = 11,
    /// UCI move text did not identify a current legal move.
    IllegalMove = 12,
    /// A move was requested after an automatic terminal result.
    GameOver = 13,
    /// Rule or game-history processing failed.
    GameError = 14,
    /// The built-in evaluation weight identity failed validation.
    InvalidWeightSet = 15,
    /// Search or search-limit processing failed.
    SearchError = 20,
    /// A bounded allocation or registry reservation failed.
    AllocationFailure = 30,
    /// An output buffer record was stale, fabricated, or already freed.
    InvalidBuffer = 31,
    /// An internal synchronization or token invariant failed.
    InternalError = 100,
    /// A Rust panic was contained before crossing the ABI boundary.
    Panic = 101,
}

/// Versioned fixed-width engine construction record.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(C)]
pub struct ChessEngineConfig {
    /// Exact byte size of this record.
    pub struct_size: u32,
    /// [`CHESS_ENGINE_ABI_VERSION`].
    pub abi_version: u32,
    /// Fixed transposition-table budget in mebibytes.
    pub transposition_table_mebibytes: u64,
}

impl ChessEngineConfig {
    /// Creates the current default construction record.
    #[must_use]
    pub const fn new() -> Self {
        Self {
            struct_size: size_of::<Self>() as u32,
            abi_version: CHESS_ENGINE_ABI_VERSION,
            transposition_table_mebibytes: EngineConfig::new()
                .transposition_table_mebibytes() as u64,
        }
    }
}

impl Default for ChessEngineConfig {
    fn default() -> Self {
        Self::new()
    }
}

/// Registry-owned immutable UTF-8 or byte output.
///
/// Callers may read `data[0..len]` while `allocation` is live. The complete
/// record must be passed unchanged to `chess_engine_buffer_free` exactly once.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(C)]
pub struct ChessEngineBuffer {
    /// Immutable byte pointer, or null for an empty buffer.
    pub data: *const u8,
    /// Number of readable bytes.
    pub len: usize,
    /// Opaque allocation token, or zero for an empty buffer.
    pub allocation: u64,
}

impl ChessEngineBuffer {
    /// Creates an empty non-owning buffer record.
    #[must_use]
    pub const fn empty() -> Self {
        Self {
            data: ptr::null(),
            len: 0,
            allocation: 0,
        }
    }
}

impl Default for ChessEngineBuffer {
    fn default() -> Self {
        Self::empty()
    }
}

/// Stable color code used by C records.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(i32)]
pub enum ChessEngineColor {
    /// No color applies.
    None = 0,
    /// White.
    White = 1,
    /// Black.
    Black = 2,
}

/// Stable game-status category.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(i32)]
pub enum ChessEngineGameStatusKind {
    /// Play may continue and no claim is currently exposed.
    Ongoing = 0,
    /// Checkmate.
    Checkmate = 1,
    /// Stalemate.
    Stalemate = 2,
    /// Automatic draw.
    AutomaticDraw = 3,
    /// Claimable draw.
    ClaimableDraw = 4,
}

/// Stable draw-reason code.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(i32)]
pub enum ChessEngineDrawReason {
    /// No draw reason applies.
    None = 0,
    /// Threefold repetition claim.
    ThreefoldRepetition = 1,
    /// Fivefold automatic repetition.
    FivefoldRepetition = 2,
    /// Fifty-move claim.
    FiftyMoveRule = 3,
    /// Seventy-five-move automatic draw.
    SeventyFiveMoveRule = 4,
    /// Proven dead position.
    DeadPosition = 5,
}

/// Versioned rule-level status record.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(C)]
pub struct ChessEngineGameStatus {
    /// Exact byte size of this record.
    pub struct_size: u32,
    /// [`CHESS_ENGINE_ABI_VERSION`].
    pub abi_version: u32,
    /// Status category.
    pub kind: ChessEngineGameStatusKind,
    /// Checkmating side when `kind` is checkmate.
    pub winner: ChessEngineColor,
    /// Draw reason when `kind` is a draw category.
    pub draw_reason: ChessEngineDrawReason,
}

impl ChessEngineGameStatus {
    /// Creates a neutral current-version record.
    #[must_use]
    pub const fn new() -> Self {
        Self {
            struct_size: size_of::<Self>() as u32,
            abi_version: CHESS_ENGINE_ABI_VERSION,
            kind: ChessEngineGameStatusKind::Ongoing,
            winner: ChessEngineColor::None,
            draw_reason: ChessEngineDrawReason::None,
        }
    }
}

impl Default for ChessEngineGameStatus {
    fn default() -> Self {
        Self::new()
    }
}

/// Versioned evaluation-weight identity record.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(C)]
pub struct ChessEngineWeightIdentity {
    /// Exact byte size of this record.
    pub struct_size: u32,
    /// [`CHESS_ENGINE_ABI_VERSION`].
    pub abi_version: u32,
    /// Evaluation schema version.
    pub schema_version: u16,
    /// Reserved; must be zero.
    pub reserved: u16,
    /// Stable weight-set identifier.
    pub identifier: u64,
    /// Canonical weight checksum.
    pub checksum: u64,
}

impl ChessEngineWeightIdentity {
    /// Creates an empty current-version record.
    #[must_use]
    pub const fn new() -> Self {
        Self {
            struct_size: size_of::<Self>() as u32,
            abi_version: CHESS_ENGINE_ABI_VERSION,
            schema_version: 0,
            reserved: 0,
            identifier: 0,
            checksum: 0,
        }
    }
}

impl Default for ChessEngineWeightIdentity {
    fn default() -> Self {
        Self::new()
    }
}

/// Versioned search request with explicit presence flags.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(C)]
pub struct ChessEngineSearchRequest {
    /// Exact byte size of this record.
    pub struct_size: u32,
    /// [`CHESS_ENGINE_ABI_VERSION`].
    pub abi_version: u32,
    /// Bitwise OR of `CHESS_ENGINE_SEARCH_FLAG_*` values.
    pub flags: u32,
    /// Reserved; must be zero.
    pub reserved: u32,
    /// Depth value when the depth flag is present.
    pub depth: u16,
    /// Reserved; must be zero.
    pub reserved_depth: u16,
    /// Node value when the node flag is present.
    pub nodes: u64,
    /// Soft time in milliseconds when the soft-time flag is present.
    pub soft_time_milliseconds: u64,
    /// Hard time in milliseconds when the hard-time flag is present.
    pub hard_time_milliseconds: u64,
    /// Opaque cancellation token when the cancellation flag is present.
    pub cancellation_handle: ChessEngineCancellationHandle,
}

impl ChessEngineSearchRequest {
    /// Creates an incomplete finite request with no limits selected.
    #[must_use]
    pub const fn new() -> Self {
        Self {
            struct_size: size_of::<Self>() as u32,
            abi_version: CHESS_ENGINE_ABI_VERSION,
            flags: 0,
            reserved: 0,
            depth: 0,
            reserved_depth: 0,
            nodes: 0,
            soft_time_milliseconds: 0,
            hard_time_milliseconds: 0,
            cancellation_handle: CHESS_ENGINE_NULL_CANCELLATION_HANDLE,
        }
    }
}

impl Default for ChessEngineSearchRequest {
    fn default() -> Self {
        Self::new()
    }
}

/// Stable score category.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(i32)]
pub enum ChessEngineScoreKind {
    /// No exact completed score exists.
    None = 0,
    /// `score_value` is centipawns from the side-to-move perspective.
    Centipawns = 1,
    /// `score_value` is signed full moves to mate.
    Mate = 2,
}

/// Stable search termination category.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(i32)]
pub enum ChessEngineSearchTerminationKind {
    /// No termination value has been written.
    None = 0,
    /// Requested completed depth reached; value is depth.
    Depth = 1,
    /// Node budget exhausted; value is nodes.
    Nodes = 2,
    /// Soft time crossed; value is milliseconds.
    SoftTime = 3,
    /// Hard time crossed; value is milliseconds.
    HardTime = 4,
    /// Explicit cancellation requested; value is zero.
    ExplicitStop = 5,
    /// Supported depth ceiling reached; value is depth.
    MaximumSupportedDepth = 6,
}

/// Stable pre-depth-one fallback category.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(i32)]
pub enum ChessEngineSearchFallbackKind {
    /// No fallback was needed.
    None = 0,
    /// The first deterministic legal root move was used.
    FirstLegalMove = 1,
    /// The root had no legal move.
    NoLegalMove = 2,
}

/// Versioned search snapshot with registry-owned move/PV buffers.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(C)]
pub struct ChessEngineSearchResult {
    /// Exact byte size of this record.
    pub struct_size: u32,
    /// [`CHESS_ENGINE_ABI_VERSION`].
    pub abi_version: u32,
    /// Canonical best move or an empty buffer.
    pub best_move: ChessEngineBuffer,
    /// Canonical ponder move or an empty buffer.
    pub ponder_move: ChessEngineBuffer,
    /// Space-separated canonical principal variation or an empty buffer.
    pub principal_variation: ChessEngineBuffer,
    /// Exact completed score category.
    pub score_kind: ChessEngineScoreKind,
    /// Centipawns or signed full moves to mate according to `score_kind`.
    pub score_value: i32,
    /// Deepest exact completed depth.
    pub completed_depth: u16,
    /// Deepest root-relative ply entered, including partial work.
    pub selective_depth: u16,
    /// Deterministic winning termination category.
    pub termination_kind: ChessEngineSearchTerminationKind,
    /// Emergency fallback category.
    pub fallback_kind: ChessEngineSearchFallbackKind,
    /// Depth, nodes, or milliseconds according to `termination_kind`.
    pub termination_value: u64,
    /// Every production node entered.
    pub nodes: u64,
    /// Every quiescence node entered.
    pub qnodes: u64,
    /// Elapsed request time in milliseconds.
    pub elapsed_milliseconds: u64,
}

impl ChessEngineSearchResult {
    /// Creates an empty current-version search result.
    #[must_use]
    pub const fn new() -> Self {
        Self {
            struct_size: size_of::<Self>() as u32,
            abi_version: CHESS_ENGINE_ABI_VERSION,
            best_move: ChessEngineBuffer::empty(),
            ponder_move: ChessEngineBuffer::empty(),
            principal_variation: ChessEngineBuffer::empty(),
            score_kind: ChessEngineScoreKind::None,
            score_value: 0,
            completed_depth: 0,
            selective_depth: 0,
            termination_kind: ChessEngineSearchTerminationKind::None,
            fallback_kind: ChessEngineSearchFallbackKind::None,
            termination_value: 0,
            nodes: 0,
            qnodes: 0,
            elapsed_milliseconds: 0,
        }
    }
}

impl Default for ChessEngineSearchResult {
    fn default() -> Self {
        Self::new()
    }
}
