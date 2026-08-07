from pathlib import Path

path = Path('.github/s4_phase5.py')
text = path.read_text()
text = text.replace(
    '        queen_mg.set_value(&mut degraded, 100);\n        queen_eg.set_value(&mut degraded, 100);',
    '        let degraded_queen_mg = baseline_values[queen_mg.index()] - 200;\n        let degraded_queen_eg = baseline_values[queen_eg.index()] - 200;\n        queen_mg.set_value(&mut degraded, degraded_queen_mg);\n        queen_eg.set_value(&mut degraded, degraded_queen_eg);',
    1,
)
old = '''        let initial_queen_distance =
            (i32::from(100_i16) - i32::from(baseline_values[queen_mg.index()])).abs()
                + (i32::from(100_i16) - i32::from(baseline_values[queen_eg.index()])).abs();'''
new = '''        let initial_queen_distance =
            (i32::from(degraded_queen_mg) - i32::from(baseline_values[queen_mg.index()])).abs()
                + (i32::from(degraded_queen_eg)
                    - i32::from(baseline_values[queen_eg.index()]))
                .abs();'''
if text.count(old) != 1:
    raise SystemExit('queen-distance fixture anchor missing')
text = text.replace(old, new, 1)

old = '''    #[test]
    fn degraded_queen_material_recovers_real_chess_loss_signal() {
        let data = dataset(OutcomeTarget::Win);'''
new = '''    fn material_recovery_dataset() -> LossDataset {
        const WHITE_NEAR_EQUAL_A: &str = "rb5k/2p5/8/8/8/8/Q7/7K w - - 0 1";
        const BLACK_NEAR_EQUAL_A: &str = "7k/q7/8/8/8/8/2P5/RB5K b - - 0 1";
        const WHITE_NEAR_EQUAL_B: &str = "rb5k/2p5/8/8/8/Q7/8/7K w - - 0 1";
        const BLACK_NEAR_EQUAL_B: &str = "7k/8/q7/8/8/8/2P5/RB5K b - - 0 1";
        LossDataset::new(
            vec![
                loss_position(WHITE_NEAR_EQUAL_A, OutcomeTarget::Draw, 4),
                loss_position(BLACK_NEAR_EQUAL_A, OutcomeTarget::Draw, 4),
            ],
            vec![
                loss_position(WHITE_NEAR_EQUAL_B, OutcomeTarget::Draw, 2),
                loss_position(BLACK_NEAR_EQUAL_B, OutcomeTarget::Draw, 2),
            ],
        )
        .expect("material recovery dataset is valid")
    }

    #[test]
    fn degraded_queen_material_recovers_real_chess_loss_signal() {
        let data = material_recovery_dataset();'''
if text.count(old) != 1:
    raise SystemExit('material recovery dataset insertion anchor missing')
text = text.replace(old, new, 1)

old = '''        let initial_training = data
            .mean_squared_error(LossPartition::Training, &degraded, k())
            .expect("initial training loss");
        let initial_validation = data
            .mean_squared_error(LossPartition::Validation, &degraded, k())
            .expect("initial validation loss");'''
new = '''        let baseline_training = data
            .mean_squared_error(LossPartition::Training, &baseline, k())
            .expect("baseline training loss");
        let baseline_validation = data
            .mean_squared_error(LossPartition::Validation, &baseline, k())
            .expect("baseline validation loss");
        let initial_training = data
            .mean_squared_error(LossPartition::Training, &degraded, k())
            .expect("initial training loss");
        let initial_validation = data
            .mean_squared_error(LossPartition::Validation, &degraded, k())
            .expect("initial validation loss");
        assert!(
            baseline_training < initial_training,
            "fixture does not expose recoverable training signal: baseline={baseline_training}, degraded={initial_training}"
        );
        assert!(
            baseline_validation < initial_validation,
            "fixture does not expose recoverable held-out signal: baseline={baseline_validation}, degraded={initial_validation}"
        );'''
if text.count(old) != 1:
    raise SystemExit('baseline-loss precondition anchor missing')
text = text.replace(old, new, 1)
path.write_text(text)
