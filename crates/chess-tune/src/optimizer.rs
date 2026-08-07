use core::fmt;

use chess_search::{EvaluationWeightSet, EvaluationWeights, WeightValidationError};

use crate::{
    tunable_values, weights_from_tunable_values, LogisticK, LossDataset, LossPartition,
    LossPipelineError, SpsaIterationDiagnostics, TunableParameter, TunableParameterMask,
    TUNABLE_PARAMETER_COUNT,
};

/// Current binary SPSA checkpoint schema.
pub const SPSA_CHECKPOINT_SCHEMA_VERSION: u16 = 1;
/// Stable identifier for this optimizer implementation and state transition contract.
pub const SPSA_OPTIMIZER_IDENTIFIER: u64 = 0x5350_5341_5f56_3031;
/// Maximum accepted optimizer iterations in one configuration.
pub const MAX_SPSA_ITERATIONS: u64 = 1_000_000_000;
/// Runtime evaluator limit inherited by optimizer bounds.
pub const MAX_SPSA_WEIGHT_MAGNITUDE: i16 = 10_000;

const CHECKPOINT_MAGIC: [u8; 8] = *b"CHSPSA1\0";
const CHECKPOINT_U64_FIELD_COUNT: usize = 9;
const CHECKPOINT_BYTE_LENGTH: usize = 8
    + 2
    + CHECKPOINT_U64_FIELD_COUNT * 8
    + TUNABLE_PARAMETER_COUNT * 8
    + TUNABLE_PARAMETER_COUNT * 2
    + TUNABLE_PARAMETER_COUNT * 2
    + 8;
const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;
const SPLITMIX_INCREMENT: u64 = 0x9e37_79b9_7f4a_7c15;

/// SPSA gain and perturbation schedules.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct SpsaSchedule {
    learning_rate: f64,
    step_decay: f64,
    perturbation_size: f64,
    perturbation_decay: f64,
    stability_constant: f64,
}

impl SpsaSchedule {
    /// Creates explicit finite schedule constants.
    pub fn new(
        learning_rate: f64,
        step_decay: f64,
        perturbation_size: f64,
        perturbation_decay: f64,
        stability_constant: f64,
    ) -> Result<Self, SpsaOptimizerError> {
        require_finite_positive("learning_rate", learning_rate)?;
        require_finite_positive("step_decay", step_decay)?;
        if !perturbation_size.is_finite() || perturbation_size < 0.5 {
            return Err(SpsaOptimizerError::InvalidScheduleValue {
                field: "perturbation_size",
                value: perturbation_size,
                requirement: "finite and at least 0.5 centipawns",
            });
        }
        if !perturbation_decay.is_finite() || perturbation_decay < 0.0 {
            return Err(SpsaOptimizerError::InvalidScheduleValue {
                field: "perturbation_decay",
                value: perturbation_decay,
                requirement: "finite and non-negative",
            });
        }
        if !stability_constant.is_finite() || stability_constant < 0.0 {
            return Err(SpsaOptimizerError::InvalidScheduleValue {
                field: "stability_constant",
                value: stability_constant,
                requirement: "finite and non-negative",
            });
        }
        Ok(Self {
            learning_rate,
            step_decay,
            perturbation_size,
            perturbation_decay,
            stability_constant,
        })
    }

    /// Initial gain coefficient.
    #[must_use]
    pub const fn learning_rate(self) -> f64 {
        self.learning_rate
    }

    /// Gain decay exponent.
    #[must_use]
    pub const fn step_decay(self) -> f64 {
        self.step_decay
    }

    /// Initial symmetric perturbation in centipawns.
    #[must_use]
    pub const fn perturbation_size(self) -> f64 {
        self.perturbation_size
    }

    /// Perturbation decay exponent.
    #[must_use]
    pub const fn perturbation_decay(self) -> f64 {
        self.perturbation_decay
    }

    /// Non-negative gain schedule offset.
    #[must_use]
    pub const fn stability_constant(self) -> f64 {
        self.stability_constant
    }

    fn gain(self, iteration: u64) -> f64 {
        self.learning_rate / (self.stability_constant + iteration as f64).powf(self.step_decay)
    }

    fn perturbation(self, iteration: u64) -> f64 {
        self.perturbation_size / (iteration as f64).powf(self.perturbation_decay)
    }
}

/// Inclusive scalar bounds applied to every tunable evaluator parameter.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct SpsaWeightBounds {
    minimum: i16,
    maximum: i16,
}

impl SpsaWeightBounds {
    /// Creates bounds compatible with runtime evaluation validation and material ordering.
    pub fn new(minimum: i16, maximum: i16) -> Result<Self, SpsaOptimizerError> {
        if minimum >= maximum
            || minimum < -MAX_SPSA_WEIGHT_MAGNITUDE
            || maximum > MAX_SPSA_WEIGHT_MAGNITUDE
        {
            return Err(SpsaOptimizerError::InvalidWeightBounds { minimum, maximum });
        }
        let material_minimum = i32::from(minimum).max(1);
        if i32::from(maximum) < material_minimum + 3 {
            return Err(SpsaOptimizerError::InvalidWeightBounds { minimum, maximum });
        }
        Ok(Self { minimum, maximum })
    }

    /// Inclusive minimum scalar value.
    #[must_use]
    pub const fn minimum(self) -> i16 {
        self.minimum
    }

    /// Inclusive maximum scalar value.
    #[must_use]
    pub const fn maximum(self) -> i16 {
        self.maximum
    }
}

/// Complete deterministic SPSA configuration.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct SpsaConfig {
    maximum_iterations: u64,
    schedule: SpsaSchedule,
    bounds: SpsaWeightBounds,
    regularization_strength: f64,
    parameter_mask: TunableParameterMask,
}

impl SpsaConfig {
    /// Creates an explicit optimizer configuration with no hidden hyperparameters.
    pub fn new(
        maximum_iterations: u64,
        schedule: SpsaSchedule,
        bounds: SpsaWeightBounds,
        regularization_strength: f64,
    ) -> Result<Self, SpsaOptimizerError> {
        if !(1..=MAX_SPSA_ITERATIONS).contains(&maximum_iterations) {
            return Err(SpsaOptimizerError::InvalidMaximumIterations {
                found: maximum_iterations,
                maximum: MAX_SPSA_ITERATIONS,
            });
        }
        if !regularization_strength.is_finite() || regularization_strength < 0.0 {
            return Err(SpsaOptimizerError::InvalidRegularization {
                value: regularization_strength,
            });
        }
        Ok(Self {
            maximum_iterations,
            schedule,
            bounds,
            regularization_strength,
            parameter_mask: TunableParameterMask::all(),
        })
    }

    /// Maximum cumulative iteration count accepted by this run.
    #[must_use]
    pub const fn maximum_iterations(self) -> u64 {
        self.maximum_iterations
    }

