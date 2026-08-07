from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one witness, found {count}: {old!r}")
    p.write_text(text.replace(old, new, 1))


# ---- S3 manifest: bind exact generation invocation and row accounting. ----
p = Path("crates/chess-tools/src/s3.rs")
text = p.read_text()
text = text.replace(
    "    engine_version: String,\n    search_policy_schema: u16,\n",
    "    engine_version: String,\n    exact_invocation: String,\n    search_policy_schema: u16,\n",
    1,
)
text = text.replace(
    "    test_occurrences: u64,\n    checksum: u64,\n",
    "    test_occurrences: u64,\n    total_position_rows: u64,\n    eligible_position_rows: u64,\n    excluded_position_rows: u64,\n    checksum: u64,\n",
    1,
)
text = text.replace(
    "        source_commit: [u8; 20],\n        dataset: &SelfPlayDataset,\n",
    "        source_commit: [u8; 20],\n        exact_invocation: String,\n        dataset: &SelfPlayDataset,\n",
    1,
)
text = text.replace(
    "        if source_commit == [0; 20] {\n            return Err(S3DatasetManifestError::ZeroSourceCommit);\n        }\n",
    "        if source_commit == [0; 20] {\n            return Err(S3DatasetManifestError::ZeroSourceCommit);\n        }\n        validate_invocation(&exact_invocation)?;\n",
    1,
)
old = '''        let dataset_checksum = hash_bytes(FNV_OFFSET, dataset.to_text().as_bytes());
        let config_checksum = canonical_config_checksum(dataset);
        let opening_checksum = canonical_opening_checksum(dataset);
        let mut manifest = Self {
            source_commit,
            engine_version: env!("CARGO_PKG_VERSION").to_owned(),
'''
new = '''        let total_position_rows = u64::try_from(dataset.positions().len())
            .map_err(|_| S3DatasetManifestError::CountOverflow)?;
        let eligible_position_rows = u64::try_from(
            dataset.positions().iter().filter(|position| position.eligible()).count(),
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
'''
if old not in text:
    raise SystemExit("s3 manifest construction witness missing")
text = text.replace(old, new, 1)
text = text.replace(
    "            test_occurrences,\n            checksum: 0,\n",
    "            test_occurrences,\n            total_position_rows,\n            eligible_position_rows,\n            excluded_position_rows,\n            checksum: 0,\n",
    1,
)
text = text.replace("        const KEYS: [&str; 21] = [", "        const KEYS: [&str; 25] = [", 1)
text = text.replace(
    '            "engine_version",\n            "search_policy_schema",\n',
    '            "engine_version",\n            "exact_invocation",\n            "search_policy_schema",\n',
    1,
)
text = text.replace(
    '            "test_occurrences",\n            "checksum",\n',
    '            "test_occurrences",\n            "total_position_rows",\n            "eligible_position_rows",\n            "excluded_position_rows",\n            "checksum",\n',
    1,
)
text = text.replace(
    '            engine_version: fields["engine_version"].clone(),\n            search_policy_schema:',
    '            engine_version: fields["engine_version"].clone(),\n            exact_invocation: fields["exact_invocation"].clone(),\n            search_policy_schema:',
    1,
)
text = text.replace(
    '            test_occurrences: parse_number(&fields["test_occurrences"], "test_occurrences")?,\n            checksum:',
    '            test_occurrences: parse_number(&fields["test_occurrences"], "test_occurrences")?,\n            total_position_rows: parse_number(&fields["total_position_rows"], "total_position_rows")?,\n            eligible_position_rows: parse_number(&fields["eligible_position_rows"], "eligible_position_rows")?,\n            excluded_position_rows: parse_number(&fields["excluded_position_rows"], "excluded_position_rows")?,\n            checksum:',
    1,
)
text = text.replace(
    '        writeln!(output, "engine_version={}", self.engine_version).expect("String write cannot fail");\n        writeln!(output, "search_policy_schema={}", self.search_policy_schema)\n',
    '        writeln!(output, "engine_version={}", self.engine_version).expect("String write cannot fail");\n        writeln!(output, "exact_invocation={}", self.exact_invocation).expect("String write cannot fail");\n        writeln!(output, "search_policy_schema={}", self.search_policy_schema)\n',
    1,
)
text = text.replace(
    '        writeln!(output, "test_occurrences={}", self.test_occurrences).expect("String write cannot fail");\n        writeln!(output, "checksum={:016x}", self.checksum).expect("String write cannot fail");\n',
    '        writeln!(output, "test_occurrences={}", self.test_occurrences).expect("String write cannot fail");\n        writeln!(output, "total_position_rows={}", self.total_position_rows).expect("String write cannot fail");\n        writeln!(output, "eligible_position_rows={}", self.eligible_position_rows).expect("String write cannot fail");\n        writeln!(output, "excluded_position_rows={}", self.excluded_position_rows).expect("String write cannot fail");\n        writeln!(output, "checksum={:016x}", self.checksum).expect("String write cannot fail");\n',
    1,
)
text = text.replace(
    "        let reconstructed = Self::from_dataset(self.source_commit, dataset)?;\n",
    "        let reconstructed = Self::from_dataset(\n            self.source_commit,\n            self.exact_invocation.clone(),\n            dataset,\n        )?;\n",
    1,
)
text = text.replace(
    "        if self.source_commit == [0; 20] {\n            return Err(S3DatasetManifestError::ZeroSourceCommit);\n        }\n        let policy = SearchPolicySet::baseline();\n",
    "        if self.source_commit == [0; 20] {\n            return Err(S3DatasetManifestError::ZeroSourceCommit);\n        }\n        validate_invocation(&self.exact_invocation)?;\n        let policy = SearchPolicySet::baseline();\n",
    1,
)
text = text.replace(
    '''        if self.games == 0
            || self
                .completed_games
                .checked_add(self.unfinished_games)
                .ok_or(S3DatasetManifestError::CountOverflow)?
                != self.games
        {
''',
    '''        if self.games == 0
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
''',
    1,
)
text = text.replace(
    '                "S3 game counts are inconsistent".to_owned(),\n',
    '                "S3 game or position-row counts are inconsistent".to_owned(),\n',
    1,
)
# Add getters before computed checksum.
witness = "    fn computed_checksum(&self) -> u64 {\n"
getters = r'''    /// Exact generation invocation bound by this package.
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

'''
if witness not in text:
    raise SystemExit("s3 computed checksum witness missing")
