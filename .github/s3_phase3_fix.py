from pathlib import Path

path = Path('.github/s3_phase3.py')
text = path.read_text()
replacements = [
    (
        'marker = "    #[test]\\n    fn report_round_trip_and_checksum_are_stable() {\\n"',
        'marker = "    #[test]\\n    fn report_records_required_losses_deltas_identities_and_exact_config() {\\n"',
    ),
    (
        '        let dataset = dataset();\n',
        '        let dataset = LossDataset::new(\n            vec![position(\n                "7k/8/8/8/8/8/Q6K/8 w - - 0 1",\n                OutcomeTarget::Win,\n                3,\n            )],\n            vec![position(\n                "7k/q7/8/8/8/8/8/7K b - - 0 1",\n                OutcomeTarget::Draw,\n                2,\n            )],\n        )\n        .expect("valid dataset");\n',
    ),
    (
        '            provenance(),\n',
        '            TuningReportProvenance::new(\n                1,\n                "0.1.0-test".to_owned(),\n                [1; 20],\n                BASELINE_WEIGHT_SET_ID,\n                2,\n                "cargo run --locked -p chess-tools -- tune-group pawn_structure".to_owned(),\n            )\n            .expect("valid provenance"),\n',
    ),
    (
        '            dataset_provenance(&dataset),\n',
        '            TrainingDatasetProvenance::new(\n                1,\n                FNV_OFFSET,\n                dataset.training_occurrences(),\n                dataset.validation_occurrences(),\n            ),\n',
    ),
]
for old, new in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'phase3 fix expected exactly one witness, found {count}: {old!r}')
    text = text.replace(old, new, 1)

start_marker = '# Write S3 metadata in staging before rename.\n'
end_marker = '# Fix existing caller compile: core now owns all calls.\n'
start = text.index(start_marker)
end = text.index(end_marker, start)
lines = [
    '# Write S3 metadata in staging before the atomic directory publication.',
    'witness = \'        fs::rename(&staging, output_dir)\\n\'',
    'replacement = r\'\'\'        if let Some(context) = s3 {',
    '            fs::write(staging.join("s3-group.txt"), format!("{}\\n", context.group.name()))',
    '                .map_err(|error| format!("failed to write S3 group identity: {error}"))?;',
    '            fs::write(',
    '                staging.join("s3-dataset-manifest.txt"),',
    '                &context.manifest_text,',
    '            )',
    '            .map_err(|error| format!("failed to write S3 dataset manifest: {error}"))?;',
    '            let s3_summary = format!(',
    '                "group\\t{}\\nmask_fingerprint\\t{:016x}\\ndataset_manifest_checksum\\t{:016x}\\ninitial_training_loss\\t{:.17e}\\nfinal_training_loss\\t{:.17e}\\ntraining_loss_delta\\t{:.17e}\\ninitial_validation_loss\\t{:.17e}\\nfinal_validation_loss\\t{:.17e}\\nvalidation_loss_delta\\t{:.17e}\\nactivated\\tfalse\\n",',
    '                context.group.name(),',
    '                context.group.mask_fingerprint(),',
    '                context.manifest.checksum(),',
    '                report.initial_training_loss,',
    '                report.final_training_loss,',
    '                report.final_training_loss - report.initial_training_loss,',
    '                report.initial_validation_loss,',
    '                report.final_validation_loss,',
    '                report.final_validation_loss - report.initial_validation_loss,',
    '            );',
    '            fs::write(staging.join("s3-summary.tsv"), s3_summary)',
    '                .map_err(|error| format!("failed to write S3 tuning summary: {error}"))?;',
    '        }',
    '        fs::rename(&staging, output_dir)',
    "'''",
    'if text.count(witness) != 1:',
    '    raise SystemExit(f"tuning publisher rename witness count is {text.count(witness)}")',
    'text = text.replace(witness, replacement, 1)',
    '',
]
text = text[:start] + '\n'.join(lines) + text[end:]
path.write_text(text)