    /// Gain and perturbation schedule.
    #[must_use]
    pub const fn schedule(self) -> SpsaSchedule {
        self.schedule
    }

    /// Hard scalar bounds.
    #[must_use]
    pub const fn bounds(self) -> SpsaWeightBounds {
        self.bounds
    }

    /// L2 penalty coefficient around the supplied initial weights.
    #[must_use]
    pub const fn regularization_strength(self) -> f64 {
        self.regularization_strength
    }

    /// Restricts optimization to an explicit non-empty parameter set.
    pub fn with_parameter_mask(
        mut self,
        parameter_mask: TunableParameterMask,
    ) -> Result<Self, SpsaOptimizerError> {
        validate_parameter_mask(parameter_mask)?;
        self.parameter_mask = parameter_mask;
        Ok(self)
    }

    /// Returns the exact selected parameter set.
    #[must_use]
    pub const fn parameter_mask(self) -> TunableParameterMask {
        self.parameter_mask
    }

    /// Stable exact-bit fingerprint used to bind checkpoints to configuration.
    #[must_use]
    pub fn fingerprint(self) -> u64 {
        let mut hash = FNV_OFFSET;
        hash = hash_bytes(hash, &self.maximum_iterations.to_le_bytes());
        for value in [
            self.schedule.learning_rate,
            self.schedule.step_decay,
            self.schedule.perturbation_size,
            self.schedule.perturbation_decay,
            self.schedule.stability_constant,
            self.regularization_strength,
        ] {
            hash = hash_bytes(hash, &value.to_bits().to_le_bytes());
        }
        hash = hash_bytes(hash, &self.bounds.minimum.to_le_bytes());
        hash = hash_bytes(hash, &self.bounds.maximum.to_le_bytes());
        if !self.parameter_mask.is_all() {
            hash = hash_bytes(hash, b"spsa-parameter-mask-v1");
            for word in self.parameter_mask.words() {
                hash = hash_bytes(hash, &word.to_le_bytes());
            }
        }
        hash
    }
}

/// Stable resumable optimizer state.
#[derive(Clone, Debug, PartialEq)]
pub struct SpsaCheckpoint {
    config_fingerprint: u64,
    dataset_fingerprint: u64,
    logistic_k: LogisticK,
    random_seed: u64,
    rng_state: u64,
    completed_iterations: u64,
    current_parameters: [f64; TUNABLE_PARAMETER_COUNT],
    reference_values: [i16; TUNABLE_PARAMETER_COUNT],
    best_values: [i16; TUNABLE_PARAMETER_COUNT],
    current_training_objective: f64,
    best_training_objective: f64,
}

impl SpsaCheckpoint {
    /// Configuration fingerprint required for resume.
    #[must_use]
    pub const fn config_fingerprint(&self) -> u64 {
        self.config_fingerprint
    }

    /// Canonical train/validation dataset fingerprint required for resume.
    #[must_use]
    pub const fn dataset_fingerprint(&self) -> u64 {
        self.dataset_fingerprint
    }

    /// Exact logistic constant used by the objective.
    #[must_use]
    pub const fn logistic_k(&self) -> LogisticK {
        self.logistic_k
    }

    /// Original explicit perturbation seed.
    #[must_use]
    pub const fn random_seed(&self) -> u64 {
        self.random_seed
    }

    /// Number of completed state transitions.
    #[must_use]
    pub const fn completed_iterations(&self) -> u64 {
        self.completed_iterations
    }

    /// Best training-objective weights observed so far.
    #[must_use]
    pub fn best_weights(&self) -> EvaluationWeights {
        weights_from_tunable_values(self.best_values)
    }

    /// Current regularized training objective.
    #[must_use]
    pub const fn current_training_objective(&self) -> f64 {
        self.current_training_objective
    }

    /// Best regularized training objective observed so far.
    #[must_use]
    pub const fn best_training_objective(&self) -> f64 {
        self.best_training_objective
    }

    /// Serializes a fixed-length, checksummed, little-endian checkpoint.
    #[must_use]
    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(CHECKPOINT_BYTE_LENGTH);
        bytes.extend_from_slice(&CHECKPOINT_MAGIC);
        bytes.extend_from_slice(&SPSA_CHECKPOINT_SCHEMA_VERSION.to_le_bytes());
        for value in [
            SPSA_OPTIMIZER_IDENTIFIER,
            self.config_fingerprint,
            self.dataset_fingerprint,
            self.logistic_k.value().to_bits(),
            self.random_seed,
            self.rng_state,
            self.completed_iterations,
            self.current_training_objective.to_bits(),
            self.best_training_objective.to_bits(),
        ] {
            bytes.extend_from_slice(&value.to_le_bytes());
        }
        for value in self.current_parameters {
            bytes.extend_from_slice(&value.to_bits().to_le_bytes());
        }
        for value in self.reference_values {
            bytes.extend_from_slice(&value.to_le_bytes());
        }
        for value in self.best_values {
            bytes.extend_from_slice(&value.to_le_bytes());
        }
        let checksum = hash_bytes(FNV_OFFSET, &bytes);
        bytes.extend_from_slice(&checksum.to_le_bytes());
        debug_assert_eq!(bytes.len(), CHECKPOINT_BYTE_LENGTH);
        bytes
    }

    /// Parses and validates the fixed checkpoint envelope and checksum.
    pub fn from_bytes(bytes: &[u8]) -> Result<Self, SpsaOptimizerError> {
        if bytes.len() != CHECKPOINT_BYTE_LENGTH {
            return Err(SpsaOptimizerError::CheckpointLength {
                expected: CHECKPOINT_BYTE_LENGTH,
                found: bytes.len(),
            });
        }
        let payload_length = bytes.len() - 8;
        let expected_checksum = u64::from_le_bytes(copy_array(&bytes[payload_length..])?);
        let found_checksum = hash_bytes(FNV_OFFSET, &bytes[..payload_length]);
        if found_checksum != expected_checksum {
            return Err(SpsaOptimizerError::CheckpointChecksum {
                expected: expected_checksum,
                found: found_checksum,
            });
        }
        let mut cursor = 0;
        let magic = take::<8>(bytes, &mut cursor)?;
        if magic != CHECKPOINT_MAGIC {
            return Err(SpsaOptimizerError::CheckpointMagic);
        }
        let schema_version = u16::from_le_bytes(take(bytes, &mut cursor)?);
        if schema_version != SPSA_CHECKPOINT_SCHEMA_VERSION {
            return Err(SpsaOptimizerError::CheckpointSchema {
                expected: SPSA_CHECKPOINT_SCHEMA_VERSION,
                found: schema_version,
            });
        }
        let optimizer_identifier = read_u64(bytes, &mut cursor)?;
        if optimizer_identifier != SPSA_OPTIMIZER_IDENTIFIER {
            return Err(SpsaOptimizerError::CheckpointOptimizer {
                expected: SPSA_OPTIMIZER_IDENTIFIER,
                found: optimizer_identifier,
            });
        }
        let config_fingerprint = read_u64(bytes, &mut cursor)?;
        let dataset_fingerprint = read_u64(bytes, &mut cursor)?;
        let logistic_k = LogisticK::new(f64::from_bits(read_u64(bytes, &mut cursor)?))?;
        let random_seed = read_u64(bytes, &mut cursor)?;
        let rng_state = read_u64(bytes, &mut cursor)?;
        let completed_iterations = read_u64(bytes, &mut cursor)?;
        let current_training_objective = f64::from_bits(read_u64(bytes, &mut cursor)?);
        let best_training_objective = f64::from_bits(read_u64(bytes, &mut cursor)?);
        require_checkpoint_finite("current_training_objective", current_training_objective)?;
        require_checkpoint_finite("best_training_objective", best_training_objective)?;

        let mut current_parameters = [0.0; TUNABLE_PARAMETER_COUNT];
        for value in &mut current_parameters {
            *value = f64::from_bits(read_u64(bytes, &mut cursor)?);
            require_checkpoint_finite("current_parameters", *value)?;
        }
        let mut reference_values = [0_i16; TUNABLE_PARAMETER_COUNT];
        for value in &mut reference_values {
            *value = i16::from_le_bytes(take(bytes, &mut cursor)?);
        }
        let mut best_values = [0_i16; TUNABLE_PARAMETER_COUNT];
        for value in &mut best_values {
            *value = i16::from_le_bytes(take(bytes, &mut cursor)?);
        }
        if cursor != payload_length {
            return Err(SpsaOptimizerError::CheckpointLength {
                expected: payload_length,
                found: cursor,
            });
        }
        if best_training_objective > current_training_objective {
            return Err(SpsaOptimizerError::CheckpointObjectiveOrder);
        }
        Ok(Self {
            config_fingerprint,
            dataset_fingerprint,
            logistic_k,
            random_seed,
            rng_state,
            completed_iterations,
            current_parameters,
            reference_values,
            best_values,
            current_training_objective,
            best_training_objective,
        })
    }
}

