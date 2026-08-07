//! S3 evaluation-strength provenance, dataset admission, and candidate-group contracts.

use core::fmt;
use std::{collections::BTreeMap, fmt::Write as _};

use chess_search::{EvaluationWeightSet, SearchPolicySet};
use chess_tune::EvaluationParameterGroup;

use crate::{
    self_play::{DatasetSplit, SelfPlayDataset, SelfPlayResult, SELF_PLAY_DATASET_SCHEMA_VERSION},
    ToolError,
};

/// Current S3 training-dataset manifest schema.
pub const S3_DATASET_MANIFEST_SCHEMA_VERSION: u16 = 1;
/// Stable S3 dataset-manifest semantic identifier.
pub const S3_DATASET_MANIFEST_IDENTIFIER: u64 = 0x5333_4441_5441_3031;
/// Minimum self-play games admitted for an S3 tuning dataset.
pub const S3_MINIMUM_TUNING_GAMES: u32 = 16;
/// Minimum completed games admitted for an S3 tuning dataset.
pub const S3_MINIMUM_COMPLETED_GAMES: u32 = 12;
/// Maximum unfinished-game fraction, expressed in per-mille.
pub const S3_MAXIMUM_UNFINISHED_PER_MILLE: u32 = 250;
/// Minimum occurrence-weighted training positions.
pub const S3_MINIMUM_TRAINING_OCCURRENCES: u64 = 128;
/// Minimum occurrence-weighted held-out validation positions.
pub const S3_MINIMUM_VALIDATION_OCCURRENCES: u64 = 16;

const MANIFEST_MARKER: &str = "CHESS_S3_TRAINING_DATASET_MANIFEST\t1";
const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;

/// Strict sidecar binding one Task-20 dataset to exact S3 production identities.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct S3DatasetManifest {
    source_commit: [u8; 20],
    engine_version: String,
    exact_invocation: String,
    search_policy_schema: u16,
    search_policy_identifier: u64,
    search_policy_checksum: u64,
    weight_schema: u16,
    weight_identifier: u64,
    weight_checksum: u64,
    dataset_schema: u16,
    dataset_checksum: u64,
    config_checksum: u64,
    opening_checksum: u64,
    games: u32,
    completed_games: u32,
    unfinished_games: u32,
    seed: u64,
    training_occurrences: u64,
    validation_occurrences: u64,
    test_occurrences: u64,
    total_position_rows: u64,
    eligible_position_rows: u64,
    excluded_position_rows: u64,
    checksum: u64,
}

