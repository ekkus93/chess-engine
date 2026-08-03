#![forbid(unsafe_code)]

use core::fmt;
use std::{error::Error, time::Duration};

use chess_book::{
    BookSelectionError, BookSelector, IndexedBook, IndexedBookError, IndexedBookQueryError,
};
use chess_core::{FenError, Game, GameError, GameStatus, MoveParseError, Position, UciMove};
use chess_search::{
    iterative_deepening_search_with_limits_and_transposition_table, EvaluationWeightSet,
    IterativeDeepeningSearchError, SearchLimitTermination, SearchLimits, SearchResult,
    SearchStopFlag, TranspositionTable, TranspositionTableAllocationError, WeightValidationError,
    DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES,
};

/// Semantic version of the safe Rust engine facade.
pub const ENGINE_VERSION: &str = env!("CARGO_PKG_VERSION");

/// Explicit opening-book policy selected by one engine configuration.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum OpeningBookSelection {
    /// Stable highest-weight selection with ascending-UCI tie resolution.
    DeterministicHighestWeight,
    /// Weighted selection from one explicit selector-local seed.
    WeightedRandom { seed: u64 },
}

impl OpeningBookSelection {
    fn selector(self) -> BookSelector {
        match self {
            Self::DeterministicHighestWeight => BookSelector::deterministic_highest_weight(),
            Self::WeightedRandom { seed } => BookSelector::weighted_random(seed),
        }
    }
}

/// Explicit construction configuration for one [`Engine`].
///
/// Configuration is copied into the engine at construction. It contains no
/// filesystem paths, environment-variable hooks, process globals, or implicit
/// discovery behavior.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct EngineConfig {
    transposition_table_mebibytes: usize,
    opening_book_enabled: bool,
    opening_book_selection: OpeningBookSelection,
}

impl EngineConfig {
    /// Creates the deterministic default configuration.
    #[must_use]
    pub const fn new() -> Self {
        Self {
            transposition_table_mebibytes: DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES,
            opening_book_enabled: false,
            opening_book_selection: OpeningBookSelection::DeterministicHighestWeight,
        }
    }

    /// Selects the fixed transposition-table budget in mebibytes.
    ///
    /// Allocation is attempted by [`Engine::new`] and failures are returned as
    /// [`EngineError::TranspositionTableAllocation`].
    #[must_use]
    pub const fn with_transposition_table_mebibytes(mut self, mebibytes: usize) -> Self {
        self.transposition_table_mebibytes = mebibytes;
        self
    }

    /// Enables or disables use of explicitly supplied opening-book data.
    #[must_use]
    pub const fn with_opening_book_enabled(mut self, enabled: bool) -> Self {
        self.opening_book_enabled = enabled;
        self
    }

    /// Selects deterministic highest-weight opening-book policy.
    #[must_use]
    pub const fn with_deterministic_opening_book(mut self) -> Self {
        self.opening_book_selection = OpeningBookSelection::DeterministicHighestWeight;
        self
    }

    /// Selects weighted opening-book policy from an explicit local seed.
    #[must_use]
    pub const fn with_weighted_opening_book(mut self, seed: u64) -> Self {
        self.opening_book_selection = OpeningBookSelection::WeightedRandom { seed };
        self
    }

    /// Returns the configured fixed transposition-table budget.
    #[must_use]
    pub const fn transposition_table_mebibytes(self) -> usize {
        self.transposition_table_mebibytes
    }

    /// Returns whether explicitly supplied opening-book data may be queried.
    #[must_use]
    pub const fn opening_book_enabled(self) -> bool {
        self.opening_book_enabled
    }

    /// Returns the explicit opening-book selection policy.
    #[must_use]
    pub const fn opening_book_selection(self) -> OpeningBookSelection {
        self.opening_book_selection
    }
}

impl Default for EngineConfig {
    fn default() -> Self {
        Self::new()
    }
}

