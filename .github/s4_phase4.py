from pathlib import Path

path = Path('crates/chess-tune/src/optimizer.rs')
text = path.read_text()

before = '''        let before_values = project_parameters(
            &self.checkpoint.current_parameters,
            self.config.bounds,
            self.config.parameter_mask,
            &self.checkpoint.reference_values,
        )?;
'''
if text.count(before) != 1:
    raise SystemExit('pre-update projection anchor missing')
text = text.replace(before, '', 1)

start_marker = '''        let mut positive_gradient_count = 0_u32;
'''
end_marker = '''        let current_weights = weights_from_tunable_values(current_values);
'''
start = text.index(start_marker, text.index('fn advance_one('))
end = text.index(end_marker, start)
replacement = '''        let update = apply_gradient_step(
            &mut self.checkpoint.current_parameters,
            &delta,
            gradient_scale,
            gain,
            self.config.bounds,
            self.config.parameter_mask,
            &self.checkpoint.reference_values,
        )?;
        let current_values = update.current_values;
'''
text = text[:start] + replacement + text[end:]

replacements = {
    '            active_parameter_count,\n': '            active_parameter_count: update.active_parameter_count,\n',
    '            positive_gradient_count,\n': '            positive_gradient_count: update.positive_gradient_count,\n',
    '            negative_gradient_count,\n': '            negative_gradient_count: update.negative_gradient_count,\n',
    '            zero_gradient_count,\n': '            zero_gradient_count: update.zero_gradient_count,\n',
    '            minimum_absolute_gradient,\n': '            minimum_absolute_gradient: update.minimum_absolute_gradient,\n',
    '            maximum_absolute_gradient,\n': '            maximum_absolute_gradient: update.maximum_absolute_gradient,\n',
    '            mean_absolute_gradient: total_absolute_gradient / active_f64,\n': '            mean_absolute_gradient: update.mean_absolute_gradient,\n',
    '            minimum_proposed_update,\n': '            minimum_proposed_update: update.minimum_proposed_update,\n',
    '            maximum_proposed_update,\n': '            maximum_proposed_update: update.maximum_proposed_update,\n',
    '            mean_proposed_update: total_proposed_update / active_f64,\n': '            mean_proposed_update: update.mean_proposed_update,\n',
    '            zero_after_quantization_count,\n': '            zero_after_quantization_count: update.zero_after_quantization_count,\n',
    '            nonzero_integer_update_count,\n': '            nonzero_integer_update_count: update.nonzero_integer_update_count,\n',
    '            clipped_update_count,\n': '            clipped_update_count: update.clipped_update_count,\n',
    '            changed_parameter_count: nonzero_integer_update_count,\n': '            changed_parameter_count: update.nonzero_integer_update_count,\n',
}
for old, new in replacements.items():
    if text.count(old) < 1:
        raise SystemExit(f'diagnostic field anchor missing: {old!r}')
    text = text.replace(old, new, 1)