impl S3DatasetManifest {
    /// Binds an already validated baseline self-play dataset to an explicit source commit.
    pub fn from_dataset(
        source_commit: [u8; 20],
        exact_invocation: String,
        dataset: &SelfPlayDataset,
    ) -> Result<Self, S3DatasetManifestError> {
        dataset
            .validate()
            .map_err(|error| S3DatasetManifestError::Dataset(error.to_string()))?;
        if source_commit == [0; 20] {
            return Err(S3DatasetManifestError::ZeroSourceCommit);
        }
        validate_invocation(&exact_invocation)?;
        let policy = SearchPolicySet::baseline();
        policy
            .validate()
            .map_err(|error| S3DatasetManifestError::Identity(error.to_string()))?;
        let weights = EvaluationWeightSet::baseline();
        weights
            .validate()
            .map_err(|error| S3DatasetManifestError::Identity(error.to_string()))?;
        for game in dataset.games() {
            for side in [game.white(), game.black()] {
                if side.engine_version() != env!("CARGO_PKG_VERSION")
                    || side.weight_schema_version() != weights.schema_version
                    || side.weight_identifier() != weights.identifier
                    || side.weight_checksum() != weights.checksum
                {
                    return Err(S3DatasetManifestError::Identity(
                        "self-play side provenance is not the authoritative baseline identity"
                            .to_owned(),
                    ));
                }
            }
        }

        let games = u32::try_from(dataset.games().len())
            .map_err(|_| S3DatasetManifestError::CountOverflow)?;
        let completed_games = u32::try_from(
            dataset
                .games()
                .iter()
                .filter(|game| game.result() != SelfPlayResult::Unfinished)
                .count(),
        )
        .map_err(|_| S3DatasetManifestError::CountOverflow)?;
        let unfinished_games = games
            .checked_sub(completed_games)
            .ok_or(S3DatasetManifestError::CountOverflow)?;
        let mut training_occurrences = 0_u64;
        let mut validation_occurrences = 0_u64;
        let mut test_occurrences = 0_u64;
        for position in dataset
            .positions()
            .iter()
            .filter(|position| position.eligible())
        {
            let destination = match position.split() {
                DatasetSplit::Train => &mut training_occurrences,
                DatasetSplit::Validation => &mut validation_occurrences,
                DatasetSplit::Test => &mut test_occurrences,
            };
            *destination = destination
                .checked_add(u64::from(position.occurrences()))
                .ok_or(S3DatasetManifestError::CountOverflow)?;
        }
        let total_position_rows = u64::try_from(dataset.positions().len())
            .map_err(|_| S3DatasetManifestError::CountOverflow)?;
        let eligible_position_rows = u64::try_from(
            dataset
                .positions()
                .iter()
                .filter(|position| position.eligible())
                .count(),
        )
        .map_err(|_| S3DatasetManifestError::CountOverflow)?;
        let excluded_position_rows = total_position_rows
            .checked_sub(eligible_position_rows)
            .ok_or(S3DatasetManifestError::CountOverflow)?;
        let dataset_checksum = hash_bytes(FNV_OFFSET, dataset.to_text().as_bytes());
        let config_checksum = canonical_config_checksum(dataset);
        let opening_checksum = canonical_opening_checksum(dataset);
        let mut manifest = Self {
            source_commit,
            engine_version: env!("CARGO_PKG_VERSION").to_owned(),
            exact_invocation,
            search_policy_schema: policy.schema_version,
            search_policy_identifier: policy.identifier,
            search_policy_checksum: policy.checksum,
            weight_schema: weights.schema_version,
            weight_identifier: weights.identifier,
            weight_checksum: weights.checksum,
            dataset_schema: SELF_PLAY_DATASET_SCHEMA_VERSION,
            dataset_checksum,
            config_checksum,
            opening_checksum,
            games,
            completed_games,
            unfinished_games,
            seed: dataset.config().seed(),
            training_occurrences,
            validation_occurrences,
            test_occurrences,
            total_position_rows,
            eligible_position_rows,
            excluded_position_rows,
            checksum: 0,
        };
        manifest.checksum = manifest.computed_checksum();
        manifest.validate()?;
        Ok(manifest)
    }