text = text.replace(witness, getters + witness, 1)
# Invocation validator before parse_commit.
witness = "fn parse_commit(value: &str) -> Result<[u8; 20], S3DatasetManifestError> {\n"
validator = r'''fn validate_invocation(value: &str) -> Result<(), S3DatasetManifestError> {
    if value.is_empty()
        || value.trim() != value
        || value.bytes().any(|byte| matches!(byte, b'\n' | b'\r' | b'\0'))
    {
        return Err(S3DatasetManifestError::Malformed(
            "exact_invocation must be non-empty canonical single-line text".to_owned(),
        ));
    }
    Ok(())
}

'''
text = text.replace(witness, validator + witness, 1)
# Tests: add invocation argument to every local constructor call.
text = text.replace("S3DatasetManifest::from_dataset(source, &dataset)", "S3DatasetManifest::from_dataset(source, \"s3-test-self-play\".to_owned(), &dataset)")
# Add a test proving invocation changes manifest identity.
marker = "    #[test]\n    fn small_pilot_is_valid_but_not_admitted_as_training_scale() {\n"
extra = r'''    #[test]
    fn exact_invocation_is_provenance_and_changes_manifest_checksum() {
        let dataset = small_dataset(6);
        let source = parse_source_commit("0123456789abcdef0123456789abcdef01234567")
            .expect("commit parses");
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

'''
if marker not in text:
    raise SystemExit("s3 test marker missing")
text = text.replace(marker, extra + marker, 1)
p.write_text(text)