anchor = '''#[derive(Clone, Copy, Debug)]
struct TrainingObjectiveBreakdown {
'''
helper = r'''#[derive(Clone, Copy, Debug)]
struct GradientStepDiagnostics {
    current_values: [i16; TUNABLE_PARAMETER_COUNT],
    active_parameter_count: u32,
    positive_gradient_count: u32,
    negative_gradient_count: u32,
    zero_gradient_count: u32,
    minimum_absolute_gradient: f64,
    maximum_absolute_gradient: f64,
    mean_absolute_gradient: f64,
    minimum_proposed_update: f64,
    maximum_proposed_update: f64,
    mean_proposed_update: f64,
    zero_after_quantization_count: u32,
    nonzero_integer_update_count: u32,
    clipped_update_count: u32,
}

fn apply_gradient_step(
    current_parameters: &mut [f64; TUNABLE_PARAMETER_COUNT],
    delta: &[i8; TUNABLE_PARAMETER_COUNT],
    gradient_scale: f64,
    gain: f64,
    bounds: SpsaWeightBounds,
    mask: TunableParameterMask,
    reference_values: &[i16; TUNABLE_PARAMETER_COUNT],
) -> Result<GradientStepDiagnostics, SpsaOptimizerError> {
    if !gradient_scale.is_finite() || !gain.is_finite() || gain <= 0.0 {
        return Err(SpsaOptimizerError::NonFiniteOptimizerState);
    }
    let before_values = project_parameters(
        current_parameters,
        bounds,
        mask,
        reference_values,
    )?;
    let active_parameter_count = u32::try_from(mask.active_count())
        .expect("tunable parameter count fits u32");
    if active_parameter_count == 0 {
        return Err(SpsaOptimizerError::EmptyParameterMask);
    }

    let mut positive_gradient_count = 0_u32;
    let mut negative_gradient_count = 0_u32;
    let mut zero_gradient_count = 0_u32;
    let mut minimum_absolute_gradient = f64::INFINITY;
    let mut maximum_absolute_gradient = 0.0_f64;
    let mut total_absolute_gradient = 0.0_f64;
    let mut minimum_proposed_update = f64::INFINITY;
    let mut maximum_proposed_update = 0.0_f64;
    let mut total_proposed_update = 0.0_f64;
    let mut clipped_update_count = 0_u32;
    let mut proposed_nonzero = [false; TUNABLE_PARAMETER_COUNT];

    for (index, (parameter, direction)) in current_parameters
        .iter_mut()
        .zip(delta.iter().copied())
        .enumerate()
    {
        let tunable = TunableParameter::from_index(index).expect("tunable index is valid");
        if !mask.contains(tunable) {
            if direction != 0 {
                return Err(SpsaOptimizerError::NonFiniteOptimizerState);
            }
            continue;
        }
        if !matches!(direction, -1 | 1) {
            return Err(SpsaOptimizerError::NonFiniteOptimizerState);
        }
        let gradient = gradient_scale * f64::from(direction);
        if gradient > 0.0 {
            positive_gradient_count += 1;
        } else if gradient < 0.0 {
            negative_gradient_count += 1;
        } else {
            zero_gradient_count += 1;
        }
        let absolute_gradient = gradient.abs();
        minimum_absolute_gradient = minimum_absolute_gradient.min(absolute_gradient);
        maximum_absolute_gradient = maximum_absolute_gradient.max(absolute_gradient);
        total_absolute_gradient += absolute_gradient;
        let proposed_update = (gain * gradient).abs();
        proposed_nonzero[index] = proposed_update > 0.0;
        minimum_proposed_update = minimum_proposed_update.min(proposed_update);
        maximum_proposed_update = maximum_proposed_update.max(proposed_update);
        total_proposed_update += proposed_update;

        let proposed = *parameter - gain * gradient;
        let clamped = proposed.clamp(f64::from(bounds.minimum), f64::from(bounds.maximum));
        if proposed != clamped {
            clipped_update_count += 1;
        }
        *parameter = clamped;
    }
    if !minimum_absolute_gradient.is_finite() || !minimum_proposed_update.is_finite() {
        return Err(SpsaOptimizerError::NonFiniteOptimizerState);
    }

    let current_values = project_parameters(current_parameters, bounds, mask, reference_values)?;
    let mut nonzero_integer_update_count = 0_u32;
    let mut zero_after_quantization_count = 0_u32;
    for parameter in TunableParameter::all() {
        if !mask.contains(parameter) {
            continue;
        }
        let index = parameter.index();
        if current_values[index] != before_values[index] {
            nonzero_integer_update_count += 1;
        } else if proposed_nonzero[index] {
            zero_after_quantization_count += 1;
        }
    }
    let active_f64 = f64::from(active_parameter_count);
    Ok(GradientStepDiagnostics {
        current_values,
        active_parameter_count,
        positive_gradient_count,
        negative_gradient_count,
        zero_gradient_count,
        minimum_absolute_gradient,
        maximum_absolute_gradient,
        mean_absolute_gradient: total_absolute_gradient / active_f64,
        minimum_proposed_update,
        maximum_proposed_update,
        mean_proposed_update: total_proposed_update / active_f64,
        zero_after_quantization_count,
        nonzero_integer_update_count,
        clipped_update_count,
    })
}

#[derive(Clone, Copy, Debug)]
struct TrainingObjectiveBreakdown {
'''
if text.count(anchor) != 1:
    raise SystemExit('gradient helper insertion anchor missing')
text = text.replace(anchor, helper, 1)

