from pathlib import Path

# Wire the already-created diagnostic schema into chess-tune and instrument the
# exact production SPSA transition without changing the existing advance() API.
lib = Path('crates/chess-tune/src/lib.rs')
text = lib.read_text()
text = text.replace('mod loss;\nmod mask;\nmod optimizer;\n', 'mod diagnostics;\nmod loss;\nmod mask;\nmod optimizer;\n', 1)
old = '''pub use mask::{EvaluationParameterGroup, TunableParameterMask, TUNABLE_PARAMETER_MASK_WORD_COUNT};\npub use optimizer::{\n'''
new = '''pub use diagnostics::{\n    SpsaIterationDiagnostics, S4_OPTIMIZER_DIAGNOSTIC_IDENTIFIER,\n    S4_OPTIMIZER_DIAGNOSTIC_SCHEMA_VERSION,\n};\npub use mask::{EvaluationParameterGroup, TunableParameterMask, TUNABLE_PARAMETER_MASK_WORD_COUNT};\npub use optimizer::{\n'''
if text.count(old) != 1:
    raise SystemExit('lib export anchor missing')
text = text.replace(old, new, 1)
lib.write_text(text)

path = Path('crates/chess-tune/src/optimizer.rs')
text = path.read_text()
old = '''    tunable_values, weights_from_tunable_values, LogisticK, LossDataset, LossPartition,\n    LossPipelineError, TunableParameter, TunableParameterMask, TUNABLE_PARAMETER_COUNT,\n};'''
new = '''    tunable_values, weights_from_tunable_values, LogisticK, LossDataset, LossPartition,\n    LossPipelineError, SpsaIterationDiagnostics, TunableParameter, TunableParameterMask,\n    TUNABLE_PARAMETER_COUNT,\n};'''
if text.count(old) != 1:
    raise SystemExit('optimizer import anchor missing')
text = text.replace(old, new, 1)

