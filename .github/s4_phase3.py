from pathlib import Path

path = Path('crates/chess-tools/src/tuning_cli.rs')
text = path.read_text()
old = '''use chess_tune::{
    EvaluationParameterGroup, KCalibrationConfig, SpsaCheckpoint, SpsaConfig, SpsaOptimizer,
    SpsaSchedule, SpsaWeightBounds,
};'''
new = '''use chess_tune::{
    EvaluationParameterGroup, KCalibrationConfig, S4OptimizerTrace, S4OptimizerTraceBinding,
    SpsaCheckpoint, SpsaConfig, SpsaOptimizer, SpsaSchedule, SpsaWeightBounds,
};'''
if text.count(old) != 1:
    raise SystemExit('tuning_cli import anchor missing')
text = text.replace(old, new, 1)

old = '''    let summary = optimizer
        .advance(&dataset, iterations)
        .map_err(|error| error.to_string())?;
    let checkpoint = optimizer.checkpoint();'''
new = '''    let initial_checkpoint = optimizer.checkpoint();
    let (summary, s4_trace) = match &s3 {
        Some(context) => {
            let binding = S4OptimizerTraceBinding {
                source_commit: file_config.source_commit,
                tuning_config_checksum: checksum_text(&config_text),
                dataset_manifest_checksum: context.manifest.checksum(),
                parameter_mask_fingerprint: context.group.mask_fingerprint(),
                initial_weight_identifier: initial_set.identifier,
                initial_weight_checksum: initial_set.checksum,
                random_seed: file_config.random_seed,
                config_fingerprint: initial_checkpoint.config_fingerprint(),
                dataset_fingerprint: initial_checkpoint.dataset_fingerprint(),
                initial_checkpoint_checksum: checkpoint_checksum(&initial_checkpoint)?,
            };
            let (summary, diagnostics) = optimizer
                .advance_with_diagnostics(&dataset, iterations)
                .map_err(|error| error.to_string())?;
            let trace = S4OptimizerTrace::new(binding, diagnostics)
                .map_err(|error| error.to_string())?;
            (summary, Some(trace))
        }
        None => (
            optimizer
                .advance(&dataset, iterations)
                .map_err(|error| error.to_string())?,
            None,
        ),
    };
    let checkpoint = optimizer.checkpoint();'''
if text.count(old) != 1:
    raise SystemExit('tuning advance anchor missing')
text = text.replace(old, new, 1)

old = '''        summary,
        s3.as_ref(),
    )?;'''
new = '''        summary,
        s3.as_ref(),
        s4_trace.as_ref(),
    )?;'''
if text.count(old) != 1:
    raise SystemExit('publish call anchor missing')
text = text.replace(old, new, 1)

old = '''    summary: chess_tune::SpsaRunSummary,
    s3: Option<&S3GroupContext>,
) -> Result<(), String> {'''
new = '''    summary: chess_tune::SpsaRunSummary,
    s3: Option<&S3GroupContext>,
    s4_trace: Option<&S4OptimizerTrace>,
) -> Result<(), String> {'''
if text.count(old) != 1:
    raise SystemExit('publish signature anchor missing')
text = text.replace(old, new, 1)

old = '''            fs::write(staging.join("s3-summary.tsv"), s3_summary)
                .map_err(|error| format!("failed to write S3 tuning summary: {error}"))?;
        }
        fs::rename(&staging, output_dir)'''
new = '''            fs::write(staging.join("s3-summary.tsv"), s3_summary)
                .map_err(|error| format!("failed to write S3 tuning summary: {error}"))?;
            let trace = s4_trace.ok_or_else(|| {
                "S3 group tuning requires the S4 optimizer trace artifact".to_owned()
            })?;
            let trace_text = trace.to_text().map_err(|error| error.to_string())?;
            fs::write(staging.join("s4-optimizer-trace.txt"), trace_text)
                .map_err(|error| format!("failed to write S4 optimizer trace: {error}"))?;
        } else if s4_trace.is_some() {
            return Err("S4 optimizer trace is only valid for provenance-bound group tuning".to_owned());
        }
        fs::rename(&staging, output_dir)'''
if text.count(old) != 1:
    raise SystemExit('publish trace insertion anchor missing')
text = text.replace(old, new, 1)

anchor = '''fn parse_unsigned(value: &str, field: &str) -> Result<u64, String> {'''
helpers = '''const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;

fn checksum_text(text: &str) -> u64 {
    hash_bytes(FNV_OFFSET, text.as_bytes())
}

fn checkpoint_checksum(checkpoint: &SpsaCheckpoint) -> Result<u64, String> {
    let bytes = checkpoint.to_bytes();
    let suffix = bytes
        .get(bytes.len().saturating_sub(8)..)
        .ok_or_else(|| "checkpoint is too short to contain its checksum".to_owned())?;
    let array: [u8; 8] = suffix
        .try_into()
        .map_err(|_| "checkpoint checksum has invalid length".to_owned())?;
    let checksum = u64::from_le_bytes(array);
    if checksum == 0 {
        return Err("checkpoint checksum must be non-zero".to_owned());
    }
    Ok(checksum)
}

fn hash_bytes(mut hash: u64, bytes: &[u8]) -> u64 {
    for byte in bytes {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    hash
}

'''
if text.count(anchor) != 1:
    raise SystemExit('helper insertion anchor missing')
text = text.replace(anchor, helpers + anchor, 1)
path.write_text(text)

# Strengthen the permanent S4 audit around trace emission.
audit = Path('scripts/task_s4_evaluation_tuning_calibration_audit.sh')
text = audit.read_text()
anchor = "require_literal 'wrong_binding_fails_closed' \"$trace\"\n"
addition = anchor + '''require_literal 'advance_with_diagnostics(&dataset, iterations)' crates/chess-tools/src/tuning_cli.rs
require_literal 's4-optimizer-trace.txt' crates/chess-tools/src/tuning_cli.rs
require_literal 'initial_checkpoint_checksum: checkpoint_checksum(&initial_checkpoint)?' crates/chess-tools/src/tuning_cli.rs
'''
if text.count(anchor) != 1:
    raise SystemExit('S4 audit CLI trace anchor missing')
text = text.replace(anchor, addition, 1)
audit.write_text(text)
