//! Deterministic offline self-play generation and versioned dataset tooling.

use core::{fmt, str::FromStr};
use std::{
    collections::{HashMap, HashSet},
    fmt::Write as _,
    time::Duration,
};

use chess_core::{Color, DrawReason, Game, GameStatus, Move, Position, UciMove};
use chess_search::{
    iterative_deepening_search_with_limits_and_transposition_table, EvaluationWeightSet,
    SearchLimits, TranspositionTable,
};

use super::ToolError;

/// Version of the strict self-play configuration file.
pub const SELF_PLAY_CONFIG_SCHEMA_VERSION: u16 = 1;
/// Version of the explicit opening-suite file.
pub const SELF_PLAY_OPENING_SCHEMA_VERSION: u16 = 1;
/// Version of the generated game-and-position dataset.
pub const SELF_PLAY_DATASET_SCHEMA_VERSION: u16 = 1;
/// Semantic engine version recorded in generated provenance.
pub const SELF_PLAY_ENGINE_VERSION: &str = env!("CARGO_PKG_VERSION");

const MAX_SELF_PLAY_GAMES: u32 = 100_000;
const MAX_SELF_PLAY_PLIES: u32 = 4_096;

/// One fixed search-limit mode used by a self-play side.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SelfPlayLimit {
    /// Complete iterative deepening through this depth.
    Depth(u16),
    /// Stop after this cumulative node budget.
    Nodes(u64),
    /// Stop after this hard wall-clock budget in milliseconds.
    TimeMilliseconds(u64),
}

impl SelfPlayLimit {
    fn search_limits(self) -> SearchLimits {
        match self {
            Self::Depth(depth) => SearchLimits::new().with_depth(depth),
            Self::Nodes(nodes) => SearchLimits::new().with_nodes(nodes),
            Self::TimeMilliseconds(milliseconds) => {
                SearchLimits::new().with_hard_time(Duration::from_millis(milliseconds))
            }
        }
    }

    fn validate(self) -> Result<(), ToolError> {
        self.search_limits()
            .validate()
            .map_err(|error| ToolError::new(error.to_string()))
    }
}

impl fmt::Display for SelfPlayLimit {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Depth(depth) => write!(formatter, "depth:{depth}"),
            Self::Nodes(nodes) => write!(formatter, "nodes:{nodes}"),
            Self::TimeMilliseconds(milliseconds) => {
                write!(formatter, "time_ms:{milliseconds}")
            }
        }
    }
}

impl FromStr for SelfPlayLimit {
    type Err = ToolError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        let (kind, number) = value
            .split_once(':')
            .ok_or_else(|| ToolError::new(format!("invalid self-play limit {value:?}")))?;
        let limit = match kind {
            "depth" => Self::Depth(parse_number(number, "depth limit")?),
            "nodes" => Self::Nodes(parse_number(number, "node limit")?),
            "time_ms" => Self::TimeMilliseconds(parse_number(number, "time limit")?),
            _ => {
                return Err(ToolError::new(format!(
                    "unsupported self-play limit kind {kind:?}"
                )))
            }
        };
        limit.validate()?;
        Ok(limit)
    }
}

/// Independent search configuration for one color.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct SelfPlaySideConfig {
    transposition_table_mebibytes: usize,
    limit: SelfPlayLimit,
    check_extension: bool,
}

impl SelfPlaySideConfig {
    /// Creates one side configuration.
    #[must_use]
    pub const fn new(transposition_table_mebibytes: usize, limit: SelfPlayLimit) -> Self {
        Self {
            transposition_table_mebibytes,
            limit,
            check_extension: false,
        }
    }

    /// Enables the bounded one-ply-per-line check extension for this side.
    #[must_use]
    pub const fn with_check_extension(mut self, enabled: bool) -> Self {
        self.check_extension = enabled;
        self
    }

    /// Returns the fixed transposition-table budget.
    #[must_use]
    pub const fn transposition_table_mebibytes(self) -> usize {
        self.transposition_table_mebibytes
    }

    /// Returns this side's fixed search limit.
    #[must_use]
    pub const fn limit(self) -> SelfPlayLimit {
        self.limit
    }

    /// Returns whether bounded check extension is enabled.
    #[must_use]
    pub const fn check_extension_enabled(self) -> bool {
        self.check_extension
    }

    fn search_limits(self) -> SearchLimits {
        let limits = self.limit.search_limits();
        if self.check_extension {
            limits.with_check_extension()
        } else {
            limits
        }
    }

    fn validate(self) -> Result<(), ToolError> {
        if self.transposition_table_mebibytes == 0 {
            return Err(ToolError::new(
                "self-play transposition-table budget must be at least one MiB",
            ));
        }
        self.limit.validate()
    }
}

/// Policy for claimable threefold- and fifty-move draws.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ClaimableDrawPolicy {
    /// End the game immediately when a claim becomes available.
    Accept,
    /// Continue until an automatic terminal state or the maximum-ply boundary.
    Continue,
}

impl fmt::Display for ClaimableDrawPolicy {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::Accept => "accept",
            Self::Continue => "continue",
        })
    }
}

impl FromStr for ClaimableDrawPolicy {
    type Err = ToolError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        match value {
            "accept" => Ok(Self::Accept),
            "continue" => Ok(Self::Continue),
            _ => Err(ToolError::new(format!(
                "invalid claimable-draw policy {value:?}"
            ))),
        }
    }
}

/// Dataset treatment for positions supplied by the opening source.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum OpeningPositionPolicy {
    /// Omit every position before the first engine-selected move.
    Exclude,
    /// Retain opening positions but mark them ineligible for training.
    Mark,
}

impl fmt::Display for OpeningPositionPolicy {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::Exclude => "exclude",
            Self::Mark => "mark",
        })
    }
}

impl FromStr for OpeningPositionPolicy {
    type Err = ToolError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        match value {
            "exclude" => Ok(Self::Exclude),
            "mark" => Ok(Self::Mark),
            _ => Err(ToolError::new(format!(
                "invalid opening-position policy {value:?}"
            ))),
        }
    }
}

/// Explicit dataset partition.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum DatasetSplit {
    /// Training partition.
    Train,
    /// Validation partition.
    Validation,
    /// Held-out test partition.
    Test,
}

impl fmt::Display for DatasetSplit {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::Train => "train",
            Self::Validation => "validation",
            Self::Test => "test",
        })
    }
}

impl FromStr for DatasetSplit {
    type Err = ToolError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        match value {
            "train" => Ok(Self::Train),
            "validation" => Ok(Self::Validation),
            "test" => Ok(Self::Test),
            _ => Err(ToolError::new(format!("invalid dataset split {value:?}"))),
        }
    }
}

/// Percent allocation for deterministic train, validation, and test splits.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct DatasetSplitPercentages {
    train: u8,
    validation: u8,
    test: u8,
}

impl DatasetSplitPercentages {
    /// Creates an explicit three-way split.
    pub fn new(train: u8, validation: u8, test: u8) -> Result<Self, ToolError> {
        let value = Self {
            train,
            validation,
            test,
        };
        value.validate()?;
        Ok(value)
    }

    /// Returns the training percentage.
    #[must_use]
    pub const fn train(self) -> u8 {
        self.train
    }

    /// Returns the validation percentage.
    #[must_use]
    pub const fn validation(self) -> u8 {
        self.validation
    }

    /// Returns the test percentage.
    #[must_use]
    pub const fn test(self) -> u8 {
        self.test
    }

    fn validate(self) -> Result<(), ToolError> {
        if self.train == 0 || self.validation == 0 || self.test == 0 {
            return Err(ToolError::new(
                "train, validation, and test percentages must all be nonzero",
            ));
        }
        let total = u16::from(self.train) + u16::from(self.validation) + u16::from(self.test);
        if total != 100 {
            return Err(ToolError::new(format!(
                "dataset split percentages must total 100, found {total}"
            )));
        }
        Ok(())
    }

    fn assign(self, game_seed: u64) -> DatasetSplit {
        let bucket = (splitmix64(game_seed ^ 0x27d4_eb2f_1656_67c5) % 100) as u8;
        if bucket < self.train {
            DatasetSplit::Train
        } else if bucket < self.train + self.validation {
            DatasetSplit::Validation
        } else {
            DatasetSplit::Test
        }
    }
}

impl Default for DatasetSplitPercentages {
    fn default() -> Self {
        Self {
            train: 80,
            validation: 10,
            test: 10,
        }
    }
}