# ---- Add an atomic S3 self-play package CLI. ----
Path("crates/chess-tools/src/s3_cli.rs").write_text(r'''use std::{fs, path::Path};

use chess_tools::{
    s3::{parse_source_commit, S3DatasetManifest},
    self_play::{generate_self_play_dataset, OpeningSuite, SelfPlayDataset, SelfPlayFileConfig},
};

const DATASET_NAME: &str = "dataset.tsv";
const MANIFEST_NAME: &str = "manifest.txt";
const CONFIG_NAME: &str = "self-play-config.txt";
const OPENINGS_NAME: &str = "openings.tsv";

pub(crate) fn run_s3_self_play(arguments: &[String]) -> Result<(), String> {
    if arguments.len() != 3 {
        return Err(
            "usage: chess-tools s3-self-play SOURCE_SHA CONFIG_PATH OUTPUT_DIR".to_owned(),
        );
    }
    let source_commit = parse_source_commit(&arguments[0]).map_err(|error| error.to_string())?;
    let config_path = Path::new(&arguments[1]);
    let output_dir = Path::new(&arguments[2]);
    let config_text = fs::read_to_string(config_path)
        .map_err(|error| format!("failed to read S3 self-play config {config_path:?}: {error}"))?;
    let file_config =
        SelfPlayFileConfig::from_text(&config_text).map_err(|error| error.to_string())?;
    let opening_path = Path::new(file_config.opening_path());
    let opening_text = fs::read_to_string(opening_path).map_err(|error| {
        format!("failed to read S3 opening suite {opening_path:?}: {error}")
    })?;
    let openings = OpeningSuite::from_text(&opening_text).map_err(|error| error.to_string())?;
    let dataset_path = output_dir.join(DATASET_NAME);
    let dataset_path_text = dataset_path.display().to_string();
    let dataset = generate_self_play_dataset(file_config.config(), &openings, &dataset_path_text)
        .map_err(|error| error.to_string())?;
    let exact_invocation = std::env::args().collect::<Vec<_>>().join(" ");
    let manifest = S3DatasetManifest::from_dataset(source_commit, exact_invocation, &dataset)
        .map_err(|error| error.to_string())?;
    publish_package(output_dir, &config_text, &opening_text, &dataset, &manifest)?;

    println!("output\t{}", output_dir.display());
    println!("dataset_checksum\t{:016x}", manifest.dataset_checksum());
    println!("manifest_checksum\t{:016x}", manifest.checksum());
    println!("training_occurrences\t{}", manifest.training_occurrences());
    println!("validation_occurrences\t{}", manifest.validation_occurrences());
    println!("excluded_rows\t{}", manifest.excluded_position_rows());
    println!(
        "admitted_for_tuning\t{}",
        manifest.validate_for_tuning().is_ok()
    );
    println!("activated\tfalse");
    Ok(())
}

pub(crate) fn run_s3_self_play_validate(arguments: &[String]) -> Result<(), String> {
    if arguments.len() != 1 {
        return Err("usage: chess-tools s3-self-play-validate DATASET_DIR".to_owned());
    }
    let directory = Path::new(&arguments[0]);
    let dataset = read_dataset(directory)?;
    let manifest = read_manifest(directory)?;
    manifest
        .validate_dataset(&dataset)
        .map_err(|error| error.to_string())?;
    println!("dataset_checksum\t{:016x}", manifest.dataset_checksum());
    println!("manifest_checksum\t{:016x}", manifest.checksum());
    println!("games\t{}", dataset.games().len());
    println!("positions\t{}", dataset.positions().len());
    println!("eligible_rows\t{}", manifest.eligible_position_rows());
    println!("excluded_rows\t{}", manifest.excluded_position_rows());
    match manifest.validate_for_tuning() {
        Ok(()) => println!("admitted_for_tuning\ttrue"),
        Err(error) => {
            println!("admitted_for_tuning\tfalse");
            println!("admission_error\t{error}");
        }
    }
    Ok(())
}

pub(crate) fn read_dataset(directory: &Path) -> Result<SelfPlayDataset, String> {
    let path = directory.join(DATASET_NAME);
    let text = fs::read_to_string(&path)
        .map_err(|error| format!("failed to read S3 dataset {path:?}: {error}"))?;
    SelfPlayDataset::from_text(&text).map_err(|error| error.to_string())
}

pub(crate) fn read_manifest(directory: &Path) -> Result<S3DatasetManifest, String> {
    let path = directory.join(MANIFEST_NAME);
    let text = fs::read_to_string(&path)
        .map_err(|error| format!("failed to read S3 manifest {path:?}: {error}"))?;
    S3DatasetManifest::from_text(&text).map_err(|error| error.to_string())
}

pub(crate) fn dataset_text(directory: &Path) -> Result<String, String> {
    let path = directory.join(DATASET_NAME);
    fs::read_to_string(&path)
        .map_err(|error| format!("failed to read S3 dataset {path:?}: {error}"))
}

pub(crate) fn manifest_text(directory: &Path) -> Result<String, String> {
    let path = directory.join(MANIFEST_NAME);
    fs::read_to_string(&path)
        .map_err(|error| format!("failed to read S3 manifest {path:?}: {error}"))
}

fn publish_package(
    output_dir: &Path,
    config_text: &str,
    opening_text: &str,
    dataset: &SelfPlayDataset,
    manifest: &S3DatasetManifest,
) -> Result<(), String> {
    if output_dir.exists() {
        return Err(format!("S3 dataset output directory already exists: {output_dir:?}"));
    }
    let parent = output_dir.parent().unwrap_or_else(|| Path::new("."));
    let name = output_dir
        .file_name()
        .ok_or_else(|| "S3 dataset output directory must have a final component".to_owned())?;
    let staging = parent.join(format!(".{}.staging", name.to_string_lossy()));
    if staging.exists() {
        return Err(format!("stale S3 dataset staging directory exists: {staging:?}"));
    }
    fs::create_dir_all(&staging)
        .map_err(|error| format!("failed to create S3 dataset staging directory: {error}"))?;
    let result = (|| {
        fs::write(staging.join(CONFIG_NAME), config_text)
            .map_err(|error| format!("failed to write S3 config copy: {error}"))?;
        fs::write(staging.join(OPENINGS_NAME), opening_text)
            .map_err(|error| format!("failed to write S3 opening copy: {error}"))?;
        fs::write(staging.join(DATASET_NAME), dataset.to_text())
            .map_err(|error| format!("failed to write S3 dataset: {error}"))?;
        fs::write(staging.join(MANIFEST_NAME), manifest.to_text())
            .map_err(|error| format!("failed to write S3 manifest: {error}"))?;
        fs::write(
            staging.join("ACTIVATION_DISABLED"),
            "S3 training data are evidence only and cannot activate production defaults.\n",
        )
        .map_err(|error| format!("failed to write S3 activation marker: {error}"))?;
        fs::rename(&staging, output_dir)
            .map_err(|error| format!("failed to publish S3 dataset directory: {error}"))?;
        Ok(())
    })();
    if result.is_err() {
        let _ = fs::remove_dir_all(&staging);
    }
    result
}
''')