    /// Parses a strict canonical manifest and validates all frozen baseline identities.
    pub fn from_text(text: &str) -> Result<Self, S3DatasetManifestError> {
        let mut lines = text.lines();
        if lines.next() != Some(MANIFEST_MARKER) {
            return Err(S3DatasetManifestError::Malformed(
                "invalid S3 dataset manifest marker".to_owned(),
            ));
        }
        let mut fields = BTreeMap::new();
        for line in lines {
            let (key, value) = line.split_once('=').ok_or_else(|| {
                S3DatasetManifestError::Malformed(format!("invalid manifest field {line:?}"))
            })?;
            if key.is_empty() || value.is_empty() || key.trim() != key || value.trim() != value {
                return Err(S3DatasetManifestError::Malformed(format!(
                    "non-canonical manifest field {line:?}"
                )));
            }
            if fields.insert(key.to_owned(), value.to_owned()).is_some() {
                return Err(S3DatasetManifestError::Malformed(format!(
                    "duplicate manifest field {key:?}"
                )));
            }
        }
        const KEYS: [&str; 25] = [
            "identifier",
            "source_commit",
            "engine_version",
            "exact_invocation",
            "search_policy_schema",
            "search_policy_identifier",
            "search_policy_checksum",
            "weight_schema",
            "weight_identifier",
            "weight_checksum",
            "dataset_schema",
            "dataset_checksum",
            "config_checksum",
            "opening_checksum",
            "games",
            "completed_games",
            "unfinished_games",
            "seed",
            "training_occurrences",
            "validation_occurrences",
            "test_occurrences",
            "total_position_rows",
            "eligible_position_rows",
            "excluded_position_rows",
            "checksum",
        ];
        if fields.len() != KEYS.len() || KEYS.iter().any(|key| !fields.contains_key(*key)) {
            return Err(S3DatasetManifestError::Malformed(
                "S3 dataset manifest fields do not match schema 1".to_owned(),
            ));
        }
        let identifier = parse_hex_u64(&fields["identifier"], "identifier")?;
        if identifier != S3_DATASET_MANIFEST_IDENTIFIER {
            return Err(S3DatasetManifestError::Identity(format!(
                "unexpected S3 dataset manifest identifier {identifier:016x}"
            )));
        }
        let manifest = Self {
            source_commit: parse_commit(&fields["source_commit"])?,
            engine_version: fields["engine_version"].clone(),
            exact_invocation: fields["exact_invocation"].clone(),
            search_policy_schema: parse_number(
                &fields["search_policy_schema"],
                "search_policy_schema",
            )?,
            search_policy_identifier: parse_hex_u64(
                &fields["search_policy_identifier"],
                "search_policy_identifier",
            )?,
            search_policy_checksum: parse_hex_u64(
                &fields["search_policy_checksum"],
                "search_policy_checksum",
            )?,
            weight_schema: parse_number(&fields["weight_schema"], "weight_schema")?,
            weight_identifier: parse_hex_u64(&fields["weight_identifier"], "weight_identifier")?,
            weight_checksum: parse_hex_u64(&fields["weight_checksum"], "weight_checksum")?,
            dataset_schema: parse_number(&fields["dataset_schema"], "dataset_schema")?,
            dataset_checksum: parse_hex_u64(&fields["dataset_checksum"], "dataset_checksum")?,
            config_checksum: parse_hex_u64(&fields["config_checksum"], "config_checksum")?,
            opening_checksum: parse_hex_u64(&fields["opening_checksum"], "opening_checksum")?,
            games: parse_number(&fields["games"], "games")?,
            completed_games: parse_number(&fields["completed_games"], "completed_games")?,
            unfinished_games: parse_number(&fields["unfinished_games"], "unfinished_games")?,
            seed: parse_number(&fields["seed"], "seed")?,
            training_occurrences: parse_number(
                &fields["training_occurrences"],
                "training_occurrences",
            )?,
            validation_occurrences: parse_number(
                &fields["validation_occurrences"],
                "validation_occurrences",
            )?,
            test_occurrences: parse_number(&fields["test_occurrences"], "test_occurrences")?,
            total_position_rows: parse_number(
                &fields["total_position_rows"],
                "total_position_rows",
            )?,
            eligible_position_rows: parse_number(
                &fields["eligible_position_rows"],
                "eligible_position_rows",
            )?,
            excluded_position_rows: parse_number(
                &fields["excluded_position_rows"],
                "excluded_position_rows",
            )?,
            checksum: parse_hex_u64(&fields["checksum"], "checksum")?,
        };
        manifest.validate()?;
        Ok(manifest)
    }