/// Fully explicit configuration for one self-play batch.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SelfPlayConfig {
    game_count: u32,
    seed: u64,
    white: SelfPlaySideConfig,
    black: SelfPlaySideConfig,
    maximum_plies: u32,
    claimable_draw_policy: ClaimableDrawPolicy,
    opening_position_policy: OpeningPositionPolicy,
    splits: DatasetSplitPercentages,
}

impl SelfPlayConfig {
    /// Creates a deterministic configuration with conservative default policies.
    #[must_use]
    pub fn new(
        game_count: u32,
        seed: u64,
        white: SelfPlaySideConfig,
        black: SelfPlaySideConfig,
    ) -> Self {
        Self {
            game_count,
            seed,
            white,
            black,
            maximum_plies: 256,
            claimable_draw_policy: ClaimableDrawPolicy::Accept,
            opening_position_policy: OpeningPositionPolicy::Exclude,
            splits: DatasetSplitPercentages::default(),
        }
    }

    /// Selects the total maximum ply count, including supplied opening moves.
    #[must_use]
    pub const fn with_maximum_plies(mut self, maximum_plies: u32) -> Self {
        self.maximum_plies = maximum_plies;
        self
    }

    /// Selects how claimable draws end games.
    #[must_use]
    pub const fn with_claimable_draw_policy(mut self, policy: ClaimableDrawPolicy) -> Self {
        self.claimable_draw_policy = policy;
        self
    }

    /// Selects how opening positions enter the dataset.
    #[must_use]
    pub const fn with_opening_position_policy(mut self, policy: OpeningPositionPolicy) -> Self {
        self.opening_position_policy = policy;
        self
    }

    /// Selects deterministic dataset split percentages.
    #[must_use]
    pub const fn with_splits(mut self, splits: DatasetSplitPercentages) -> Self {
        self.splits = splits;
        self
    }

    /// Returns the requested number of games.
    #[must_use]
    pub const fn game_count(&self) -> u32 {
        self.game_count
    }

    /// Returns the batch seed.
    #[must_use]
    pub const fn seed(&self) -> u64 {
        self.seed
    }

    /// Returns White's independent engine configuration.
    #[must_use]
    pub const fn white(&self) -> SelfPlaySideConfig {
        self.white
    }

    /// Returns Black's independent engine configuration.
    #[must_use]
    pub const fn black(&self) -> SelfPlaySideConfig {
        self.black
    }

    /// Returns the maximum total game length in plies.
    #[must_use]
    pub const fn maximum_plies(&self) -> u32 {
        self.maximum_plies
    }

    /// Returns the claimable-draw policy.
    #[must_use]
    pub const fn claimable_draw_policy(&self) -> ClaimableDrawPolicy {
        self.claimable_draw_policy
    }

    /// Returns the opening-position dataset policy.
    #[must_use]
    pub const fn opening_position_policy(&self) -> OpeningPositionPolicy {
        self.opening_position_policy
    }

    /// Returns deterministic partition percentages.
    #[must_use]
    pub const fn splits(&self) -> DatasetSplitPercentages {
        self.splits
    }

    fn validate_basic(&self) -> Result<(), ToolError> {
        if self.game_count == 0 || self.game_count > MAX_SELF_PLAY_GAMES {
            return Err(ToolError::new(format!(
                "self-play game count must be between 1 and {MAX_SELF_PLAY_GAMES}, found {}",
                self.game_count
            )));
        }
        if self.maximum_plies == 0 || self.maximum_plies > MAX_SELF_PLAY_PLIES {
            return Err(ToolError::new(format!(
                "self-play maximum plies must be between 1 and {MAX_SELF_PLAY_PLIES}, found {}",
                self.maximum_plies
            )));
        }
        self.white.validate()?;
        self.black.validate()?;
        self.splits.validate()
    }

    fn validate_with_openings(&self, openings: &OpeningSuite) -> Result<(), ToolError> {
        self.validate_basic()?;
        openings.validate()?;
        for opening in openings.lines() {
            let opening_plies = u32::try_from(opening.moves.len())
                .map_err(|_| ToolError::new("opening move count exceeds u32"))?;
            if opening_plies >= self.maximum_plies {
                return Err(ToolError::new(format!(
                    "opening {:?} has {opening_plies} plies but maximum_plies is {}",
                    opening.identifier, self.maximum_plies
                )));
            }
            if self.claimable_draw_policy == ClaimableDrawPolicy::Accept {
                let mut game = opening.instantiate()?;
                let status = game
                    .status()
                    .map_err(|error| ToolError::new(error.to_string()))?;
                if matches!(status, GameStatus::ClaimableDraw(_)) {
                    return Err(ToolError::new(format!(
                        "opening {:?} already reaches an accepted claimable draw",
                        opening.identifier
                    )));
                }
            }
        }
        Ok(())
    }
}

/// Parsed self-play configuration plus its explicitly named opening source.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SelfPlayFileConfig {
    config: SelfPlayConfig,
    opening_path: String,
}

impl SelfPlayFileConfig {
    /// Strictly parses a version-1 key/value configuration file.
    pub fn from_text(text: &str) -> Result<Self, ToolError> {
        let mut values = HashMap::new();
        for (line_index, line) in text.lines().enumerate() {
            let trimmed = line.trim();
            if trimmed.is_empty() || trimmed.starts_with('#') {
                continue;
            }
            let (key, value) = trimmed.split_once('=').ok_or_else(|| {
                ToolError::new(format!(
                    "self-play config line {} is not key=value",
                    line_index + 1
                ))
            })?;
            if !is_config_key(key) {
                return Err(ToolError::new(format!(
                    "unknown self-play config key {key:?}"
                )));
            }
            if values.insert(key.to_owned(), value.to_owned()).is_some() {
                return Err(ToolError::new(format!(
                    "duplicate self-play config key {key:?}"
                )));
            }
        }

        let schema: u16 = parse_number(&take_required(&mut values, "schema")?, "schema")?;
        if schema != SELF_PLAY_CONFIG_SCHEMA_VERSION {
            return Err(ToolError::new(format!(
                "unsupported self-play config schema {schema}"
            )));
        }
        let game_count = parse_number(&take_required(&mut values, "games")?, "games")?;
        let seed = parse_number(&take_required(&mut values, "seed")?, "seed")?;
        let maximum_plies = parse_number(
            &take_required(&mut values, "maximum_plies")?,
            "maximum_plies",
        )?;
        let white = parse_side_config(&mut values, "white")?;
        let black = parse_side_config(&mut values, "black")?;
        let claimable_draw_policy = take_required(&mut values, "claimable_draw")?.parse()?;
        let opening_position_policy = take_required(&mut values, "opening_positions")?.parse()?;
        let splits = DatasetSplitPercentages::new(
            parse_number(&take_required(&mut values, "split_train")?, "split_train")?,
            parse_number(
                &take_required(&mut values, "split_validation")?,
                "split_validation",
            )?,
            parse_number(&take_required(&mut values, "split_test")?, "split_test")?,
        )?;
        let opening_path = take_required(&mut values, "opening_path")?;
        validate_text_field("opening_path", &opening_path)?;
        if opening_path.is_empty() {
            return Err(ToolError::new("opening_path must not be empty"));
        }
        if !values.is_empty() {
            return Err(ToolError::new("unconsumed self-play configuration keys"));
        }

        let config = SelfPlayConfig::new(game_count, seed, white, black)
            .with_maximum_plies(maximum_plies)
            .with_claimable_draw_policy(claimable_draw_policy)
            .with_opening_position_policy(opening_position_policy)
            .with_splits(splits);
        config.validate_basic()?;
        Ok(Self {
            config,
            opening_path,
        })
    }

    /// Returns the complete non-I/O configuration.
    #[must_use]
    pub const fn config(&self) -> &SelfPlayConfig {
        &self.config
    }

    /// Returns the explicitly supplied opening-suite path.
    #[must_use]
    pub fn opening_path(&self) -> &str {
        &self.opening_path
    }
}

/// One validated opening line selected by identifier.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct OpeningLine {
    identifier: String,
    initial_fen: String,
    moves: Vec<String>,
}

impl OpeningLine {
    /// Returns the stable opening identifier.
    #[must_use]
    pub fn identifier(&self) -> &str {
        &self.identifier
    }

