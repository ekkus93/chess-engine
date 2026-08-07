from pathlib import Path

path = Path('crates/chess-tools/src/tuning_cli.rs')
text = path.read_text()

old = '''use chess_tools::s3::S3DatasetManifest;
use chess_tools::self_play::SelfPlayDataset;
use chess_tools::tuning::{
    loss_dataset_and_provenance_from_self_play_text, write_candidate_artifact_atomic,
    write_tuning_report_atomic, TuningReport, TuningReportProvenance,
};'''
new = '''use chess_tools::s3::S3DatasetManifest;
use chess_tools::s3_candidate::{S3CandidateEnvelope, S3CandidateRegistry, S3LossEvidence};
use chess_tools::self_play::SelfPlayDataset;
use chess_tools::tuning::{
    loss_dataset_and_provenance_from_self_play_text, write_candidate_artifact_atomic,
    write_tuning_report_atomic, TuningReport, TuningReportProvenance,
};'''
if text.count(old) != 1:
    raise SystemExit('candidate registry import anchor missing')
text = text.replace(old, new, 1)

old = '''            let trace_text = trace.to_text().map_err(|error| error.to_string())?;
            fs::write(staging.join("s4-optimizer-trace.txt"), trace_text)
                .map_err(|error| format!("failed to write S4 optimizer trace: {error}"))?;

            let mask = context.group.mask();'''
new = '''            let trace_text = trace.to_text().map_err(|error| error.to_string())?;
            fs::write(staging.join("s4-optimizer-trace.txt"), trace_text)
                .map_err(|error| format!("failed to write S4 optimizer trace: {error}"))?;

            let report_text = report.serialize().map_err(|error| error.to_string())?;
            let loss = S3LossEvidence::assess(
                report.initial_training_loss,
                report.final_training_loss,
                report.initial_validation_loss,
                report.final_validation_loss,
            )
            .map_err(|error| error.to_string())?;
            let envelope = S3CandidateEnvelope::new(
                context.group,
                candidate,
                context.manifest.checksum(),
                config_text,
                &report_text,
                report.provenance.exact_command.clone(),
                loss,
            )
            .map_err(|error| error.to_string())?;
            envelope
                .validate_artifact(candidate)
                .map_err(|error| error.to_string())?;
            let mut registry = S3CandidateRegistry::default();
            registry
                .register(envelope.clone())
                .map_err(|error| error.to_string())?;
            if registry.len() != 1 || registry.is_empty() {
                return Err("candidate registry did not retain exactly one candidate".to_owned());
            }
            let envelope_text = envelope.to_text().map_err(|error| error.to_string())?;
            fs::write(staging.join("s3-candidate-envelope.txt"), envelope_text)
                .map_err(|error| format!("failed to write S3 candidate envelope: {error}"))?;
            let registry_summary = format!(
                concat!(
                    "candidate_identifier\t{:016x}\n",
                    "candidate_value_checksum\t{:016x}\n",
                    "candidate_artifact_checksum\t{:016x}\n",
                    "candidate_envelope_checksum\t{:016x}\n",
                    "loss_decision\t{}\n",
                    "registered_count\t{}\n",
                    "activated\tfalse\n"
                ),
                envelope.candidate_identifier,
                envelope.value_checksum,
                envelope.artifact_checksum,
                envelope.checksum,
                envelope.loss_decision.name(),
                registry.len(),
            );
            fs::write(staging.join("s3-candidate-registry.tsv"), registry_summary)
                .map_err(|error| format!("failed to write S3 candidate registry summary: {error}"))?;

            let mask = context.group.mask();'''
if text.count(old) != 1:
    raise SystemExit('candidate envelope insertion anchor missing')
text = text.replace(old, new, 1)
path.write_text(text)

audit = Path('scripts/task_s4_evaluation_tuning_calibration_audit.sh')
text = audit.read_text()
anchor = "require_literal 's4-summary.tsv' crates/chess-tools/src/tuning_cli.rs\n"
addition = anchor + '''require_literal 's3-candidate-envelope.txt' crates/chess-tools/src/tuning_cli.rs
require_literal 's3-candidate-registry.tsv' crates/chess-tools/src/tuning_cli.rs
require_literal 'S3CandidateRegistry::default()' crates/chess-tools/src/tuning_cli.rs
require_literal '.validate_artifact(candidate)' crates/chess-tools/src/tuning_cli.rs
require_literal 'loss_decision\\t{}' crates/chess-tools/src/tuning_cli.rs
'''
if text.count(anchor) != 1:
    raise SystemExit('candidate registry audit anchor missing')
text = text.replace(anchor, addition, 1)
audit.write_text(text)
