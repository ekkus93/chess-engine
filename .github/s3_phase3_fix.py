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
path.write_text(text)