# ---- Fix masked report objective to use the same mask semantics as the optimizer. ----
p = Path("crates/chess-tools/src/tuning/report.rs")
text = p.read_text()
text = text.replace(
    "    TunableParameter, SPSA_OPTIMIZER_IDENTIFIER, TUNABLE_PARAMETER_COUNT,\n",
    "    TunableParameter, TunableParameterMask, SPSA_OPTIMIZER_IDENTIFIER, TUNABLE_PARAMETER_COUNT,\n",
    1,
)
text = text.replace(
    "            config.regularization_strength(),\n        );\n",
    "            config.regularization_strength(),\n            config.parameter_mask(),\n        );\n",
    1,
)
old = '''fn regularized_training_objective(
    initial: EvaluationWeights,
    candidate: EvaluationWeights,
    training_loss: f64,
    regularization_strength: f64,
) -> f64 {
    let initial_values = tunable_values(&initial);
    let candidate_values = tunable_values(&candidate);
    let mean_squared_delta = initial_values
        .iter()
        .zip(candidate_values)
        .map(|(initial_value, candidate_value)| {
            let difference = f64::from(candidate_value) - f64::from(*initial_value);
            difference * difference
        })
        .sum::<f64>()
        / TUNABLE_PARAMETER_COUNT as f64;
    training_loss + regularization_strength * mean_squared_delta
}
'''
new = '''fn regularized_training_objective(
    initial: EvaluationWeights,
    candidate: EvaluationWeights,
    training_loss: f64,
    regularization_strength: f64,
    mask: TunableParameterMask,
) -> f64 {
    let initial_values = tunable_values(&initial);
    let candidate_values = tunable_values(&candidate);
    let mean_squared_delta = TunableParameter::all()
        .filter(|parameter| mask.contains(*parameter))
        .map(|parameter| {
            let index = parameter.index();
            let difference =
                f64::from(candidate_values[index]) - f64::from(initial_values[index]);
            difference * difference
        })
        .sum::<f64>()
        / mask.active_count() as f64;
    training_loss + regularization_strength * mean_squared_delta
}
'''
if old not in text:
    raise SystemExit("tuning report regularization helper witness missing")
