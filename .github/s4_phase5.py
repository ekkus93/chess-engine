from pathlib import Path

path = Path('crates/chess-tune/src/optimizer.rs')
text = path.read_text()

# Add LossPartition to the test imports for direct chess-loss evidence.
old = '''        tunable_values, weights_from_tunable_values, EvaluationParameterGroup, LogisticK,
        LossDataset, LossPosition, OutcomeTarget, TunableParameter, TunableParameterMask,
        TUNABLE_PARAMETER_COUNT,
'''
new = '''        tunable_values, weights_from_tunable_values, EvaluationParameterGroup, LogisticK,
        LossDataset, LossPartition, LossPosition, OutcomeTarget, TunableParameter,
        TunableParameterMask, TUNABLE_PARAMETER_COUNT,
'''
if text.count(old) != 1:
    raise SystemExit('test LossPartition import anchor missing')
text = text.replace(old, new, 1)

end = text.rfind('\n}')
tests = r'''

    const S4_DEGRADED_TEST_WEIGHT_ID: u64 = 0x5334_4445_4752_3031;

    fn material_only_mask() -> TunableParameterMask {
        TunableParameterMask::from_parameters(
            (0..10).map(|index| TunableParameter::from_index(index).expect("material parameter")),
        )
    }

    #[test]
    fn degraded_queen_material_recovers_real_chess_loss_signal() {
        let data = dataset(OutcomeTarget::Win);
        let baseline = EvaluationWeights::DEFAULT;
        let baseline_values = tunable_values(&baseline);
        let queen_mg = TunableParameter::from_index(8).expect("queen middlegame material");
        let queen_eg = TunableParameter::from_index(9).expect("queen endgame material");
        assert!(queen_mg.name().starts_with("material.queen."));
        assert!(queen_eg.name().starts_with("material.queen."));

        let mut degraded = baseline;
        queen_mg.set_value(&mut degraded, 100);
        queen_eg.set_value(&mut degraded, 100);
        EvaluationWeightSet::new(S4_DEGRADED_TEST_WEIGHT_ID, degraded)
            .validate()
            .expect("test-only degraded evaluator remains structurally valid");

        let initial_training = data
            .mean_squared_error(LossPartition::Training, &degraded, k())
            .expect("initial training loss");
        let initial_validation = data
            .mean_squared_error(LossPartition::Validation, &degraded, k())
            .expect("initial validation loss");
        let mask = material_only_mask();
        let recovery_config = SpsaConfig::new(
            128,
            SpsaSchedule::new(2_048.0, 0.602, 8.0, 0.101, 10.0)
                .expect("recovery schedule"),
            SpsaWeightBounds::new(-2_000, 2_000).expect("recovery bounds"),
            1.0e-5,
        )
        .expect("recovery config")
        .with_parameter_mask(mask)
        .expect("all material parameters form a valid mask");
        let mut optimizer = SpsaOptimizer::new(
            recovery_config,
            0x5344_5245_434f_5645,
            degraded,
            &data,
            k(),
        )
        .expect("degraded recovery optimizer starts");
        let (summary, diagnostics) = optimizer
            .advance_with_diagnostics(&data, 128)
            .expect("degraded recovery completes");
        let recovered = summary.best_weights();
        let recovered_values = tunable_values(&recovered);
        let final_training = data
            .mean_squared_error(LossPartition::Training, &recovered, k())
            .expect("recovered training loss");
        let final_validation = data
            .mean_squared_error(LossPartition::Validation, &recovered, k())
            .expect("recovered validation loss");

        let initial_queen_distance =
            (i32::from(100_i16) - i32::from(baseline_values[queen_mg.index()])).abs()
                + (i32::from(100_i16) - i32::from(baseline_values[queen_eg.index()])).abs();
        let recovered_queen_distance =
            (i32::from(recovered_values[queen_mg.index()])
                - i32::from(baseline_values[queen_mg.index()]))
            .abs()
                + (i32::from(recovered_values[queen_eg.index()])
                    - i32::from(baseline_values[queen_eg.index()]))
                .abs();

        assert!(
            recovered_queen_distance < initial_queen_distance,
            "queen material did not move toward the authoritative baseline: initial={initial_queen_distance}, recovered={recovered_queen_distance}"
        );
        assert!(
            final_training < initial_training,
            "real chess training loss did not improve: initial={initial_training}, final={final_training}"
        );
        assert!(
            final_validation <= initial_validation + 0.02,
            "held-out degradation exceeded the predeclared 0.02 tolerance: initial={initial_validation}, final={final_validation}"
        );
        assert!(
            diagnostics
                .iter()
                .any(|diagnostic| diagnostic.changed_parameter_count() > 0),
            "degraded recovery never produced an effective runtime weight update"
        );
        assert_ne!(
            weight_value_checksum(&recovered),
            weight_value_checksum(&degraded),
            "recovery candidate must have a distinct runtime value checksum"
        );

        for parameter in TunableParameter::all() {
            if !mask.contains(parameter) {
                assert_eq!(
                    recovered_values[parameter.index()],
                    baseline_values[parameter.index()],
                    "inactive parameter changed during degraded recovery: {}",
                    parameter.name()
                );
            }
        }
    }
'''
text = text[:end] + tests + text[end:]
path.write_text(text)

audit = Path('scripts/task_s4_evaluation_tuning_calibration_audit.sh')
text = audit.read_text()
anchor = "require_literal 'multi_parameter_known_answer_preserves_inactive_values_and_converges' \"$optimizer\"\n"
addition = anchor + '''require_literal 'S4_DEGRADED_TEST_WEIGHT_ID' "$optimizer"
require_literal 'degraded_queen_material_recovers_real_chess_loss_signal' "$optimizer"
require_literal 'final_validation <= initial_validation + 0.02' "$optimizer"
'''
if text.count(anchor) != 1:
    raise SystemExit('degraded recovery audit anchor missing')
text = text.replace(anchor, addition, 1)

# The test-only identity must not appear in public production adapters.
anchor = "# Temporary S4 staging controls must never become permanent evidence.\n"
check = '''for path in crates/chess-uci/src crates/chess-ffi/src crates/chess-jni/src crates/chess-jni/kotlin/src/main android-harness; do
  if grep -R --line-number --include='*.rs' --include='*.kt' 'S4_DEGRADED_TEST_WEIGHT_ID' "$path"; then
    fail "test-only degraded S4 evaluator escaped through $path"
  fi
done

'''
if text.count(anchor) != 1:
    raise SystemExit('adapter guard insertion anchor missing')
text = text.replace(anchor, check + anchor, 1)
audit.write_text(text)