/// Stable identity of the evaluation weights used by this engine instance.
///
/// Task 18.1 reports the built-in baseline evaluator honestly. The facade does
/// not advertise caller-supplied weights until production search supports using
/// them throughout the complete search path.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct EvaluationWeightIdentity {
    schema_version: u16,
    identifier: u64,
    checksum: u64,
}

impl EvaluationWeightIdentity {
    fn from_set(set: EvaluationWeightSet) -> Self {
        Self {
            schema_version: set.schema_version,
            identifier: set.identifier,
            checksum: set.checksum,
        }
    }

    /// Returns the versioned serialized weight schema.
    #[must_use]
    pub const fn schema_version(self) -> u16 {
        self.schema_version
    }

    /// Returns the stable weight-set identifier.
    #[must_use]
    pub const fn identifier(self) -> u64 {
        self.identifier
    }

    /// Returns the canonical checksum over schema, identifier, and values.
    #[must_use]
    pub const fn checksum(self) -> u64 {
        self.checksum
    }
}

/// Thread-safe, request-local cancellation signal for a synchronous search.
///
/// Clone this handle before starting [`Engine::search`] on a worker thread, then
/// call [`Self::cancel`] from another thread. Clones share one atomic stop state.
/// A handle is not reset automatically; callers should normally create one per
/// request, or call [`Self::reset`] explicitly before intentional reuse.
#[derive(Clone, Debug, Default)]
pub struct SearchCancellationHandle {
    stop_flag: SearchStopFlag,
}

impl SearchCancellationHandle {
    /// Creates a clear cancellation handle.
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    /// Requests an orderly stop at the next bounded search checkpoint.
    pub fn cancel(&self) {
        self.stop_flag.request_stop();
    }

    /// Clears a previously requested stop before intentional handle reuse.
    pub fn reset(&self) {
        self.stop_flag.reset();
    }

    /// Returns whether cancellation has been requested.
    #[must_use]
    pub fn is_cancelled(&self) -> bool {
        self.stop_flag.is_stop_requested()
    }
}

/// Typed facade-owned limits for one synchronous search request.
///
/// Builders delegate to the authoritative `chess-search` limit contract. An
/// invalid or incomplete combination is rejected by [`Engine::search`] before
/// the engine's game state is touched.
#[derive(Clone, Debug)]
pub struct SearchRequest {
    limits: SearchLimits,
}

impl SearchRequest {
    /// Creates an incomplete finite request that must receive an automatic limit.
    #[must_use]
    pub const fn new() -> Self {
        Self {
            limits: SearchLimits::new(),
        }
    }

    /// Creates an explicit infinite request bound to a cancellation handle.
    #[must_use]
    pub fn infinite(cancellation: &SearchCancellationHandle) -> Self {
        Self {
            limits: SearchLimits::new()
                .infinite()
                .with_stop_flag(cancellation.stop_flag.clone()),
        }
    }

    /// Adds a maximum completed depth.
    #[must_use]
    pub fn with_depth(mut self, depth: u16) -> Self {
        self.limits = self.limits.with_depth(depth);
        self
    }

    /// Adds a hard cumulative node budget.
    #[must_use]
    pub fn with_nodes(mut self, nodes: u64) -> Self {
        self.limits = self.limits.with_nodes(nodes);
        self
    }

    /// Adds a soft time budget checked after completed iterations.
    #[must_use]
    pub fn with_soft_time(mut self, soft_time: Duration) -> Self {
        self.limits = self.limits.with_soft_time(soft_time);
        self
    }

    /// Adds a hard time budget checked inside the production search tree.
    #[must_use]
    pub fn with_hard_time(mut self, hard_time: Duration) -> Self {
        self.limits = self.limits.with_hard_time(hard_time);
        self
    }

    /// Adds a request-local explicit cancellation signal.
    #[must_use]
    pub fn with_cancellation(mut self, cancellation: &SearchCancellationHandle) -> Self {
        self.limits = self.limits.with_stop_flag(cancellation.stop_flag.clone());
        self
    }