text = text.replace(old, new, 1)
# Add a masked-report regression near tests end.
text = text.replace(
    "        LogisticK, LossDataset, LossPosition, OutcomeTarget, SpsaConfig, SpsaOptimizer,\n        SpsaSchedule, SpsaWeightBounds, TrainingDatasetProvenance, TUNABLE_PARAMETER_COUNT,\n",
    "        EvaluationParameterGroup, LogisticK, LossDataset, LossPosition, OutcomeTarget,\n        SpsaConfig, SpsaOptimizer, SpsaSchedule, SpsaWeightBounds, TrainingDatasetProvenance,\n        TUNABLE_PARAMETER_COUNT,\n",
    1,
)
marker = "    #[test]\n    fn report_round_trip_and_checksum_are_stable() {\n"
extra = r'''    #[test]
    fn masked_optimizer_report_uses_the_same_regularization_domain() {
        let dataset = dataset();
        let schedule = SpsaSchedule::new(1.0, 0.602, 1.0, 0.101, 10.0).expect("schedule");
        let config = SpsaConfig::new(
            4,
            schedule,
            SpsaWeightBounds::new(-2_000, 2_000).expect("bounds"),
            0.001,
        )
        .expect("config")
        .with_parameter_mask(EvaluationParameterGroup::PawnStructure.mask())
        .expect("mask");
        let mut optimizer = SpsaOptimizer::new(
            config,
            7,
            EvaluationWeights::DEFAULT,
            &dataset,
            LogisticK::new(1.0).expect("K"),
        )
        .expect("optimizer");
        optimizer.advance(&dataset, 4).expect("advance");
        let report = TuningReport::from_checkpoint(
            provenance(),
            dataset_provenance(&dataset),
            config,
            &dataset,
            EvaluationWeights::DEFAULT,
            optimizer.checkpoint(),
        )
        .expect("masked report builds");
        report.validate().expect("masked report validates");
    }

'''
if marker not in text:
    raise SystemExit("tuning report test marker missing")
text = text.replace(marker, extra + marker, 1)
p.write_text(text)

# ---- Group-aware tuning CLI, strictly bound to an admitted S3 dataset package. ----
p = Path("crates/chess-tools/src/tuning_cli.rs")
text = p.read_text()
text = text.replace(
    "    KCalibrationConfig, SpsaCheckpoint, SpsaConfig, SpsaOptimizer, SpsaSchedule, SpsaWeightBounds,\n",
    "    EvaluationParameterGroup, KCalibrationConfig, SpsaCheckpoint, SpsaConfig, SpsaOptimizer,\n    SpsaSchedule, SpsaWeightBounds,\n",
    1,
)
text = text.replace(
    "use chess_tools::tuning::{\n",
    "use chess_tools::s3::S3DatasetManifest;\nuse chess_tools::self_play::SelfPlayDataset;\nuse chess_tools::tuning::{\n",
    1,
)
# optimizer config takes optional group.
text = text.replace(
    "    fn optimizer_config(&self) -> Result<SpsaConfig, String> {\n",
    "    fn optimizer_config(&self, group: Option<EvaluationParameterGroup>) -> Result<SpsaConfig, String> {\n",
    1,
)
old = '''        SpsaConfig::new(
            self.maximum_iterations,
            schedule,
            bounds,
            self.regularization_strength,
        )
        .map_err(|error| error.to_string())
'''
new = '''        let config = SpsaConfig::new(
            self.maximum_iterations,
            schedule,
            bounds,
            self.regularization_strength,
        )
        .map_err(|error| error.to_string())?;
        match group {
            Some(group) => config
                .with_parameter_mask(group.mask())
                .map_err(|error| error.to_string()),
            None => Ok(config),
        }
'''
if old not in text:
    raise SystemExit("tuning optimizer config witness missing")