/// Stateful deterministic SPSA optimizer.
#[derive(Clone, Debug)]
pub struct SpsaOptimizer {
    config: SpsaConfig,
    checkpoint: SpsaCheckpoint,
}

impl SpsaOptimizer {
    /// Starts a new run from explicit initial weights, data, `K`, and seed.
    pub fn new(
        config: SpsaConfig,
        random_seed: u64,
        initial_weights: EvaluationWeights,
        dataset: &LossDataset,
        logistic_k: LogisticK,
    ) -> Result<Self, SpsaOptimizerError> {
        validate_parameter_mask(config.parameter_mask)?;
        validate_runtime_weights(initial_weights)?;
        let reference_values = tunable_values(&initial_weights);
        validate_values_within_bounds(&reference_values, config.bounds)?;
        let current_parameters = reference_values.map(f64::from);
        let dataset_fingerprint = loss_dataset_fingerprint(dataset);
        let current_training_objective = regularized_training_objective(
            dataset,
            &initial_weights,
            logistic_k,
            &reference_values,
            config.regularization_strength,
            config.parameter_mask,
        )?;
        Ok(Self {
            config,
            checkpoint: SpsaCheckpoint {
                config_fingerprint: config.fingerprint(),
                dataset_fingerprint,
                logistic_k,
                random_seed,
                rng_state: random_seed,
                completed_iterations: 0,
                current_parameters,
                reference_values,
                best_values: reference_values,
                current_training_objective,
                best_training_objective: current_training_objective,
            },
        })
    }

    /// Resumes an exact checkpoint only when configuration, data, and weights remain compatible.
    pub fn resume(
        config: SpsaConfig,
        dataset: &LossDataset,
        checkpoint: SpsaCheckpoint,
    ) -> Result<Self, SpsaOptimizerError> {
        validate_parameter_mask(config.parameter_mask)?;
        let expected_config = config.fingerprint();
        if checkpoint.config_fingerprint != expected_config {
            return Err(SpsaOptimizerError::CheckpointConfigMismatch {
                expected: expected_config,
                found: checkpoint.config_fingerprint,
            });
        }
        let expected_dataset = loss_dataset_fingerprint(dataset);
        if checkpoint.dataset_fingerprint != expected_dataset {
            return Err(SpsaOptimizerError::CheckpointDatasetMismatch {
                expected: expected_dataset,
                found: checkpoint.dataset_fingerprint,
            });
        }
        if checkpoint.completed_iterations > config.maximum_iterations {
            return Err(SpsaOptimizerError::IterationLimitExceeded {
                completed: checkpoint.completed_iterations,
                requested: 0,
                maximum: config.maximum_iterations,
            });
        }
        validate_values_within_bounds(&checkpoint.reference_values, config.bounds)?;
        validate_values_within_bounds(&checkpoint.best_values, config.bounds)?;
        validate_runtime_weights(weights_from_tunable_values(checkpoint.reference_values))?;
        validate_runtime_weights(weights_from_tunable_values(checkpoint.best_values))?;
        let current_values = project_parameters(
            &checkpoint.current_parameters,
            config.bounds,
            config.parameter_mask,
            &checkpoint.reference_values,
        )?;
        validate_runtime_weights(weights_from_tunable_values(current_values))?;
        let current_weights = weights_from_tunable_values(current_values);
        let current_objective = regularized_training_objective(
            dataset,
            &current_weights,
            checkpoint.logistic_k,
            &checkpoint.reference_values,
            config.regularization_strength,
            config.parameter_mask,
        )?;
        let best_weights = weights_from_tunable_values(checkpoint.best_values);
        let best_objective = regularized_training_objective(
            dataset,
            &best_weights,
            checkpoint.logistic_k,
            &checkpoint.reference_values,
            config.regularization_strength,
            config.parameter_mask,
        )?;
        require_objective_match(
            "current_training_objective",
            checkpoint.current_training_objective,
            current_objective,
        )?;
        require_objective_match(
            "best_training_objective",
            checkpoint.best_training_objective,
            best_objective,
        )?;
        Ok(Self { config, checkpoint })
    }

    /// Returns the immutable configuration.
    #[must_use]
    pub const fn config(&self) -> SpsaConfig {
        self.config
    }

    /// Returns a complete resumable snapshot.
    #[must_use]
    pub fn checkpoint(&self) -> SpsaCheckpoint {
        self.checkpoint.clone()
    }

    /// Advances a positive number of iterations without consulting validation loss.
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