    /// Returns the canonical initial six-field FEN.
    #[must_use]
    pub fn initial_fen(&self) -> &str {
        &self.initial_fen
    }

    /// Returns the canonical legal UCI opening moves.
    #[must_use]
    pub fn moves(&self) -> &[String] {
        &self.moves
    }

    fn instantiate(&self) -> Result<Game, ToolError> {
        let position = Position::from_fen(&self.initial_fen)
            .map_err(|error| ToolError::new(error.to_string()))?;
        let mut game = Game::new(position);
        for value in &self.moves {
            let current = resolve_game_uci(&mut game, value)?;
            game.make_move(current)
                .map_err(|error| ToolError::new(error.to_string()))?;
        }
        Ok(game)
    }
}

/// Explicit versioned opening diversification source.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct OpeningSuite {
    lines: Vec<OpeningLine>,
}

impl OpeningSuite {
    /// Parses and validates a complete opening-suite text image.
    pub fn from_text(text: &str) -> Result<Self, ToolError> {
        let mut lines = text.lines();
        let header = lines
            .next()
            .ok_or_else(|| ToolError::new("opening suite is empty"))?;
        let expected_header =
            format!("CHESS_SELF_PLAY_OPENINGS\t{SELF_PLAY_OPENING_SCHEMA_VERSION}");
        if header != expected_header {
            return Err(ToolError::new(format!(
                "invalid opening-suite header {header:?}"
            )));
        }

        let mut parsed = Vec::new();
        let mut identifiers = HashSet::new();
        for (line_index, line) in lines.enumerate() {
            if line.is_empty() || line.starts_with('#') {
                continue;
            }
            let fields = exact_fields(line, 3, "opening row")?;
            let identifier = fields[0];
            validate_identifier(identifier)?;
            if !identifiers.insert(identifier.to_owned()) {
                return Err(ToolError::new(format!(
                    "duplicate opening identifier {identifier:?}"
                )));
            }
            let position = Position::from_fen(fields[1]).map_err(|error| {
                ToolError::new(format!(
                    "opening row {} has invalid FEN: {error}",
                    line_index + 2
                ))
            })?;
            let canonical_fen = position.to_fen();
            let mut game = Game::new(position);
            let mut canonical_moves = Vec::new();
            if fields[2] != "-" {
                for value in fields[2].split_ascii_whitespace() {
                    let current = resolve_game_uci(&mut game, value)?;
                    canonical_moves.push(current.to_uci());
                    game.make_move(current)
                        .map_err(|error| ToolError::new(error.to_string()))?;
                }
            }
            let status = game
                .status()
                .map_err(|error| ToolError::new(error.to_string()))?;
            if status.is_terminal() {
                return Err(ToolError::new(format!(
                    "opening {identifier:?} ends in terminal status {status:?}"
                )));
            }
            parsed.push(OpeningLine {
                identifier: identifier.to_owned(),
                initial_fen: canonical_fen,
                moves: canonical_moves,
            });
        }
        let suite = Self { lines: parsed };
        suite.validate()?;
        Ok(suite)
    }

    /// Returns every validated opening line in source order.
    #[must_use]
    pub fn lines(&self) -> &[OpeningLine] {
        &self.lines
    }

    fn validate(&self) -> Result<(), ToolError> {
        if self.lines.is_empty() {
            return Err(ToolError::new(
                "opening diversification source must contain at least one line",
            ));
        }
        Ok(())
    }
}

/// Absolute result of one generated game.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SelfPlayResult {
    /// White won.
    WhiteWin,
    /// Black won.
    BlackWin,
    /// Completed draw.
    Draw,
    /// Game reached the maximum-ply policy without adjudication.
    Unfinished,
}

impl fmt::Display for SelfPlayResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::WhiteWin => "1-0",
            Self::BlackWin => "0-1",
            Self::Draw => "1/2-1/2",
            Self::Unfinished => "*",
        })
    }
}

impl FromStr for SelfPlayResult {
    type Err = ToolError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        match value {
            "1-0" => Ok(Self::WhiteWin),
            "0-1" => Ok(Self::BlackWin),
            "1/2-1/2" => Ok(Self::Draw),
            "*" => Ok(Self::Unfinished),
            _ => Err(ToolError::new(format!(
                "invalid self-play result {value:?}"
            ))),
        }
    }
}

/// Exact rule, claim, or policy reason that ended a game.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SelfPlayTermination {
    /// Checkmate with the recorded winner.
    Checkmate(Color),
    /// Stalemate.
    Stalemate,
    /// Automatic rules draw.
    AutomaticDraw(DrawReason),
    /// Claimable draw accepted by configuration.
    ClaimedDraw(DrawReason),
    /// Maximum ply reached without silently declaring a draw.
    MaximumPly(u32),
}

impl fmt::Display for SelfPlayTermination {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Checkmate(winner) => write!(formatter, "checkmate:{winner}"),
            Self::Stalemate => formatter.write_str("stalemate"),
            Self::AutomaticDraw(reason) => {
                write!(formatter, "automatic_draw:{}", draw_reason_token(*reason))
            }
            Self::ClaimedDraw(reason) => {
                write!(formatter, "claimed_draw:{}", draw_reason_token(*reason))
            }
            Self::MaximumPly(maximum) => write!(formatter, "maximum_ply:{maximum}"),
        }
    }
}

impl FromStr for SelfPlayTermination {
    type Err = ToolError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        if value == "stalemate" {
            return Ok(Self::Stalemate);
        }
        let (kind, detail) = value
            .split_once(':')
            .ok_or_else(|| ToolError::new(format!("invalid termination {value:?}")))?;
        match kind {
            "checkmate" => Ok(Self::Checkmate(parse_color(detail)?)),
            "automatic_draw" => Ok(Self::AutomaticDraw(parse_draw_reason(detail)?)),
            "claimed_draw" => Ok(Self::ClaimedDraw(parse_draw_reason(detail)?)),
            "maximum_ply" => Ok(Self::MaximumPly(parse_number(detail, "maximum ply")?)),
            _ => Err(ToolError::new(format!("invalid termination kind {kind:?}"))),
        }
    }
}

/// Engine, evaluator, and search provenance for one side.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SideProvenance {
    engine_version: String,
    weight_schema_version: u16,
    weight_identifier: u64,
    weight_checksum: u64,
    config: SelfPlaySideConfig,
}

impl SideProvenance {
    /// Returns the recorded engine version.
    #[must_use]
    pub fn engine_version(&self) -> &str {
        &self.engine_version
    }

    /// Returns the evaluator schema version.
    #[must_use]
    pub const fn weight_schema_version(&self) -> u16 {
        self.weight_schema_version
    }

    /// Returns the evaluator identity.
    #[must_use]
    pub const fn weight_identifier(&self) -> u64 {
        self.weight_identifier
    }

    /// Returns the evaluator checksum.
    #[must_use]
    pub const fn weight_checksum(&self) -> u64 {
        self.weight_checksum
    }

    /// Returns the side's independent search configuration.
    #[must_use]
    pub const fn config(&self) -> SelfPlaySideConfig {
        self.config
    }
}

/// Complete provenance and move record for one self-play game.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SelfPlayGameRecord {
    game_id: u32,
    split: DatasetSplit,
    game_seed: u64,
    opening_identifier: String,
    initial_fen: String,
    opening_ply_count: u32,
    moves: Vec<String>,
    final_fen: String,
    result: SelfPlayResult,
    termination: SelfPlayTermination,
    white: SideProvenance,
    black: SideProvenance,
    replay_command: String,
}

impl SelfPlayGameRecord {
    /// Returns the stable zero-based game identifier.
    #[must_use]
    pub const fn game_id(&self) -> u32 {
        self.game_id
    }

    /// Returns the deterministic dataset partition.
    #[must_use]
    pub const fn split(&self) -> DatasetSplit {
        self.split
    }

    /// Returns the game-local derived seed.
    #[must_use]
    pub const fn game_seed(&self) -> u64 {
        self.game_seed
    }

    /// Returns the selected opening identifier.
    #[must_use]
    pub fn opening_identifier(&self) -> &str {
        &self.opening_identifier
    }

    /// Returns the canonical initial FEN.
    #[must_use]
    pub fn initial_fen(&self) -> &str {
        &self.initial_fen
    }

    /// Returns the number of supplied opening plies.
    #[must_use]
    pub const fn opening_ply_count(&self) -> u32 {
        self.opening_ply_count
    }