    /// Serializes the exact canonical sidecar text.
    #[must_use]
    pub fn to_text(&self) -> String {
        let mut output = String::new();
        writeln!(output, "{MANIFEST_MARKER}").expect("String write cannot fail");
        writeln!(output, "identifier={S3_DATASET_MANIFEST_IDENTIFIER:016x}")
            .expect("String write cannot fail");
        writeln!(
            output,
            "source_commit={}",
            format_commit(self.source_commit)
        )
        .expect("String write cannot fail");
        writeln!(output, "engine_version={}", self.engine_version)
            .expect("String write cannot fail");
        writeln!(output, "exact_invocation={}", self.exact_invocation)
            .expect("String write cannot fail");
        writeln!(output, "search_policy_schema={}", self.search_policy_schema)
            .expect("String write cannot fail");
        writeln!(
            output,
            "search_policy_identifier={:016x}",
            self.search_policy_identifier
        )
        .expect("String write cannot fail");
        writeln!(
            output,
            "search_policy_checksum={:016x}",
            self.search_policy_checksum
        )
        .expect("String write cannot fail");
        writeln!(output, "weight_schema={}", self.weight_schema).expect("String write cannot fail");
        writeln!(output, "weight_identifier={:016x}", self.weight_identifier)
            .expect("String write cannot fail");
        writeln!(output, "weight_checksum={:016x}", self.weight_checksum)
            .expect("String write cannot fail");
        writeln!(output, "dataset_schema={}", self.dataset_schema)
            .expect("String write cannot fail");
        writeln!(output, "dataset_checksum={:016x}", self.dataset_checksum)
            .expect("String write cannot fail");
        writeln!(output, "config_checksum={:016x}", self.config_checksum)
            .expect("String write cannot fail");
        writeln!(output, "opening_checksum={:016x}", self.opening_checksum)
            .expect("String write cannot fail");
        writeln!(output, "games={}", self.games).expect("String write cannot fail");
        writeln!(output, "completed_games={}", self.completed_games)
            .expect("String write cannot fail");
        writeln!(output, "unfinished_games={}", self.unfinished_games)
            .expect("String write cannot fail");
        writeln!(output, "seed={}", self.seed).expect("String write cannot fail");
        writeln!(output, "training_occurrences={}", self.training_occurrences)
            .expect("String write cannot fail");
        writeln!(
            output,
            "validation_occurrences={}",
            self.validation_occurrences
        )
        .expect("String write cannot fail");
        writeln!(output, "test_occurrences={}", self.test_occurrences)
            .expect("String write cannot fail");
        writeln!(output, "total_position_rows={}", self.total_position_rows)
            .expect("String write cannot fail");
        writeln!(
            output,
            "eligible_position_rows={}",
            self.eligible_position_rows
        )
        .expect("String write cannot fail");
        writeln!(
            output,
            "excluded_position_rows={}",
            self.excluded_position_rows
        )
        .expect("String write cannot fail");
        writeln!(output, "checksum={:016x}", self.checksum).expect("String write cannot fail");
        output
    }

    /// Validates this sidecar against one exact dataset image.
    pub fn validate_dataset(
        &self,
        dataset: &SelfPlayDataset,
    ) -> Result<(), S3DatasetManifestError> {
        let reconstructed =
            Self::from_dataset(self.source_commit, self.exact_invocation.clone(), dataset)?;
        if &reconstructed != self {
            return Err(S3DatasetManifestError::Dataset(
                "S3 dataset manifest does not match the supplied dataset".to_owned(),
            ));
        }
        Ok(())
    }