        let update = apply_gradient_step(
            &mut self.checkpoint.current_parameters,
            &delta,
            gradient_scale,
            gain,
            self.config.bounds,
            self.config.parameter_mask,
            &self.checkpoint.reference_values,
        )?;
        let current_values = update.current_values;
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
            active_parameter_count: update.active_parameter_count,
            positive_gradient_count: update.positive_gradient_count,
            negative_gradient_count: update.negative_gradient_count,
            zero_gradient_count: update.zero_gradient_count,
            minimum_absolute_gradient: update.minimum_absolute_gradient,
            maximum_absolute_gradient: update.maximum_absolute_gradient,
            mean_absolute_gradient: update.mean_absolute_gradient,
            minimum_proposed_update: update.minimum_proposed_update,
            maximum_proposed_update: update.maximum_proposed_update,
            mean_proposed_update: update.mean_proposed_update,
            zero_after_quantization_count: update.zero_after_quantization_count,
            nonzero_integer_update_count: update.nonzero_integer_update_count,
            clipped_update_count: update.clipped_update_count,
            changed_parameter_count: update.nonzero_integer_update_count,
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
}

/// Snapshot returned after one bounded advance operation.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct SpsaRunSummary {
    iterations_advanced: u64,
    completed_iterations: u64,
    current_weights: EvaluationWeights,
    best_weights: EvaluationWeights,
    current_training_objective: f64,
    best_training_objective: f64,
    current_validation_mse: f64,
    best_validation_mse: f64,
}

impl SpsaRunSummary {
    /// Iterations performed by this call.
    #[must_use]
    pub const fn iterations_advanced(self) -> u64 {
        self.iterations_advanced
    }

    /// Cumulative completed iterations.
    #[must_use]
    pub const fn completed_iterations(self) -> u64 {
        self.completed_iterations
    }

    /// Current rounded runtime weights.
    #[must_use]
    pub const fn current_weights(self) -> EvaluationWeights {
        self.current_weights
    }

    /// Best training-objective weights observed so far.
    #[must_use]
    pub const fn best_weights(self) -> EvaluationWeights {
        self.best_weights
    }

    /// Current regularized training objective.
    #[must_use]
    pub const fn current_training_objective(self) -> f64 {
        self.current_training_objective
    }

    /// Best regularized training objective observed so far.
    #[must_use]
    pub const fn best_training_objective(self) -> f64 {
        self.best_training_objective
    }

    /// Current unregularized held-out validation MSE.
    #[must_use]
    pub const fn current_validation_mse(self) -> f64 {
        self.current_validation_mse
    }

    /// Validation MSE for the training-selected best weights.
    #[must_use]
    pub const fn best_validation_mse(self) -> f64 {
        self.best_validation_mse
    }
}

/// Invalid configuration, checkpoint, dataset binding, or numerical transition.
#[derive(Clone, Debug, PartialEq)]
pub enum SpsaOptimizerError {
    /// One schedule value violated its documented domain.
    InvalidScheduleValue {
        field: &'static str,
        value: f64,
        requirement: &'static str,
    },
    /// Hard bounds were reversed, too narrow, or outside runtime support.
    InvalidWeightBounds { minimum: i16, maximum: i16 },
    /// Maximum iteration count was zero or unbounded.
    InvalidMaximumIterations { found: u64, maximum: u64 },
    /// L2 coefficient was negative, infinite, or not a number.
    InvalidRegularization { value: f64 },
    /// No optimizer parameter was selected.
    EmptyParameterMask,
    /// Material values must be tuned as one coupled ordering-constrained group.
    PartialMaterialParameterMask { selected: usize },
    /// Initial or resumed weights violated runtime evaluator constraints.
    InvalidWeights { error: WeightValidationError },
    /// One explicit initial or checkpoint value was outside configured bounds.
    ParameterOutOfBounds {
        parameter: TunableParameter,
        value: i16,
        minimum: i16,
        maximum: i16,
    },
    /// No-op advance requests are rejected.
    ZeroIterations,
    /// Cumulative iteration addition overflowed.
    IterationCountOverflow,
    /// Requested work exceeded the explicit run cap.
    IterationLimitExceeded {
        completed: u64,
        requested: u64,
        maximum: u64,
    },
    /// Loss evaluation failed.
    Loss { error: LossPipelineError },
    /// A schedule, gradient, or parameter became non-finite.
    NonFiniteOptimizerState,
    /// Checkpoint byte length was not exact.
    CheckpointLength { expected: usize, found: usize },
    /// Checkpoint magic was not recognized.
    CheckpointMagic,
    /// Checkpoint schema was unsupported.
    CheckpointSchema { expected: u16, found: u16 },
    /// Checkpoint optimizer identity did not match this implementation.
    CheckpointOptimizer { expected: u64, found: u64 },
    /// Checkpoint checksum failed.
    CheckpointChecksum { expected: u64, found: u64 },
    /// Checkpoint contained a non-finite value.
    CheckpointNonFinite { field: &'static str },
    /// Stored best loss was larger than current loss.
    CheckpointObjectiveOrder,
    /// Resume configuration differed from the checkpoint.
    CheckpointConfigMismatch { expected: u64, found: u64 },
    /// Resume or advance dataset differed from the checkpoint.
    CheckpointDatasetMismatch { expected: u64, found: u64 },
    /// Stored objective did not reproduce against the bound data and configuration.
    CheckpointObjectiveMismatch {
        field: &'static str,
        stored: f64,
        recomputed: f64,
    },
}

impl fmt::Display for SpsaOptimizerError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InvalidScheduleValue {
                field,
                value,
                requirement,
            } => write!(
                formatter,
                "SPSA schedule {field} must be {requirement}, found {value}"
            ),
            Self::InvalidWeightBounds { minimum, maximum } => write!(
                formatter,
                "SPSA weight bounds are invalid: {minimum}..={maximum}"
            ),
            Self::InvalidMaximumIterations { found, maximum } => write!(
                formatter,
                "SPSA maximum iterations must be between 1 and {maximum}, found {found}"
            ),
            Self::InvalidRegularization { value } => write!(
                formatter,
                "SPSA regularization must be finite and non-negative, found {value}"
            ),
            Self::EmptyParameterMask => {
                formatter.write_str("SPSA parameter mask must select at least one parameter")
            }
            Self::PartialMaterialParameterMask { selected } => write!(
                formatter,
                "SPSA material ordering requires selecting either zero or all 10 material parameters; found {selected}"
            ),
            Self::InvalidWeights { error } => write!(formatter, "invalid SPSA weights: {error}"),
            Self::ParameterOutOfBounds {
                parameter,
                value,
                minimum,
                maximum,
            } => write!(
                formatter,
                "SPSA parameter {parameter}={value} is outside {minimum}..={maximum}"
            ),
            Self::ZeroIterations => formatter.write_str("SPSA advance iterations must be nonzero"),
            Self::IterationCountOverflow => formatter.write_str("SPSA iteration count overflow"),
            Self::IterationLimitExceeded {
                completed,
                requested,
                maximum,
            } => write!(
                formatter,
                "SPSA iteration limit exceeded: completed {completed}, requested {requested}, maximum {maximum}"
            ),
            Self::Loss { error } => write!(formatter, "SPSA loss evaluation failed: {error}"),
            Self::NonFiniteOptimizerState => {
                formatter.write_str("SPSA optimizer produced non-finite state")
            }
            Self::CheckpointLength { expected, found } => write!(
                formatter,
                "SPSA checkpoint length mismatch: expected {expected}, found {found}"
            ),
            Self::CheckpointMagic => formatter.write_str("SPSA checkpoint magic mismatch"),
            Self::CheckpointSchema { expected, found } => write!(
                formatter,
                "SPSA checkpoint schema mismatch: expected {expected}, found {found}"
            ),
            Self::CheckpointOptimizer { expected, found } => write!(
                formatter,
                "SPSA checkpoint optimizer mismatch: expected {expected:016x}, found {found:016x}"
            ),
            Self::CheckpointChecksum { expected, found } => write!(
                formatter,
                "SPSA checkpoint checksum mismatch: expected {expected:016x}, found {found:016x}"
            ),
            Self::CheckpointNonFinite { field } => {
                write!(formatter, "SPSA checkpoint field {field} is non-finite")
            }
            Self::CheckpointObjectiveOrder => formatter.write_str(
                "SPSA checkpoint best objective must not exceed current objective",
            ),
            Self::CheckpointConfigMismatch { expected, found } => write!(
                formatter,
                "SPSA checkpoint configuration mismatch: expected {expected:016x}, found {found:016x}"
            ),
            Self::CheckpointDatasetMismatch { expected, found } => write!(
                formatter,
                "SPSA checkpoint dataset mismatch: expected {expected:016x}, found {found:016x}"
            ),
            Self::CheckpointObjectiveMismatch {
                field,
                stored,
                recomputed,
            } => write!(
                formatter,
                "SPSA checkpoint {field} mismatch: stored {stored}, recomputed {recomputed}"
            ),
        }
    }
}