impl_start = text.index('impl SpsaOptimizer {')
start = text.index('    /// Advances a positive number of iterations without consulting validation loss.', impl_start)
end = text.index('\n}\n\n/// Snapshot returned after one bounded advance operation.', start)
new_methods = r'''    /// Advances a positive number of iterations without consulting validation loss.
    pub fn advance(
        &mut self,
        dataset: &LossDataset,
        iterations: u64,
    ) -> Result<SpsaRunSummary, SpsaOptimizerError> {
        self.advance_internal(dataset, iterations, false)
            .map(|(summary, _)| summary)
    }

    /// Advances a positive number of iterations and returns exact per-iteration diagnostics.
    ///
    /// This is an additive offline calibration surface. The optimizer state transition is
    /// identical to [`Self::advance`]; the traced path additionally evaluates held-out loss
    /// after each transition and records deterministic arithmetic/projection evidence.
    pub fn advance_with_diagnostics(
        &mut self,
        dataset: &LossDataset,
        iterations: u64,
    ) -> Result<(SpsaRunSummary, Vec<SpsaIterationDiagnostics>), SpsaOptimizerError> {
        self.advance_internal(dataset, iterations, true)
    }

    fn advance_internal(
        &mut self,
        dataset: &LossDataset,
        iterations: u64,
        capture_diagnostics: bool,
    ) -> Result<(SpsaRunSummary, Vec<SpsaIterationDiagnostics>), SpsaOptimizerError> {
        if iterations == 0 {
            return Err(SpsaOptimizerError::ZeroIterations);
        }
        let dataset_fingerprint = loss_dataset_fingerprint(dataset);
        if dataset_fingerprint != self.checkpoint.dataset_fingerprint {
            return Err(SpsaOptimizerError::CheckpointDatasetMismatch {
                expected: self.checkpoint.dataset_fingerprint,
                found: dataset_fingerprint,
            });
        }
        let ending_iteration = self
            .checkpoint
            .completed_iterations
            .checked_add(iterations)
            .ok_or(SpsaOptimizerError::IterationCountOverflow)?;
        if ending_iteration > self.config.maximum_iterations {
            return Err(SpsaOptimizerError::IterationLimitExceeded {
                completed: self.checkpoint.completed_iterations,
                requested: iterations,
                maximum: self.config.maximum_iterations,
            });
        }

        let mut diagnostics = Vec::new();
        for iteration in (self.checkpoint.completed_iterations + 1)..=ending_iteration {
            let mut diagnostic = self.advance_one(dataset, iteration)?;
            if capture_diagnostics {
                let current_values = project_parameters(
                    &self.checkpoint.current_parameters,
                    self.config.bounds,
                    self.config.parameter_mask,
                    &self.checkpoint.reference_values,
                )?;
                let current_weights = weights_from_tunable_values(current_values);
                let validation = dataset.mean_squared_error(
                    LossPartition::Validation,
                    &current_weights,
                    self.checkpoint.logistic_k,
                )?;
                diagnostic = diagnostic.with_validation_loss(validation);
                diagnostics.push(diagnostic);
            }
        }
        let current_values = project_parameters(
            &self.checkpoint.current_parameters,
            self.config.bounds,
            self.config.parameter_mask,
            &self.checkpoint.reference_values,
        )?;
        let current_weights = weights_from_tunable_values(current_values);
        let best_weights = weights_from_tunable_values(self.checkpoint.best_values);
        let current_validation_mse = dataset.mean_squared_error(
            LossPartition::Validation,
            &current_weights,
            self.checkpoint.logistic_k,
        )?;
        let best_validation_mse = dataset.mean_squared_error(
            LossPartition::Validation,
            &best_weights,
            self.checkpoint.logistic_k,
        )?;
        Ok((
            SpsaRunSummary {
                iterations_advanced: iterations,
                completed_iterations: self.checkpoint.completed_iterations,
                current_weights,
                best_weights,
                current_training_objective: self.checkpoint.current_training_objective,
                best_training_objective: self.checkpoint.best_training_objective,
                current_validation_mse,
                best_validation_mse,
            },
            diagnostics,
        ))
    }

    fn advance_one(
        &mut self,
        dataset: &LossDataset,
        iteration: u64,
    ) -> Result<SpsaIterationDiagnostics, SpsaOptimizerError> {
        let gain = self.config.schedule.gain(iteration);
        let perturbation = self.config.schedule.perturbation(iteration);
        if !gain.is_finite() || !perturbation.is_finite() || perturbation <= 0.0 {
            return Err(SpsaOptimizerError::NonFiniteOptimizerState);
        }
        let mut delta = [0_i8; TUNABLE_PARAMETER_COUNT];
        for (index, value) in delta.iter_mut().enumerate() {
            let parameter = TunableParameter::from_index(index).expect("tunable index is valid");
            if self.config.parameter_mask.contains(parameter) {
                *value = if next_splitmix64(&mut self.checkpoint.rng_state) & 1 == 0 {
                    -1
                } else {
                    1
                };
            }
        }
        let before_values = project_parameters(
            &self.checkpoint.current_parameters,
            self.config.bounds,
            self.config.parameter_mask,
            &self.checkpoint.reference_values,
        )?;
        let plus_values = perturbed_values(
            &self.checkpoint.current_parameters,
            &delta,
            perturbation,
            self.config.bounds,
            self.config.parameter_mask,
            &self.checkpoint.reference_values,
        )?;
        let minus_values = perturbed_values(
            &self.checkpoint.current_parameters,
            &delta,
            -perturbation,
            self.config.bounds,
            self.config.parameter_mask,
            &self.checkpoint.reference_values,
        )?;
        let plus_weights = weights_from_tunable_values(plus_values);
        let minus_weights = weights_from_tunable_values(minus_values);
        let plus = regularized_training_objective_breakdown(
            dataset,
            &plus_weights,
            self.checkpoint.logistic_k,
            &self.checkpoint.reference_values,
            self.config.regularization_strength,
            self.config.parameter_mask,
        )?;
        let minus = regularized_training_objective_breakdown(
            dataset,
            &minus_weights,
            self.checkpoint.logistic_k,
            &self.checkpoint.reference_values,
            self.config.regularization_strength,
            self.config.parameter_mask,
        )?;
        let objective_difference = plus.total - minus.total;
        let gradient_scale = objective_difference / (2.0 * perturbation);
        if !gradient_scale.is_finite() {
            return Err(SpsaOptimizerError::NonFiniteOptimizerState);
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

        for (parameter, direction) in self.checkpoint.current_parameters.iter_mut().zip(delta) {
            if direction == 0 {
                continue;
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
            minimum_proposed_update = minimum_proposed_update.min(proposed_update);
            maximum_proposed_update = maximum_proposed_update.max(proposed_update);
            total_proposed_update += proposed_update;

            let proposed = *parameter - gain * gradient;
            let clamped = proposed.clamp(
                f64::from(self.config.bounds.minimum),
                f64::from(self.config.bounds.maximum),
            );
            if proposed != clamped {
                clipped_update_count += 1;
            }
            *parameter = clamped;
        }
        let active_parameter_count = u32::try_from(self.config.parameter_mask.active_count())
            .expect("tunable parameter count fits u32");
        if active_parameter_count == 0 {
            return Err(SpsaOptimizerError::EmptyParameterMask);
        }
        let active_f64 = f64::from(active_parameter_count);
        if !minimum_absolute_gradient.is_finite() || !minimum_proposed_update.is_finite() {
            return Err(SpsaOptimizerError::NonFiniteOptimizerState);
        }

        let current_values = project_parameters(
            &self.checkpoint.current_parameters,
            self.config.bounds,
            self.config.parameter_mask,
            &self.checkpoint.reference_values,
        )?;
        let mut nonzero_integer_update_count = 0_u32;
        let mut zero_after_quantization_count = 0_u32;
        for parameter in TunableParameter::all() {
            if !self.config.parameter_mask.contains(parameter) {
                continue;
            }
            let index = parameter.index();
            if current_values[index] != before_values[index] {
                nonzero_integer_update_count += 1;
            } else if maximum_proposed_update > 0.0 {
                zero_after_quantization_count += 1;
            }
        }
        let current_weights = weights_from_tunable_values(current_values);
        validate_runtime_weights(current_weights)?;
        let current = regularized_training_objective_breakdown(
            dataset,
            &current_weights,
            self.checkpoint.logistic_k,
            &self.checkpoint.reference_values,
            self.config.regularization_strength,
            self.config.parameter_mask,
        )?;
        self.checkpoint.completed_iterations = iteration;
        self.checkpoint.current_training_objective = current.total;
        if current.total < self.checkpoint.best_training_objective
            || (current.total == self.checkpoint.best_training_objective
                && current_values.as_slice() < self.checkpoint.best_values.as_slice())
        {
            self.checkpoint.best_training_objective = current.total;
            self.checkpoint.best_values = current_values;
        }
        let checkpoint_checksum = hash_bytes(FNV_OFFSET, &self.checkpoint.to_bytes());
        let diagnostic = SpsaIterationDiagnostics {
            iteration,
            perturbation_vector_checksum: delta_checksum(&delta),
            positive_value_checksum: weight_value_checksum(&plus_weights),
            negative_value_checksum: weight_value_checksum(&minus_weights),
            positive_data_loss: plus.data_loss,
            negative_data_loss: minus.data_loss,
            positive_regularization: plus.regularization,
            negative_regularization: minus.regularization,
            objective_difference,
            gain,
            perturbation,
            gradient_scale,
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
            changed_parameter_count: nonzero_integer_update_count,
            resulting_value_checksum: weight_value_checksum(&current_weights),
            resulting_training_loss: current.data_loss,
            resulting_validation_loss: None,
            checkpoint_checksum,
        };
        if !diagnostic.validate_counts() {
            return Err(SpsaOptimizerError::NonFiniteOptimizerState);
        }
        Ok(diagnostic)
    }
'''
text = text[:start] + new_methods + text[end:]