    /// Applies the predeclared minimum-data and unfinished-game admission policy.
    pub fn validate_for_tuning(&self) -> Result<(), S3DatasetAdmissionError> {
        if self.games < S3_MINIMUM_TUNING_GAMES {
            return Err(S3DatasetAdmissionError::TooFewGames {
                found: self.games,
                minimum: S3_MINIMUM_TUNING_GAMES,
            });
        }
        if self.completed_games < S3_MINIMUM_COMPLETED_GAMES {
            return Err(S3DatasetAdmissionError::TooFewCompletedGames {
                found: self.completed_games,
                minimum: S3_MINIMUM_COMPLETED_GAMES,
            });
        }
        let unfinished_per_mille = u64::from(self.unfinished_games) * 1_000 / u64::from(self.games);
        if unfinished_per_mille > u64::from(S3_MAXIMUM_UNFINISHED_PER_MILLE) {
            return Err(S3DatasetAdmissionError::TooManyUnfinishedGames {
                unfinished: self.unfinished_games,
                games: self.games,
                maximum_per_mille: S3_MAXIMUM_UNFINISHED_PER_MILLE,
            });
        }
        if self.training_occurrences < S3_MINIMUM_TRAINING_OCCURRENCES {
            return Err(S3DatasetAdmissionError::TooFewTrainingOccurrences {
                found: self.training_occurrences,
                minimum: S3_MINIMUM_TRAINING_OCCURRENCES,
            });
        }
        if self.validation_occurrences < S3_MINIMUM_VALIDATION_OCCURRENCES {
            return Err(S3DatasetAdmissionError::TooFewValidationOccurrences {
                found: self.validation_occurrences,
                minimum: S3_MINIMUM_VALIDATION_OCCURRENCES,
            });
        }
        Ok(())
    }

    /// Exact source commit bound by this package.
    #[must_use]
    pub const fn source_commit(&self) -> [u8; 20] {
        self.source_commit
    }

    /// Canonical Task-20 dataset checksum.
    #[must_use]
    pub const fn dataset_checksum(&self) -> u64 {
        self.dataset_checksum
    }

    /// Complete manifest checksum.
    #[must_use]
    pub const fn checksum(&self) -> u64 {
        self.checksum
    }

    /// Occurrence-weighted training count.
    #[must_use]
    pub const fn training_occurrences(&self) -> u64 {
        self.training_occurrences
    }

    /// Occurrence-weighted validation count.
    #[must_use]
    pub const fn validation_occurrences(&self) -> u64 {
        self.validation_occurrences
    }

    fn validate(&self) -> Result<(), S3DatasetManifestError> {
        if self.source_commit == [0; 20] {
            return Err(S3DatasetManifestError::ZeroSourceCommit);
        }
        validate_invocation(&self.exact_invocation)?;
        let policy = SearchPolicySet::baseline();
        let weights = EvaluationWeightSet::baseline();
        if self.engine_version != env!("CARGO_PKG_VERSION")
            || self.search_policy_schema != policy.schema_version
            || self.search_policy_identifier != policy.identifier
            || self.search_policy_checksum != policy.checksum
            || self.weight_schema != weights.schema_version
            || self.weight_identifier != weights.identifier
            || self.weight_checksum != weights.checksum
            || self.dataset_schema != SELF_PLAY_DATASET_SCHEMA_VERSION
        {
            return Err(S3DatasetManifestError::Identity(
                "S3 dataset manifest does not bind the authoritative v0.1 baseline identity"
                    .to_owned(),
            ));
        }
        if self.dataset_checksum == 0 || self.config_checksum == 0 || self.opening_checksum == 0 {
            return Err(S3DatasetManifestError::Malformed(
                "S3 dataset checksums must be non-zero".to_owned(),
            ));
        }
        if self.games == 0
            || self
                .completed_games
                .checked_add(self.unfinished_games)
                .ok_or(S3DatasetManifestError::CountOverflow)?
                != self.games
            || self
                .eligible_position_rows
                .checked_add(self.excluded_position_rows)
                .ok_or(S3DatasetManifestError::CountOverflow)?
                != self.total_position_rows
        {
            return Err(S3DatasetManifestError::Malformed(
                "S3 game or position-row counts are inconsistent".to_owned(),
            ));
        }
        let expected = self.computed_checksum();
        if self.checksum != expected {
            return Err(S3DatasetManifestError::ChecksumMismatch {
                expected,
                found: self.checksum,
            });
        }
        Ok(())
    }

    /// Exact generation invocation bound by this package.
    #[must_use]
    pub fn exact_invocation(&self) -> &str {
        &self.exact_invocation
    }

    /// Total unique dataset position rows before eligibility filtering.
    #[must_use]
    pub const fn total_position_rows(&self) -> u64 {
        self.total_position_rows
    }