impl std::error::Error for SpsaOptimizerError {}

impl From<LossPipelineError> for SpsaOptimizerError {
    fn from(error: LossPipelineError) -> Self {
        Self::Loss { error }
    }
}

fn require_finite_positive(field: &'static str, value: f64) -> Result<(), SpsaOptimizerError> {
    if !value.is_finite() || value <= 0.0 {
        return Err(SpsaOptimizerError::InvalidScheduleValue {
            field,
            value,
            requirement: "finite and positive",
        });
    }
    Ok(())
}

fn require_checkpoint_finite(field: &'static str, value: f64) -> Result<(), SpsaOptimizerError> {
    if !value.is_finite() {
        return Err(SpsaOptimizerError::CheckpointNonFinite { field });
    }
    Ok(())
}

fn require_objective_match(
    field: &'static str,
    stored: f64,
    recomputed: f64,
) -> Result<(), SpsaOptimizerError> {
    let tolerance = 1.0e-12 * stored.abs().max(recomputed.abs()).max(1.0);
    if (stored - recomputed).abs() > tolerance {
        return Err(SpsaOptimizerError::CheckpointObjectiveMismatch {
            field,
            stored,
            recomputed,
        });
    }
    Ok(())
}

fn validate_parameter_mask(mask: TunableParameterMask) -> Result<(), SpsaOptimizerError> {
    if mask.is_empty() {
        return Err(SpsaOptimizerError::EmptyParameterMask);
    }
    let selected_material = TunableParameter::all()
        .take(10)
        .filter(|parameter| mask.contains(*parameter))
        .count();
    if selected_material != 0 && selected_material != 10 {
        return Err(SpsaOptimizerError::PartialMaterialParameterMask {
            selected: selected_material,
        });
    }
    Ok(())
}

fn validate_runtime_weights(weights: EvaluationWeights) -> Result<(), SpsaOptimizerError> {
    EvaluationWeightSet::new(SPSA_OPTIMIZER_IDENTIFIER, weights)
        .validate()
        .map_err(|error| SpsaOptimizerError::InvalidWeights { error })
}

fn validate_values_within_bounds(
    values: &[i16; TUNABLE_PARAMETER_COUNT],
    bounds: SpsaWeightBounds,
) -> Result<(), SpsaOptimizerError> {
    for parameter in TunableParameter::all() {
        let value = values[parameter.index()];
        if value < bounds.minimum || value > bounds.maximum {
            return Err(SpsaOptimizerError::ParameterOutOfBounds {
                parameter,
                value,
                minimum: bounds.minimum,
                maximum: bounds.maximum,
            });
        }
    }
    Ok(())
}

fn project_parameters(
    parameters: &[f64; TUNABLE_PARAMETER_COUNT],
    bounds: SpsaWeightBounds,
    mask: TunableParameterMask,
    reference_values: &[i16; TUNABLE_PARAMETER_COUNT],
) -> Result<[i16; TUNABLE_PARAMETER_COUNT], SpsaOptimizerError> {
    let mut values = [0_i16; TUNABLE_PARAMETER_COUNT];
    for (index, (destination, value)) in values.iter_mut().zip(parameters).enumerate() {
        if !value.is_finite() {
            return Err(SpsaOptimizerError::NonFiniteOptimizerState);
        }
        let parameter = TunableParameter::from_index(index).expect("tunable index is valid");
        *destination = if mask.contains(parameter) {
            value
                .round()
                .clamp(f64::from(bounds.minimum), f64::from(bounds.maximum)) as i16
        } else {
            reference_values[index]
        };
    }
    if mask.contains(TunableParameter::from_index(0).expect("material parameter exists")) {
        project_material_ordering(&mut values, bounds);
    }
    Ok(values)
}

fn project_material_ordering(
    values: &mut [i16; TUNABLE_PARAMETER_COUNT],
    bounds: SpsaWeightBounds,
) {
    for phase in 0..2 {
        let pawn_index = phase;
        let knight_index = 2 + phase;
        let bishop_index = 4 + phase;
        let rook_index = 6 + phase;
        let queen_index = 8 + phase;
        let minimum = i32::from(bounds.minimum).max(1);
        let maximum = i32::from(bounds.maximum);
        let pawn = i32::from(values[pawn_index]).clamp(minimum, maximum - 3);
        let knight = i32::from(values[knight_index]).clamp(pawn + 1, maximum - 2);
        let bishop = i32::from(values[bishop_index]).clamp(pawn + 1, maximum - 2);
        let rook = i32::from(values[rook_index]).clamp(knight.max(bishop) + 1, maximum - 1);
        let queen = i32::from(values[queen_index]).clamp(rook + 1, maximum);
        values[pawn_index] = pawn as i16;
        values[knight_index] = knight as i16;
        values[bishop_index] = bishop as i16;
        values[rook_index] = rook as i16;
        values[queen_index] = queen as i16;
    }
}