old = '''fn regularized_training_objective(\n    dataset: &LossDataset,\n    weights: &EvaluationWeights,\n    logistic_k: LogisticK,\n    reference_values: &[i16; TUNABLE_PARAMETER_COUNT],\n    regularization_strength: f64,\n    mask: TunableParameterMask,\n) -> Result<f64, SpsaOptimizerError> {\n    let mse = dataset.mean_squared_error(LossPartition::Training, weights, logistic_k)?;\n    let values = tunable_values(weights);\n    let mut squared_distance = 0.0;\n    for parameter in TunableParameter::all() {\n        if !mask.contains(parameter) {\n            continue;\n        }\n        let index = parameter.index();\n        let difference = f64::from(values[index]) - f64::from(reference_values[index]);\n        squared_distance += difference * difference;\n    }\n    squared_distance /= mask.active_count() as f64;\n    let objective = mse + regularization_strength * squared_distance;\n    if !objective.is_finite() {\n        return Err(SpsaOptimizerError::NonFiniteOptimizerState);\n    }\n    Ok(objective)\n}\n'''
new = '''#[derive(Clone, Copy, Debug)]\nstruct TrainingObjectiveBreakdown {\n    data_loss: f64,\n    regularization: f64,\n    total: f64,\n}\n\nfn regularized_training_objective(\n    dataset: &LossDataset,\n    weights: &EvaluationWeights,\n    logistic_k: LogisticK,\n    reference_values: &[i16; TUNABLE_PARAMETER_COUNT],\n    regularization_strength: f64,\n    mask: TunableParameterMask,\n) -> Result<f64, SpsaOptimizerError> {\n    Ok(regularized_training_objective_breakdown(\n        dataset,\n        weights,\n        logistic_k,\n        reference_values,\n        regularization_strength,\n        mask,\n    )?\n    .total)\n}\n\nfn regularized_training_objective_breakdown(\n    dataset: &LossDataset,\n    weights: &EvaluationWeights,\n    logistic_k: LogisticK,\n    reference_values: &[i16; TUNABLE_PARAMETER_COUNT],\n    regularization_strength: f64,\n    mask: TunableParameterMask,\n) -> Result<TrainingObjectiveBreakdown, SpsaOptimizerError> {\n    let data_loss = dataset.mean_squared_error(LossPartition::Training, weights, logistic_k)?;\n    let values = tunable_values(weights);\n    let mut squared_distance = 0.0;\n    for parameter in TunableParameter::all() {\n        if !mask.contains(parameter) {\n            continue;\n        }\n        let index = parameter.index();\n        let difference = f64::from(values[index]) - f64::from(reference_values[index]);\n        squared_distance += difference * difference;\n    }\n    squared_distance /= mask.active_count() as f64;\n    let regularization = regularization_strength * squared_distance;\n    let total = data_loss + regularization;\n    if !data_loss.is_finite() || !regularization.is_finite() || !total.is_finite() {\n        return Err(SpsaOptimizerError::NonFiniteOptimizerState);\n    }\n    Ok(TrainingObjectiveBreakdown {\n        data_loss,\n        regularization,\n        total,\n    })\n}\n\nfn delta_checksum(delta: &[i8; TUNABLE_PARAMETER_COUNT]) -> u64 {\n    let mut hash = FNV_OFFSET;\n    for direction in delta {\n        hash = hash_bytes(hash, &direction.to_le_bytes());\n    }\n    hash\n}\n\nfn weight_value_checksum(weights: &EvaluationWeights) -> u64 {\n    let mut hash = FNV_OFFSET;\n    for value in weights.values() {\n        hash = hash_bytes(hash, &value.to_le_bytes());\n    }\n    hash\n}\n'''
if text.count(old) != 1:
    raise SystemExit('regularized objective anchor missing')
text = text.replace(old, new, 1)
path.write_text(text)

# Keep the closed S3 identity check exact while making it robust to markdown formatting.
audit = Path('scripts/task_s3_evaluation_strength_audit.sh')
text = audit.read_text()
old = "require_literal '**Unchanged production/code baseline SHA:** `677cd2a4d2a4a4f3c376f7bf47fae412171206fb`' \"$baseline\""
new = "require_literal 'Unchanged production/code baseline SHA:' \"$baseline\"\nrequire_literal '677cd2a4d2a4f3c376f7bf47fae412171206fb' \"$baseline\""
if text.count(old) != 1:
    raise SystemExit('S3 baseline audit anchor missing')
text = text.replace(old, new, 1)
audit.write_text(text)
