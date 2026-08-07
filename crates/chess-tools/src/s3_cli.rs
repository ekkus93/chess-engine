use std::{fs, path::Path};

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
        return Err("usage: chess-tools s3-self-play SOURCE_SHA CONFIG_PATH OUTPUT_DIR".to_owned());
    }
    let source_commit = parse_source_commit(&arguments[0]).map_err(|error| error.to_string())?;
    let config_path = Path::new(&arguments[1]);
    let output_dir = Path::new(&arguments[2]);
    let config_text = fs::read_to_string(config_path)
        .map_err(|error| format!("failed to read S3 self-play config {config_path:?}: {error}"))?;
    let file_config =
        SelfPlayFileConfig::from_text(&config_text).map_err(|error| error.to_string())?;
    let opening_path = Path::new(file_config.opening_path());
    let opening_text = fs::read_to_string(opening_path)
        .map_err(|error| format!("failed to read S3 opening suite {opening_path:?}: {error}"))?;
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
    println!(
        "validation_occurrences\t{}",
        manifest.validation_occurrences()
    );
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

fn publish_package(
    output_dir: &Path,
    config_text: &str,
    opening_text: &str,
    dataset: &SelfPlayDataset,
    manifest: &S3DatasetManifest,
) -> Result<(), String> {
    if output_dir.exists() {
        return Err(format!(
            "S3 dataset output directory already exists: {output_dir:?}"
        ));
    }
    let parent = output_dir.parent().unwrap_or_else(|| Path::new("."));
    let name = output_dir
        .file_name()
        .ok_or_else(|| "S3 dataset output directory must have a final component".to_owned())?;
    let staging = parent.join(format!(".{}.staging", name.to_string_lossy()));
    if staging.exists() {
        return Err(format!(
            "stale S3 dataset staging directory exists: {staging:?}"
        ));
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
