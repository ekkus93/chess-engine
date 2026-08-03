from __future__ import annotations

import os
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    content = read(path)
    count = content.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one anchor, found {count}: {old[:100]!r}")
    write(path, content.replace(old, new, 1))


# Direct dependency boundaries: adapters/facade may depend on chess-book; core/search do not.
for cargo_path in ["crates/chess-ffi/Cargo.toml", "crates/chess-uci/Cargo.toml"]:
    replace_once(
        cargo_path,
        "[dependencies]\nchess-core = { path = \"../chess-core\" }\n",
        "[dependencies]\nchess-book = { path = \"../chess-book\" }\nchess-core = { path = \"../chess-core\" }\n",
    )

# Safe facade error values remain clonable.
replace_once(
    "crates/chess-book/src/policy.rs",
    "#[derive(Debug, Eq, PartialEq)]\npub enum BookSelectionError<E> {",
    "#[derive(Clone, Debug, Eq, PartialEq)]\npub enum BookSelectionError<E> {",
)

safe_path = "crates/chess-ffi/src/safe.rs"
replace_once(
    safe_path,
    "use chess_core::{FenError, Game, GameError, GameStatus, MoveParseError, Position, UciMove};\n",
    "use chess_book::{\n    BookSelectionError, BookSelector, IndexedBook, IndexedBookError, IndexedBookQueryError,\n};\nuse chess_core::{FenError, Game, GameError, GameStatus, MoveParseError, Position, UciMove};\n",
)
replace_once(
    safe_path,
    "/// Explicit construction configuration for one [`Engine`].\n",
    "/// Explicit opening-book policy selected by one engine configuration.\n"
    "#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n"
    "pub enum OpeningBookSelection {\n"
    "    /// Stable highest-weight selection with ascending-UCI tie resolution.\n"
    "    DeterministicHighestWeight,\n"
    "    /// Weighted selection from one explicit selector-local seed.\n"
    "    WeightedRandom { seed: u64 },\n"
    "}\n\n"
    "impl OpeningBookSelection {\n"
    "    fn selector(self) -> BookSelector {\n"
    "        match self {\n"
    "            Self::DeterministicHighestWeight => BookSelector::deterministic_highest_weight(),\n"
    "            Self::WeightedRandom { seed } => BookSelector::weighted_random(seed),\n"
    "        }\n"
    "    }\n"
    "}\n\n"
    "/// Explicit construction configuration for one [`Engine`].\n",
)
replace_once(
    safe_path,
    "pub struct EngineConfig {\n    transposition_table_mebibytes: usize,\n}",
    "pub struct EngineConfig {\n"
    "    transposition_table_mebibytes: usize,\n"
    "    opening_book_enabled: bool,\n"
    "    opening_book_selection: OpeningBookSelection,\n"
    "}",
)
replace_once(
    safe_path,
    "        Self {\n            transposition_table_mebibytes: DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES,\n        }",
    "        Self {\n"
    "            transposition_table_mebibytes: DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES,\n"
    "            opening_book_enabled: false,\n"
    "            opening_book_selection: OpeningBookSelection::DeterministicHighestWeight,\n"
    "        }",
)
replace_once(
    safe_path,
    "    /// Returns the configured fixed transposition-table budget.\n    #[must_use]\n    pub const fn transposition_table_mebibytes(self) -> usize {\n        self.transposition_table_mebibytes\n    }\n",
    "    /// Enables or disables use of explicitly supplied opening-book data.\n"
    "    #[must_use]\n"
    "    pub const fn with_opening_book_enabled(mut self, enabled: bool) -> Self {\n"
    "        self.opening_book_enabled = enabled;\n"
    "        self\n"
    "    }\n\n"
    "    /// Selects deterministic highest-weight opening-book policy.\n"
    "    #[must_use]\n"
    "    pub const fn with_deterministic_opening_book(mut self) -> Self {\n"
    "        self.opening_book_selection = OpeningBookSelection::DeterministicHighestWeight;\n"
    "        self\n"
    "    }\n\n"
    "    /// Selects weighted opening-book policy from an explicit local seed.\n"
    "    #[must_use]\n"
    "    pub const fn with_weighted_opening_book(mut self, seed: u64) -> Self {\n"
    "        self.opening_book_selection = OpeningBookSelection::WeightedRandom { seed };\n"
    "        self\n"
    "    }\n\n"
    "    /// Returns the configured fixed transposition-table budget.\n"
    "    #[must_use]\n"
    "    pub const fn transposition_table_mebibytes(self) -> usize {\n"
    "        self.transposition_table_mebibytes\n"
    "    }\n\n"
    "    /// Returns whether explicitly supplied opening-book data may be queried.\n"
    "    #[must_use]\n"
    "    pub const fn opening_book_enabled(self) -> bool {\n"
    "        self.opening_book_enabled\n"
    "    }\n\n"
    "    /// Returns the explicit opening-book selection policy.\n"
    "    #[must_use]\n"
    "    pub const fn opening_book_selection(self) -> OpeningBookSelection {\n"
    "        self.opening_book_selection\n"
    "    }\n",
)
replace_once(
    safe_path,
    "    /// Reserving the bounded legal-move output vector failed.\n    LegalMoveStorageAllocation { move_count: usize },\n",
    "    /// Explicitly supplied indexed opening-book bytes were invalid.\n"
    "    InvalidOpeningBook(IndexedBookError),\n"
    "    /// Opening-book lookup, legality validation, or selection failed.\n"
    "    OpeningBookSelection(BookSelectionError<IndexedBookQueryError>),\n"
    "    /// Reserving the bounded legal-move output vector failed.\n"
    "    LegalMoveStorageAllocation { move_count: usize },\n",
)
replace_once(
    safe_path,
    "            Self::InvalidWeightSet(error) => error.fmt(formatter),\n            Self::LegalMoveStorageAllocation { move_count } => write!(\n",
    "            Self::InvalidWeightSet(error) => error.fmt(formatter),\n"
    "            Self::InvalidOpeningBook(error) => write!(formatter, \"invalid opening book: {error}\"),\n"
    "            Self::OpeningBookSelection(error) => error.fmt(formatter),\n"
    "            Self::LegalMoveStorageAllocation { move_count } => write!(\n",
)
replace_once(
    safe_path,
    "            Self::InvalidWeightSet(error) => Some(error),\n            Self::IllegalMove { .. } | Self::LegalMoveStorageAllocation { .. } => None,\n",
    "            Self::InvalidWeightSet(error) => Some(error),\n"
    "            Self::InvalidOpeningBook(error) => Some(error),\n"
    "            Self::OpeningBookSelection(error) => Some(error),\n"
    "            Self::IllegalMove { .. } | Self::LegalMoveStorageAllocation { .. } => None,\n",
)
replace_once(
    safe_path,
    "impl From<WeightValidationError> for EngineError {\n    fn from(value: WeightValidationError) -> Self {\n        Self::InvalidWeightSet(value)\n    }\n}\n",
    "impl From<WeightValidationError> for EngineError {\n"
    "    fn from(value: WeightValidationError) -> Self {\n"
    "        Self::InvalidWeightSet(value)\n"
    "    }\n"
    "}\n\n"
    "impl From<IndexedBookError> for EngineError {\n"
    "    fn from(value: IndexedBookError) -> Self {\n"
    "        Self::InvalidOpeningBook(value)\n"
    "    }\n"
    "}\n\n"
    "impl From<BookSelectionError<IndexedBookQueryError>> for EngineError {\n"
    "    fn from(value: BookSelectionError<IndexedBookQueryError>) -> Self {\n"
    "        Self::OpeningBookSelection(value)\n"
    "    }\n"
    "}\n",
)
replace_once(
    safe_path,
    "    transposition_table: TranspositionTable,\n    weight_identity: EvaluationWeightIdentity,\n",
    "    transposition_table: TranspositionTable,\n"
    "    weight_identity: EvaluationWeightIdentity,\n"
    "    opening_book: Option<IndexedBook>,\n"
    "    book_selector: BookSelector,\n",
)
replace_once(
    safe_path,
    "    /// Constructs an engine in the standard starting position.\n    pub fn new(config: EngineConfig) -> Result<Self, EngineError> {\n        let weight_set = EvaluationWeightSet::baseline();\n        weight_set.validate()?;\n        let transposition_table = TranspositionTable::new(config.transposition_table_mebibytes())?;\n        Ok(Self {\n            config,\n            game: Game::starting(),\n            transposition_table,\n            weight_identity: EvaluationWeightIdentity::from_set(weight_set),\n        })\n    }\n",
    "    /// Constructs an engine without opening-book data.\n"
    "    ///\n"
    "    /// Opening-book enablement may remain configured, but absence of data is\n"
    "    /// normal and [`Self::opening_book_move`] returns `Ok(None)`.\n"
    "    pub fn new(config: EngineConfig) -> Result<Self, EngineError> {\n"
    "        Self::new_with_opening_book(config, None)\n"
    "    }\n\n"
    "    /// Constructs an engine with an explicitly supplied validated indexed book.\n"
    "    pub fn new_with_opening_book(\n"
    "        config: EngineConfig,\n"
    "        opening_book: Option<IndexedBook>,\n"
    "    ) -> Result<Self, EngineError> {\n"
    "        let weight_set = EvaluationWeightSet::baseline();\n"
    "        weight_set.validate()?;\n"
    "        let transposition_table = TranspositionTable::new(config.transposition_table_mebibytes())?;\n"
    "        let book_selector = config.opening_book_selection().selector();\n"
    "        Ok(Self {\n"
    "            config,\n"
    "            game: Game::starting(),\n"
    "            transposition_table,\n"
    "            weight_identity: EvaluationWeightIdentity::from_set(weight_set),\n"
    "            opening_book,\n"
    "            book_selector,\n"
    "        })\n"
    "    }\n\n"
    "    /// Parses and injects one complete versioned indexed-book byte image.\n"
    "    pub fn new_with_indexed_book_bytes(\n"
    "        config: EngineConfig,\n"
    "        bytes: &[u8],\n"
    "    ) -> Result<Self, EngineError> {\n"
    "        let opening_book = IndexedBook::from_bytes(bytes)?;\n"
    "        Self::new_with_opening_book(config, Some(opening_book))\n"
    "    }\n",
)
replace_once(
    safe_path,
    "    /// Runs one synchronous limit-controlled search without mutating played state.\n",
    "    /// Returns one selected legal opening-book move for the current position.\n"
    "    ///\n"
    "    /// Disabled configuration, absent explicitly supplied data, and a valid\n"
    "    /// book with no current-position entry all return `Ok(None)`. Backend,\n"
    "    /// legality, and policy failures remain typed and never fall through.\n"
    "    pub fn opening_book_move(&mut self) -> Result<Option<String>, EngineError> {\n"
    "        if !self.config.opening_book_enabled() {\n"
    "            return Ok(None);\n"
    "        }\n"
    "        let Some(opening_book) = self.opening_book.as_ref() else {\n"
    "            return Ok(None);\n"
    "        };\n"
    "        self.book_selector\n"
    "            .select(opening_book, self.game.position())\n"
    "            .map(|selected| selected.map(|current| current.chess_move().to_uci()))\n"
    "            .map_err(EngineError::from)\n"
    "    }\n\n"
    "    /// Runs one synchronous limit-controlled search without mutating played state.\n",
)