    /// Rows eligible for the configured split semantics.
    #[must_use]
    pub const fn eligible_position_rows(&self) -> u64 {
        self.eligible_position_rows
    }

    /// Rows excluded by opening/unfinished-game policy.
    #[must_use]
    pub const fn excluded_position_rows(&self) -> u64 {
        self.excluded_position_rows
    }

    fn computed_checksum(&self) -> u64 {
        let mut clone = self.clone();
        clone.checksum = 0;
        hash_bytes(FNV_OFFSET, clone.to_text().as_bytes())
    }
}

/// Strict manifest parse, identity, or binding error.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum S3DatasetManifestError {
    ZeroSourceCommit,
    CountOverflow,
    Dataset(String),
    Identity(String),
    Malformed(String),
    ChecksumMismatch { expected: u64, found: u64 },
}

impl fmt::Display for S3DatasetManifestError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::ZeroSourceCommit => formatter.write_str("S3 source commit must be non-zero"),
            Self::CountOverflow => formatter.write_str("S3 dataset count overflow"),
            Self::Dataset(message) | Self::Identity(message) | Self::Malformed(message) => {
                formatter.write_str(message)
            }
            Self::ChecksumMismatch { expected, found } => write!(
                formatter,
                "S3 dataset manifest checksum mismatch: expected {expected:016x}, found {found:016x}"
            ),
        }
    }
}

impl std::error::Error for S3DatasetManifestError {}

/// Dataset that is valid but does not meet the S3 tuning admission policy.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum S3DatasetAdmissionError {
    TooFewGames {
        found: u32,
        minimum: u32,
    },
    TooFewCompletedGames {
        found: u32,
        minimum: u32,
    },
    TooManyUnfinishedGames {
        unfinished: u32,
        games: u32,
        maximum_per_mille: u32,
    },
    TooFewTrainingOccurrences {
        found: u64,
        minimum: u64,
    },
    TooFewValidationOccurrences {
        found: u64,
        minimum: u64,
    },
}

impl fmt::Display for S3DatasetAdmissionError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match *self {
            Self::TooFewGames { found, minimum } => {
                write!(
                    formatter,
                    "S3 tuning requires at least {minimum} games, found {found}"
                )
            }
            Self::TooFewCompletedGames { found, minimum } => write!(
                formatter,
                "S3 tuning requires at least {minimum} completed games, found {found}"
            ),
            Self::TooManyUnfinishedGames {
                unfinished,
                games,
                maximum_per_mille,
            } => write!(
                formatter,
                "S3 unfinished-game rate {unfinished}/{games} exceeds {maximum_per_mille} per mille"
            ),
            Self::TooFewTrainingOccurrences { found, minimum } => write!(
                formatter,
                "S3 tuning requires at least {minimum} training occurrences, found {found}"
            ),
            Self::TooFewValidationOccurrences { found, minimum } => write!(
                formatter,
                "S3 tuning requires at least {minimum} validation occurrences, found {found}"
            ),
        }
    }
}

impl std::error::Error for S3DatasetAdmissionError {}

/// Returns all predeclared existing-evaluator tuning groups and their immutable masks.
#[must_use]
pub fn evaluation_groups() -> [(EvaluationParameterGroup, usize, u64); 6] {
    EvaluationParameterGroup::ALL.map(|group| {
        let mask = group.mask();
        (group, mask.active_count(), mask.fingerprint())
    })
}