    /// Returns all opening and engine-selected moves.
    #[must_use]
    pub fn moves(&self) -> &[String] {
        &self.moves
    }

    /// Returns the canonical final FEN.
    #[must_use]
    pub fn final_fen(&self) -> &str {
        &self.final_fen
    }

    /// Returns the absolute game result.
    #[must_use]
    pub const fn result(&self) -> SelfPlayResult {
        self.result
    }

    /// Returns the exact termination reason.
    #[must_use]
    pub const fn termination(&self) -> SelfPlayTermination {
        self.termination
    }

    /// Returns White's complete provenance.
    #[must_use]
    pub const fn white(&self) -> &SideProvenance {
        &self.white
    }

    /// Returns Black's complete provenance.
    #[must_use]
    pub const fn black(&self) -> &SideProvenance {
        &self.black
    }

    /// Returns the recorded standalone replay command.
    #[must_use]
    pub fn replay_command(&self) -> &str {
        &self.replay_command
    }
}

/// Filtering classification retained with one position record.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum PositionFilterReason {
    /// Eligible non-opening position from a completed game.
    Eligible,
    /// Opening-source position retained only for provenance.
    Opening,
    /// Position belongs to an unfinished maximum-ply game.
    UnfinishedMaximumPly,
}

impl fmt::Display for PositionFilterReason {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::Eligible => "eligible",
            Self::Opening => "opening",
            Self::UnfinishedMaximumPly => "unfinished_maximum_ply",
        })
    }
}

impl FromStr for PositionFilterReason {
    type Err = ToolError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        match value {
            "eligible" => Ok(Self::Eligible),
            "opening" => Ok(Self::Opening),
            "unfinished_maximum_ply" => Ok(Self::UnfinishedMaximumPly),
            _ => Err(ToolError::new(format!(
                "invalid position filter reason {value:?}"
            ))),
        }
    }
}

/// One versioned position-dataset record.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SelfPlayPositionRecord {
    game_id: u32,
    ply: u32,
    split: DatasetSplit,
    fen: String,
    side_to_move: Color,
    outcome: SelfPlayResult,
    active_side: SideProvenance,
    opening_position: bool,
    eligible: bool,
    filter_reason: PositionFilterReason,
    occurrences: u32,
}

impl SelfPlayPositionRecord {
    /// Returns the first game containing this exact retained record.
    #[must_use]
    pub const fn game_id(&self) -> u32 {
        self.game_id
    }

    /// Returns the first ply containing this exact retained record.
    #[must_use]
    pub const fn ply(&self) -> u32 {
        self.ply
    }

    /// Returns the explicit dataset partition.
    #[must_use]
    pub const fn split(&self) -> DatasetSplit {
        self.split
    }

    /// Returns the lossless canonical six-field FEN.
    #[must_use]
    pub fn fen(&self) -> &str {
        &self.fen
    }

    /// Returns the side to move encoded by the FEN.
    #[must_use]
    pub const fn side_to_move(&self) -> Color {
        self.side_to_move
    }

    /// Returns the absolute final game outcome.
    #[must_use]
    pub const fn outcome(&self) -> SelfPlayResult {
        self.outcome
    }

    /// Returns active-side engine and evaluator metadata.
    #[must_use]
    pub const fn active_side(&self) -> &SideProvenance {
        &self.active_side
    }

    /// Returns whether this was supplied by the opening source.
    #[must_use]
    pub const fn opening_position(&self) -> bool {
        self.opening_position
    }

    /// Returns whether the record is eligible for downstream training.
    #[must_use]
    pub const fn eligible(&self) -> bool {
        self.eligible
    }

    /// Returns the explicit filtering classification.
    #[must_use]
    pub const fn filter_reason(&self) -> PositionFilterReason {
        self.filter_reason
    }

    /// Returns the number of exact duplicate records merged into this row.
    #[must_use]
    pub const fn occurrences(&self) -> u32 {
        self.occurrences
    }
}

/// Complete validated versioned self-play dataset.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SelfPlayDataset {
    config: SelfPlayConfig,
    openings: Vec<OpeningLine>,
    games: Vec<SelfPlayGameRecord>,
    positions: Vec<SelfPlayPositionRecord>,
}

impl SelfPlayDataset {
    /// Returns the generating configuration.
    #[must_use]
    pub const fn config(&self) -> &SelfPlayConfig {
        &self.config
    }

    /// Returns the embedded opening source.
    #[must_use]
    pub fn openings(&self) -> &[OpeningLine] {
        &self.openings
    }

    /// Returns all complete game records.
    #[must_use]
    pub fn games(&self) -> &[SelfPlayGameRecord] {
        &self.games
    }

    /// Returns all filtered and deterministically deduplicated position rows.
    #[must_use]
    pub fn positions(&self) -> &[SelfPlayPositionRecord] {
        &self.positions
    }

    /// Serializes the complete dataset to the strict version-1 TSV format.
    #[must_use]
    pub fn to_text(&self) -> String {
        let mut output = String::new();
        writeln!(
            output,
            "CHESS_SELF_PLAY_DATASET\t{SELF_PLAY_DATASET_SCHEMA_VERSION}"
        )
        .expect("writing to String cannot fail");
        writeln!(
            output,
            "CONFIG\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}",
            self.config.game_count,
            self.config.seed,
            self.config.maximum_plies,
            self.config.claimable_draw_policy,
            self.config.opening_position_policy,
            self.config.splits.train,
            self.config.splits.validation,
            self.config.splits.test,
            self.config.white.limit,
            self.config.white.transposition_table_mebibytes,
            self.config.white.check_extension,
            self.config.black.limit,
            self.config.black.transposition_table_mebibytes,
            self.config.black.check_extension,
            self.openings.len(),
            self.games.len(),
            self.positions.len()
        )
        .expect("writing to String cannot fail");
        for opening in &self.openings {
            writeln!(
                output,
                "OPENING\t{}\t{}\t{}\t{}",
                opening.identifier,
                opening.initial_fen,
                opening.moves.len(),
                join_moves(&opening.moves)
            )
            .expect("writing to String cannot fail");
        }
        for game in &self.games {
            writeln!(
                output,
                "GAME\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{:016x}\t{:016x}\t{}\t{}\t{}\t{}\t{}\t{:016x}\t{:016x}\t{}\t{}\t{}\t{}",
                game.game_id,
                game.split,
                game.game_seed,
                game.opening_identifier,
                game.initial_fen,
                game.opening_ply_count,
                join_moves(&game.moves),
                game.final_fen,
                game.result,
                game.termination,
                game.white.engine_version,
                game.white.weight_schema_version,
                game.white.weight_identifier,
                game.white.weight_checksum,
                game.white.config.limit,
                game.white.config.transposition_table_mebibytes,
                game.white.config.check_extension,
                game.black.engine_version,
                game.black.weight_schema_version,
                game.black.weight_identifier,
                game.black.weight_checksum,
                game.black.config.limit,
                game.black.config.transposition_table_mebibytes,
                game.black.config.check_extension,
                game.replay_command
            )
            .expect("writing to String cannot fail");
        }
        for position in &self.positions {
            writeln!(
                output,
                "POSITION\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{:016x}\t{:016x}\t{}\t{}\t{}\t{}\t{}\t{}\t{}",
                position.game_id,
                position.ply,
                position.split,
                position.fen,
                position.side_to_move,
                position.outcome,
                position.active_side.engine_version,
                position.active_side.weight_schema_version,
                position.active_side.weight_identifier,
                position.active_side.weight_checksum,
                position.active_side.config.limit,
                position.active_side.config.transposition_table_mebibytes,
                position.active_side.config.check_extension,
                position.opening_position,
                position.eligible,
                position.filter_reason,
                position.occurrences
            )
            .expect("writing to String cannot fail");
        }
        output
    }

