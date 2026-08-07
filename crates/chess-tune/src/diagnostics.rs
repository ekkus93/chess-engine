use crate::TUNABLE_PARAMETER_COUNT;

/// Version of the per-iteration S4 optimizer diagnostic contract.
pub const S4_OPTIMIZER_DIAGNOSTIC_SCHEMA_VERSION: u16 = 1;
/// Stable semantic identity for S4 optimizer iteration diagnostics.
pub const S4_OPTIMIZER_DIAGNOSTIC_IDENTIFIER: u64 = 0x5334_4449_4147_3031;

/// Exact accounting for one SPSA state transition.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct SpsaIterationDiagnostics {
    pub(crate) iteration: u64,
    pub(crate) perturbation_vector_checksum: u64,
    pub(crate) positive_value_checksum: u64,
    pub(crate) negative_value_checksum: u64,
    pub(crate) positive_data_loss: f64,
    pub(crate) negative_data_loss: f64,
    pub(crate) positive_regularization: f64,
    pub(crate) negative_regularization: f64,
    pub(crate) objective_difference: f64,
    pub(crate) gain: f64,
    pub(crate) perturbation: f64,
    pub(crate) gradient_scale: f64,
    pub(crate) active_parameter_count: u32,
    pub(crate) positive_gradient_count: u32,
    pub(crate) negative_gradient_count: u32,
    pub(crate) zero_gradient_count: u32,
    pub(crate) minimum_absolute_gradient: f64,
    pub(crate) maximum_absolute_gradient: f64,
    pub(crate) mean_absolute_gradient: f64,
    pub(crate) minimum_proposed_update: f64,
    pub(crate) maximum_proposed_update: f64,
    pub(crate) mean_proposed_update: f64,
    pub(crate) zero_after_quantization_count: u32,
    pub(crate) nonzero_integer_update_count: u32,
    pub(crate) clipped_update_count: u32,
    pub(crate) changed_parameter_count: u32,
    pub(crate) resulting_value_checksum: u64,
    pub(crate) resulting_training_loss: f64,
    pub(crate) resulting_validation_loss: Option<f64>,
    pub(crate) checkpoint_checksum: u64,
}

impl SpsaIterationDiagnostics {
    /// One-based optimizer iteration number.
    #[must_use]
    pub const fn iteration(self) -> u64 {
        self.iteration
    }

    /// FNV identity of the exact active ±1 perturbation vector.
    #[must_use]
    pub const fn perturbation_vector_checksum(self) -> u64 {
        self.perturbation_vector_checksum
    }

    /// Value-only identity of the positive perturbation candidate.
    #[must_use]
    pub const fn positive_value_checksum(self) -> u64 {
        self.positive_value_checksum
    }

    /// Value-only identity of the negative perturbation candidate.
    #[must_use]
    pub const fn negative_value_checksum(self) -> u64 {
        self.negative_value_checksum
    }

    /// Unregularized training loss of the positive candidate.
    #[must_use]
    pub const fn positive_data_loss(self) -> f64 {
        self.positive_data_loss
    }

    /// Unregularized training loss of the negative candidate.
    #[must_use]
    pub const fn negative_data_loss(self) -> f64 {
        self.negative_data_loss
    }

    /// Regularization contribution added to the positive data loss.
    #[must_use]
    pub const fn positive_regularization(self) -> f64 {
        self.positive_regularization
    }

    /// Regularization contribution added to the negative data loss.
    #[must_use]
    pub const fn negative_regularization(self) -> f64 {
        self.negative_regularization
    }

    /// Positive total objective minus negative total objective.
    #[must_use]
    pub const fn objective_difference(self) -> f64 {
        self.objective_difference
    }

    /// SPSA gain for this iteration.
    #[must_use]
    pub const fn gain(self) -> f64 {
        self.gain
    }

    /// Symmetric perturbation magnitude for this iteration.
    #[must_use]
    pub const fn perturbation(self) -> f64 {
        self.perturbation
    }