# Re-export safe book configuration from the facade crate.
replace_once(
    "crates/chess-ffi/src/lib.rs",
    "    Engine, EngineConfig, EngineError, EvaluationWeightIdentity, SearchCancellationHandle,\n",
    "    Engine, EngineConfig, EngineError, EvaluationWeightIdentity, OpeningBookSelection,\n    SearchCancellationHandle,\n",
)

# Safe-facade focused tests.
replace_once(
    "crates/chess-ffi/tests/safe_facade.rs",
    "use chess_core::{Color, GameStatus, Move};\n",
    "use chess_book::{IndexedBook, IndexedBookRecord};\nuse chess_core::{Color, GameStatus, Move, Position};\n",
)
replace_once(
    "crates/chess-ffi/tests/safe_facade.rs",
    "fn assert_send<T: Send>() {}\n",
    "fn starting_book_bytes() -> Vec<u8> {\n"
    "    let position = Position::starting();\n"
    "    let record = IndexedBookRecord::new(\n"
    "        &position,\n"
    "        \"e2e4\".parse().expect(\"test move syntax is valid\"),\n"
    "        100,\n"
    "    )\n"
    "    .expect(\"starting record is valid\");\n"
    "    IndexedBook::from_records(vec![record])\n"
    "        .expect(\"test book is valid\")\n"
    "        .to_bytes()\n"
    "}\n\n"
    "fn assert_send<T: Send>() {}\n",
)
with open(ROOT / "crates/chess-ffi/tests/safe_facade.rs", "a", encoding="utf-8") as handle:
    handle.write(
        "\n#[test]\n"
        "fn opening_book_configuration_is_explicit_and_absence_is_normal() {\n"
        "    let enabled = EngineConfig::new()\n"
        "        .with_transposition_table_mebibytes(1)\n"
        "        .with_opening_book_enabled(true);\n"
        "    let mut without_data = Engine::new(enabled).expect(\"engine without book constructs\");\n"
        "    assert_eq!(without_data.opening_book_move(), Ok(None));\n"
        "    let result = without_data\n"
        "        .search(SearchRequest::new().with_depth(1))\n"
        "        .expect(\"normal search remains available without a book\");\n"
        "    assert!(result.best_move().is_some());\n\n"
        "    let bytes = starting_book_bytes();\n"
        "    let mut disabled = Engine::new_with_indexed_book_bytes(\n"
        "        enabled.with_opening_book_enabled(false),\n"
        "        &bytes,\n"
        "    )\n"
        "    .expect(\"valid disabled book constructs\");\n"
        "    assert_eq!(disabled.opening_book_move(), Ok(None));\n"
        "}\n\n"
        "#[test]\n"
        "fn injected_indexed_book_returns_legal_move_and_no_entry_falls_through() {\n"
        "    let bytes = starting_book_bytes();\n"
        "    let config = EngineConfig::new()\n"
        "        .with_transposition_table_mebibytes(1)\n"
        "        .with_opening_book_enabled(true);\n"
        "    let mut engine = Engine::new_with_indexed_book_bytes(config, &bytes)\n"
        "        .expect(\"valid indexed book constructs\");\n"
        "    assert_eq!(engine.opening_book_move(), Ok(Some(\"e2e4\".to_owned())));\n"
        "    engine.play_move(\"e2e4\").expect(\"book move is legal\");\n"
        "    assert_eq!(engine.opening_book_move(), Ok(None));\n"
        "}\n\n"
        "#[test]\n"
        "fn corrupt_explicit_book_is_rejected_before_engine_construction() {\n"
        "    let config = EngineConfig::new().with_opening_book_enabled(true);\n"
        "    assert!(matches!(\n"
        "        Engine::new_with_indexed_book_bytes(config, b\"not a book\"),\n"
        "        Err(EngineError::InvalidOpeningBook(_))\n"
        "    ));\n"
        "}\n"
    )