    /// Parses and fully validates one strict version-1 dataset.
    pub fn from_text(text: &str) -> Result<Self, ToolError> {
        let mut lines = text.lines();
        let header = lines
            .next()
            .ok_or_else(|| ToolError::new("self-play dataset is empty"))?;
        let expected_header =
            format!("CHESS_SELF_PLAY_DATASET\t{SELF_PLAY_DATASET_SCHEMA_VERSION}");
        if header != expected_header {
            return Err(ToolError::new(format!(
                "invalid self-play dataset header {header:?}"
            )));
        }
        let config_line = lines
            .next()
            .ok_or_else(|| ToolError::new("self-play dataset is missing CONFIG"))?;
        let config_fields = exact_fields(config_line, 18, "CONFIG")?;
        if config_fields[0] != "CONFIG" {
            return Err(ToolError::new("self-play dataset is missing CONFIG"));
        }
        let config = SelfPlayConfig::new(
            parse_number(config_fields[1], "game count")?,
            parse_number(config_fields[2], "seed")?,
            SelfPlaySideConfig::new(
                parse_number(config_fields[10], "white TT MiB")?,
                config_fields[9].parse()?,
            )
            .with_check_extension(parse_bool(config_fields[11], "white check extension")?),
            SelfPlaySideConfig::new(
                parse_number(config_fields[13], "black TT MiB")?,
                config_fields[12].parse()?,
            )
            .with_check_extension(parse_bool(config_fields[14], "black check extension")?),
        )
        .with_maximum_plies(parse_number(config_fields[3], "maximum plies")?)
        .with_claimable_draw_policy(config_fields[4].parse()?)
        .with_opening_position_policy(config_fields[5].parse()?)
        .with_splits(DatasetSplitPercentages::new(
            parse_number(config_fields[6], "train split")?,
            parse_number(config_fields[7], "validation split")?,
            parse_number(config_fields[8], "test split")?,
        )?);
        let opening_count = parse_number(config_fields[15], "opening count")?;
        let game_count = parse_number(config_fields[16], "recorded game count")?;
        let position_count = parse_number(config_fields[17], "position count")?;

        let mut openings = Vec::new();
        openings
            .try_reserve_exact(opening_count)
            .map_err(|_| ToolError::new("failed to reserve opening records"))?;
        for _ in 0..opening_count {
            let line = lines
                .next()
                .ok_or_else(|| ToolError::new("truncated OPENING records"))?;
            openings.push(parse_opening_record(line)?);
        }
        let mut games = Vec::new();
        games
            .try_reserve_exact(game_count)
            .map_err(|_| ToolError::new("failed to reserve game records"))?;
        for _ in 0..game_count {
            let line = lines
                .next()
                .ok_or_else(|| ToolError::new("truncated GAME records"))?;
            games.push(parse_game_record(line)?);
        }
        let mut positions = Vec::new();
        positions
            .try_reserve_exact(position_count)
            .map_err(|_| ToolError::new("failed to reserve position records"))?;
        for _ in 0..position_count {
            let line = lines
                .next()
                .ok_or_else(|| ToolError::new("truncated POSITION records"))?;
            positions.push(parse_position_record(line)?);
        }
        if lines.next().is_some() {
            return Err(ToolError::new(
                "self-play dataset contains trailing records",
            ));
        }
        let dataset = Self {
            config,
            openings,
            games,
            positions,
        };
        dataset.validate()?;
        Ok(dataset)
    }

    /// Replays one recorded game using only its initial FEN and move list.
    pub fn replay_game(&self, game_id: u32) -> Result<SelfPlayReplaySummary, ToolError> {
        let record = self
            .games
            .iter()
            .find(|game| game.game_id == game_id)
            .ok_or_else(|| ToolError::new(format!("unknown self-play game {game_id}")))?;
        let opening = self
            .openings
            .iter()
            .find(|opening| opening.identifier == record.opening_identifier)
            .ok_or_else(|| {
                ToolError::new(format!(
                    "game {game_id} references missing opening {:?}",
                    record.opening_identifier
                ))
            })?;
        if record.initial_fen != opening.initial_fen {
            return Err(ToolError::new(format!(
                "game {game_id} initial FEN does not match its opening"
            )));
        }
        let opening_ply_count = usize::try_from(record.opening_ply_count)
            .map_err(|_| ToolError::new("opening ply count exceeds usize"))?;
        if record.moves.len() < opening_ply_count
            || &record.moves[..opening_ply_count] != opening.moves.as_slice()
        {
            return Err(ToolError::new(format!(
                "game {game_id} move list does not begin with its opening"
            )));
        }
        let position = Position::from_fen(&record.initial_fen)
            .map_err(|error| ToolError::new(error.to_string()))?;
        let mut game = Game::new(position);
        for value in &record.moves {
            let current = resolve_game_uci(&mut game, value)?;
            game.make_move(current)
                .map_err(|error| ToolError::new(error.to_string()))?;
        }
        let final_fen = game.position().to_fen();
        if final_fen != record.final_fen {
            return Err(ToolError::new(format!(
                "game {game_id} replay FEN mismatch"
            )));
        }
        validate_replayed_termination(&mut game, record, &self.config)?;
        Ok(SelfPlayReplaySummary {
            game_id,
            final_fen,
            result: record.result,
            termination: record.termination,
            plies: u32::try_from(record.moves.len())
                .map_err(|_| ToolError::new("game move count exceeds u32"))?,
        })
    }

    /// Validates all schema, provenance, replay, split, filtering, and duplicate rules.
    pub fn validate(&self) -> Result<(), ToolError> {
        self.config.validate_basic()?;
        let opening_suite = OpeningSuite {
            lines: self.openings.clone(),
        };
        self.config.validate_with_openings(&opening_suite)?;
        let expected_game_count = usize::try_from(self.config.game_count)
            .map_err(|_| ToolError::new("game count exceeds usize"))?;
        if self.games.len() != expected_game_count {
            return Err(ToolError::new(format!(
                "expected {expected_game_count} game records, found {}",
                self.games.len()
            )));
        }
        if self.positions.is_empty() {
            return Err(ToolError::new(
                "self-play dataset contains no position records",
            ));
        }

        let mut identifiers = HashSet::new();
        for opening in &self.openings {
            validate_identifier(&opening.identifier)?;
            if !identifiers.insert(opening.identifier.clone()) {
                return Err(ToolError::new(format!(
                    "duplicate embedded opening {:?}",
                    opening.identifier
                )));
            }
            opening.instantiate()?;
        }

        let opening_offset = (splitmix64(self.config.seed) % self.openings.len() as u64) as usize;
        for (index, game) in self.games.iter().enumerate() {
            let expected_id =
                u32::try_from(index).map_err(|_| ToolError::new("game index exceeds u32"))?;
            if game.game_id != expected_id {
                return Err(ToolError::new(format!(
                    "expected game id {expected_id}, found {}",
                    game.game_id
                )));
            }
            let expected_seed = game_seed(self.config.seed, game.game_id);
            if game.game_seed != expected_seed {
                return Err(ToolError::new(format!(
                    "game {} seed mismatch",
                    game.game_id
                )));
            }
            let expected_opening = &self.openings[(opening_offset + index) % self.openings.len()];
            if game.opening_identifier != expected_opening.identifier {
                return Err(ToolError::new(format!(
                    "game {} opening selection mismatch",
                    game.game_id
                )));
            }
            if game.split != self.config.splits.assign(game.game_seed) {
                return Err(ToolError::new(format!(
                    "game {} split mismatch",
                    game.game_id
                )));
            }
            validate_side_provenance(&game.white)?;
            validate_side_provenance(&game.black)?;
            if game.white.config != self.config.white || game.black.config != self.config.black {
                return Err(ToolError::new(format!(
                    "game {} side configuration mismatch",
                    game.game_id
                )));
            }
            validate_text_field("replay command", &game.replay_command)?;
            if game.replay_command.is_empty() || !game.replay_command.contains("self-play-replay") {
                return Err(ToolError::new(format!(
                    "game {} has no reproducible replay command",
                    game.game_id
                )));
            }
            if game.moves.len() > self.config.maximum_plies as usize {
                return Err(ToolError::new(format!(
                    "game {} exceeds the configured maximum ply count",
                    game.game_id
                )));
            }
            self.replay_game(game.game_id)?;
        }

        let mut duplicate_keys = HashSet::new();
        for position in &self.positions {
            let game = self
                .games
                .get(position.game_id as usize)
                .ok_or_else(|| ToolError::new("position references unknown game"))?;
            if position.split != game.split || position.outcome != game.result {
                return Err(ToolError::new(format!(
                    "position game {} provenance mismatch",
                    position.game_id
                )));
            }
            if position.ply > game.moves.len() as u32 {
                return Err(ToolError::new(format!(
                    "position game {} has out-of-range ply {}",
                    position.game_id, position.ply
                )));
            }
            if replay_fen_at_ply(game, position.ply)? != position.fen {
                return Err(ToolError::new(format!(
                    "position game {} ply {} does not match game replay",
                    position.game_id, position.ply
                )));
            }
            let parsed = Position::from_fen(&position.fen)
                .map_err(|error| ToolError::new(error.to_string()))?;
            if parsed.to_fen() != position.fen || parsed.side_to_move() != position.side_to_move {
                return Err(ToolError::new(format!(
                    "position game {} ply {} has noncanonical metadata",
                    position.game_id, position.ply
                )));
            }
            let expected_active = match position.side_to_move {
                Color::White => &game.white,
                Color::Black => &game.black,
            };
            if &position.active_side != expected_active {
                return Err(ToolError::new(format!(
                    "position game {} ply {} active-side provenance mismatch",
                    position.game_id, position.ply
                )));
            }
            if position.occurrences == 0 {
                return Err(ToolError::new("position occurrences must be nonzero"));
            }
            if position.opening_position != (position.ply <= game.opening_ply_count) {
                return Err(ToolError::new(
                    "position opening marker does not match the recorded opening boundary",
                ));
            }
            validate_filtering(position, game, self.config.opening_position_policy)?;
            let key = duplicate_key(position);
            if !duplicate_keys.insert(key) {
                return Err(ToolError::new(
                    "duplicate position rows were not merged deterministically",
                ));
            }
        }
        Ok(())
    }
}