# Extend test imports and append focused quantization/known-answer tests before module close.
old = '''    use crate::{
        tunable_values, EvaluationParameterGroup, LogisticK, LossDataset, LossPosition,
        OutcomeTarget, TunableParameter, TunableParameterMask,
    };
'''
new = '''    use crate::{
        tunable_values, weights_from_tunable_values, EvaluationParameterGroup, LogisticK,
        LossDataset, LossPosition, OutcomeTarget, TunableParameter, TunableParameterMask,
        TUNABLE_PARAMETER_COUNT,
    };
'''
if text.count(old) != 1:
    raise SystemExit('test crate import anchor missing')
text = text.replace(old, new, 1)
old = '''    use super::{
        SpsaCheckpoint, SpsaConfig, SpsaOptimizer, SpsaOptimizerError, SpsaSchedule,
        SpsaWeightBounds, SPSA_OPTIMIZER_IDENTIFIER,
    };
'''
new = '''    use super::{
        apply_gradient_step, delta_checksum, next_splitmix64, perturbed_values,
        regularized_training_objective_breakdown, weight_value_checksum, SpsaCheckpoint,
        SpsaConfig, SpsaOptimizer, SpsaOptimizerError, SpsaSchedule, SpsaWeightBounds,
        SPSA_OPTIMIZER_IDENTIFIER,
    };
'''
if text.count(old) != 1:
    raise SystemExit('test super import anchor missing')
text = text.replace(old, new, 1)

