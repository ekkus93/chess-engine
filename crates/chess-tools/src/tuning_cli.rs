//! Strict filesystem adapter for reproducible offline tuning runs.

use std::{collections::BTreeMap, fs, path::Path};

use chess_search::{EvaluationWeightSet, EvaluationWeights};
use chess_tune::{
    KCalibrationConfig, SpsaCheckpoint, SpsaConfig, SpsaOptimizer, SpsaSchedule,
    SpsaWeightBounds,
};

use chess_tools::tuning::{
    loss_dataset_and_provenance_from_self_play_text, write_candidate_artifact_atomic,
    write_tuning_report_atomic, TuningReport, TuningReportProvenance,
};

const CONFIG_MARKER: &str = "CHESS_TUNING_CONFIG\t1";
const ENGINE_VERSION: &str = env!("CARGO_PKG_VERSION");

#[derive(Clone, Debug, PartialEq)]
struct TuningFileConfig {
    engine_identifier: u64,
    initial_weight_identifier: u64,
    candidate_weight_identifier: u64,
    source_commit: [u8; 20],
    generated_at_unix_seconds: u64,
    maximum_iterations: u64,
    advance_iterations: u64,
    learning_rate: f64,
    step_decay: f64,
    perturbation_size: f64,
    perturbation_decay: f64,
    stability_constant: f64,
    minimum_weight: i16,
    maximum_weight: i16,
    regularization_strength: f64,
    random_seed: u64,
    k_minimum: f64,
    k_maximum: f64,
    k_intervals: u32,
}

impl TuningFileConfig {
    fn parse(text: &str) -> Result<Self, String> {
        let mut lines = text.lines();
        if lines.next() != Some(CONFIG_MARKER) {
            return Err(format!("tuning config must begin with {CONFIG_MARKER:?}"));
        }
        let mut fields = BTreeMap::new();
        for (index, raw) in lines.enumerate() {
            let line = raw.trim();
            if line.is_empty() || line.starts_with('#') {
                continue;
            }
            let (key, value) = line
                .split_once('=')
                .ok_or_else(|| format!("invalid tuning config line {}: {raw:?}", index + 2))?;
            if key.trim() != key || value.trim() != value || key.is_empty() || value.is_empty() {
                return Err(format!(
                    "non-canonical tuning config line {}: {raw:?}",
                    index + 2
                ));
            }
            if fields.insert(key.to_owned(), value.to_owned()).is_some() {
                return Err(format!("duplicate tuning config field {key:?}"));
            }
        }
        const EXPECTED: [&str; 18] = [
            "advance_iterations",
            "candidate_weight_identifier",
            "engine_identifier",
            "generated_at_unix_seconds",
            "initial_weight_identifier",
            "k_intervals",
            "k_maximum",
            "k_minimum",
            "learning_rate",
            "maximum_iterations",
            "maximum_weight",
            "minimum_weight",
            "perturbation_decay",
            "perturbation_size",
            "random_seed",
            "regularization_strength",
            "source_commit",
            "stability_constant",
        ];
        for key in fields.keys() {
            if !EXPECTED.contains(&key.as_str()) && key != "step_decay" {
                return Err(format!("unknown tuning config field {key:?}"));
            }
        }
        for key in EXPECTED.into_iter().chain(["step_decay"]) {
            if !fields.contains_key(key) {
                return Err(format!("missing tuning config field {key:?}"));
            }
        }
        let get = |key: &str| -> Result<&str, String> {
            fields
                .get(key)
                .map(String::as_str)
                .ok_or_else(|| format!("missing tuning config field {key:?}"))
        };
        let parse_u64 = |key: &str| parse_unsigned(get(key)?, key);
        let parse_f64 = |key: &str| {
            get(key)?.parse::<f64>().map_err(|error| {
                format!("invalid floating-point tuning field {key:?}: {error}")
            })
        };
        let maximum_iterations = parse_u64("maximum_iterations")?;
        let advance_iterations = parse_u64("advance_iterations")?;
        if advance_iterations == 0 || advance_iterations > maximum_iterations {
            return Err("advance_iterations must be in 1..=maximum_iterations".to_owned());
        }
        Ok(Self {
            engine_identifier: parse_u64("engine_identifier")?,
            initial_weight_identifier: parse_u64("initial_weight_identifier")?,
            candidate_weight_identifier: parse_u64("candidate_weight_identifier")?,
            source_commit: parse_source_commit(get("source_commit")?)?,
            generated_at_unix_seconds: parse_u64("generated_at_unix_seconds")?,
            maximum_iterations,
            advance_iterations,
            learning_rate: parse_f64("learning_rate")?,
            step_decay: parse_f64("step_decay")?,
            perturbation_size: parse_f64("perturbation_size")?,
            perturbation_decay: parse_f64("perturbation_decay")?,
            stability_constant: parse_f64("stability_constant")?,
            minimum_weight: get("minimum_weight")?
                .parse::<i16>()
                .map_err(|error| format!("invalid minimum_weight: {error}"))?,
            maximum_weight: get("maximum_weight")?
                .parse::<i16>()
                .map_err(|error| format!("invalid maximum_weight: {error}"))?,
            regularization_strength: parse_f64("regularization_strength")?,
            random_seed: parse_u64("random_seed")?,
            k_minimum: parse_f64("k_minimum")?,
            k_maximum: parse_f64("k_maximum")?,
            k_intervals: u32::try_from(parse_u64("k_intervals")?)
                .map_err(|_| "k_intervals exceeds u32".to_owned())?,
        })
    }