fn canonical_config_checksum(dataset: &SelfPlayDataset) -> u64 {
    let config = dataset.config();
    let splits = config.splits();
    let text = format!(
        "games={}\nseed={}\nmaximum_plies={}\nclaimable_draw={}\nopening_positions={}\nsplit_train={}\nsplit_validation={}\nsplit_test={}\nwhite_limit={}\nwhite_tt_mib={}\nwhite_check_extension={}\nblack_limit={}\nblack_tt_mib={}\nblack_check_extension={}\n",
        config.game_count(),
        config.seed(),
        config.maximum_plies(),
        config.claimable_draw_policy(),
        config.opening_position_policy(),
        splits.train(),
        splits.validation(),
        splits.test(),
        config.white().limit(),
        config.white().transposition_table_mebibytes(),
        config.white().check_extension_enabled(),
        config.black().limit(),
        config.black().transposition_table_mebibytes(),
        config.black().check_extension_enabled(),
    );
    hash_bytes(FNV_OFFSET, text.as_bytes())
}

fn canonical_opening_checksum(dataset: &SelfPlayDataset) -> u64 {
    let mut text = String::new();
    for opening in dataset.openings() {
        writeln!(
            text,
            "{}\t{}\t{}",
            opening.identifier(),
            opening.initial_fen(),
            opening.moves().join(" ")
        )
        .expect("String write cannot fail");
    }
    hash_bytes(FNV_OFFSET, text.as_bytes())
}

fn validate_invocation(value: &str) -> Result<(), S3DatasetManifestError> {
    if value.is_empty()
        || value.trim() != value
        || value
            .bytes()
            .any(|byte| matches!(byte, b'\n' | b'\r' | b'\0'))
    {
        return Err(S3DatasetManifestError::Malformed(
            "exact_invocation must be non-empty canonical single-line text".to_owned(),
        ));
    }
    Ok(())
}

fn parse_commit(value: &str) -> Result<[u8; 20], S3DatasetManifestError> {
    if value.len() != 40 || !value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(S3DatasetManifestError::Malformed(
            "source_commit must be exactly 40 hexadecimal characters".to_owned(),
        ));
    }
    let mut output = [0_u8; 20];
    for (index, destination) in output.iter_mut().enumerate() {
        *destination = u8::from_str_radix(&value[index * 2..index * 2 + 2], 16).map_err(|_| {
            S3DatasetManifestError::Malformed("invalid source_commit hexadecimal".to_owned())
        })?;
    }
    Ok(output)
}

fn format_commit(commit: [u8; 20]) -> String {
    commit.iter().map(|byte| format!("{byte:02x}")).collect()
}

fn parse_hex_u64(value: &str, field: &str) -> Result<u64, S3DatasetManifestError> {
    if value.len() != 16 || !value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(S3DatasetManifestError::Malformed(format!(
            "{field} must be 16 hexadecimal characters"
        )));
    }
    u64::from_str_radix(value, 16)
        .map_err(|_| S3DatasetManifestError::Malformed(format!("invalid {field}")))
}

fn parse_number<T>(value: &str, field: &str) -> Result<T, S3DatasetManifestError>
where
    T: std::str::FromStr,
    T::Err: fmt::Display,
{
    value
        .parse::<T>()
        .map_err(|error| S3DatasetManifestError::Malformed(format!("invalid {field}: {error}")))
}