# Additive C ABI functions preserve the version-1 record layout.
functions_path = "crates/chess-ffi/src/c_abi/functions.rs"
replace_once(
    functions_path,
    "unsafe fn read_utf8<'a>(data: *const u8, len: usize, label: &str) -> AbiResult<&'a str> {\n",
    "unsafe fn read_bytes<'a>(data: *const u8, len: usize, label: &str) -> AbiResult<&'a [u8]> {\n"
    "    if len == 0 {\n"
    "        return Ok(&[]);\n"
    "    }\n"
    "    if data.is_null() {\n"
    "        return Err(null_pointer(label));\n"
    "    }\n"
    "    // SAFETY: The C caller guarantees a readable byte range of exactly `len` bytes.\n"
    "    Ok(unsafe { slice::from_raw_parts(data, len) })\n"
    "}\n\n"
    "unsafe fn read_utf8<'a>(data: *const u8, len: usize, label: &str) -> AbiResult<&'a str> {\n",
)
replace_once(
    functions_path,
    "        EngineError::InvalidWeightSet(_) => ChessEngineResultCode::InvalidWeightSet,\n",
    "        EngineError::InvalidWeightSet(_) => ChessEngineResultCode::InvalidWeightSet,\n"
    "        EngineError::InvalidOpeningBook(_) => ChessEngineResultCode::InvalidOpeningBook,\n"
    "        EngineError::OpeningBookSelection(_) => ChessEngineResultCode::OpeningBookError,\n",
)
replace_once(
    functions_path,
    "/// Invalidates one opaque engine token.\n",
    "/// Creates one opaque engine from explicit indexed opening-book bytes.\n"
    "///\n"
    "/// # Safety\n"
    "///\n"
    "/// Pointer contracts match [`chess_engine_create`]. `book_data` must reference\n"
    "/// exactly `book_len` readable bytes. `book_enabled` must be zero or one.\n"
    "#[no_mangle]\n"
    "pub unsafe extern \"C\" fn chess_engine_create_with_indexed_book(\n"
    "    config: *const ChessEngineConfig,\n"
    "    book_data: *const u8,\n"
    "    book_len: usize,\n"
    "    book_enabled: u8,\n"
    "    out_handle: *mut ChessEngineHandle,\n"
    ") -> ChessEngineResultCode {\n"
    "    boundary(|| {\n"
    "        if out_handle.is_null() {\n"
    "            return Err(null_pointer(\"output engine handle\"));\n"
    "        }\n"
    "        // SAFETY: Required by this function's C contract and checked for null above.\n"
    "        unsafe { write_copy(out_handle, CHESS_ENGINE_NULL_HANDLE) };\n"
    "        if book_enabled > 1 {\n"
    "            return Err(invalid_argument(\"opening-book enabled value must be zero or one\"));\n"
    "        }\n"
    "        let config = if config.is_null() {\n"
    "            EngineConfig::new()\n"
    "        } else {\n"
    "            // SAFETY: Required by this function's C contract.\n"
    "            validate_config(unsafe { read_copy(config) })?\n"
    "        }\n"
    "        .with_opening_book_enabled(book_enabled != 0);\n"
    "        // SAFETY: Required by this function's C contract.\n"
    "        let bytes = unsafe { read_bytes(book_data, book_len, \"opening-book input\") }?;\n"
    "        let engine = Engine::new_with_indexed_book_bytes(config, bytes).map_err(engine_failure)?;\n"
    "        let handle = insert_engine(engine)?;\n"
    "        // SAFETY: Required by this function's C contract and checked for null above.\n"
    "        unsafe { write_copy(out_handle, handle) };\n"
    "        Ok(())\n"
    "    })\n"
    "}\n\n"
    "/// Invalidates one opaque engine token.\n",
)
replace_once(
    functions_path,
    "/// Returns deterministic legal UCI moves separated by `\\n` bytes.\n",
    "/// Returns the selected legal opening-book move, or an empty buffer.\n"
    "///\n"
    "/// # Safety\n"
    "///\n"
    "/// `out_buffer` must point to a fresh writable [`ChessEngineBuffer`] record.\n"
    "#[no_mangle]\n"
    "pub unsafe extern \"C\" fn chess_engine_get_opening_book_move(\n"
    "    handle: ChessEngineHandle,\n"
    "    out_buffer: *mut ChessEngineBuffer,\n"
    ") -> ChessEngineResultCode {\n"
    "    boundary(|| {\n"
    "        if out_buffer.is_null() {\n"
    "            return Err(null_pointer(\"output opening-book move buffer\"));\n"
    "        }\n"
    "        // SAFETY: Required by this function's C contract and checked for null above.\n"
    "        unsafe { write_copy(out_buffer, ChessEngineBuffer::empty()) };\n"
    "        let entry = resolve_engine(handle)?;\n"
    "        let selected = {\n"
    "            let mut engine = lock_engine(&entry)?;\n"
    "            engine.opening_book_move().map_err(engine_failure)?\n"
    "        };\n"
    "        let buffer = allocate_buffer(selected.unwrap_or_default().into_bytes())?;\n"
    "        // SAFETY: Required by this function's C contract and checked for null above.\n"
    "        unsafe { write_copy(out_buffer, buffer) };\n"
    "        Ok(())\n"
    "    })\n"
    "}\n\n"
    "/// Returns deterministic legal UCI moves separated by `\\n` bytes.\n",
)