/// Result of replaying one dataset game.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SelfPlayReplaySummary {
    game_id: u32,
    final_fen: String,
    result: SelfPlayResult,
    termination: SelfPlayTermination,
    plies: u32,
}

impl SelfPlayReplaySummary {
    /// Returns the replayed game identifier.
    #[must_use]
    pub const fn game_id(&self) -> u32 {
        self.game_id
    }

    /// Returns the verified final FEN.
    #[must_use]
    pub fn final_fen(&self) -> &str {
        &self.final_fen
    }

    /// Returns the verified result.
    #[must_use]
    pub const fn result(&self) -> SelfPlayResult {
        self.result
    }

    /// Returns the verified termination reason.
    #[must_use]
    pub const fn termination(&self) -> SelfPlayTermination {
        self.termination
    }

    /// Returns the replayed move count.
    #[must_use]
    pub const fn plies(&self) -> u32 {
        self.plies
    }
}

#[derive(Clone, Debug)]
struct RawPosition {
    ply: u32,
    fen: String,
    side_to_move: Color,
    opening_position: bool,
}

/// Runs a deterministic self-play batch and returns a validated in-memory dataset.
pub fn generate_self_play_dataset(
    config: &SelfPlayConfig,
    openings: &OpeningSuite,
    output_path: &str,
) -> Result<SelfPlayDataset, ToolError> {
    config.validate_with_openings(openings)?;
    validate_text_field("output path", output_path)?;
    if output_path.is_empty() {
        return Err(ToolError::new("self-play output path must not be empty"));
    }

    let baseline = EvaluationWeightSet::baseline();
    baseline
        .validate()
        .map_err(|error| ToolError::new(error.to_string()))?;
    let white = side_provenance(config.white, baseline);
    let black = side_provenance(config.black, baseline);
    let game_capacity = usize::try_from(config.game_count)
        .map_err(|_| ToolError::new("game count exceeds usize"))?;
    let mut games = Vec::new();
    games
        .try_reserve_exact(game_capacity)
        .map_err(|_| ToolError::new("failed to reserve game records"))?;
    let mut positions = Vec::new();
    let mut duplicate_indices = HashMap::new();
    let opening_offset = (splitmix64(config.seed) % openings.lines.len() as u64) as usize;

    for game_id in 0..config.game_count {
        let opening_index = (opening_offset + game_id as usize) % openings.lines.len();
        let opening = &openings.lines[opening_index];
        let game_seed = game_seed(config.seed, game_id);
        let split = config.splits.assign(game_seed);
        let (game, raw_positions, result, termination) = run_game(config, opening, &white, &black)?;
        let moves = game
            .moves()
            .iter()
            .map(|current| current.to_uci())
            .collect::<Vec<_>>();
        let replay_command = format!(
            "chess-tools self-play-replay {} {game_id}",
            shell_quote(output_path)
        );
        let record = SelfPlayGameRecord {
            game_id,
            split,
            game_seed,
            opening_identifier: opening.identifier.clone(),
            initial_fen: opening.initial_fen.clone(),
            opening_ply_count: u32::try_from(opening.moves.len())
                .map_err(|_| ToolError::new("opening move count exceeds u32"))?,
            moves,
            final_fen: game.position().to_fen(),
            result,
            termination,
            white: white.clone(),
            black: black.clone(),
            replay_command,
        };
        append_positions(
            &mut positions,
            &mut duplicate_indices,
            &record,
            raw_positions,
            config.opening_position_policy,
        )?;
        games.push(record);
    }

    if positions.is_empty() {
        return Err(ToolError::new(
            "self-play produced no position records after filtering",
        ));
    }
    let dataset = SelfPlayDataset {
        config: config.clone(),
        openings: openings.lines.clone(),
        games,
        positions,
    };
    dataset.validate()?;
    Ok(dataset)
}

fn run_game(
    config: &SelfPlayConfig,
    opening: &OpeningLine,
    white: &SideProvenance,
    black: &SideProvenance,
) -> Result<(Game, Vec<RawPosition>, SelfPlayResult, SelfPlayTermination), ToolError> {
    let mut game = Game::new(
        Position::from_fen(&opening.initial_fen)
            .map_err(|error| ToolError::new(error.to_string()))?,
    );
    let capacity = usize::try_from(config.maximum_plies + 1)
        .map_err(|_| ToolError::new("maximum plies exceeds usize"))?;
    let mut raw_positions = Vec::new();
    raw_positions
        .try_reserve_exact(capacity)
        .map_err(|_| ToolError::new("failed to reserve raw positions"))?;
    raw_positions.push(raw_position(&game, true)?);
    for value in &opening.moves {
        let current = resolve_game_uci(&mut game, value)?;
        game.make_move(current)
            .map_err(|error| ToolError::new(error.to_string()))?;
        raw_positions.push(raw_position(&game, true)?);
    }

    let mut white_table = TranspositionTable::new(white.config.transposition_table_mebibytes)
        .map_err(|error| ToolError::new(error.to_string()))?;
    let mut black_table = TranspositionTable::new(black.config.transposition_table_mebibytes)
        .map_err(|error| ToolError::new(error.to_string()))?;

    loop {
        let status = game
            .status()
            .map_err(|error| ToolError::new(error.to_string()))?;
        if let Some((result, termination)) = completed_status(status, config.claimable_draw_policy)
        {
            return Ok((game, raw_positions, result, termination));
        }
        let ply_count = u32::try_from(game.ply_count())
            .map_err(|_| ToolError::new("game ply count exceeds u32"))?;
        if ply_count >= config.maximum_plies {
            return Ok((
                game,
                raw_positions,
                SelfPlayResult::Unfinished,
                SelfPlayTermination::MaximumPly(config.maximum_plies),
            ));
        }

        let side = game.position().side_to_move();
        let (side_config, table) = match side {
            Color::White => (white.config, &mut white_table),
            Color::Black => (black.config, &mut black_table),
        };
        let mut position = game.position().clone();
        let mut history = game.search_history();
        let search = iterative_deepening_search_with_limits_and_transposition_table(
            &mut position,
            &mut history,
            side_config.search_limits(),
            table,
        )
        .map_err(|error| ToolError::new(error.to_string()))?;
        let current = search.best_move().ok_or_else(|| {
            ToolError::new(format!(
                "nonterminal self-play position at ply {ply_count} produced no move"
            ))
        })?;
        game.make_move(current)
            .map_err(|error| ToolError::new(error.to_string()))?;
        raw_positions.push(raw_position(&game, false)?);
    }
}

fn raw_position(game: &Game, opening_position: bool) -> Result<RawPosition, ToolError> {
    Ok(RawPosition {
        ply: u32::try_from(game.ply_count())
            .map_err(|_| ToolError::new("game ply count exceeds u32"))?,
        fen: game.position().to_fen(),
        side_to_move: game.position().side_to_move(),
        opening_position,
    })
}