    fn optimizer_config(&self) -> Result<SpsaConfig, String> {
        let schedule = SpsaSchedule::new(
            self.learning_rate,
            self.step_decay,
            self.perturbation_size,
            self.perturbation_decay,
            self.stability_constant,
        )
        .map_err(|error| error.to_string())?;
        let bounds = SpsaWeightBounds::new(self.minimum_weight, self.maximum_weight)
            .map_err(|error| error.to_string())?;
        SpsaConfig::new(
            self.maximum_iterations,
            schedule,
            bounds,
            self.regularization_strength,
        )
        .map_err(|error| error.to_string())
    }
}

pub(crate) fn run_tuning_command(arguments: &[String]) -> Result<(), String> {
    if !(arguments.len() == 3 || arguments.len() == 4) {
        return Err(
            "usage: chess-tools tune CONFIG_PATH DATASET_PATH OUTPUT_DIR [PREVIOUS_OUTPUT_DIR]"
                .to_owned(),
        );
    }
    let config_path = Path::new(&arguments[0]);
    let dataset_path = Path::new(&arguments[1]);
    let output_dir = Path::new(&arguments[2]);
    let previous_output_dir = arguments.get(3).map(String::as_str).map(Path::new);
    let config_text = fs::read_to_string(config_path)
        .map_err(|error| format!("failed to read tuning config {config_path:?}: {error}"))?;
    let file_config = TuningFileConfig::parse(&config_text)?;
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
    let optimizer_config = file_config.optimizer_config()?;
    let mut optimizer = match previous_output_dir {
        Some(path) => {
            let previous_config_path = path.join("tuning-config.txt");
            let previous_config = fs::read_to_string(&previous_config_path).map_err(|error| {
                format!("failed to read previous tuning config {previous_config_path:?}: {error}")
            })?;
            if previous_config != config_text {
                return Err("resume requires the exact previous tuning configuration".to_owned());
            }
            let checkpoint_path = path.join("checkpoint.bin");
            let bytes = fs::read(&checkpoint_path)
                .map_err(|error| format!("failed to read checkpoint {checkpoint_path:?}: {error}"))?;
            let checkpoint = SpsaCheckpoint::from_bytes(&bytes).map_err(|error| error.to_string())?;
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
    )?;
    println!("output\t{}", output_dir.display());
    println!("iterations\t{}", checkpoint.completed_iterations());
    println!(
        "candidate\t{:016x}",
        file_config.candidate_weight_identifier
    );
    println!("activated\tfalse");
    Ok(())
}

fn publish_output_directory(
    output_dir: &Path,
    config_text: &str,
    checkpoint: &SpsaCheckpoint,
    report: &TuningReport,
    candidate: &chess_tune::NamedWeightArtifact,
    summary: chess_tune::SpsaRunSummary,
) -> Result<(), String> {
    if output_dir.exists() {
        return Err(format!(
            "tuning output directory already exists: {output_dir:?}"
        ));
    }
    let parent = output_dir.parent().unwrap_or_else(|| Path::new("."));
    let name = output_dir
        .file_name()
        .ok_or_else(|| "tuning output directory must have a final component".to_owned())?;
    let staging = parent.join(format!(".{}.staging", name.to_string_lossy()));
    if staging.exists() {
        return Err(format!(
            "stale tuning staging directory exists: {staging:?}"
        ));
    }
    fs::create_dir_all(&staging)
        .map_err(|error| format!("failed to create tuning staging directory: {error}"))?;
    let result = (|| {
        fs::write(staging.join("tuning-config.txt"), config_text)
            .map_err(|error| format!("failed to write tuning config: {error}"))?;
        fs::write(staging.join("checkpoint.bin"), checkpoint.to_bytes())
            .map_err(|error| format!("failed to write checkpoint: {error}"))?;
        write_tuning_report_atomic(
            &staging.join("tuning-report.txt"),
            &staging.join("tuning-report.txt.tmp"),
            report,
        )
        .map_err(|error| error.to_string())?;
        write_candidate_artifact_atomic(
            &staging.join("candidate-weights.txt"),
            &staging.join("candidate-weights.txt.tmp"),
            candidate,
        )
        .map_err(|error| error.to_string())?;
        let summary_text = format!(
            "completed_iterations\t{}\ncurrent_training_objective\t{:.17e}\nbest_training_objective\t{:.17e}\ncurrent_validation_mse\t{:.17e}\nbest_validation_mse\t{:.17e}\nactivated\tfalse\n",
            summary.completed_iterations(),
            summary.current_training_objective(),
            summary.best_training_objective(),
            summary.current_validation_mse(),
            summary.best_validation_mse(),
        );
        fs::write(staging.join("summary.tsv"), summary_text)
            .map_err(|error| format!("failed to write tuning summary: {error}"))?;
        fs::write(
            staging.join("ACTIVATION_DISABLED"),
            "This candidate is inactive. Activation requires the independent Task 21 gate.\n",
        )
        .map_err(|error| format!("failed to write activation marker: {error}"))?;
        fs::rename(&staging, output_dir)
            .map_err(|error| format!("failed to publish tuning output directory: {error}"))?;
        Ok(())
    })();
    if result.is_err() {
        let _ = fs::remove_dir_all(&staging);
    }
    result
}

fn parse_unsigned(value: &str, field: &str) -> Result<u64, String> {
    let parsed = if let Some(hex) = value.strip_prefix("0x") {
        u64::from_str_radix(hex, 16)
    } else {
        value.parse::<u64>()
    };
    parsed.map_err(|error| format!("invalid unsigned tuning field {field:?}: {error}"))
}

fn parse_source_commit(value: &str) -> Result<[u8; 20], String> {
    if value.len() != 40 || !value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err("source_commit must be exactly 40 hexadecimal characters".to_owned());
    }
    let mut output = [0_u8; 20];
    for (index, current) in output.iter_mut().enumerate() {
        *current = u8::from_str_radix(&value[index * 2..index * 2 + 2], 16)
            .map_err(|error| format!("invalid source_commit: {error}"))?;
    }
    if output.iter().all(|byte| *byte == 0) {
        return Err("source_commit must not be all zeroes".to_owned());
    }
    Ok(output)
}

