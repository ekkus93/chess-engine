from pathlib import Path

path = Path('crates/chess-tools/src/tuning_cli.rs')
text = path.read_text()
old = '''use chess_tune::{
    EvaluationParameterGroup, KCalibrationConfig, S4OptimizerTrace, S4OptimizerTraceBinding,
    SpsaCheckpoint, SpsaConfig, SpsaOptimizer, SpsaSchedule, SpsaWeightBounds,
};'''
new = '''use chess_tune::{
    EvaluationParameterGroup, KCalibrationConfig, S4OptimizerTrace, S4OptimizerTraceBinding,
    SpsaCheckpoint, SpsaConfig, SpsaOptimizer, SpsaSchedule, SpsaWeightBounds, TunableParameter,
};'''
if text.count(old) != 1:
    raise SystemExit('S4 summary import anchor missing')
text = text.replace(old, new, 1)

old = '''            fs::write(staging.join("s4-optimizer-trace.txt"), trace_text)
                .map_err(|error| format!("failed to write S4 optimizer trace: {error}"))?;
        }
        fs::rename(&staging, output_dir)'''
new = '''            fs::write(staging.join("s4-optimizer-trace.txt"), trace_text)
                .map_err(|error| format!("failed to write S4 optimizer trace: {error}"))?;

            let mask = context.group.mask();
            let mut changed_parameter_count = 0_u32;
            let mut maximum_absolute_parameter_delta = 0_i32;
            let mut total_absolute_parameter_delta = 0_u64;
            for parameter in TunableParameter::all() {
                if !mask.contains(parameter) {
                    continue;
                }
                let initial = i32::from(parameter.value(&EvaluationWeights::DEFAULT));
                let final_value = i32::from(parameter.value(&candidate.weights));
                let delta = (final_value - initial).abs();
                if delta != 0 {
                    changed_parameter_count += 1;
                }
                maximum_absolute_parameter_delta = maximum_absolute_parameter_delta.max(delta);
                total_absolute_parameter_delta += u64::try_from(delta)
                    .expect("absolute i16 parameter delta fits u64");
            }
            let active_count = u32::try_from(mask.active_count())
                .expect("tunable parameter count fits u32");
            let mean_absolute_parameter_delta =
                total_absolute_parameter_delta as f64 / f64::from(active_count);
            let zero_after_quantization_count: u64 = trace
                .iterations()
                .iter()
                .map(|diagnostic| u64::from(diagnostic.zero_after_quantization_count()))
                .sum();
            let clipping_count: u64 = trace
                .iterations()
                .iter()
                .map(|diagnostic| u64::from(diagnostic.clipped_update_count()))
                .sum();
            let s4_summary = format!(
                concat!(
                    "group\t{}\nmask_fingerprint\t{:016x}\nactive_parameter_count\t{}\n",
                    "initial_training_loss\t{:.17e}\nfinal_training_loss\t{:.17e}\ntraining_loss_delta\t{:.17e}\n",
                    "initial_validation_loss\t{:.17e}\nfinal_validation_loss\t{:.17e}\nvalidation_loss_delta\t{:.17e}\n",
                    "changed_parameter_count\t{}\nmaximum_absolute_parameter_delta\t{}\n",
                    "mean_absolute_parameter_delta\t{:.17e}\nzero_after_quantization_count\t{}\n",
                    "clipping_count\t{}\ncandidate_value_checksum\t{:016x}\n",
                    "candidate_artifact_checksum\t{:016x}\ntrace_checksum\t{:016x}\n",
                    "activated\tfalse\ndisposition\tunassessed\n"
                ),
                context.group.name(),
                context.group.mask_fingerprint(),
                active_count,
                report.initial_training_loss,
                report.final_training_loss,
                report.final_training_loss - report.initial_training_loss,
                report.initial_validation_loss,
                report.final_validation_loss,
                report.final_validation_loss - report.initial_validation_loss,
                changed_parameter_count,
                maximum_absolute_parameter_delta,
                mean_absolute_parameter_delta,
                zero_after_quantization_count,
                clipping_count,
                evaluation_value_checksum(&candidate.weights),
                candidate.checksum,
                trace.checksum(),
            );
            fs::write(staging.join("s4-summary.tsv"), s4_summary)
                .map_err(|error| format!("failed to write S4 tuning summary: {error}"))?;
        }
        fs::rename(&staging, output_dir)'''
if text.count(old) != 1:
    raise SystemExit('S4 summary publication anchor missing')
text = text.replace(old, new, 1)

anchor = '''fn checksum_text(text: &str) -> u64 {
    hash_bytes(FNV_OFFSET, text.as_bytes())
}
'''
addition = anchor + '''
fn evaluation_value_checksum(weights: &EvaluationWeights) -> u64 {
    let mut hash = FNV_OFFSET;
    for value in weights.values() {
        hash = hash_bytes(hash, &value.to_le_bytes());
    }
    hash
}
'''
if text.count(anchor) != 1:
    raise SystemExit('S4 value checksum helper anchor missing')
text = text.replace(anchor, addition, 1)
path.write_text(text)

audit = Path('scripts/task_s4_evaluation_tuning_calibration_audit.sh')
text = audit.read_text()
anchor = "require_literal 's4-optimizer-trace.txt' crates/chess-tools/src/tuning_cli.rs\n"
addition = anchor + '''require_literal 's4-summary.tsv' crates/chess-tools/src/tuning_cli.rs
require_literal 'changed_parameter_count' crates/chess-tools/src/tuning_cli.rs
require_literal 'maximum_absolute_parameter_delta' crates/chess-tools/src/tuning_cli.rs
require_literal 'mean_absolute_parameter_delta' crates/chess-tools/src/tuning_cli.rs
require_literal 'zero_after_quantization_count' crates/chess-tools/src/tuning_cli.rs
require_literal 'clipping_count' crates/chess-tools/src/tuning_cli.rs
require_literal 'candidate_value_checksum' crates/chess-tools/src/tuning_cli.rs
require_literal 'disposition\\tunassessed' crates/chess-tools/src/tuning_cli.rs
'''
if text.count(anchor) != 1:
    raise SystemExit('S4 summary audit anchor missing')
text = text.replace(anchor, addition, 1)
audit.write_text(text)