fn completed_status(
    status: GameStatus,
    policy: ClaimableDrawPolicy,
) -> Option<(SelfPlayResult, SelfPlayTermination)> {
    match status {
        GameStatus::Ongoing => None,
        GameStatus::Checkmate { winner } => Some((
            result_for_winner(winner),
            SelfPlayTermination::Checkmate(winner),
        )),
        GameStatus::Stalemate => Some((SelfPlayResult::Draw, SelfPlayTermination::Stalemate)),
        GameStatus::AutomaticDraw(reason) => Some((
            SelfPlayResult::Draw,
            SelfPlayTermination::AutomaticDraw(reason),
        )),
        GameStatus::ClaimableDraw(reason) => match policy {
            ClaimableDrawPolicy::Accept => Some((
                SelfPlayResult::Draw,
                SelfPlayTermination::ClaimedDraw(reason),
            )),
            ClaimableDrawPolicy::Continue => None,
        },
    }
}

fn append_positions(
    positions: &mut Vec<SelfPlayPositionRecord>,
    duplicate_indices: &mut HashMap<String, usize>,
    game: &SelfPlayGameRecord,
    raw_positions: Vec<RawPosition>,
    opening_policy: OpeningPositionPolicy,
) -> Result<(), ToolError> {
    for raw in raw_positions {
        if raw.opening_position && opening_policy == OpeningPositionPolicy::Exclude {
            continue;
        }
        let filter_reason = if raw.opening_position {
            PositionFilterReason::Opening
        } else if matches!(game.termination, SelfPlayTermination::MaximumPly(_)) {
            PositionFilterReason::UnfinishedMaximumPly
        } else {
            PositionFilterReason::Eligible
        };
        let eligible = filter_reason == PositionFilterReason::Eligible;
        let active_side = match raw.side_to_move {
            Color::White => game.white.clone(),
            Color::Black => game.black.clone(),
        };
        let record = SelfPlayPositionRecord {
            game_id: game.game_id,
            ply: raw.ply,
            split: game.split,
            fen: raw.fen,
            side_to_move: raw.side_to_move,
            outcome: game.result,
            active_side,
            opening_position: raw.opening_position,
            eligible,
            filter_reason,
            occurrences: 1,
        };
        let key = duplicate_key(&record);
        if let Some(index) = duplicate_indices.get(&key).copied() {
            positions[index].occurrences = positions[index]
                .occurrences
                .checked_add(1)
                .ok_or_else(|| ToolError::new("position duplicate count overflow"))?;
        } else {
            let index = positions.len();
            duplicate_indices.insert(key, index);
            positions.push(record);
        }
    }
    Ok(())
}

fn validate_filtering(
    position: &SelfPlayPositionRecord,
    game: &SelfPlayGameRecord,
    opening_policy: OpeningPositionPolicy,
) -> Result<(), ToolError> {
    if position.opening_position {
        if opening_policy != OpeningPositionPolicy::Mark
            || position.filter_reason != PositionFilterReason::Opening
            || position.eligible
        {
            return Err(ToolError::new(
                "opening position violates explicit filtering policy",
            ));
        }
    } else if matches!(game.termination, SelfPlayTermination::MaximumPly(_)) {
        if position.filter_reason != PositionFilterReason::UnfinishedMaximumPly
            || position.eligible
            || position.outcome != SelfPlayResult::Unfinished
        {
            return Err(ToolError::new(
                "maximum-ply position was silently treated as eligible or drawn",
            ));
        }
    } else if position.filter_reason != PositionFilterReason::Eligible || !position.eligible {
        return Err(ToolError::new(
            "completed non-opening position must be eligible",
        ));
    }
    Ok(())
}

fn validate_replayed_termination(
    game: &mut Game,
    record: &SelfPlayGameRecord,
    config: &SelfPlayConfig,
) -> Result<(), ToolError> {
    let status = game
        .status()
        .map_err(|error| ToolError::new(error.to_string()))?;
    let expected_result = match record.termination {
        SelfPlayTermination::Checkmate(winner) => {
            if status != (GameStatus::Checkmate { winner }) {
                return Err(ToolError::new("checkmate termination mismatch"));
            }
            result_for_winner(winner)
        }
        SelfPlayTermination::Stalemate => {
            if status != GameStatus::Stalemate {
                return Err(ToolError::new("stalemate termination mismatch"));
            }
            SelfPlayResult::Draw
        }
        SelfPlayTermination::AutomaticDraw(reason) => {
            if status != GameStatus::AutomaticDraw(reason) {
                return Err(ToolError::new("automatic-draw termination mismatch"));
            }
            SelfPlayResult::Draw
        }
        SelfPlayTermination::ClaimedDraw(reason) => {
            if config.claimable_draw_policy != ClaimableDrawPolicy::Accept
                || status != GameStatus::ClaimableDraw(reason)
            {
                return Err(ToolError::new("claimed-draw termination mismatch"));
            }
            SelfPlayResult::Draw
        }
        SelfPlayTermination::MaximumPly(maximum) => {
            if maximum != config.maximum_plies
                || game.ply_count() != maximum as usize
                || status.is_terminal()
            {
                return Err(ToolError::new("maximum-ply termination mismatch"));
            }
            SelfPlayResult::Unfinished
        }
    };
    if record.result != expected_result {
        return Err(ToolError::new("game result does not match termination"));
    }
    Ok(())
}

fn validate_side_provenance(provenance: &SideProvenance) -> Result<(), ToolError> {
    validate_text_field("engine version", &provenance.engine_version)?;
    if provenance.engine_version.is_empty() || provenance.weight_schema_version == 0 {
        return Err(ToolError::new(
            "side provenance requires a nonempty engine version and weight schema",
        ));
    }
    provenance.config.validate()
}

fn replay_fen_at_ply(record: &SelfPlayGameRecord, ply: u32) -> Result<String, ToolError> {
    let target = usize::try_from(ply).map_err(|_| ToolError::new("ply exceeds usize"))?;
    if target > record.moves.len() {
        return Err(ToolError::new("position ply exceeds game move count"));
    }
    let position = Position::from_fen(&record.initial_fen)
        .map_err(|error| ToolError::new(error.to_string()))?;
    let mut game = Game::new(position);
    for value in &record.moves[..target] {
        let current = resolve_game_uci(&mut game, value)?;
        game.make_move(current)
            .map_err(|error| ToolError::new(error.to_string()))?;
    }
    Ok(game.position().to_fen())
}

fn parse_opening_record(line: &str) -> Result<OpeningLine, ToolError> {
    let fields = exact_fields(line, 5, "OPENING")?;
    if fields[0] != "OPENING" {
        return Err(ToolError::new("expected OPENING record"));
    }
    validate_identifier(fields[1])?;
    let position =
        Position::from_fen(fields[2]).map_err(|error| ToolError::new(error.to_string()))?;
    if position.to_fen() != fields[2] {
        return Err(ToolError::new("embedded opening FEN is not canonical"));
    }
    let expected_count: usize = parse_number(fields[3], "opening move count")?;
    let moves = parse_moves(fields[4]);
    if moves.len() != expected_count {
        return Err(ToolError::new("embedded opening move count mismatch"));
    }
    let opening = OpeningLine {
        identifier: fields[1].to_owned(),
        initial_fen: fields[2].to_owned(),
        moves,
    };
    let mut game = opening.instantiate()?;
    if game
        .status()
        .map_err(|error| ToolError::new(error.to_string()))?
        .is_terminal()
    {
        return Err(ToolError::new("embedded opening ends terminally"));
    }
    Ok(opening)
}

fn parse_game_record(line: &str) -> Result<SelfPlayGameRecord, ToolError> {
    let fields = exact_fields(line, 26, "GAME")?;
    if fields[0] != "GAME" {
        return Err(ToolError::new("expected GAME record"));
    }
    Ok(SelfPlayGameRecord {
        game_id: parse_number(fields[1], "game id")?,
        split: fields[2].parse()?,
        game_seed: parse_number(fields[3], "game seed")?,
        opening_identifier: fields[4].to_owned(),
        initial_fen: fields[5].to_owned(),
        opening_ply_count: parse_number(fields[6], "opening ply count")?,
        moves: parse_moves(fields[7]),
        final_fen: fields[8].to_owned(),
        result: fields[9].parse()?,
        termination: fields[10].parse()?,
        white: parse_side_provenance(&fields[11..18])?,
        black: parse_side_provenance(&fields[18..25])?,
        replay_command: fields[25].to_owned(),
    })
}