# Stable result codes and C header declarations.
replace_once(
    "crates/chess-ffi/src/c_abi/types.rs",
    "    /// Search or search-limit processing failed.\n    SearchError = 20,\n",
    "    /// Explicit indexed opening-book bytes were invalid.\n"
    "    InvalidOpeningBook = 16,\n"
    "    /// Opening-book lookup, legality validation, or selection failed.\n"
    "    OpeningBookError = 21,\n"
    "    /// Search or search-limit processing failed.\n"
    "    SearchError = 20,\n",
)
header_path = "crates/chess-ffi/include/chess_engine.h"
replace_once(
    header_path,
    "    CHESS_ENGINE_RESULT_INVALID_WEIGHT_SET = 15,\n    CHESS_ENGINE_RESULT_SEARCH_ERROR = 20,\n",
    "    CHESS_ENGINE_RESULT_INVALID_WEIGHT_SET = 15,\n"
    "    CHESS_ENGINE_RESULT_INVALID_OPENING_BOOK = 16,\n"
    "    CHESS_ENGINE_RESULT_SEARCH_ERROR = 20,\n"
    "    CHESS_ENGINE_RESULT_OPENING_BOOK_ERROR = 21,\n",
)
replace_once(
    header_path,
    "ChessEngineResultCode chess_engine_destroy(ChessEngineHandle handle);\n",
    "ChessEngineResultCode chess_engine_create_with_indexed_book(\n"
    "    const ChessEngineConfig *config,\n"
    "    const uint8_t *book_data,\n"
    "    size_t book_len,\n"
    "    uint8_t book_enabled,\n"
    "    ChessEngineHandle *out_handle\n"
    ");\n"
    "ChessEngineResultCode chess_engine_destroy(ChessEngineHandle handle);\n",
)
replace_once(
    header_path,
    "ChessEngineResultCode chess_engine_get_legal_moves(\n",
    "ChessEngineResultCode chess_engine_get_opening_book_move(\n"
    "    ChessEngineHandle handle,\n"
    "    ChessEngineBuffer *out_buffer\n"
    ");\n"
    "ChessEngineResultCode chess_engine_get_legal_moves(\n",
)

# C ABI focused test constructs a valid book with the authoritative serializer.
replace_once(
    "crates/chess-ffi/tests/c_abi_contract.rs",
    "use chess_ffi::c_abi::*;\n",
    "use chess_book::{IndexedBook, IndexedBookRecord};\nuse chess_core::Position;\nuse chess_ffi::c_abi::*;\n",
)
with open(ROOT / "crates/chess-ffi/tests/c_abi_contract.rs", "a", encoding="utf-8") as handle:
    handle.write(
        "\n#[test]\n"
        "fn explicit_indexed_book_round_trips_through_additive_abi() {\n"
        "    let position = Position::starting();\n"
        "    let record = IndexedBookRecord::new(\n"
        "        &position,\n"
        "        \"e2e4\".parse().expect(\"test move syntax is valid\"),\n"
        "        100,\n"
        "    )\n"
        "    .expect(\"test record is valid\");\n"
        "    let bytes = IndexedBook::from_records(vec![record])\n"
        "        .expect(\"test book is valid\")\n"
        "        .to_bytes();\n"
        "    let mut config = ChessEngineConfig::new();\n"
        "    config.transposition_table_mebibytes = 1;\n"
        "    let mut handle = CHESS_ENGINE_NULL_HANDLE;\n"
        "    // SAFETY: All input and output ranges are valid for the call.\n"
        "    assert_eq!(\n"
        "        unsafe {\n"
        "            chess_engine_create_with_indexed_book(\n"
        "                &config,\n"
        "                bytes.as_ptr(),\n"
        "                bytes.len(),\n"
        "                1,\n"
        "                &mut handle,\n"
        "            )\n"
        "        },\n"
        "        ChessEngineResultCode::Ok\n"
        "    );\n"
        "    let mut selected = ChessEngineBuffer::empty();\n"
        "    // SAFETY: `selected` is a fresh writable output record.\n"
        "    assert_eq!(\n"
        "        unsafe { chess_engine_get_opening_book_move(handle, &mut selected) },\n"
        "        ChessEngineResultCode::Ok\n"
        "    );\n"
        "    assert_eq!(buffer_text(&selected), \"e2e4\");\n"
        "    free_buffer(&mut selected);\n"
        "    assert_eq!(chess_engine_destroy(handle), ChessEngineResultCode::Ok);\n\n"
        "    let mut invalid_handle = CHESS_ENGINE_NULL_HANDLE;\n"
        "    // SAFETY: The invalid byte range is readable and the output is writable.\n"
        "    assert_eq!(\n"
        "        unsafe {\n"
        "            chess_engine_create_with_indexed_book(\n"
        "                &config,\n"
        "                b\"bad\".as_ptr(),\n"
        "                3,\n"
        "                1,\n"
        "                &mut invalid_handle,\n"
        "            )\n"
        "        },\n"
        "        ChessEngineResultCode::InvalidOpeningBook\n"
        "    );\n"
        "    assert_eq!(invalid_handle, CHESS_ENGINE_NULL_HANDLE);\n"
        "}\n"
    )