fn perturbed_values(
    parameters: &[f64; TUNABLE_PARAMETER_COUNT],
    delta: &[i8; TUNABLE_PARAMETER_COUNT],
    perturbation: f64,
    bounds: SpsaWeightBounds,
    mask: TunableParameterMask,
    reference_values: &[i16; TUNABLE_PARAMETER_COUNT],
) -> Result<[i16; TUNABLE_PARAMETER_COUNT], SpsaOptimizerError> {
    let mut perturbed = [0.0; TUNABLE_PARAMETER_COUNT];
    for ((destination, parameter), direction) in perturbed.iter_mut().zip(parameters).zip(delta) {
        *destination = *parameter + perturbation * f64::from(*direction);
    }
    project_parameters(&perturbed, bounds, mask, reference_values)
}

#[derive(Clone, Copy, Debug)]
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
    let before_values = project_parameters(current_parameters, bounds, mask, reference_values)?;
    let active_parameter_count =
        u32::try_from(mask.active_count()).expect("tunable parameter count fits u32");
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
    data_loss: f64,
    regularization: f64,
    total: f64,
}

fn regularized_training_objective(
    dataset: &LossDataset,
    weights: &EvaluationWeights,
    logistic_k: LogisticK,
    reference_values: &[i16; TUNABLE_PARAMETER_COUNT],
    regularization_strength: f64,
    mask: TunableParameterMask,
) -> Result<f64, SpsaOptimizerError> {
    Ok(regularized_training_objective_breakdown(
        dataset,
        weights,
        logistic_k,
        reference_values,
        regularization_strength,
        mask,
    )?
    .total)
}

fn regularized_training_objective_breakdown(
    dataset: &LossDataset,
    weights: &EvaluationWeights,
    logistic_k: LogisticK,
    reference_values: &[i16; TUNABLE_PARAMETER_COUNT],
    regularization_strength: f64,
    mask: TunableParameterMask,
) -> Result<TrainingObjectiveBreakdown, SpsaOptimizerError> {
    let data_loss = dataset.mean_squared_error(LossPartition::Training, weights, logistic_k)?;
    let values = tunable_values(weights);
    let mut squared_distance = 0.0;
    for parameter in TunableParameter::all() {
        if !mask.contains(parameter) {
            continue;
        }
        let index = parameter.index();
        let difference = f64::from(values[index]) - f64::from(reference_values[index]);
        squared_distance += difference * difference;
    }
    squared_distance /= mask.active_count() as f64;
    let regularization = regularization_strength * squared_distance;
    let total = data_loss + regularization;
    if !data_loss.is_finite() || !regularization.is_finite() || !total.is_finite() {
        return Err(SpsaOptimizerError::NonFiniteOptimizerState);
    }
    Ok(TrainingObjectiveBreakdown {
        data_loss,
        regularization,
        total,
    })
}

fn delta_checksum(delta: &[i8; TUNABLE_PARAMETER_COUNT]) -> u64 {
    let mut hash = FNV_OFFSET;
    for direction in delta {
        hash = hash_bytes(hash, &direction.to_le_bytes());
    }
    hash
}

fn weight_value_checksum(weights: &EvaluationWeights) -> u64 {
    let mut hash = FNV_OFFSET;
    for value in weights.values() {
        hash = hash_bytes(hash, &value.to_le_bytes());
    }
    hash
}

fn loss_dataset_fingerprint(dataset: &LossDataset) -> u64 {
    let mut hash = FNV_OFFSET;
    for (partition_tag, positions) in [(0_u8, dataset.training()), (1_u8, dataset.validation())] {
        hash = hash_bytes(hash, &[partition_tag]);
        hash = hash_bytes(hash, &(positions.len() as u64).to_le_bytes());
        for position in positions {
            let fen = position.position().to_fen();
            hash = hash_bytes(hash, &(fen.len() as u64).to_le_bytes());
            hash = hash_bytes(hash, fen.as_bytes());
            let outcome = match position.outcome() {
                crate::OutcomeTarget::Loss => 0,
                crate::OutcomeTarget::Draw => 1,
                crate::OutcomeTarget::Win => 2,
            };
            hash = hash_bytes(hash, &[outcome]);
            hash = hash_bytes(hash, &position.occurrences().to_le_bytes());
        }
    }
    hash
}