fn parse_position_record(line: &str) -> Result<SelfPlayPositionRecord, ToolError> {
    let fields = exact_fields(line, 18, "POSITION")?;
    if fields[0] != "POSITION" {
        return Err(ToolError::new("expected POSITION record"));
    }
    Ok(SelfPlayPositionRecord {
        game_id: parse_number(fields[1], "position game id")?,
        ply: parse_number(fields[2], "position ply")?,
        split: fields[3].parse()?,
        fen: fields[4].to_owned(),
        side_to_move: parse_color(fields[5])?,
        outcome: fields[6].parse()?,
        active_side: parse_side_provenance(&fields[7..14])?,
        opening_position: parse_bool(fields[14], "opening position")?,
        eligible: parse_bool(fields[15], "eligible")?,
        filter_reason: fields[16].parse()?,
        occurrences: parse_number(fields[17], "occurrences")?,
    })
}

fn parse_side_provenance(fields: &[&str]) -> Result<SideProvenance, ToolError> {
    if fields.len() != 7 {
        return Err(ToolError::new("invalid side provenance field count"));
    }
    Ok(SideProvenance {
        engine_version: fields[0].to_owned(),
        weight_schema_version: parse_number(fields[1], "weight schema")?,
        weight_identifier: parse_hex_u64(fields[2], "weight identifier")?,
        weight_checksum: parse_hex_u64(fields[3], "weight checksum")?,
        config: SelfPlaySideConfig::new(parse_number(fields[5], "TT MiB")?, fields[4].parse()?)
            .with_check_extension(parse_bool(fields[6], "check extension")?),
    })
}

fn parse_side_config(
    values: &mut HashMap<String, String>,
    prefix: &str,
) -> Result<SelfPlaySideConfig, ToolError> {
    let limit = take_required(values, &format!("{prefix}_limit"))?.parse()?;
    let transposition_table_mebibytes = parse_number(
        &take_required(values, &format!("{prefix}_tt_mib"))?,
        "transposition-table MiB",
    )?;
    let check_extension = parse_bool(
        &take_required(values, &format!("{prefix}_check_extension"))?,
        "check extension",
    )?;
    Ok(
        SelfPlaySideConfig::new(transposition_table_mebibytes, limit)
            .with_check_extension(check_extension),
    )
}

fn is_config_key(key: &str) -> bool {
    matches!(
        key,
        "schema"
            | "games"
            | "seed"
            | "maximum_plies"
            | "claimable_draw"
            | "opening_positions"
            | "split_train"
            | "split_validation"
            | "split_test"
            | "opening_path"
            | "white_limit"
            | "white_tt_mib"
            | "white_check_extension"
            | "black_limit"
            | "black_tt_mib"
            | "black_check_extension"
    )
}

fn take_required(values: &mut HashMap<String, String>, key: &str) -> Result<String, ToolError> {
    values
        .remove(key)
        .ok_or_else(|| ToolError::new(format!("missing self-play config key {key:?}")))
}

fn side_provenance(config: SelfPlaySideConfig, set: EvaluationWeightSet) -> SideProvenance {
    SideProvenance {
        engine_version: SELF_PLAY_ENGINE_VERSION.to_owned(),
        weight_schema_version: set.schema_version,
        weight_identifier: set.identifier,
        weight_checksum: set.checksum,
        config,
    }
}

fn game_seed(seed: u64, game_id: u32) -> u64 {
    splitmix64(seed ^ u64::from(game_id).wrapping_mul(0x9e37_79b9_7f4a_7c15))
}

fn splitmix64(mut value: u64) -> u64 {
    value = value.wrapping_add(0x9e37_79b9_7f4a_7c15);
    value = (value ^ (value >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
    value = (value ^ (value >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
    value ^ (value >> 31)
}

fn resolve_game_uci(game: &mut Game, value: &str) -> Result<Move, ToolError> {
    let syntax = value
        .parse::<UciMove>()
        .map_err(|error| ToolError::new(error.to_string()))?;
    let legal = game
        .legal_moves()
        .map_err(|error| ToolError::new(error.to_string()))?;
    let mut matches = legal.iter().filter(|candidate| syntax.matches(*candidate));
    let current = matches
        .next()
        .ok_or_else(|| ToolError::new(format!("move {value:?} is not legal")))?;
    if matches.next().is_some() {
        return Err(ToolError::new(format!(
            "move {value:?} resolved to multiple legal identities"
        )));
    }
    Ok(current)
}

fn result_for_winner(winner: Color) -> SelfPlayResult {
    match winner {
        Color::White => SelfPlayResult::WhiteWin,
        Color::Black => SelfPlayResult::BlackWin,
    }
}

fn draw_reason_token(reason: DrawReason) -> &'static str {
    match reason {
        DrawReason::ThreefoldRepetition => "threefold_repetition",
        DrawReason::FivefoldRepetition => "fivefold_repetition",
        DrawReason::FiftyMoveRule => "fifty_move_rule",
        DrawReason::SeventyFiveMoveRule => "seventy_five_move_rule",
        DrawReason::DeadPosition => "dead_position",
    }
}

fn parse_draw_reason(value: &str) -> Result<DrawReason, ToolError> {
    match value {
        "threefold_repetition" => Ok(DrawReason::ThreefoldRepetition),
        "fivefold_repetition" => Ok(DrawReason::FivefoldRepetition),
        "fifty_move_rule" => Ok(DrawReason::FiftyMoveRule),
        "seventy_five_move_rule" => Ok(DrawReason::SeventyFiveMoveRule),
        "dead_position" => Ok(DrawReason::DeadPosition),
        _ => Err(ToolError::new(format!("invalid draw reason {value:?}"))),
    }
}

fn parse_color(value: &str) -> Result<Color, ToolError> {
    match value {
        "white" => Ok(Color::White),
        "black" => Ok(Color::Black),
        _ => Err(ToolError::new(format!("invalid color {value:?}"))),
    }
}

fn parse_bool(value: &str, context: &str) -> Result<bool, ToolError> {
    match value {
        "true" => Ok(true),
        "false" => Ok(false),
        _ => Err(ToolError::new(format!(
            "invalid {context} boolean {value:?}"
        ))),
    }
}

fn parse_number<T>(value: &str, context: &str) -> Result<T, ToolError>
where
    T: FromStr,
    T::Err: fmt::Display,
{
    value
        .parse::<T>()
        .map_err(|error| ToolError::new(format!("invalid {context} {value:?}: {error}")))
}

fn parse_hex_u64(value: &str, context: &str) -> Result<u64, ToolError> {
    u64::from_str_radix(value, 16)
        .map_err(|error| ToolError::new(format!("invalid {context} {value:?}: {error}")))
}

fn exact_fields<'a>(
    line: &'a str,
    expected: usize,
    context: &str,
) -> Result<Vec<&'a str>, ToolError> {
    let fields = line.split('\t').collect::<Vec<_>>();
    if fields.len() != expected {
        return Err(ToolError::new(format!(
            "{context} requires {expected} tab-separated fields, found {}",
            fields.len()
        )));
    }
    Ok(fields)
}

fn validate_identifier(value: &str) -> Result<(), ToolError> {
    if value.is_empty()
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_' | b'.'))
    {
        return Err(ToolError::new(format!(
            "invalid opening identifier {value:?}"
        )));
    }
    Ok(())
}

fn validate_text_field(context: &str, value: &str) -> Result<(), ToolError> {
    if value
        .bytes()
        .any(|byte| matches!(byte, b'\t' | b'\r' | b'\n'))
    {
        return Err(ToolError::new(format!(
            "{context} must not contain tabs or newlines"
        )));
    }
    Ok(())
}

fn parse_moves(value: &str) -> Vec<String> {
    if value == "-" {
        Vec::new()
    } else {
        value.split(',').map(str::to_owned).collect()
    }
}

fn join_moves(moves: &[String]) -> String {
    if moves.is_empty() {
        "-".to_owned()
    } else {
        moves.join(",")
    }
}

fn duplicate_key(position: &SelfPlayPositionRecord) -> String {
    format!(
        "{}\t{}\t{}\t{}",
        position.split, position.fen, position.outcome, position.filter_reason
    )
}

fn shell_quote(value: &str) -> String {
    if value
        .bytes()
        .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'/' | b'.' | b'_' | b'-'))
    {
        value.to_owned()
    } else {
        format!("'{}'", value.replace('\'', "'\"'\"'"))
    }
}