# UCI OwnBook option and explicit adapter-owned book use.
uci_path = "crates/chess-uci/src/lib.rs"
replace_once(
    uci_path,
    "    check_extension: bool,\n}",
    "    check_extension: bool,\n    own_book: bool,\n}",
)
replace_once(
    uci_path,
    "    /// Returns whether the bounded one-ply check extension is enabled.\n    #[must_use]\n    pub const fn check_extension(self) -> bool {\n        self.check_extension\n    }\n",
    "    /// Returns whether the bounded one-ply check extension is enabled.\n"
    "    #[must_use]\n"
    "    pub const fn check_extension(self) -> bool {\n"
    "        self.check_extension\n"
    "    }\n\n"
    "    /// Returns whether an explicitly supplied opening book may be queried.\n"
    "    #[must_use]\n"
    "    pub const fn own_book(self) -> bool {\n"
    "        self.own_book\n"
    "    }\n",
)
replace_once(
    uci_path,
    "            check_extension: false,\n",
    "            check_extension: false,\n            own_book: false,\n",
)
replace_once(
    uci_path,
    "            \"option name CheckExtension type check default false\".to_owned(),\n",
    "            \"option name CheckExtension type check default false\".to_owned(),\n"
    "            \"option name OwnBook type check default false\".to_owned(),\n",
)
replace_once(
    uci_path,
    "            Ok((name, _)) => UciResponse::error(format!(\"unsupported option {name:?}\")),\n",
    "            Ok((name, value)) if name == \"OwnBook\" => match parse_boolean(&value) {\n"
    "                Ok(own_book) => {\n"
    "                    self.options.own_book = own_book;\n"
    "                    UciResponse::default()\n"
    "                }\n"
    "                Err(error) => UciResponse::error(error),\n"
    "            },\n"
    "            Ok((name, _)) => UciResponse::error(format!(\"unsupported option {name:?}\")),\n",
)
replace_once(
    uci_path,
    "                \"option name CheckExtension type check default false\",\n                \"uciok\",\n",
    "                \"option name CheckExtension type check default false\",\n"
    "                \"option name OwnBook type check default false\",\n"
    "                \"uciok\",\n",
)
replace_once(
    uci_path,
    "        assert!(session\n            .handle_line(\"setoption name CheckExtension value true\")\n            .lines()\n            .is_empty());\n",
    "        assert!(session\n"
    "            .handle_line(\"setoption name CheckExtension value true\")\n"
    "            .lines()\n"
    "            .is_empty());\n"
    "        assert!(session\n"
    "            .handle_line(\"setoption name OwnBook value true\")\n"
    "            .lines()\n"
    "            .is_empty());\n",
)
replace_once(
    uci_path,
    "                check_extension: true,\n            }\n",
    "                check_extension: true,\n                own_book: true,\n            }\n",
)
replace_once(
    uci_path,
    "                assert!(request.options().check_extension());\n",
    "                assert!(request.options().check_extension());\n"
    "                assert!(!request.options().own_book());\n",
)