end = text.rfind('\n}')
tests = r'''

    fn single_non_material_parameter() -> TunableParameter {
        TunableParameter::from_index(778).expect("first mobility parameter is tunable")
    }

    fn one_parameter_mask() -> TunableParameterMask {
        TunableParameterMask::from_parameters([single_non_material_parameter()])
    }

    #[test]
    fn subinteger_update_is_explicitly_quantization_limited() {
        let reference = tunable_values(&EvaluationWeights::DEFAULT);
        let mut current = reference.map(f64::from);
        let parameter = single_non_material_parameter();
        let mask = one_parameter_mask();
        let mut delta = [0_i8; TUNABLE_PARAMETER_COUNT];
        delta[parameter.index()] = 1;
        let before_checksum = weight_value_checksum(&EvaluationWeights::DEFAULT);
        let update = apply_gradient_step(
            &mut current,
            &delta,
            0.002,
            0.1,
            SpsaWeightBounds::new(-2_000, 2_000).expect("bounds"),
            mask,
            &reference,
        )
        .expect("subinteger update is valid");
        assert_eq!(update.active_parameter_count, 1);
        assert_eq!(update.zero_after_quantization_count, 1);
        assert_eq!(update.nonzero_integer_update_count, 0);
        assert_eq!(update.clipped_update_count, 0);
        assert!((update.maximum_proposed_update - 0.0002).abs() < 1.0e-15);
        assert_eq!(update.current_values, reference);
        assert_eq!(
            weight_value_checksum(&weights_from_tunable_values(update.current_values)),
            before_checksum
        );
    }

    #[test]
    fn effective_integer_update_changes_runtime_checksum() {
        let reference = tunable_values(&EvaluationWeights::DEFAULT);
        let mut current = reference.map(f64::from);
        let parameter = single_non_material_parameter();
        let mask = one_parameter_mask();
        let mut delta = [0_i8; TUNABLE_PARAMETER_COUNT];
        delta[parameter.index()] = 1;
        let before_checksum = weight_value_checksum(&EvaluationWeights::DEFAULT);
        let update = apply_gradient_step(
            &mut current,
            &delta,
            -1.0,
            1.0,
            SpsaWeightBounds::new(-2_000, 2_000).expect("bounds"),
            mask,
            &reference,
        )
        .expect("integer update is valid");
        assert_eq!(update.nonzero_integer_update_count, 1);
        assert_eq!(update.zero_after_quantization_count, 0);
        assert_ne!(update.current_values[parameter.index()], reference[parameter.index()]);
        assert_ne!(
            weight_value_checksum(&weights_from_tunable_values(update.current_values)),
            before_checksum
        );
    }

    #[test]
    fn clipping_accounting_is_signed_and_exact() {
        let parameter = single_non_material_parameter();
        let mask = one_parameter_mask();
        let bounds = SpsaWeightBounds::new(-2_000, 2_000).expect("bounds");
        let mut delta = [0_i8; TUNABLE_PARAMETER_COUNT];
        delta[parameter.index()] = 1;

        for (start, gradient, expected) in [(1_999_i16, -100.0, 2_000_i16), (-1_999, 100.0, -2_000)] {
            let mut reference = tunable_values(&EvaluationWeights::DEFAULT);
            reference[parameter.index()] = start;
            let mut current = reference.map(f64::from);
            let update = apply_gradient_step(
                &mut current,
                &delta,
                gradient,
                1.0,
                bounds,
                mask,
                &reference,
            )
            .expect("clipped update is valid");
            assert_eq!(update.clipped_update_count, 1);
            assert_eq!(update.nonzero_integer_update_count, 1);
            assert_eq!(update.current_values[parameter.index()], expected);
        }
    }

    #[test]
    fn regularization_contribution_is_independently_accounted() {
        let data = dataset(OutcomeTarget::Win);
        let parameter = single_non_material_parameter();
        let mask = one_parameter_mask();
        let reference = tunable_values(&EvaluationWeights::DEFAULT);
        let mut weights = EvaluationWeights::DEFAULT;
        parameter.set_value(&mut weights, reference[parameter.index()] + 10);
        let breakdown = regularized_training_objective_breakdown(
            &data,
            &weights,
            k(),
            &reference,
            0.5,
            mask,
        )
        .expect("regularized objective is valid");
        assert!((breakdown.regularization - 50.0).abs() < 1.0e-12);
        assert!((breakdown.total - breakdown.data_loss - 50.0).abs() < 1.0e-12);
    }

    fn synthetic_spsa_run(
        seed: u64,
        mut current: [f64; TUNABLE_PARAMETER_COUNT],
        reference: [i16; TUNABLE_PARAMETER_COUNT],
        mask: TunableParameterMask,
        targets: &[(TunableParameter, i16)],
        iterations: u64,
        gain: f64,
    ) -> ([i16; TUNABLE_PARAMETER_COUNT], Vec<u64>) {
        let bounds = SpsaWeightBounds::new(-2_000, 2_000).expect("bounds");
        let mut rng = seed;
        let mut perturbation_checksums = Vec::new();
        for _ in 0..iterations {
            let mut delta = [0_i8; TUNABLE_PARAMETER_COUNT];
            for parameter in TunableParameter::all() {
                if mask.contains(parameter) {
                    delta[parameter.index()] = if next_splitmix64(&mut rng) & 1 == 0 { -1 } else { 1 };
                }
            }
            perturbation_checksums.push(delta_checksum(&delta));
            let plus = perturbed_values(&current, &delta, 2.0, bounds, mask, &reference)
                .expect("positive synthetic perturbation");
            let minus = perturbed_values(&current, &delta, -2.0, bounds, mask, &reference)
                .expect("negative synthetic perturbation");
            let objective = |values: &[i16; TUNABLE_PARAMETER_COUNT]| -> f64 {
                targets
                    .iter()
                    .map(|(parameter, target)| {
                        let error = f64::from(values[parameter.index()] - *target);
                        error * error
                    })
                    .sum()
            };
            let gradient_scale = (objective(&plus) - objective(&minus)) / 4.0;
            apply_gradient_step(
                &mut current,
                &delta,
                gradient_scale,
                gain,
                bounds,
                mask,
                &reference,
            )
            .expect("synthetic gradient update");
        }
        let final_values = super::project_parameters(&current, bounds, mask, &reference)
            .expect("synthetic final projection");
        (final_values, perturbation_checksums)
    }

    #[test]
    fn one_parameter_known_answer_moves_toward_optimum_deterministically() {
        let parameter = single_non_material_parameter();
        let mask = one_parameter_mask();
        let reference = tunable_values(&EvaluationWeights::DEFAULT);
        let mut initial = reference;
        initial[parameter.index()] = 0;
        let initial_f64 = initial.map(f64::from);
        let target = 20_i16;

        let (first, first_trace) = synthetic_spsa_run(
            0x1234,
            initial_f64,
            initial,
            mask,
            &[(parameter, target)],
            6,
            0.25,
        );
        let (second, second_trace) = synthetic_spsa_run(
            0x1234,
            initial_f64,
            initial,
            mask,
            &[(parameter, target)],
            6,
            0.25,
        );
        assert_eq!(first, second);
        assert_eq!(first_trace, second_trace);
        assert!((i32::from(first[parameter.index()]) - i32::from(target)).abs() < 20);
        assert!(first[parameter.index()] > 0);

        let (_, changed_seed_trace) = synthetic_spsa_run(
            0x5678,
            initial_f64,
            initial,
            mask,
            &[(parameter, target)],
            6,
            0.25,
        );
        assert_ne!(first_trace, changed_seed_trace);
    }

    #[test]
    fn multi_parameter_known_answer_preserves_inactive_values_and_converges() {
        let parameters = [
            TunableParameter::from_index(778).expect("mobility parameter"),
            TunableParameter::from_index(780).expect("mobility parameter"),
            TunableParameter::from_index(786).expect("feature parameter"),
        ];
        let mask = TunableParameterMask::from_parameters(parameters);
        let reference = tunable_values(&EvaluationWeights::DEFAULT);
        let mut initial = reference;
        for parameter in parameters {
            initial[parameter.index()] = 0;
        }
        let targets = [(parameters[0], 12_i16), (parameters[1], -9_i16), (parameters[2], 7_i16)];
        let initial_f64 = initial.map(f64::from);
        let (final_values, _) = synthetic_spsa_run(
            0x5eed,
            initial_f64,
            initial,
            mask,
            &targets,
            96,
            0.02,
        );
        for (parameter, target) in targets {
            assert!(
                (i32::from(final_values[parameter.index()]) - i32::from(target)).abs()
                    < i32::from(target).abs().max(1),
                "{} did not move closer to target",
                parameter.name()
            );
        }
        for parameter in TunableParameter::all() {
            if !mask.contains(parameter) {
                assert_eq!(final_values[parameter.index()], reference[parameter.index()]);
            }
        }
    }
'''
text = text[:end] + tests + text[end:]
path.write_text(text)