    /// Enables the optional bounded one-ply-per-line check extension.
    #[must_use]
    pub fn with_check_extension(mut self) -> Self {
        self.limits = self.limits.with_check_extension();
        self
    }

    /// Returns the requested depth limit.
    #[must_use]
    pub const fn depth(&self) -> Option<u16> {
        self.limits.depth()
    }

    /// Returns the requested node limit.
    #[must_use]
    pub const fn nodes(&self) -> Option<u64> {
        self.limits.nodes()
    }

    /// Returns the requested soft time limit.
    #[must_use]
    pub const fn soft_time(&self) -> Option<Duration> {
        self.limits.soft_time()
    }

    /// Returns the requested hard time limit.
    #[must_use]
    pub const fn hard_time(&self) -> Option<Duration> {
        self.limits.hard_time()
    }

    /// Returns whether this is explicit infinite-search mode.
    #[must_use]
    pub const fn is_infinite(&self) -> bool {
        self.limits.is_infinite()
    }

    /// Returns whether the bounded check extension is enabled.
    #[must_use]
    pub const fn check_extension_enabled(&self) -> bool {
        self.limits.check_extension_enabled()
    }

    fn into_limits(self) -> SearchLimits {
        self.limits
    }
}

impl Default for SearchRequest {
    fn default() -> Self {
        Self::new()
    }
}

/// Fail-loud error returned by the safe engine facade.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum EngineError {
    /// Strict six-field FEN parsing failed.
    InvalidFen(FenError),
    /// UCI coordinate-move syntax was malformed.
    InvalidMoveSyntax(MoveParseError),
    /// Syntactically valid UCI text did not identify a current legal move.
    IllegalMove { value: String },
    /// Rule or game-history processing failed.
    Game(GameError),
    /// Search or search-limit processing failed.
    Search(IterativeDeepeningSearchError),
    /// Fixed transposition-table configuration or allocation failed.
    TranspositionTableAllocation(TranspositionTableAllocationError),
    /// The built-in evaluation identity failed its own validation contract.
    InvalidWeightSet(WeightValidationError),
    /// Explicitly supplied indexed opening-book bytes were invalid.
    InvalidOpeningBook(IndexedBookError),
    /// Opening-book lookup, legality validation, or selection failed.
    OpeningBookSelection(BookSelectionError<IndexedBookQueryError>),
    /// Reserving the bounded legal-move output vector failed.
    LegalMoveStorageAllocation { move_count: usize },
}

impl fmt::Display for EngineError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InvalidFen(error) => write!(formatter, "invalid position FEN: {error}"),
            Self::InvalidMoveSyntax(error) => write!(formatter, "invalid UCI move: {error}"),
            Self::IllegalMove { value } => write!(
                formatter,
                "UCI move {value:?} is not legal in the current position"
            ),
            Self::Game(error) => error.fmt(formatter),
            Self::Search(error) => error.fmt(formatter),
            Self::TranspositionTableAllocation(error) => error.fmt(formatter),
            Self::InvalidWeightSet(error) => error.fmt(formatter),
            Self::InvalidOpeningBook(error) => write!(formatter, "invalid opening book: {error}"),
            Self::OpeningBookSelection(error) => error.fmt(formatter),
            Self::LegalMoveStorageAllocation { move_count } => write!(
                formatter,
                "failed to reserve storage for {move_count} legal moves"
            ),
        }
    }
}

impl Error for EngineError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::InvalidFen(error) => Some(error),
            Self::InvalidMoveSyntax(error) => Some(error),
            Self::Game(error) => Some(error),
            Self::Search(error) => Some(error),
            Self::TranspositionTableAllocation(error) => Some(error),
            Self::InvalidWeightSet(error) => Some(error),
            Self::InvalidOpeningBook(error) => Some(error),
            Self::OpeningBookSelection(error) => Some(error),
            Self::IllegalMove { .. } | Self::LegalMoveStorageAllocation { .. } => None,
        }
    }
}