# Binary UCI adapter explicitly reads only a requested --book path.
main_path = "crates/chess-uci/src/main.rs"
replace_once(
    main_path,
    "use std::{\n    io::{self, BufRead, Write},\n    sync::Arc,\n};\n\nuse chess_uci::{UciEvent, UciSession};\n",
    "use std::{\n"
    "    env, fs,\n"
    "    ffi::OsString,\n"
    "    io::{self, BufRead, Write},\n"
    "    path::PathBuf,\n"
    "    sync::Arc,\n"
    "};\n\n"
    "use chess_book::{BookSelector, IndexedBook};\n"
    "use chess_uci::{SearchRequest, UciEvent, UciSession};\n",
)
replace_once(
    main_path,
    "fn main() -> io::Result<()> {\n    let stdin = io::stdin();\n    run_protocol_loop(stdin.lock(), io::stdout())\n}\n\nfn run_protocol_loop<R, W>(input: R, output: W) -> io::Result<()>\nwhere\n    R: BufRead,\n    W: Write + Send + 'static,\n{\n",
    "fn main() -> io::Result<()> {\n"
    "    let opening_book = load_opening_book(env::args_os().skip(1))?;\n"
    "    let stdin = io::stdin();\n"
    "    run_protocol_loop_with_book(stdin.lock(), io::stdout(), opening_book)\n"
    "}\n\n"
    "fn load_opening_book<I>(arguments: I) -> io::Result<Option<IndexedBook>>\n"
    "where\n"
    "    I: IntoIterator<Item = OsString>,\n"
    "{\n"
    "    let mut arguments = arguments.into_iter();\n"
    "    let Some(flag) = arguments.next() else {\n"
    "        return Ok(None);\n"
    "    };\n"
    "    if flag != \"--book\" {\n"
    "        return Err(io::Error::new(\n"
    "            io::ErrorKind::InvalidInput,\n"
    "            format!(\"unsupported argument {flag:?}; expected --book <path>\"),\n"
    "        ));\n"
    "    }\n"
    "    let path = arguments.next().map(PathBuf::from).ok_or_else(|| {\n"
    "        io::Error::new(io::ErrorKind::InvalidInput, \"--book requires a path\")\n"
    "    })?;\n"
    "    if let Some(extra) = arguments.next() {\n"
    "        return Err(io::Error::new(\n"
    "            io::ErrorKind::InvalidInput,\n"
    "            format!(\"unexpected extra argument {extra:?}\"),\n"
    "        ));\n"
    "    }\n"
    "    let bytes = fs::read(&path)?;\n"
    "    IndexedBook::from_bytes(&bytes).map(Some).map_err(|error| {\n"
    "        io::Error::new(\n"
    "            io::ErrorKind::InvalidData,\n"
    "            format!(\"invalid opening book {}: {error}\", path.display()),\n"
    "        )\n"
    "    })\n"
    "}\n\n"
    "fn run_protocol_loop<R, W>(input: R, output: W) -> io::Result<()>\n"
    "where\n"
    "    R: BufRead,\n"
    "    W: Write + Send + 'static,\n"
    "{\n"
    "    run_protocol_loop_with_book(input, output, None)\n"
    "}\n\n"
    "fn run_protocol_loop_with_book<R, W>(\n"
    "    input: R,\n"
    "    output: W,\n"
    "    opening_book: Option<IndexedBook>,\n"
    ") -> io::Result<()>\n"
    "where\n"
    "    R: BufRead,\n"
    "    W: Write + Send + 'static,\n"
    "{\n",
)
replace_once(
    main_path,
    "    let mut session = UciSession::new();\n    let mut workers = SearchWorkerSlot::new(search_output);\n",
    "    let mut session = UciSession::new();\n"
    "    let mut workers = SearchWorkerSlot::new(search_output);\n"
    "    let mut book_selector = BookSelector::deterministic_highest_weight();\n",
)
replace_once(
    main_path,
    "            Some(UciEvent::StartSearch(request)) => {\n                report_optional_worker_outcome(\n                    output.as_ref(),\n                    workers.start(request.as_ref().clone()),\n                )?;\n            }\n",
    "            Some(UciEvent::StartSearch(request)) => {\n"
    "                match select_opening_book_move(\n"
    "                    &mut book_selector,\n"
    "                    opening_book.as_ref(),\n"
    "                    request.as_ref(),\n"
    "                ) {\n"
    "                    Ok(Some(chess_move)) => {\n"
    "                        report_optional_worker_outcome(output.as_ref(), workers.discard())?;\n"
    "                        output.write_line(&format!(\"bestmove {chess_move}\"))?;\n"
    "                    }\n"
    "                    Ok(None) => {\n"
    "                        report_optional_worker_outcome(\n"
    "                            output.as_ref(),\n"
    "                            workers.start(request.as_ref().clone()),\n"
    "                        )?;\n"
    "                    }\n"
    "                    Err(error) => {\n"
    "                        report_optional_worker_outcome(output.as_ref(), workers.discard())?;\n"
    "                        output.write_line(&format!(\"info string error: {error}\"))?;\n"
    "                    }\n"
    "                }\n"
    "            }\n",
)
replace_once(
    main_path,
    "fn report_optional_worker_outcome<W>(\n",
    "fn select_opening_book_move(\n"
    "    selector: &mut BookSelector,\n"
    "    opening_book: Option<&IndexedBook>,\n"
    "    request: &SearchRequest,\n"
    ") -> Result<Option<String>, String> {\n"
    "    if !request.options().own_book() {\n"
    "        return Ok(None);\n"
    "    }\n"
    "    let Some(opening_book) = opening_book else {\n"
    "        return Ok(None);\n"
    "    };\n"
    "    selector\n"
    "        .select(opening_book, request.game().position())\n"
    "        .map(|selected| selected.map(|current| current.chess_move().to_uci()))\n"
    "        .map_err(|error| error.to_string())\n"
    "}\n\n"
    "fn report_optional_worker_outcome<W>(\n",
)
with open(ROOT / main_path, "a", encoding="utf-8") as handle:
    handle.write(
        "\n#[cfg(test)]\n"
        "mod book_tests {\n"
        "    use super::*;\n"
        "    use chess_book::IndexedBookRecord;\n"
        "    use chess_core::Position;\n\n"
        "    fn request(own_book: bool) -> SearchRequest {\n"
        "        let mut session = UciSession::new();\n"
        "        if own_book {\n"
        "            assert!(session\n"
        "                .handle_line(\"setoption name OwnBook value true\")\n"
        "                .lines()\n"
        "                .is_empty());\n"
        "        }\n"
        "        let response = session.handle_line(\"go depth 1\");\n"
        "        match response.event() {\n"
        "            Some(UciEvent::StartSearch(request)) => request.as_ref().clone(),\n"
        "            other => panic!(\"expected search request, found {other:?}\"),\n"
        "        }\n"
        "    }\n\n"
        "    fn starting_book() -> IndexedBook {\n"
        "        let position = Position::starting();\n"
        "        IndexedBook::from_records(vec![\n"
        "            IndexedBookRecord::new(\n"
        "                &position,\n"
        "                \"e2e4\".parse().expect(\"test move syntax is valid\"),\n"
        "                100,\n"
        "            )\n"
        "            .expect(\"test record is valid\"),\n"
        "        ])\n"
        "        .expect(\"test book is valid\")\n"
        "    }\n\n"
        "    #[test]\n"
        "    fn own_book_hit_bypasses_search_only_when_enabled_and_supplied() {\n"
        "        let book = starting_book();\n"
        "        let mut selector = BookSelector::deterministic_highest_weight();\n"
        "        assert_eq!(\n"
        "            select_opening_book_move(&mut selector, Some(&book), &request(true)),\n"
        "            Ok(Some(\"e2e4\".to_owned()))\n"
        "        );\n"
        "        assert_eq!(\n"
        "            select_opening_book_move(&mut selector, Some(&book), &request(false)),\n"
        "            Ok(None)\n"
        "        );\n"
        "        assert_eq!(\n"
        "            select_opening_book_move(&mut selector, None, &request(true)),\n"
        "            Ok(None)\n"
        "        );\n"
        "    }\n"
        "}\n"
    )

# JNI bridge adds byte-array construction and a book-move query through the C ABI.
bridge_path = "crates/chess-jni/src/bridge.rs"
replace_once(
    bridge_path,
    "    chess_engine_cancellation_reset, chess_engine_create, chess_engine_destroy,\n",
    "    chess_engine_cancellation_reset, chess_engine_create,\n"
    "    chess_engine_create_with_indexed_book, chess_engine_destroy,\n",
)
replace_once(
    bridge_path,
    "    chess_engine_get_fen, chess_engine_get_game_status, chess_engine_get_legal_moves,\n",
    "    chess_engine_get_fen, chess_engine_get_game_status, chess_engine_get_legal_moves,\n"
    "    chess_engine_get_opening_book_move,\n",
)
replace_once(
    bridge_path,
    "pub(crate) fn destroy_engine(handle: jlong) -> BridgeResult<()> {\n",
    "pub(crate) fn create_engine_with_indexed_book(\n"
    "    transposition_table_mebibytes: jlong,\n"
    "    book_bytes: &[u8],\n"
    "    enabled: jboolean,\n"
    ") -> BridgeResult<jlong> {\n"
    "    let table_size = u64::try_from(transposition_table_mebibytes).map_err(|_| {\n"
    "        BridgeError::InvalidArgument(\n"
    "            \"transposition-table budget must be a positive signed 64-bit value\".to_owned(),\n"
    "        )\n"
    "    })?;\n"
    "    if table_size == 0 {\n"
    "        return Err(BridgeError::InvalidArgument(\n"
    "            \"transposition-table budget must be greater than zero\".to_owned(),\n"
    "        ));\n"
    "    }\n"
    "    let mut config = ChessEngineConfig::new();\n"
    "    config.transposition_table_mebibytes = table_size;\n"
    "    let mut handle = CHESS_ENGINE_NULL_HANDLE;\n"
    "    // SAFETY: All records and the immutable byte range remain live for the call.\n"
    "    ensure_code(unsafe {\n"
    "        chess_engine_create_with_indexed_book(\n"
    "            &config,\n"
    "            book_bytes.as_ptr(),\n"
    "            book_bytes.len(),\n"
    "            if enabled == JNI_FALSE { 0 } else { 1 },\n"
    "            &mut handle,\n"
    "        )\n"
    "    })?;\n"
    "    Ok(token_to_jlong(handle))\n"
    "}\n\n"
    "pub(crate) fn destroy_engine(handle: jlong) -> BridgeResult<()> {\n",
)
replace_once(
    bridge_path,
    "pub(crate) fn legal_moves(handle: jlong) -> BridgeResult<String> {\n",
    "pub(crate) fn opening_book_move(handle: jlong) -> BridgeResult<String> {\n"
    "    take_text(|output| {\n"
    "        // SAFETY: `output` points to a fresh writable buffer record.\n"
    "        unsafe { chess_engine_get_opening_book_move(token_from_jlong(handle), output) }\n"
    "    })\n"
    "}\n\n"
    "pub(crate) fn legal_moves(handle: jlong) -> BridgeResult<String> {\n",
)