# Bind the diagnosis document and new regression witnesses into the permanent S4 audit.
audit = Path('scripts/task_s4_evaluation_tuning_calibration_audit.sh')
text = audit.read_text()
anchor = 'baseline=docs/RUST_CHESS_ENGINE_S4_BASELINE_2026-08-07.md\n'
addition = anchor + 'diagnosis=docs/RUST_CHESS_ENGINE_S4_ZERO_MOVEMENT_DIAGNOSIS_2026-08-07.md\n'
if text.count(anchor) != 1:
    raise SystemExit('diagnosis path audit anchor missing')
text = text.replace(anchor, addition, 1)
old = 'for path in "$spec" "$tracker" "$baseline" "$legacy"'
new = 'for path in "$spec" "$tracker" "$baseline" "$diagnosis" "$legacy"'
if text.count(old) != 1:
    raise SystemExit('diagnosis required-file audit anchor missing')
text = text.replace(old, new, 1)
anchor = "require_literal 'A failed permanent gate is not reclassified as green' \"$baseline\"\n"
addition = anchor + '''require_literal '**Workflow run:** `31198269449`' "$diagnosis"
require_literal '**Workflow job:** `92931740915`' "$diagnosis"
require_literal '**Artifact ID:** `9001742616`' "$diagnosis"
require_literal 'quantization_limited' "$diagnosis"
require_literal '`6,480`' "$diagnosis"
require_literal '`2.06410316075983228e-04`' "$diagnosis"
'''
if text.count(anchor) != 1:
    raise SystemExit('diagnosis witness audit anchor missing')
text = text.replace(anchor, addition, 1)
anchor = "require_literal 'initial_checkpoint_checksum: checkpoint_checksum(&initial_checkpoint)?' crates/chess-tools/src/tuning_cli.rs\n"
addition = anchor + '''require_literal 'fn apply_gradient_step(' "$optimizer"
require_literal 'subinteger_update_is_explicitly_quantization_limited' "$optimizer"
require_literal 'effective_integer_update_changes_runtime_checksum' "$optimizer"
require_literal 'clipping_accounting_is_signed_and_exact' "$optimizer"
require_literal 'regularization_contribution_is_independently_accounted' "$optimizer"
require_literal 'one_parameter_known_answer_moves_toward_optimum_deterministically' "$optimizer"
require_literal 'multi_parameter_known_answer_preserves_inactive_values_and_converges' "$optimizer"
'''
if text.count(anchor) != 1:
    raise SystemExit('optimizer regression audit anchor missing')
text = text.replace(anchor, addition, 1)
audit.write_text(text)