#[cfg(test)]
mod tests {
    use super::{parse_source_commit, TuningFileConfig, CONFIG_MARKER};

    fn valid_config() -> String {
        format!(
            "{CONFIG_MARKER}\nengine_identifier=0x5441534b32350001\ninitial_weight_identifier=0x424153454c494e45\ncandidate_weight_identifier=0x43414e4449444154\nsource_commit=1111111111111111111111111111111111111111\ngenerated_at_unix_seconds=1\nmaximum_iterations=2\nadvance_iterations=1\nlearning_rate=0.01\nstep_decay=0.602\nperturbation_size=2.0\nperturbation_decay=0.101\nstability_constant=10.0\nminimum_weight=-2000\nmaximum_weight=2000\nregularization_strength=0.000001\nrandom_seed=7\nk_minimum=0.01\nk_maximum=2.0\nk_intervals=10\n"
        )
    }

    #[test]
    fn strict_config_parses() {
        let parsed = TuningFileConfig::parse(&valid_config()).expect("valid config");
        assert_eq!(parsed.maximum_iterations, 2);
        assert_eq!(parsed.advance_iterations, 1);
        assert_eq!(parsed.source_commit, [0x11; 20]);
    }

    #[test]
    fn unknown_duplicate_and_missing_fields_fail() {
        assert!(TuningFileConfig::parse(&(valid_config() + "unknown=1\n")).is_err());
        assert!(TuningFileConfig::parse(&(valid_config() + "random_seed=8\n")).is_err());
        assert!(TuningFileConfig::parse(&valid_config().replace("random_seed=7\n", "")).is_err());
    }

    #[test]
    fn source_commit_is_exact_and_nonzero() {
        assert_eq!(
            parse_source_commit("abababababababababababababababababababab").expect("commit"),
            [0xab; 20]
        );
        assert!(parse_source_commit("00").is_err());
        assert!(parse_source_commit("0000000000000000000000000000000000000000").is_err());
    }
}