jni_path = "crates/chess-jni/src/lib.rs"
replace_once(
    jni_path,
    "    objects::{JObject, JString},\n",
    "    objects::{JByteArray, JObject, JString},\n",
)
replace_once(
    jni_path,
    "#[export_name = \"Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeDestroy\"]\n",
    "#[export_name = \"Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeCreateWithIndexedBook\"]\n"
    "pub extern \"system\" fn native_create_with_indexed_book(\n"
    "    mut env: JNIEnv<'_>,\n"
    "    _binding: JObject<'_>,\n"
    "    transposition_table_mebibytes: jlong,\n"
    "    book_data: JByteArray<'_>,\n"
    "    enabled: jboolean,\n"
    ") -> jlong {\n"
    "    boundary(&mut env, 0, |env| {\n"
    "        if book_data.is_null() {\n"
    "            return Err(bridge::BridgeError::InvalidArgument(\n"
    "                \"opening-book byte array is null\".to_owned(),\n"
    "            ));\n"
    "        }\n"
    "        let bytes = env.convert_byte_array(&book_data)?;\n"
    "        bridge::create_engine_with_indexed_book(\n"
    "            transposition_table_mebibytes,\n"
    "            &bytes,\n"
    "            enabled,\n"
    "        )\n"
    "    })\n"
    "}\n\n"
    "#[export_name = \"Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeDestroy\"]\n",
)
replace_once(
    jni_path,
    "#[export_name = \"Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeLegalMoves\"]\n",
    "#[export_name = \"Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeOpeningBookMove\"]\n"
    "pub extern \"system\" fn native_opening_book_move(\n"
    "    mut env: JNIEnv<'_>,\n"
    "    _binding: JObject<'_>,\n"
    "    handle: jlong,\n"
    ") -> jstring {\n"
    "    boundary(&mut env, null_jstring(), |env| {\n"
    "        output_string(env, &bridge::opening_book_move(handle)?)\n"
    "    })\n"
    "}\n\n"
    "#[export_name = \"Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeLegalMoves\"]\n",
)

kotlin_path = "crates/chess-jni/kotlin/src/main/kotlin/com/ekkus93/chessengine/ChessEngine.kt"
replace_once(
    kotlin_path,
    "    INVALID_WEIGHT_SET(15),\n    SEARCH_ERROR(20),\n",
    "    INVALID_WEIGHT_SET(15),\n"
    "    INVALID_OPENING_BOOK(16),\n"
    "    SEARCH_ERROR(20),\n"
    "    OPENING_BOOK_ERROR(21),\n",
)
replace_once(
    kotlin_path,
    "    fun legalMoves(): List<String> =\n",
    "    fun openingBookMove(): String? =\n"
    "        withHandle(NativeChessEngineBindings::nativeOpeningBookMove).ifEmpty { null }\n\n"
    "    fun legalMoves(): List<String> =\n",
)
replace_once(
    kotlin_path,
    "        fun create(\n            transpositionTableMebibytes: Long = DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES,\n        ): ChessEngine {\n",
    "        fun create(\n"
    "            transpositionTableMebibytes: Long = DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES,\n"
    "        ): ChessEngine {\n",
)
replace_once(
    kotlin_path,
    "            return ChessEngine(\n                NativeHandleState(\n                    NativeChessEngineBindings.nativeCreate(transpositionTableMebibytes),\n                ),\n            )\n        }\n",
    "            return ChessEngine(\n"
    "                NativeHandleState(\n"
    "                    NativeChessEngineBindings.nativeCreate(transpositionTableMebibytes),\n"
    "                ),\n"
    "            )\n"
    "        }\n\n"
    "        fun createWithIndexedBook(\n"
    "            indexedBook: ByteArray,\n"
    "            transpositionTableMebibytes: Long = DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES,\n"
    "            openingBookEnabled: Boolean = true,\n"
    "        ): ChessEngine {\n"
    "            require(indexedBook.isNotEmpty()) { \"indexed opening-book bytes cannot be empty\" }\n"
    "            require(transpositionTableMebibytes > 0) {\n"
    "                \"transposition-table budget must be greater than zero\"\n"
    "            }\n"
    "            return ChessEngine(\n"
    "                NativeHandleState(\n"
    "                    NativeChessEngineBindings.nativeCreateWithIndexedBook(\n"
    "                        transpositionTableMebibytes,\n"
    "                        indexedBook,\n"
    "                        openingBookEnabled,\n"
    "                    ),\n"
    "                ),\n"
    "            )\n"
    "        }\n",
)
replace_once(
    kotlin_path,
    "    external fun nativeCreate(transpositionTableMebibytes: Long): Long\n",
    "    external fun nativeCreate(transpositionTableMebibytes: Long): Long\n"
    "    external fun nativeCreateWithIndexedBook(\n"
    "        transpositionTableMebibytes: Long,\n"
    "        indexedBook: ByteArray,\n"
    "        enabled: Boolean,\n"
    "    ): Long\n",
)
replace_once(
    kotlin_path,
    "    external fun nativeLegalMoves(handle: Long): String\n",
    "    external fun nativeOpeningBookMove(handle: Long): String\n"
    "    external fun nativeLegalMoves(handle: Long): String\n",
)

# JNI declaration contract includes the additive methods.
replace_once(
    "crates/chess-jni/tests/jni_contract.rs",
    "        \"nativeCreate\",\n        \"nativeDestroy\",\n",
    "        \"nativeCreate\",\n"
    "        \"nativeCreateWithIndexedBook\",\n"
    "        \"nativeDestroy\",\n",
)
replace_once(
    "crates/chess-jni/tests/jni_contract.rs",
    "        \"nativeFen\",\n        \"nativeLegalMoves\",\n",
    "        \"nativeFen\",\n"
    "        \"nativeOpeningBookMove\",\n"
    "        \"nativeLegalMoves\",\n",
)