text = text.replace(old, new, 1)
# Replace public run function with wrappers and core.
start = text.index("pub(crate) fn run_tuning_command(arguments: &[String]) -> Result<(), String> {")
end = text.index("fn publish_output_directory(\n", start)
core = r'''pub(crate) fn run_tuning_command(arguments: &[String]) -> Result<(), String> {
    if !(arguments.len() == 3 || arguments.len() == 4) {
        return Err(
            "usage: chess-tools tune CONFIG_PATH DATASET_PATH OUTPUT_DIR [PREVIOUS_OUTPUT_DIR]"
                .to_owned(),
        );
    }
    run_tuning(
        Path::new(&arguments[0]),
        Path::new(&arguments[1]),
        Path::new(&arguments[2]),
        arguments.get(3).map(String::as_str).map(Path::new),
        None,
    )
}

pub(crate) fn run_group_tuning_command(arguments: &[String]) -> Result<(), String> {
    if !(arguments.len() == 4 || arguments.len() == 5) {
        return Err(
            "usage: chess-tools tune-group GROUP CONFIG_PATH S3_DATASET_DIR OUTPUT_DIR [PREVIOUS_OUTPUT_DIR]"
                .to_owned(),
        );
    }
    let group = parse_group(&arguments[0])?;
    let dataset_dir = Path::new(&arguments[2]);
    let dataset_path = dataset_dir.join("dataset.tsv");
    let manifest_path = dataset_dir.join("manifest.txt");
    let manifest_text = fs::read_to_string(&manifest_path)
        .map_err(|error| format!("failed to read S3 manifest {manifest_path:?}: {error}"))?;
    let manifest = S3DatasetManifest::from_text(&manifest_text).map_err(|error| error.to_string())?;
    let dataset_text = fs::read_to_string(&dataset_path)
        .map_err(|error| format!("failed to read S3 dataset {dataset_path:?}: {error}"))?;
    let self_play = SelfPlayDataset::from_text(&dataset_text).map_err(|error| error.to_string())?;
    manifest
        .validate_dataset(&self_play)
        .map_err(|error| error.to_string())?;
    manifest
        .validate_for_tuning()
        .map_err(|error| format!("S3 dataset is not admitted for tuning: {error}"))?;
    run_tuning(
        Path::new(&arguments[1]),
        &dataset_path,
        Path::new(&arguments[3]),
        arguments.get(4).map(String::as_str).map(Path::new),
        Some(S3GroupContext {
            group,
            manifest,
            manifest_text,
        }),
    )
}

struct S3GroupContext {
    group: EvaluationParameterGroup,
    manifest: S3DatasetManifest,
    manifest_text: String,
}

fn run_tuning(
    config_path: &Path,
    dataset_path: &Path,
    output_dir: &Path,
    previous_output_dir: Option<&Path>,
    s3: Option<S3GroupContext>,
) -> Result<(), String> {
    let config_text = fs::read_to_string(config_path)
        .map_err(|error| format!("failed to read tuning config {config_path:?}: {error}"))?;
    let file_config = TuningFileConfig::parse(&config_text)?;
    if let Some(context) = &s3 {
        if context.manifest.source_commit() != file_config.source_commit {
            return Err("S3 dataset source commit differs from tuning config source_commit".to_owned());
        }
    }
    let dataset_text = fs::read_to_string(dataset_path)
        .map_err(|error| format!("failed to read tuning dataset {dataset_path:?}: {error}"))?;
    let (dataset, dataset_provenance) =
        loss_dataset_and_provenance_from_self_play_text(&dataset_text)
            .map_err(|error| error.to_string())?;
    let initial_set = EvaluationWeightSet::baseline();
    if file_config.initial_weight_identifier != initial_set.identifier {
        return Err(format!(
            "initial_weight_identifier must equal built-in baseline {:016x}",
            initial_set.identifier
        ));
    }
    let group = s3.as_ref().map(|context| context.group);
    let optimizer_config = file_config.optimizer_config(group)?;
    let mut optimizer = match previous_output_dir {
        Some(path) => {
            let previous_config_path = path.join("tuning-config.txt");
            let previous_config = fs::read_to_string(&previous_config_path).map_err(|error| {
                format!("failed to read previous tuning config {previous_config_path:?}: {error}")
            })?;
            if previous_config != config_text {
                return Err("resume requires the exact previous tuning configuration".to_owned());
            }
            if let Some(context) = &s3 {
                let previous_group_path = path.join("s3-group.txt");
                let previous_group = fs::read_to_string(&previous_group_path).map_err(|error| {
                    format!("failed to read previous S3 group {previous_group_path:?}: {error}")
                })?;
                if previous_group != format!("{}\n", context.group.name()) {
                    return Err("resume requires the exact previous S3 tuning group".to_owned());
                }
                let previous_manifest_path = path.join("s3-dataset-manifest.txt");
                let previous_manifest = fs::read_to_string(&previous_manifest_path).map_err(|error| {
                    format!("failed to read previous S3 manifest {previous_manifest_path:?}: {error}")
                })?;
                if previous_manifest != context.manifest_text {
                    return Err("resume requires the exact previous S3 dataset manifest".to_owned());
                }
            }
            let checkpoint_path = path.join("checkpoint.bin");
            let bytes = fs::read(&checkpoint_path).map_err(|error| {
                format!("failed to read checkpoint {checkpoint_path:?}: {error}")
            })?;
            let checkpoint =
                SpsaCheckpoint::from_bytes(&bytes).map_err(|error| error.to_string())?;
            if checkpoint.random_seed() != file_config.random_seed {
                return Err("resume random_seed differs from checkpoint".to_owned());
            }
            SpsaOptimizer::resume(optimizer_config, &dataset, checkpoint)
                .map_err(|error| error.to_string())?
        }
        None => {
            let calibration = KCalibrationConfig::new(
                file_config.k_minimum,
                file_config.k_maximum,
                file_config.k_intervals,
            )
            .map_err(|error| error.to_string())?;
            let logistic_k = dataset
                .calibrate_k(&EvaluationWeights::DEFAULT, calibration)
                .map_err(|error| error.to_string())?
                .k();
            SpsaOptimizer::new(
                optimizer_config,
                file_config.random_seed,
                EvaluationWeights::DEFAULT,
                &dataset,
                logistic_k,
            )
            .map_err(|error| error.to_string())?
        }
    };
    let remaining = optimizer_config
        .maximum_iterations()
        .saturating_sub(optimizer.checkpoint().completed_iterations());
    let iterations = file_config.advance_iterations.min(remaining);
    if iterations == 0 {
        return Err("checkpoint already reached maximum_iterations".to_owned());
    }
    let summary = optimizer
        .advance(&dataset, iterations)
        .map_err(|error| error.to_string())?;
    let checkpoint = optimizer.checkpoint();
    let exact_command = std::env::args().collect::<Vec<_>>().join(" ");
    let provenance = TuningReportProvenance::new(
        file_config.engine_identifier,
        ENGINE_VERSION.to_owned(),
        file_config.source_commit,
        file_config.initial_weight_identifier,
        file_config.candidate_weight_identifier,
        exact_command,
    )
    .map_err(|error| error.to_string())?;
    let report = TuningReport::from_checkpoint(
        provenance,
        dataset_provenance,
        optimizer_config,
        &dataset,
        EvaluationWeights::DEFAULT,
        &checkpoint,
    )
    .map_err(|error| error.to_string())?;
    let candidate = report
        .candidate_artifact(file_config.generated_at_unix_seconds)
        .map_err(|error| error.to_string())?;
    publish_output_directory(
        output_dir,
        &config_text,
        &checkpoint,
        &report,
        &candidate,
        summary,
        s3.as_ref(),
    )?;
    println!("output\t{}", output_dir.display());
    println!("iterations\t{}", checkpoint.completed_iterations());
    println!(
        "candidate\t{:016x}",
        file_config.candidate_weight_identifier
    );
    if let Some(context) = &s3 {
        println!("group\t{}", context.group.name());
        println!("mask\t{:016x}", context.group.mask_fingerprint());
        println!(
            "training_loss_delta\t{:.17e}",
            report.final_training_loss - report.initial_training_loss
        );
        println!(
            "validation_loss_delta\t{:.17e}",
            report.final_validation_loss - report.initial_validation_loss
        );
    }
    println!("activated\tfalse");
    Ok(())
}

fn parse_group(value: &str) -> Result<EvaluationParameterGroup, String> {
    EvaluationParameterGroup::ALL
        .into_iter()
        .find(|group| group.name() == value)
        .ok_or_else(|| format!("unknown S3 evaluation parameter group {value:?}"))
}

'''
text = text[:start] + core + text[end:]
# Add S3 context argument to publisher.
text = text.replace(
    "    summary: chess_tune::SpsaRunSummary,\n) -> Result<(), String> {\n",
    "    summary: chess_tune::SpsaRunSummary,\n    s3: Option<&S3GroupContext>,\n) -> Result<(), String> {\n",
    1,
)
# Write S3 metadata in staging before rename.
witness = '''        fs::write(
            staging.join("ACTIVATION_DISABLED"),
            "This candidate is inactive. Activation requires the independent Task 21 gate.\n",
        )
        .map_err(|error| format!("failed to write activation marker: {error}"))?;
'''
replacement = witness + r'''        if let Some(context) = s3 {
            fs::write(staging.join("s3-group.txt"), format!("{}\n", context.group.name()))
                .map_err(|error| format!("failed to write S3 group identity: {error}"))?;
            fs::write(
                staging.join("s3-dataset-manifest.txt"),
                &context.manifest_text,
            )
            .map_err(|error| format!("failed to write S3 dataset manifest: {error}"))?;
            let s3_summary = format!(
                "group\t{}\nmask_fingerprint\t{:016x}\ndataset_manifest_checksum\t{:016x}\ninitial_training_loss\t{:.17e}\nfinal_training_loss\t{:.17e}\ntraining_loss_delta\t{:.17e}\ninitial_validation_loss\t{:.17e}\nfinal_validation_loss\t{:.17e}\nvalidation_loss_delta\t{:.17e}\nactivated\tfalse\n",
                context.group.name(),
                context.group.mask_fingerprint(),
                context.manifest.checksum(),
                report.initial_training_loss,
                report.final_training_loss,
                report.final_training_loss - report.initial_training_loss,
                report.initial_validation_loss,
                report.final_validation_loss,
                report.final_validation_loss - report.initial_validation_loss,
            );
            fs::write(staging.join("s3-summary.tsv"), s3_summary)
                .map_err(|error| format!("failed to write S3 tuning summary: {error}"))?;
        }
'''
if witness not in text:
    raise SystemExit("tuning publish activation witness missing")