    /// Central-difference scalar before multiplying by each ±1 direction.
    #[must_use]
    pub const fn gradient_scale(self) -> f64 {
        self.gradient_scale
    }

    /// Number of parameters selected by the mask.
    #[must_use]
    pub const fn active_parameter_count(self) -> u32 {
        self.active_parameter_count
    }

    /// Number of active parameters with a positive gradient estimate.
    #[must_use]
    pub const fn positive_gradient_count(self) -> u32 {
        self.positive_gradient_count
    }

    /// Number of active parameters with a negative gradient estimate.
    #[must_use]
    pub const fn negative_gradient_count(self) -> u32 {
        self.negative_gradient_count
    }

    /// Number of active parameters with an exactly zero gradient estimate.
    #[must_use]
    pub const fn zero_gradient_count(self) -> u32 {
        self.zero_gradient_count
    }

    /// Minimum absolute gradient estimate over active parameters.
    #[must_use]
    pub const fn minimum_absolute_gradient(self) -> f64 {
        self.minimum_absolute_gradient
    }

    /// Maximum absolute gradient estimate over active parameters.
    #[must_use]
    pub const fn maximum_absolute_gradient(self) -> f64 {
        self.maximum_absolute_gradient
    }

    /// Mean absolute gradient estimate over active parameters.
    #[must_use]
    pub const fn mean_absolute_gradient(self) -> f64 {
        self.mean_absolute_gradient
    }

    /// Minimum absolute proposed floating-point update over active parameters.
    #[must_use]
    pub const fn minimum_proposed_update(self) -> f64 {
        self.minimum_proposed_update
    }

    /// Maximum absolute proposed floating-point update over active parameters.
    #[must_use]
    pub const fn maximum_proposed_update(self) -> f64 {
        self.maximum_proposed_update
    }

    /// Mean absolute proposed floating-point update over active parameters.
    #[must_use]
    pub const fn mean_proposed_update(self) -> f64 {
        self.mean_proposed_update
    }

    /// Active non-zero floating updates whose runtime integer value did not change.
    #[must_use]
    pub const fn zero_after_quantization_count(self) -> u32 {
        self.zero_after_quantization_count
    }

    /// Active parameters whose projected integer value changed this iteration.
    #[must_use]
    pub const fn nonzero_integer_update_count(self) -> u32 {
        self.nonzero_integer_update_count
    }

    /// Active floating updates clipped by explicit optimizer bounds.
    #[must_use]
    pub const fn clipped_update_count(self) -> u32 {
        self.clipped_update_count
    }

    /// Dense tunable parameters whose effective runtime value changed.
    #[must_use]
    pub const fn changed_parameter_count(self) -> u32 {
        self.changed_parameter_count
    }

    /// Value-only checksum of the resulting runtime evaluator.
    #[must_use]
    pub const fn resulting_value_checksum(self) -> u64 {
        self.resulting_value_checksum
    }

    /// Unregularized training MSE after this iteration.
    #[must_use]
    pub const fn resulting_training_loss(self) -> f64 {
        self.resulting_training_loss
    }

    /// Optional held-out validation MSE, populated only by the traced path.
    #[must_use]
    pub const fn resulting_validation_loss(self) -> Option<f64> {
        self.resulting_validation_loss
    }

    /// Checksum over the serialized post-iteration checkpoint image.
    #[must_use]
    pub const fn checkpoint_checksum(self) -> u64 {
        self.checkpoint_checksum
    }

    pub(crate) fn with_validation_loss(mut self, value: f64) -> Self {
        self.resulting_validation_loss = Some(value);
        self
    }

    pub(crate) fn validate_counts(self) -> bool {
        let active = self.active_parameter_count as usize;
        active <= TUNABLE_PARAMETER_COUNT
            && self.positive_gradient_count as usize
                + self.negative_gradient_count as usize
                + self.zero_gradient_count as usize
                == active
            && self.zero_after_quantization_count as usize <= active
            && self.nonzero_integer_update_count as usize <= active
            && self.clipped_update_count as usize <= active
            && self.changed_parameter_count as usize <= active
    }
}