# Android-only asset adapter example; shared Kotlin remains host-JVM compatible.
write(
    "android-harness/android-smoke/src/main/kotlin/com/ekkus93/chessengine/harness/ChessEngineAssetFactory.kt",
    "package com.ekkus93.chessengine.harness\n\n"
    "import android.content.Context\n"
    "import com.ekkus93.chessengine.ChessEngine\n\n"
    "/** Explicit Android adapter that supplies one packaged indexed book asset. */\n"
    "object ChessEngineAssetFactory {\n"
    "    fun create(\n"
    "        context: Context,\n"
    "        assetName: String = \"opening-book-v1.bin\",\n"
    "        transpositionTableMebibytes: Long = 1L,\n"
    "        openingBookEnabled: Boolean = true,\n"
    "    ): ChessEngine {\n"
    "        val bytes = context.assets.open(assetName).use { it.readBytes() }\n"
    "        return ChessEngine.createWithIndexedBook(\n"
    "            indexedBook = bytes,\n"
    "            transpositionTableMebibytes = transpositionTableMebibytes,\n"
    "            openingBookEnabled = openingBookEnabled,\n"
    "        )\n"
    "    }\n"
    "}\n",
)
replace_once(
    "android-harness/android-smoke/src/androidTest/kotlin/com/ekkus93/chessengine/harness/ChessEngineInstrumentedTest.kt",
    "import org.junit.Assert.assertNotEquals\n",
    "import org.junit.Assert.assertNotEquals\nimport org.junit.Assert.assertNull\n",
)
replace_once(
    "android-harness/android-smoke/src/androidTest/kotlin/com/ekkus93/chessengine/harness/ChessEngineInstrumentedTest.kt",
    "    @Test(timeout = 60_000L)\n    fun sampleMainThreadEntryRunsTheNativeCallOnTheWorker() {\n",
    "    @Test(timeout = 60_000L)\n"
    "    fun packagedIndexedBookAssetIsExplicitAndMissingEntriesFallThrough() {\n"
    "        val context = InstrumentationRegistry.getInstrumentation().targetContext\n"
    "        ChessEngineAssetFactory.create(context).use { engine ->\n"
    "            assertEquals(\"e2e4\", engine.openingBookMove())\n"
    "            engine.playMove(\"e2e4\")\n"
    "            assertNull(engine.openingBookMove())\n"
    "            val result = engine.search(SearchRequest(depth = 1)).await()\n"
    "            assertEquals(SearchTerminationKind.DEPTH, result.terminationKind)\n"
    "            assertTrue(result.bestMove in engine.legalMoves())\n"
    "        }\n\n"
    "        ChessEngine.create().use { engine ->\n"
    "            assertNull(engine.openingBookMove())\n"
    "            assertTrue(engine.search(SearchRequest(depth = 1)).await().bestMove != null)\n"
    "        }\n"
    "    }\n\n"
    "    @Test(timeout = 60_000L)\n"
    "    fun sampleMainThreadEntryRunsTheNativeCallOnTheWorker() {\n",
)

# Generate a deterministic one-record version-1 book asset for the starting position.
asset_path = ROOT / "android-harness/android-smoke/src/main/assets/opening-book-v1.bin"
asset_path.parent.mkdir(parents=True, exist_ok=True)
key = b"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -"
move = b"e2e4"
record = bytearray(104)
record[0] = len(key)
record[1] = len(move)
struct.pack_into("<H", record, 2, 0)
struct.pack_into("<I", record, 4, 100)
struct.pack_into("<I", record, 8, 0)
record[12 : 12 + len(key)] = key
record[96 : 96 + len(move)] = move
header = bytearray(64)
header[:8] = b"CHBKIDX\0"
struct.pack_into("<H", header, 8, 1)
struct.pack_into("<H", header, 10, 64)
struct.pack_into("<I", header, 12, 0x01020304)
struct.pack_into("<H", header, 16, 104)
struct.pack_into("<H", header, 18, 1)
struct.pack_into("<I", header, 20, 0)
struct.pack_into("<Q", header, 24, 1)
struct.pack_into("<Q", header, 32, len(record))
struct.pack_into("<I", header, 40, zlib.crc32(record) & 0xFFFFFFFF)
struct.pack_into("<I", header, 44, 0)
struct.pack_into("<I", header, 44, zlib.crc32(header) & 0xFFFFFFFF)
asset_path.write_bytes(bytes(header + record))

write(
    "docs/RUST_OPENING_BOOK_ADAPTER_INTEGRATION.md",
    "# Rust opening-book adapter integration\n\n"
    "Task 19.4 connects the validated Task 19.3 book policy to explicit adapter boundaries.\n\n"
    "## Safe Rust facade\n\n"
    "`EngineConfig` keeps opening books disabled by default and selects deterministic highest-weight policy unless a caller explicitly chooses a seeded weighted policy. `Engine::new` owns no book and operates normally. Callers may inject a validated `IndexedBook` or complete indexed-format bytes, then query `opening_book_move()` before normal search. Disabled configuration, absent data, and a valid book without a current-position record return `Ok(None)`. Corrupt data and legality/policy errors remain typed.\n\n"
    "## UCI adapter\n\n"
    "The binary advertises `OwnBook`, default `false`. A backend exists only when the process is launched with `--book <path>`; no current-directory, environment, or default-path discovery occurs. When `OwnBook` is true, a legal hit emits `bestmove` immediately. No configured file, disabled `OwnBook`, or no position entry continues through the unchanged worker search. Load and selection failures are fail visible.\n\n"
    "## C ABI, JNI, and Android asset example\n\n"
    "The ABI adds construction from explicit indexed bytes and a selected-book-move query without changing the version-1 config record. JNI and Kotlin expose `createWithIndexedBook` and `openingBookMove`. The Android harness demonstrates reading `opening-book-v1.bin` from `AssetManager` and supplying those bytes explicitly; the shared host-JVM wrapper has no Android dependency.\n\n"
    "## Deferred Task 19.5\n\n"
    "Task 19.5 retains broader malformed-book, legality, deterministic-seed, no-entry, disabled-book, and platform regression coverage plus the overall Task 19 completion gate.\n",
)

print("Task 19.4 patch applied")