impl From<FenError> for EngineError {
    fn from(value: FenError) -> Self {
        Self::InvalidFen(value)
    }
}

impl From<MoveParseError> for EngineError {
    fn from(value: MoveParseError) -> Self {
        Self::InvalidMoveSyntax(value)
    }
}

impl From<GameError> for EngineError {
    fn from(value: GameError) -> Self {
        Self::Game(value)
    }
}

impl From<IterativeDeepeningSearchError> for EngineError {
    fn from(value: IterativeDeepeningSearchError) -> Self {
        Self::Search(value)
    }
}

impl From<TranspositionTableAllocationError> for EngineError {
    fn from(value: TranspositionTableAllocationError) -> Self {
        Self::TranspositionTableAllocation(value)
    }
}

impl From<WeightValidationError> for EngineError {
    fn from(value: WeightValidationError) -> Self {
        Self::InvalidWeightSet(value)
    }
}

impl From<IndexedBookError> for EngineError {
    fn from(value: IndexedBookError) -> Self {
        Self::InvalidOpeningBook(value)
    }
}

impl From<BookSelectionError<IndexedBookQueryError>> for EngineError {
    fn from(value: BookSelectionError<IndexedBookQueryError>) -> Self {
        Self::OpeningBookSelection(value)
    }
}

/// Stateful, process-independent safe Rust facade over rules and search.
///
/// # Ownership
///
/// An `Engine` exclusively owns one [`Game`] and one fixed-capacity
/// [`TranspositionTable`]. It borrows no caller memory and opens no files.
/// Position replacement discards prior played-move history and clears table
/// entries while retaining the bounded allocation.
///
/// # Thread safety
///
/// The facade starts no threads and provides no internal locking. Stateful
/// methods require `&mut self`, so one engine cannot be searched or mutated
/// concurrently through safe Rust without caller-provided synchronization.
/// `Engine` may be moved to a worker thread. Search is synchronous; another
/// thread may request cancellation through a cloned [`SearchCancellationHandle`].
/// No manual `Send` or `Sync` implementation is used.
#[derive(Debug)]
pub struct Engine {
    config: EngineConfig,
    game: Game,
    transposition_table: TranspositionTable,
    weight_identity: EvaluationWeightIdentity,
    opening_book: Option<IndexedBook>,
    book_selector: BookSelector,
}

impl Engine {
    /// Constructs an engine without opening-book data.
    ///
    /// Opening-book enablement may remain configured, but absence of data is
    /// normal and [`Self::opening_book_move`] returns `Ok(None)`.
    pub fn new(config: EngineConfig) -> Result<Self, EngineError> {
        Self::new_with_opening_book(config, None)
    }

    /// Constructs an engine with an explicitly supplied validated indexed book.
    pub fn new_with_opening_book(
        config: EngineConfig,
        opening_book: Option<IndexedBook>,
    ) -> Result<Self, EngineError> {
        let weight_set = EvaluationWeightSet::baseline();
        weight_set.validate()?;
        let transposition_table = TranspositionTable::new(config.transposition_table_mebibytes())?;
        let book_selector = config.opening_book_selection().selector();
        Ok(Self {
            config,
            game: Game::starting(),
            transposition_table,
            weight_identity: EvaluationWeightIdentity::from_set(weight_set),
            opening_book,
            book_selector,
        })
    }

    /// Parses and injects one complete versioned indexed-book byte image.
    pub fn new_with_indexed_book_bytes(
        config: EngineConfig,
        bytes: &[u8],
    ) -> Result<Self, EngineError> {
        let opening_book = IndexedBook::from_bytes(bytes)?;
        Self::new_with_opening_book(config, Some(opening_book))
    }

    /// Returns the immutable construction configuration.
    #[must_use]
    pub const fn config(&self) -> EngineConfig {
        self.config
    }