fn next_splitmix64(state: &mut u64) -> u64 {
    *state = state.wrapping_add(SPLITMIX_INCREMENT);
    let mut value = *state;
    value = (value ^ (value >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
    value = (value ^ (value >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
    value ^ (value >> 31)
}

fn hash_bytes(mut hash: u64, bytes: &[u8]) -> u64 {
    for byte in bytes {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    hash
}

fn take<const LENGTH: usize>(
    bytes: &[u8],
    cursor: &mut usize,
) -> Result<[u8; LENGTH], SpsaOptimizerError> {
    let end = cursor
        .checked_add(LENGTH)
        .ok_or(SpsaOptimizerError::CheckpointLength {
            expected: bytes.len(),
            found: *cursor,
        })?;
    let slice = bytes
        .get(*cursor..end)
        .ok_or(SpsaOptimizerError::CheckpointLength {
            expected: bytes.len(),
            found: end,
        })?;
    *cursor = end;
    copy_array(slice)
}

fn copy_array<const LENGTH: usize>(bytes: &[u8]) -> Result<[u8; LENGTH], SpsaOptimizerError> {
    bytes
        .try_into()
        .map_err(|_| SpsaOptimizerError::CheckpointLength {
            expected: LENGTH,
            found: bytes.len(),
        })
}

fn read_u64(bytes: &[u8], cursor: &mut usize) -> Result<u64, SpsaOptimizerError> {
    Ok(u64::from_le_bytes(take(bytes, cursor)?))
}

#[cfg(test)]
mod tests {
    use chess_core::Position;
    use chess_search::{EvaluationWeightSet, EvaluationWeights};

    use crate::{
        tunable_values, weights_from_tunable_values, EvaluationParameterGroup, LogisticK,
        LossDataset, LossPartition, LossPosition, OutcomeTarget, TunableParameter,
        TunableParameterMask, TUNABLE_PARAMETER_COUNT,
    };

    use super::{
        apply_gradient_step, delta_checksum, next_splitmix64, perturbed_values,
        regularized_training_objective_breakdown, weight_value_checksum, SpsaCheckpoint,
        SpsaConfig, SpsaOptimizer, SpsaOptimizerError, SpsaSchedule, SpsaWeightBounds,
        SPSA_OPTIMIZER_IDENTIFIER,
    };

    const WHITE_ADVANTAGE: &str = "7k/8/8/8/8/8/Q6K/8 w - - 0 1";
    const BLACK_ADVANTAGE: &str = "7k/q7/8/8/8/8/8/7K b - - 0 1";

    fn loss_position(fen: &str, outcome: OutcomeTarget, occurrences: u32) -> LossPosition {
        LossPosition::new(
            Position::from_fen(fen).expect("fixture FEN is valid"),
            outcome,
            occurrences,
        )
        .expect("loss row is valid")
    }

    fn dataset(validation_outcome: OutcomeTarget) -> LossDataset {
        LossDataset::new(
            vec![
                loss_position(WHITE_ADVANTAGE, OutcomeTarget::Win, 3),
                loss_position(BLACK_ADVANTAGE, OutcomeTarget::Win, 2),
            ],
            vec![loss_position(WHITE_ADVANTAGE, validation_outcome, 1)],
        )
        .expect("dataset is valid")
    }

    fn config(maximum_iterations: u64) -> SpsaConfig {
        SpsaConfig::new(
            maximum_iterations,
            SpsaSchedule::new(8.0, 0.602, 2.0, 0.101, 10.0).expect("schedule is valid"),
            SpsaWeightBounds::new(-2_000, 2_000).expect("bounds are valid"),
            1.0e-7,
        )
        .expect("config is valid")
    }

    fn k() -> LogisticK {
        LogisticK::new(1.0).expect("K is valid")
    }

    #[test]
    fn configuration_rejects_unsafe_domains() {
        assert!(SpsaSchedule::new(0.0, 0.602, 2.0, 0.101, 10.0).is_err());
        assert!(SpsaSchedule::new(8.0, 0.602, 0.49, 0.101, 10.0).is_err());
        assert!(SpsaWeightBounds::new(10, 10).is_err());
        assert!(SpsaWeightBounds::new(-10_001, 2_000).is_err());
        assert!(SpsaConfig::new(
            0,
            SpsaSchedule::new(8.0, 0.602, 2.0, 0.101, 10.0).expect("schedule"),
            SpsaWeightBounds::new(-2_000, 2_000).expect("bounds"),
            0.0,
        )
        .is_err());
    }

    #[test]
    fn identical_seed_and_inputs_are_bit_reproducible() {
        let data = dataset(OutcomeTarget::Win);
        let mut first = SpsaOptimizer::new(config(20), 42, EvaluationWeights::DEFAULT, &data, k())
            .expect("optimizer starts");
        let mut second = SpsaOptimizer::new(config(20), 42, EvaluationWeights::DEFAULT, &data, k())
            .expect("optimizer starts");
        let first_summary = first.advance(&data, 10).expect("advance succeeds");
        let second_summary = second.advance(&data, 10).expect("advance succeeds");
        assert_eq!(first_summary, second_summary);
        assert_eq!(first.checkpoint(), second.checkpoint());
    }

    #[test]
    fn checkpoint_round_trip_and_resume_match_uninterrupted_run() {
        let data = dataset(OutcomeTarget::Win);
        let mut uninterrupted =
            SpsaOptimizer::new(config(20), 77, EvaluationWeights::DEFAULT, &data, k())
                .expect("optimizer starts");
        uninterrupted.advance(&data, 12).expect("advance succeeds");

        let mut staged = SpsaOptimizer::new(config(20), 77, EvaluationWeights::DEFAULT, &data, k())
            .expect("optimizer starts");
        staged.advance(&data, 5).expect("advance succeeds");
        let encoded = staged.checkpoint().to_bytes();
        let decoded = SpsaCheckpoint::from_bytes(&encoded).expect("checkpoint parses");
        let mut resumed =
            SpsaOptimizer::resume(config(20), &data, decoded).expect("resume succeeds");
        resumed.advance(&data, 7).expect("advance succeeds");

        assert_eq!(uninterrupted.checkpoint(), resumed.checkpoint());
    }

    #[test]
    fn validation_partition_does_not_change_optimizer_state() {
        let first_data = dataset(OutcomeTarget::Win);
        let second_data = dataset(OutcomeTarget::Loss);
        let mut first =
            SpsaOptimizer::new(config(10), 99, EvaluationWeights::DEFAULT, &first_data, k())
                .expect("optimizer starts");
        let mut second = SpsaOptimizer::new(
            config(10),
            99,
            EvaluationWeights::DEFAULT,
            &second_data,
            k(),
        )
        .expect("optimizer starts");
        first.advance(&first_data, 10).expect("advance succeeds");
        second.advance(&second_data, 10).expect("advance succeeds");
        let first_checkpoint = first.checkpoint();
        let second_checkpoint = second.checkpoint();
        assert_eq!(
            first_checkpoint.current_parameters,
            second_checkpoint.current_parameters
        );
        assert_eq!(first_checkpoint.best_values, second_checkpoint.best_values);
        assert_eq!(first_checkpoint.rng_state, second_checkpoint.rng_state);
        assert_eq!(
            first_checkpoint.current_training_objective,
            second_checkpoint.current_training_objective
        );
        assert_eq!(
            first_checkpoint.best_training_objective,
            second_checkpoint.best_training_objective
        );
    }

    #[test]
    fn projected_candidates_preserve_bounds_and_runtime_weight_invariants() {
        let data = dataset(OutcomeTarget::Win);
        let mut optimizer =
            SpsaOptimizer::new(config(30), 123, EvaluationWeights::DEFAULT, &data, k())
                .expect("optimizer starts");
        let summary = optimizer.advance(&data, 30).expect("advance succeeds");
        for weights in [summary.current_weights(), summary.best_weights()] {
            EvaluationWeightSet::new(SPSA_OPTIMIZER_IDENTIFIER, weights)
                .validate()
                .expect("optimized weights remain valid");
            for value in crate::tunable_values(&weights) {
                assert!((-2_000..=2_000).contains(&value));
            }
        }
        assert!(
            summary.best_training_objective() <= optimizer.checkpoint().best_training_objective()
        );
    }

    #[test]
    fn masked_optimizer_never_changes_inactive_parameters() {
        let data = dataset(OutcomeTarget::Win);
        let mask = EvaluationParameterGroup::PawnStructure.mask();
        let masked_config = config(20)
            .with_parameter_mask(mask)
            .expect("group mask is valid");
        let baseline = tunable_values(&EvaluationWeights::DEFAULT);
        let mut optimizer = SpsaOptimizer::new(
            masked_config,
            0x5eed,
            EvaluationWeights::DEFAULT,
            &data,
            k(),
        )
        .expect("masked optimizer starts");
        let summary = optimizer
            .advance(&data, 20)
            .expect("masked advance succeeds");
        for weights in [summary.current_weights(), summary.best_weights()] {
            let values = tunable_values(&weights);
            for parameter in TunableParameter::all() {
                if !mask.contains(parameter) {
                    assert_eq!(
                        values[parameter.index()],
                        baseline[parameter.index()],
                        "inactive parameter changed: {}",
                        parameter.name()
                    );
                }
            }
        }
    }

    #[test]
    fn checkpoint_best_weights_preserve_inactive_parameters_after_masked_run() {
        let data = dataset(OutcomeTarget::Win);
        let mask = EvaluationParameterGroup::PawnStructure.mask();
        let masked_config = config(20)
            .with_parameter_mask(mask)
            .expect("group mask is valid");
        let baseline = tunable_values(&EvaluationWeights::DEFAULT);
        let mut optimizer = SpsaOptimizer::new(
            masked_config,
            0x5344_4841_5244_454e,
            EvaluationWeights::DEFAULT,
            &data,
            k(),
        )
        .expect("masked optimizer starts");
        optimizer
            .advance(&data, 20)
            .expect("masked advance succeeds");
        let best = tunable_values(&optimizer.checkpoint().best_weights());
        for parameter in TunableParameter::all() {
            if !mask.contains(parameter) {
                assert_eq!(
                    best[parameter.index()],
                    baseline[parameter.index()],
                    "inactive checkpoint best weight changed: {}",
                    parameter.name()
                );
            }
        }
    }

    #[test]
    fn mask_identity_binds_checkpoint_configuration() {
        let full = config(10);
        let group = config(10)
            .with_parameter_mask(EvaluationParameterGroup::PawnStructure.mask())
            .expect("group mask is valid");
        assert_ne!(full.fingerprint(), group.fingerprint());

        let empty = config(10).with_parameter_mask(TunableParameterMask::empty());
        assert_eq!(empty, Err(SpsaOptimizerError::EmptyParameterMask));

        let partial_material = TunableParameterMask::from_parameters([
            TunableParameter::from_index(0).expect("first material parameter"),
        ]);
        assert_eq!(
            config(10).with_parameter_mask(partial_material),
            Err(SpsaOptimizerError::PartialMaterialParameterMask { selected: 1 })
        );
    }

    #[test]
    fn checkpoint_corruption_and_binding_mismatches_fail_loudly() {
        let data = dataset(OutcomeTarget::Win);
        let optimizer = SpsaOptimizer::new(config(10), 5, EvaluationWeights::DEFAULT, &data, k())
            .expect("optimizer starts");
        let mut bytes = optimizer.checkpoint().to_bytes();
        bytes[100] ^= 0x80;
        assert!(matches!(
            SpsaCheckpoint::from_bytes(&bytes),
            Err(SpsaOptimizerError::CheckpointChecksum { .. })
        ));

        let checkpoint = optimizer.checkpoint();
        assert!(matches!(
            SpsaOptimizer::resume(config(11), &data, checkpoint.clone()),
            Err(SpsaOptimizerError::CheckpointConfigMismatch { .. })
        ));
        let other_data = dataset(OutcomeTarget::Draw);
        assert!(matches!(
            SpsaOptimizer::resume(config(10), &other_data, checkpoint),
            Err(SpsaOptimizerError::CheckpointDatasetMismatch { .. })
        ));
    }

    #[test]
    fn advance_enforces_positive_work_and_cumulative_limit() {
        let data = dataset(OutcomeTarget::Win);
        let mut optimizer =
            SpsaOptimizer::new(config(2), 1, EvaluationWeights::DEFAULT, &data, k())
                .expect("optimizer starts");
        assert_eq!(
            optimizer.advance(&data, 0),
            Err(SpsaOptimizerError::ZeroIterations)
        );
        optimizer.advance(&data, 2).expect("bounded work succeeds");
        assert!(matches!(
            optimizer.advance(&data, 1),
            Err(SpsaOptimizerError::IterationLimitExceeded { .. })
        ));
    }

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
        assert_ne!(
            update.current_values[parameter.index()],
            reference[parameter.index()]
        );
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

        for (start, gradient, expected) in [(1_999_i16, -100.0, 2_000_i16), (-1_999, 100.0, -2_000)]
        {
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
        let breakdown =
            regularized_training_objective_breakdown(&data, &weights, k(), &reference, 0.5, mask)
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
                    delta[parameter.index()] = if next_splitmix64(&mut rng) & 1 == 0 {
                        -1
                    } else {
                        1
                    };
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
        let targets = [
            (parameters[0], 12_i16),
            (parameters[1], -9_i16),
            (parameters[2], 7_i16),
        ];
        let initial_f64 = initial.map(f64::from);
        let (final_values, _) =
            synthetic_spsa_run(0x5eed, initial_f64, initial, mask, &targets, 96, 0.02);
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
                assert_eq!(
                    final_values[parameter.index()],
                    reference[parameter.index()]
                );
            }
        }
    }

    const S4_DEGRADED_TEST_WEIGHT_ID: u64 = 0x5334_4445_4752_3031;

    fn material_only_mask() -> TunableParameterMask {
        TunableParameterMask::from_parameters(
            (0..10).map(|index| TunableParameter::from_index(index).expect("material parameter")),
        )
    }

    fn material_recovery_dataset() -> LossDataset {
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
        let data = material_recovery_dataset();
        let baseline = EvaluationWeights::DEFAULT;
        let baseline_values = tunable_values(&baseline);
        let queen_mg = TunableParameter::from_index(8).expect("queen middlegame material");
        let queen_eg = TunableParameter::from_index(9).expect("queen endgame material");
        assert!(queen_mg.name().starts_with("material.queen."));
        assert!(queen_eg.name().starts_with("material.queen."));

        let mut degraded = baseline;
        let degraded_queen_mg = baseline_values[queen_mg.index()] - 200;
        let degraded_queen_eg = baseline_values[queen_eg.index()] - 200;
        queen_mg.set_value(&mut degraded, degraded_queen_mg);
        queen_eg.set_value(&mut degraded, degraded_queen_eg);
        EvaluationWeightSet::new(S4_DEGRADED_TEST_WEIGHT_ID, degraded)
            .validate()
            .expect("test-only degraded evaluator remains structurally valid");

        let baseline_training = data
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
        );
        let mask = material_only_mask();
        let recovery_config = SpsaConfig::new(
            128,
            SpsaSchedule::new(2_048.0, 0.602, 8.0, 0.101, 10.0).expect("recovery schedule"),
            SpsaWeightBounds::new(-2_000, 2_000).expect("recovery bounds"),
            1.0e-5,
        )
        .expect("recovery config")
        .with_parameter_mask(mask)
        .expect("all material parameters form a valid mask");
        let mut optimizer =
            SpsaOptimizer::new(recovery_config, 0x5344_5245_434f_5645, degraded, &data, k())
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

        let initial_queen_distance = (i32::from(degraded_queen_mg)
            - i32::from(baseline_values[queen_mg.index()]))
        .abs()
            + (i32::from(degraded_queen_eg) - i32::from(baseline_values[queen_eg.index()])).abs();
        let recovered_queen_distance = (i32::from(recovered_values[queen_mg.index()])
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
}