fn hash_bytes(mut hash: u64, bytes: &[u8]) -> u64 {
    for byte in bytes {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    hash
}

/// Parses an exact forty-hex-character source commit for manifest construction.
pub fn parse_source_commit(value: &str) -> Result<[u8; 20], S3DatasetManifestError> {
    parse_commit(value)
}

/// Converts a tooling error into the S3 dataset error domain for command adapters.
pub fn dataset_tool_error(error: ToolError) -> S3DatasetManifestError {
    S3DatasetManifestError::Dataset(error.to_string())
}

#[cfg(test)]
mod tests {
    use crate::self_play::{
        generate_self_play_dataset, DatasetSplitPercentages, OpeningPositionPolicy, OpeningSuite,
        SelfPlayConfig, SelfPlayLimit, SelfPlaySideConfig,
    };

    use super::{
        evaluation_groups, parse_source_commit, S3DatasetAdmissionError, S3DatasetManifest,
        S3_MINIMUM_TUNING_GAMES,
    };

    fn small_dataset(games: u32) -> crate::self_play::SelfPlayDataset {
        let openings = OpeningSuite::from_text(concat!(
            "CHESS_SELF_PLAY_OPENINGS\t1\n",
            "king-pawn\trnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\te2e4 e7e5\n",
            "queen-pawn\trnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\td2d4 d7d5\n",
            "english\trnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\tc2c4 e7e5\n",
        ))
        .expect("opening fixture parses");
        let side = SelfPlaySideConfig::new(1, SelfPlayLimit::Depth(1));
        let config = SelfPlayConfig::new(games, 0x5333, side, side)
            .with_maximum_plies(10)
            .with_opening_position_policy(OpeningPositionPolicy::Exclude)
            .with_splits(DatasetSplitPercentages::new(60, 20, 20).expect("splits are valid"));
        generate_self_play_dataset(&config, &openings, "s3-test-dataset.tsv")
            .expect("small self-play dataset generates")
    }

    #[test]
    fn manifest_round_trip_binds_exact_dataset_and_source() {
        let dataset = small_dataset(6);
        let source =
            parse_source_commit("0123456789abcdef0123456789abcdef01234567").expect("commit parses");
        let manifest =
            S3DatasetManifest::from_dataset(source, "s3-test-self-play".to_owned(), &dataset)
                .expect("manifest builds");
        let text = manifest.to_text();
        let parsed = S3DatasetManifest::from_text(&text).expect("manifest parses");
        assert_eq!(parsed, manifest);
        parsed
            .validate_dataset(&dataset)
            .expect("dataset binding validates");
        assert_ne!(parsed.dataset_checksum(), 0);
        assert_ne!(parsed.checksum(), 0);
    }

    #[test]
    fn manifest_checksum_and_dataset_binding_fail_closed() {
        let dataset = small_dataset(6);
        let source =
            parse_source_commit("0123456789abcdef0123456789abcdef01234567").expect("commit parses");
        let manifest =
            S3DatasetManifest::from_dataset(source, "s3-test-self-play".to_owned(), &dataset)
                .expect("manifest builds");
        let corrupt = manifest.to_text().replace("seed=21299", "seed=21300");
        assert!(S3DatasetManifest::from_text(&corrupt).is_err());

        let other = small_dataset(7);
        assert!(manifest.validate_dataset(&other).is_err());
    }

    #[test]
    fn exact_invocation_is_provenance_and_changes_manifest_checksum() {
        let dataset = small_dataset(6);
        let source =
            parse_source_commit("0123456789abcdef0123456789abcdef01234567").expect("commit parses");
        let first = S3DatasetManifest::from_dataset(
            source,
            "chess-tools s3-self-play first".to_owned(),
            &dataset,
        )
        .expect("first manifest builds");
        let second = S3DatasetManifest::from_dataset(
            source,
            "chess-tools s3-self-play second".to_owned(),
            &dataset,
        )
        .expect("second manifest builds");
        assert_ne!(first.checksum(), second.checksum());
        assert_ne!(first.to_text(), second.to_text());
    }

    #[test]
    fn small_pilot_is_valid_but_not_admitted_as_training_scale() {
        let dataset = small_dataset(6);
        let source =
            parse_source_commit("0123456789abcdef0123456789abcdef01234567").expect("commit parses");
        let manifest =
            S3DatasetManifest::from_dataset(source, "s3-test-self-play".to_owned(), &dataset)
                .expect("manifest builds");
        assert_eq!(
            manifest.validate_for_tuning(),
            Err(S3DatasetAdmissionError::TooFewGames {
                found: 6,
                minimum: S3_MINIMUM_TUNING_GAMES,
            })
        );
    }

    #[test]
    fn predeclared_groups_have_stable_nonzero_identity() {
        let groups = evaluation_groups();
        assert_eq!(groups.len(), 6);
        assert!(groups
            .iter()
            .all(|(_, count, checksum)| *count > 0 && *checksum != 0));
    }
}