    /// Returns the safe facade's semantic version.
    #[must_use]
    pub const fn version() -> &'static str {
        ENGINE_VERSION
    }

    /// Returns the exact evaluation-weight identity used by production search.
    #[must_use]
    pub const fn weight_identity(&self) -> EvaluationWeightIdentity {
        self.weight_identity
    }

    /// Replaces the game with the standard starting position and fresh history.
    pub fn reset_position(&mut self) {
        self.game.reset_to_starting();
        self.transposition_table.clear();
    }

    /// Transactionally replaces the root with a strict playable six-field FEN.
    ///
    /// Parsing and validation finish before either game history or transposition
    /// entries are changed.
    pub fn set_position(&mut self, fen: &str) -> Result<(), EngineError> {
        let position = Position::from_fen(fen)?;
        self.game.set_position(position);
        self.transposition_table.clear();
        Ok(())
    }

    /// Returns canonical six-field FEN for the current played position.
    #[must_use]
    pub fn fen(&self) -> String {
        self.game.position().to_fen()
    }

    /// Returns every legal move in deterministic canonical UCI notation.
    pub fn legal_moves(&mut self) -> Result<Vec<String>, EngineError> {
        let legal_moves = self.game.legal_moves()?;
        let move_count = legal_moves.len();
        let mut output = Vec::new();
        output
            .try_reserve_exact(move_count)
            .map_err(|_| EngineError::LegalMoveStorageAllocation { move_count })?;
        output.extend(legal_moves.iter().map(|current| current.to_uci()));
        Ok(output)
    }

    /// Plays one exact current legal move expressed in UCI notation.
    ///
    /// Malformed or illegal input leaves the game, history, and position FEN
    /// unchanged. Automatic terminal positions reject further moves explicitly.
    pub fn play_move(&mut self, value: &str) -> Result<(), EngineError> {
        let syntax = value.parse::<UciMove>()?;
        let status = self.game.status()?;
        if status.is_terminal() {
            return Err(GameError::GameOver { status }.into());
        }
        let legal_moves = self.game.legal_moves()?;
        let current = legal_moves
            .iter()
            .find(|candidate| syntax.matches(*candidate))
            .ok_or_else(|| EngineError::IllegalMove {
                value: value.to_owned(),
            })?;
        self.game.make_move(current)?;
        Ok(())
    }

    /// Returns the current rule-level game status.
    pub fn game_status(&mut self) -> Result<GameStatus, EngineError> {
        self.game.status().map_err(EngineError::from)
    }

    /// Returns one selected legal opening-book move for the current position.
    ///
    /// Disabled configuration, absent explicitly supplied data, and a valid
    /// book with no current-position entry all return `Ok(None)`. Backend,
    /// legality, and policy failures remain typed and never fall through.
    pub fn opening_book_move(&mut self) -> Result<Option<String>, EngineError> {
        if !self.config.opening_book_enabled() {
            return Ok(None);
        }
        let Some(opening_book) = self.opening_book.as_ref() else {
            return Ok(None);
        };
        self.book_selector
            .select(opening_book, self.game.position())
            .map(|selected| selected.map(|current| current.chess_move().to_uci()))
            .map_err(EngineError::from)
    }

    /// Runs one synchronous limit-controlled search without mutating played state.
    ///
    /// The current position and repetition history are cloned into a detached
    /// search root. The engine reuses its bounded transposition-table allocation,
    /// while the owned game, canonical FEN, move history, and rule status remain
    /// unchanged on success, cancellation, and error paths.
    pub fn search(&mut self, request: SearchRequest) -> Result<SearchResult, EngineError> {
        let mut position = self.game.position().clone();
        let mut history = self.game.search_history();
        iterative_deepening_search_with_limits_and_transposition_table(
            &mut position,
            &mut history,
            request.into_limits(),
            &mut self.transposition_table,
        )
        .map_err(EngineError::from)
    }

    /// Returns the winning termination reason from a completed facade search.
    #[must_use]
    pub const fn search_termination(result: &SearchResult) -> SearchLimitTermination {
        result.termination()
    }
}