text = text.replace(witness, replacement, 1)
# Fix existing caller compile: core now owns all calls.
# Tests still call optimizer_config() directly: update to None.
text = text.replace(".optimizer_config()", ".optimizer_config(None)")
p.write_text(text)

# ---- Wire binary commands. ----
p = Path("crates/chess-tools/src/main.rs")
text = p.read_text()
text = text.replace("mod tuning_cli;\n", "mod s3_cli;\nmod tuning_cli;\n", 1)
text = text.replace(
    "  chess-tools self-play CONFIG_PATH OUTPUT_PATH\\n  chess-tools self-play-validate DATASET_PATH\\n  chess-tools self-play-replay DATASET_PATH GAME_ID\\n  chess-tools tune CONFIG_PATH DATASET_PATH OUTPUT_DIR [PREVIOUS_OUTPUT_DIR]\\n  chess-tools oracle\"\n",
    "  chess-tools self-play CONFIG_PATH OUTPUT_PATH\\n  chess-tools self-play-validate DATASET_PATH\\n  chess-tools self-play-replay DATASET_PATH GAME_ID\\n  chess-tools s3-self-play SOURCE_SHA CONFIG_PATH OUTPUT_DIR\\n  chess-tools s3-self-play-validate DATASET_DIR\\n  chess-tools tune CONFIG_PATH DATASET_PATH OUTPUT_DIR [PREVIOUS_OUTPUT_DIR]\\n  chess-tools tune-group GROUP CONFIG_PATH S3_DATASET_DIR OUTPUT_DIR [PREVIOUS_OUTPUT_DIR]\\n  chess-tools oracle\"\n",
    1,
)
text = text.replace(
    '''        "tune" => {
            tuning_cli::run_tuning_command(&arguments[1..])?;
        }
''',
    '''        "s3-self-play" => {
            s3_cli::run_s3_self_play(&arguments[1..])?;
        }
        "s3-self-play-validate" => {
            s3_cli::run_s3_self_play_validate(&arguments[1..])?;
        }
        "tune" => {
            tuning_cli::run_tuning_command(&arguments[1..])?;
        }
        "tune-group" => {
            tuning_cli::run_group_tuning_command(&arguments[1..])?;
        }
''',
    1,
)
p.write_text(text)

# ---- Documentation ----
p = Path("docs/RUST_CHESS_ENGINE_S3_PIPELINE.md")
text = p.read_text()
text += r'''

## S3 command surface

The S3 package commands are explicit and offline:

```text
chess-tools s3-self-play SOURCE_SHA CONFIG_PATH OUTPUT_DIR
chess-tools s3-self-play-validate DATASET_DIR
chess-tools tune-group GROUP CONFIG_PATH S3_DATASET_DIR OUTPUT_DIR [PREVIOUS_OUTPUT_DIR]
```

`s3-self-play` publishes one directory through a same-parent staging rename. The directory contains the exact input config, exact opening-suite text, canonical dataset, canonical manifest, and an activation-disabled marker. The manifest binds the exact command-line invocation as single-line provenance and records total, eligible, and excluded unique position-row counts.

`tune-group` refuses a dataset package unless its manifest matches the dataset, satisfies S3 admission thresholds, and has the same source commit as the tuning config. The selected group becomes the optimizer parameter mask and therefore part of the checkpoint-bound config fingerprint. Resume additionally requires the exact prior group name and exact dataset manifest text.

The legacy `tune` command remains the historical all-parameter Task-21 adapter and its config format is unchanged.
'''
p.write_text(text)
