from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one witness, found {count}: {old!r}")
    p.write_text(text.replace(old, new, 1))


mask = Path("crates/chess-tune/src/mask.rs")
mask.write_text(r'''use crate::{
    EvaluationFeature, TunableParameter, TunableParameterDescriptor, TUNABLE_PARAMETER_COUNT,
};

/// Number of machine words required to represent every named evaluator parameter.
pub const TUNABLE_PARAMETER_MASK_WORD_COUNT: usize = TUNABLE_PARAMETER_COUNT.div_ceil(64);

const LAST_WORD_BITS: usize = TUNABLE_PARAMETER_COUNT % 64;
const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;

/// Fixed-size deterministic selection of named evaluator parameters.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TunableParameterMask {
    words: [u64; TUNABLE_PARAMETER_MASK_WORD_COUNT],
}

impl TunableParameterMask {
    /// Selects no parameters.
    #[must_use]
    pub const fn empty() -> Self {
        Self {
            words: [0; TUNABLE_PARAMETER_MASK_WORD_COUNT],
        }
    }

    /// Selects every named parameter.
    #[must_use]
    pub fn all() -> Self {
        let mut words = [u64::MAX; TUNABLE_PARAMETER_MASK_WORD_COUNT];
        if LAST_WORD_BITS != 0 {
            words[TUNABLE_PARAMETER_MASK_WORD_COUNT - 1] = (1_u64 << LAST_WORD_BITS) - 1;
        }
        Self { words }
    }

    /// Builds a selection from stable parameter identities.
    #[must_use]
    pub fn from_parameters(parameters: impl IntoIterator<Item = TunableParameter>) -> Self {
        let mut output = Self::empty();
        for parameter in parameters {
            output.set(parameter);
        }
        output
    }

    /// Returns whether one parameter is selected.
    #[must_use]
    pub const fn contains(self, parameter: TunableParameter) -> bool {
        let index = parameter.index();
        let word = index / 64;
        let bit = index % 64;
        self.words[word] & (1_u64 << bit) != 0
    }

    /// Returns the number of selected parameters.
    #[must_use]
    pub fn active_count(self) -> usize {
        self.words.iter().map(|word| word.count_ones() as usize).sum()
    }

    /// Returns whether no parameter is selected.
    #[must_use]
    pub const fn is_empty(self) -> bool {
        let mut index = 0;
        while index < TUNABLE_PARAMETER_MASK_WORD_COUNT {
            if self.words[index] != 0 {
                return false;
            }
            index += 1;
        }
        true
    }

    /// Returns whether every named parameter is selected.
    #[must_use]
    pub fn is_all(self) -> bool {
        self == Self::all()
    }

    /// Returns the union of two selections.
    #[must_use]
    pub fn union(self, other: Self) -> Self {
        let mut output = Self::empty();
        for (destination, (left, right)) in output
            .words
            .iter_mut()
            .zip(self.words.into_iter().zip(other.words))
        {
            *destination = left | right;
        }
        output
    }

    /// Returns a stable FNV-1a identity over the raw selection words.
    #[must_use]
    pub fn fingerprint(self) -> u64 {
        let mut hash = FNV_OFFSET;
        for word in self.words {
            for byte in word.to_le_bytes() {
                hash ^= u64::from(byte);
                hash = hash.wrapping_mul(FNV_PRIME);
            }
        }
        hash
    }

    /// Returns the stable raw word image for provenance and tests.
    #[must_use]
    pub const fn words(self) -> [u64; TUNABLE_PARAMETER_MASK_WORD_COUNT] {
        self.words
    }

    fn set(&mut self, parameter: TunableParameter) {
        let index = parameter.index();
        self.words[index / 64] |= 1_u64 << (index % 64);
    }
}

/// S3's predeclared existing-evaluator tuning groups.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum EvaluationParameterGroup {
    /// Material values and all piece-square tables.
    MaterialAndPieceSquare,
    /// Mobility plus bishop-pair and rook-activity terms.
    MobilityAndActivity,
    /// Isolated, doubled, passed, and connected pawn terms.
    PawnStructure,
    /// King shield, king-zone pressure, and space.
    KingSafetyAndSpace,
    /// Both tapered components of the king-activity term.
    EndgameKingActivity,
    /// Every existing named evaluator parameter.
    FullExistingEvaluator,
}

impl EvaluationParameterGroup {
    /// Stable S3 group order.
    pub const ALL: [Self; 6] = [
        Self::MaterialAndPieceSquare,
        Self::MobilityAndActivity,
        Self::PawnStructure,
        Self::KingSafetyAndSpace,
        Self::EndgameKingActivity,
        Self::FullExistingEvaluator,
    ];

    /// Stable machine-readable group name.
    #[must_use]
    pub const fn name(self) -> &'static str {
        match self {
            Self::MaterialAndPieceSquare => "material_and_piece_square",
            Self::MobilityAndActivity => "mobility_and_activity",
            Self::PawnStructure => "pawn_structure",
            Self::KingSafetyAndSpace => "king_safety_and_space",
            Self::EndgameKingActivity => "endgame_king_activity",
            Self::FullExistingEvaluator => "full_existing_evaluator",
        }
    }

    /// Returns the exact deterministic parameter mask for this group.
    #[must_use]
    pub fn mask(self) -> TunableParameterMask {
        if self == Self::FullExistingEvaluator {
            return TunableParameterMask::all();
        }
        TunableParameterMask::from_parameters(TunableParameter::all().filter(|parameter| {
            match (self, parameter.descriptor()) {
                (
                    Self::MaterialAndPieceSquare,
                    TunableParameterDescriptor::Material { .. }
                    | TunableParameterDescriptor::PieceSquare { .. },
                ) => true,
                (Self::MobilityAndActivity, TunableParameterDescriptor::Mobility { .. }) => true,
                (
                    Self::MobilityAndActivity,
                    TunableParameterDescriptor::Feature { feature, .. },
                ) => matches!(
                    feature,
                    EvaluationFeature::BishopPair
                        | EvaluationFeature::RookOpenFile
                        | EvaluationFeature::RookSemiOpenFile
                        | EvaluationFeature::RookSeventhRank
                ),
                (
                    Self::PawnStructure,
                    TunableParameterDescriptor::Feature { feature, .. },
                ) => matches!(
                    feature,
                    EvaluationFeature::IsolatedPawn
                        | EvaluationFeature::DoubledPawn
                        | EvaluationFeature::PassedPawn
                        | EvaluationFeature::ConnectedPawn
                ),
                (
                    Self::KingSafetyAndSpace,
                    TunableParameterDescriptor::Feature { feature, .. },
                ) => matches!(
                    feature,
                    EvaluationFeature::KingShield
                        | EvaluationFeature::KingZoneAttack
                        | EvaluationFeature::Space
                ),
                (
                    Self::EndgameKingActivity,
                    TunableParameterDescriptor::Feature {
                        feature: EvaluationFeature::KingActivity,
                        ..
                    },
                ) => true,
                _ => false,
            }
        }))
    }

    /// Stable identity of the exact group mask.
    #[must_use]
    pub fn mask_fingerprint(self) -> u64 {
        self.mask().fingerprint()
    }
}

#[cfg(test)]
mod tests {
    use super::{EvaluationParameterGroup, TunableParameterMask};
    use crate::{TunableParameter, TUNABLE_PARAMETER_COUNT};

    #[test]
    fn group_masks_cover_the_existing_evaluator_without_overlap() {
        let expected = [778, 16, 8, 6, 2, 810];
        for (group, count) in EvaluationParameterGroup::ALL.into_iter().zip(expected) {
            assert_eq!(group.mask().active_count(), count, "{}", group.name());
            assert_ne!(group.mask_fingerprint(), 0);
        }

        let mut union = TunableParameterMask::empty();
        for group in EvaluationParameterGroup::ALL.into_iter().take(5) {
            let mask = group.mask();
            for parameter in TunableParameter::all() {
                assert!(
                    !(union.contains(parameter) && mask.contains(parameter)),
                    "parameter {} appears in more than one pre-full group",
                    parameter.name()
                );
            }
            union = union.union(mask);
        }
        assert_eq!(union.active_count(), TUNABLE_PARAMETER_COUNT);
        assert_eq!(union, TunableParameterMask::all());
    }

    #[test]
    fn raw_mask_round_trip_is_stable() {
        let selected = TunableParameterMask::from_parameters([
            TunableParameter::from_index(0).expect("first parameter"),
            TunableParameter::from_index(TUNABLE_PARAMETER_COUNT - 1).expect("last parameter"),
        ]);
        assert_eq!(selected.active_count(), 2);
        assert!(!selected.is_all());
        assert!(!selected.is_empty());
        assert_ne!(selected.fingerprint(), TunableParameterMask::all().fingerprint());
    }
}
''')

replace_once(
    "crates/chess-tune/src/lib.rs",
    "mod loss;\nmod optimizer;\n",
    "mod loss;\nmod mask;\nmod optimizer;\n",
)
replace_once(
    "crates/chess-tune/src/lib.rs",
    "pub use optimizer::{\n",
    "pub use mask::{\n    EvaluationParameterGroup, TunableParameterMask, TUNABLE_PARAMETER_MASK_WORD_COUNT,\n};\npub use optimizer::{\n",
)

# Make SPSA group-aware without changing the fingerprint of the legacy full mask.
opt = Path("crates/chess-tune/src/optimizer.rs")
text = opt.read_text()
text = text.replace(
    "    LossPipelineError, TunableParameter, TUNABLE_PARAMETER_COUNT,\n",
    "    LossPipelineError, TunableParameter, TunableParameterMask, TUNABLE_PARAMETER_COUNT,\n",
    1,
)
text = text.replace(
    "    regularization_strength: f64,\n}\n\nimpl SpsaConfig {",
    "    regularization_strength: f64,\n    parameter_mask: TunableParameterMask,\n}\n\nimpl SpsaConfig {",
    1,
)
text = text.replace(
    "            bounds,\n            regularization_strength,\n        })",
    "            bounds,\n            regularization_strength,\n            parameter_mask: TunableParameterMask::all(),\n        })",
    1,
)
old = '''    /// L2 penalty coefficient around the supplied initial weights.\n    #[must_use]\n    pub const fn regularization_strength(self) -> f64 {\n        self.regularization_strength\n    }\n\n    /// Stable exact-bit fingerprint used to bind checkpoints to configuration.\n'''
new = '''    /// L2 penalty coefficient around the supplied initial weights.\n    #[must_use]\n    pub const fn regularization_strength(self) -> f64 {\n        self.regularization_strength\n    }\n\n    /// Restricts optimization to an explicit non-empty parameter set.\n    pub fn with_parameter_mask(\n        mut self,\n        parameter_mask: TunableParameterMask,\n    ) -> Result<Self, SpsaOptimizerError> {\n        validate_parameter_mask(parameter_mask)?;\n        self.parameter_mask = parameter_mask;\n        Ok(self)\n    }\n\n    /// Returns the exact selected parameter set.\n    #[must_use]\n    pub const fn parameter_mask(self) -> TunableParameterMask {\n        self.parameter_mask\n    }\n\n    /// Stable exact-bit fingerprint used to bind checkpoints to configuration.\n'''
if old not in text:
    raise SystemExit("optimizer getter insertion witness missing")
text = text.replace(old, new, 1)
old = '''        hash = hash_bytes(hash, &self.bounds.minimum.to_le_bytes());\n        hash_bytes(hash, &self.bounds.maximum.to_le_bytes())\n    }\n}\n'''
new = '''        hash = hash_bytes(hash, &self.bounds.minimum.to_le_bytes());\n        hash = hash_bytes(hash, &self.bounds.maximum.to_le_bytes());\n        if !self.parameter_mask.is_all() {\n            hash = hash_bytes(hash, b"spsa-parameter-mask-v1");\n            for word in self.parameter_mask.words() {\n                hash = hash_bytes(hash, &word.to_le_bytes());\n            }\n        }\n        hash\n    }\n}\n'''
if old not in text:
    raise SystemExit("optimizer fingerprint witness missing")
text = text.replace(old, new, 1)
text = text.replace(
    "    /// Initial or resumed weights violated runtime evaluator constraints.\n    InvalidWeights { error: WeightValidationError },\n",
    "    /// No optimizer parameter was selected.\n    EmptyParameterMask,\n    /// Material values must be tuned as one coupled ordering-constrained group.\n    PartialMaterialParameterMask { selected: usize },\n    /// Initial or resumed weights violated runtime evaluator constraints.\n    InvalidWeights { error: WeightValidationError },\n",
    1,
)
text = text.replace(
    '''            Self::InvalidRegularization { value } => write!(\n                formatter,\n                "SPSA regularization must be finite and non-negative, found {value}"\n            ),\n            Self::InvalidWeights { error } => write!(formatter, "invalid SPSA weights: {error}"),\n''',
    '''            Self::InvalidRegularization { value } => write!(\n                formatter,\n                "SPSA regularization must be finite and non-negative, found {value}"\n            ),\n            Self::EmptyParameterMask => {\n                formatter.write_str("SPSA parameter mask must select at least one parameter")\n            }\n            Self::PartialMaterialParameterMask { selected } => write!(\n                formatter,\n                "SPSA material ordering requires selecting either zero or all 10 material parameters; found {selected}"\n            ),\n            Self::InvalidWeights { error } => write!(formatter, "invalid SPSA weights: {error}"),\n''',
    1,
)
# Current checkpoint helper keeps the legacy all-mask projection; group optimizers use config-bound projections internally.
text = text.replace(
    "        let values = project_parameters(&self.current_parameters, bounds)?;\n",
    "        let values = project_parameters(\n            &self.current_parameters,\n            bounds,\n            TunableParameterMask::all(),\n            &self.reference_values,\n        )?;\n",
    1,
)
# Exact objective calls.
text = text.replace(
    "            &reference_values,\n            config.regularization_strength,\n        )?;",
    "            &reference_values,\n            config.regularization_strength,\n            config.parameter_mask,\n        )?;",
    1,
)
text = text.replace(
    "        let current_values = project_parameters(&checkpoint.current_parameters, config.bounds)?;\n",
    "        let current_values = project_parameters(\n            &checkpoint.current_parameters,\n            config.bounds,\n            config.parameter_mask,\n            &checkpoint.reference_values,\n        )?;\n",
    1,
)
text = text.replace(
    "            &checkpoint.reference_values,\n            config.regularization_strength,\n        )?;",
    "            &checkpoint.reference_values,\n            config.regularization_strength,\n            config.parameter_mask,\n        )?;",
    2,
)
text = text.replace(
    "            project_parameters(&self.checkpoint.current_parameters, self.config.bounds)?;\n",
    "            project_parameters(\n                &self.checkpoint.current_parameters,\n                self.config.bounds,\n                self.config.parameter_mask,\n                &self.checkpoint.reference_values,\n            )?;\n",
    2,
)
# Delta only on active parameters.
old = '''        let mut delta = [0_i8; TUNABLE_PARAMETER_COUNT];\n        for value in &mut delta {\n            *value = if next_splitmix64(&mut self.checkpoint.rng_state) & 1 == 0 {\n                -1\n            } else {\n                1\n            };\n        }\n'''
new = '''        let mut delta = [0_i8; TUNABLE_PARAMETER_COUNT];\n        for (index, value) in delta.iter_mut().enumerate() {\n            let parameter = TunableParameter::from_index(index).expect("tunable index is valid");\n            if self.config.parameter_mask.contains(parameter) {\n                *value = if next_splitmix64(&mut self.checkpoint.rng_state) & 1 == 0 {\n                    -1\n                } else {\n                    1\n                };\n            }\n        }\n'''
if old not in text:
    raise SystemExit("optimizer delta witness missing")
text = text.replace(old, new, 1)
# Perturbed calls.
text = text.replace(
    "            perturbation,\n            self.config.bounds,\n        )?;",
    "            perturbation,\n            self.config.bounds,\n            self.config.parameter_mask,\n            &self.checkpoint.reference_values,\n        )?;",
    1,
)
text = text.replace(
    "            -perturbation,\n            self.config.bounds,\n        )?;",
    "            -perturbation,\n            self.config.bounds,\n            self.config.parameter_mask,\n            &self.checkpoint.reference_values,\n        )?;",
    1,
)
old = '''        for (parameter, direction) in self.checkpoint.current_parameters.iter_mut().zip(delta) {\n            *parameter -= gain * gradient_scale * f64::from(direction);\n            *parameter = parameter.clamp(\n                f64::from(self.config.bounds.minimum),\n                f64::from(self.config.bounds.maximum),\n            );\n        }\n'''
new = '''        for (parameter, direction) in self.checkpoint.current_parameters.iter_mut().zip(delta) {\n            if direction == 0 {\n                continue;\n            }\n            *parameter -= gain * gradient_scale * f64::from(direction);\n            *parameter = parameter.clamp(\n                f64::from(self.config.bounds.minimum),\n                f64::from(self.config.bounds.maximum),\n            );\n        }\n'''
if old not in text:
    raise SystemExit("optimizer update witness missing")
text = text.replace(old, new, 1)
# Last current objective in advance_one.
text = text.replace(
    "            &self.checkpoint.reference_values,\n            self.config.regularization_strength,\n        )?;",
    "            &self.checkpoint.reference_values,\n            self.config.regularization_strength,\n            self.config.parameter_mask,\n        )?;",
    1,
)
# Replace helper functions.
start = text.index("fn project_parameters(\n")
end = text.index("fn project_material_ordering(\n", start)
text = text[:start] + r'''fn project_parameters(
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
                .clamp(f64::from(bounds.minimum), f64::from(bounds.maximum))
                as i16
        } else {
            reference_values[index]
        };
    }
    if mask.contains(TunableParameter::from_index(0).expect("material parameter exists")) {
        project_material_ordering(&mut values, bounds);
    }
    Ok(values)
}

''' + text[end:]
start = text.index("fn perturbed_values(\n")
end = text.index("fn regularized_training_objective(\n", start)
text = text[:start] + r'''fn perturbed_values(
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

''' + text[end:]
start = text.index("fn regularized_training_objective(\n")
end = text.index("fn loss_dataset_fingerprint(\n", start)
text = text[:start] + r'''fn regularized_training_objective(
    dataset: &LossDataset,
    weights: &EvaluationWeights,
    logistic_k: LogisticK,
    reference_values: &[i16; TUNABLE_PARAMETER_COUNT],
    regularization_strength: f64,
    mask: TunableParameterMask,
) -> Result<f64, SpsaOptimizerError> {
    let mse = dataset.mean_squared_error(LossPartition::Training, weights, logistic_k)?;
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
    let objective = mse + regularization_strength * squared_distance;
    if !objective.is_finite() {
        return Err(SpsaOptimizerError::NonFiniteOptimizerState);
    }
    Ok(objective)
}

''' + text[end:]
# Insert mask validation before runtime weights helper.
witness = "fn validate_runtime_weights(weights: EvaluationWeights) -> Result<(), SpsaOptimizerError> {\n"
insert = r'''fn validate_parameter_mask(mask: TunableParameterMask) -> Result<(), SpsaOptimizerError> {
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

'''
if witness not in text:
    raise SystemExit("optimizer validate witness missing")
text = text.replace(witness, insert + witness, 1)
# Ensure new optimizer receives validated mask even if a config is constructed through future internals.
text = text.replace(
    "    ) -> Result<Self, SpsaOptimizerError> {\n        validate_runtime_weights(initial_weights)?;\n",
    "    ) -> Result<Self, SpsaOptimizerError> {\n        validate_parameter_mask(config.parameter_mask)?;\n        validate_runtime_weights(initial_weights)?;\n",
    1,
)
text = text.replace(
    "    ) -> Result<Self, SpsaOptimizerError> {\n        let expected_config = config.fingerprint();\n",
    "    ) -> Result<Self, SpsaOptimizerError> {\n        validate_parameter_mask(config.parameter_mask)?;\n        let expected_config = config.fingerprint();\n",
    1,
)
# Add mask tests inside optimizer test module.
text = text.replace(
    "    use crate::{LogisticK, LossDataset, LossPosition, OutcomeTarget};\n",
    "    use crate::{\n        tunable_values, EvaluationParameterGroup, LogisticK, LossDataset, LossPosition,\n        OutcomeTarget, TunableParameter, TunableParameterMask,\n    };\n",
    1,
)
marker = "    #[test]\n    fn checkpoint_corruption_and_binding_mismatches_fail_loudly() {\n"
extra = r'''    #[test]
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
        let summary = optimizer.advance(&data, 20).expect("masked advance succeeds");
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

'''
if marker not in text:
    raise SystemExit("optimizer test insertion witness missing")
text = text.replace(marker, extra + marker, 1)
opt.write_text(text)

# S3 dataset sidecar and admission policy.
s3 = Path("crates/chess-tools/src/s3.rs")
s3.write_text(r'''//! S3 evaluation-strength provenance, dataset admission, and candidate-group contracts.

use core::fmt;
use std::{collections::BTreeMap, fmt::Write as _};

use chess_search::{EvaluationWeightSet, SearchPolicySet};
use chess_tune::EvaluationParameterGroup;

use crate::{
    self_play::{DatasetSplit, SelfPlayDataset, SelfPlayResult, SELF_PLAY_DATASET_SCHEMA_VERSION},
    ToolError,
};

/// Current S3 training-dataset manifest schema.
pub const S3_DATASET_MANIFEST_SCHEMA_VERSION: u16 = 1;
/// Stable S3 dataset-manifest semantic identifier.
pub const S3_DATASET_MANIFEST_IDENTIFIER: u64 = 0x5333_4441_5441_3031;
/// Minimum self-play games admitted for an S3 tuning dataset.
pub const S3_MINIMUM_TUNING_GAMES: u32 = 16;
/// Minimum completed games admitted for an S3 tuning dataset.
pub const S3_MINIMUM_COMPLETED_GAMES: u32 = 12;
/// Maximum unfinished-game fraction, expressed in per-mille.
pub const S3_MAXIMUM_UNFINISHED_PER_MILLE: u32 = 250;
/// Minimum occurrence-weighted training positions.
pub const S3_MINIMUM_TRAINING_OCCURRENCES: u64 = 128;
/// Minimum occurrence-weighted held-out validation positions.
pub const S3_MINIMUM_VALIDATION_OCCURRENCES: u64 = 16;

const MANIFEST_MARKER: &str = "CHESS_S3_TRAINING_DATASET_MANIFEST\t1";
const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;

/// Strict sidecar binding one Task-20 dataset to exact S3 production identities.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct S3DatasetManifest {
    source_commit: [u8; 20],
    engine_version: String,
    search_policy_schema: u16,
    search_policy_identifier: u64,
    search_policy_checksum: u64,
    weight_schema: u16,
    weight_identifier: u64,
    weight_checksum: u64,
    dataset_schema: u16,
    dataset_checksum: u64,
    config_checksum: u64,
    opening_checksum: u64,
    games: u32,
    completed_games: u32,
    unfinished_games: u32,
    seed: u64,
    training_occurrences: u64,
    validation_occurrences: u64,
    test_occurrences: u64,
    checksum: u64,
}

impl S3DatasetManifest {
    /// Binds an already validated baseline self-play dataset to an explicit source commit.
    pub fn from_dataset(
        source_commit: [u8; 20],
        dataset: &SelfPlayDataset,
    ) -> Result<Self, S3DatasetManifestError> {
        dataset
            .validate()
            .map_err(|error| S3DatasetManifestError::Dataset(error.to_string()))?;
        if source_commit == [0; 20] {
            return Err(S3DatasetManifestError::ZeroSourceCommit);
        }
        let policy = SearchPolicySet::baseline();
        policy
            .validate()
            .map_err(|error| S3DatasetManifestError::Identity(error.to_string()))?;
        let weights = EvaluationWeightSet::baseline();
        weights
            .validate()
            .map_err(|error| S3DatasetManifestError::Identity(error.to_string()))?;
        for game in dataset.games() {
            for side in [game.white(), game.black()] {
                if side.engine_version() != env!("CARGO_PKG_VERSION")
                    || side.weight_schema_version() != weights.schema_version
                    || side.weight_identifier() != weights.identifier
                    || side.weight_checksum() != weights.checksum
                {
                    return Err(S3DatasetManifestError::Identity(
                        "self-play side provenance is not the authoritative baseline identity"
                            .to_owned(),
                    ));
                }
            }
        }

        let games = u32::try_from(dataset.games().len())
            .map_err(|_| S3DatasetManifestError::CountOverflow)?;
        let completed_games = u32::try_from(
            dataset
                .games()
                .iter()
                .filter(|game| game.result() != SelfPlayResult::Unfinished)
                .count(),
        )
        .map_err(|_| S3DatasetManifestError::CountOverflow)?;
        let unfinished_games = games
            .checked_sub(completed_games)
            .ok_or(S3DatasetManifestError::CountOverflow)?;
        let mut training_occurrences = 0_u64;
        let mut validation_occurrences = 0_u64;
        let mut test_occurrences = 0_u64;
        for position in dataset.positions().iter().filter(|position| position.eligible()) {
            let destination = match position.split() {
                DatasetSplit::Train => &mut training_occurrences,
                DatasetSplit::Validation => &mut validation_occurrences,
                DatasetSplit::Test => &mut test_occurrences,
            };
            *destination = destination
                .checked_add(u64::from(position.occurrences()))
                .ok_or(S3DatasetManifestError::CountOverflow)?;
        }
        let dataset_checksum = hash_bytes(FNV_OFFSET, dataset.to_text().as_bytes());
        let config_checksum = canonical_config_checksum(dataset);
        let opening_checksum = canonical_opening_checksum(dataset);
        let mut manifest = Self {
            source_commit,
            engine_version: env!("CARGO_PKG_VERSION").to_owned(),
            search_policy_schema: policy.schema_version,
            search_policy_identifier: policy.identifier,
            search_policy_checksum: policy.checksum,
            weight_schema: weights.schema_version,
            weight_identifier: weights.identifier,
            weight_checksum: weights.checksum,
            dataset_schema: SELF_PLAY_DATASET_SCHEMA_VERSION,
            dataset_checksum,
            config_checksum,
            opening_checksum,
            games,
            completed_games,
            unfinished_games,
            seed: dataset.config().seed(),
            training_occurrences,
            validation_occurrences,
            test_occurrences,
            checksum: 0,
        };
        manifest.checksum = manifest.computed_checksum();
        manifest.validate()?;
        Ok(manifest)
    }

    /// Parses a strict canonical manifest and validates all frozen baseline identities.
    pub fn from_text(text: &str) -> Result<Self, S3DatasetManifestError> {
        let mut lines = text.lines();
        if lines.next() != Some(MANIFEST_MARKER) {
            return Err(S3DatasetManifestError::Malformed(
                "invalid S3 dataset manifest marker".to_owned(),
            ));
        }
        let mut fields = BTreeMap::new();
        for line in lines {
            let (key, value) = line.split_once('=').ok_or_else(|| {
                S3DatasetManifestError::Malformed(format!("invalid manifest field {line:?}"))
            })?;
            if key.is_empty() || value.is_empty() || key.trim() != key || value.trim() != value {
                return Err(S3DatasetManifestError::Malformed(format!(
                    "non-canonical manifest field {line:?}"
                )));
            }
            if fields.insert(key.to_owned(), value.to_owned()).is_some() {
                return Err(S3DatasetManifestError::Malformed(format!(
                    "duplicate manifest field {key:?}"
                )));
            }
        }
        const KEYS: [&str; 21] = [
            "identifier",
            "source_commit",
            "engine_version",
            "search_policy_schema",
            "search_policy_identifier",
            "search_policy_checksum",
            "weight_schema",
            "weight_identifier",
            "weight_checksum",
            "dataset_schema",
            "dataset_checksum",
            "config_checksum",
            "opening_checksum",
            "games",
            "completed_games",
            "unfinished_games",
            "seed",
            "training_occurrences",
            "validation_occurrences",
            "test_occurrences",
            "checksum",
        ];
        if fields.len() != KEYS.len() || KEYS.iter().any(|key| !fields.contains_key(*key)) {
            return Err(S3DatasetManifestError::Malformed(
                "S3 dataset manifest fields do not match schema 1".to_owned(),
            ));
        }
        let identifier = parse_hex_u64(&fields["identifier"], "identifier")?;
        if identifier != S3_DATASET_MANIFEST_IDENTIFIER {
            return Err(S3DatasetManifestError::Identity(format!(
                "unexpected S3 dataset manifest identifier {identifier:016x}"
            )));
        }
        let manifest = Self {
            source_commit: parse_commit(&fields["source_commit"] )?,
            engine_version: fields["engine_version"].clone(),
            search_policy_schema: parse_number(&fields["search_policy_schema"], "search_policy_schema")?,
            search_policy_identifier: parse_hex_u64(&fields["search_policy_identifier"], "search_policy_identifier")?,
            search_policy_checksum: parse_hex_u64(&fields["search_policy_checksum"], "search_policy_checksum")?,
            weight_schema: parse_number(&fields["weight_schema"], "weight_schema")?,
            weight_identifier: parse_hex_u64(&fields["weight_identifier"], "weight_identifier")?,
            weight_checksum: parse_hex_u64(&fields["weight_checksum"], "weight_checksum")?,
            dataset_schema: parse_number(&fields["dataset_schema"], "dataset_schema")?,
            dataset_checksum: parse_hex_u64(&fields["dataset_checksum"], "dataset_checksum")?,
            config_checksum: parse_hex_u64(&fields["config_checksum"], "config_checksum")?,
            opening_checksum: parse_hex_u64(&fields["opening_checksum"], "opening_checksum")?,
            games: parse_number(&fields["games"], "games")?,
            completed_games: parse_number(&fields["completed_games"], "completed_games")?,
            unfinished_games: parse_number(&fields["unfinished_games"], "unfinished_games")?,
            seed: parse_number(&fields["seed"], "seed")?,
            training_occurrences: parse_number(&fields["training_occurrences"], "training_occurrences")?,
            validation_occurrences: parse_number(&fields["validation_occurrences"], "validation_occurrences")?,
            test_occurrences: parse_number(&fields["test_occurrences"], "test_occurrences")?,
            checksum: parse_hex_u64(&fields["checksum"], "checksum")?,
        };
        manifest.validate()?;
        Ok(manifest)
    }

    /// Serializes the exact canonical sidecar text.
    #[must_use]
    pub fn to_text(&self) -> String {
        let mut output = String::new();
        writeln!(output, "{MANIFEST_MARKER}").expect("String write cannot fail");
        writeln!(output, "identifier={S3_DATASET_MANIFEST_IDENTIFIER:016x}")
            .expect("String write cannot fail");
        writeln!(output, "source_commit={}", format_commit(self.source_commit))
            .expect("String write cannot fail");
        writeln!(output, "engine_version={}", self.engine_version).expect("String write cannot fail");
        writeln!(output, "search_policy_schema={}", self.search_policy_schema)
            .expect("String write cannot fail");
        writeln!(output, "search_policy_identifier={:016x}", self.search_policy_identifier)
            .expect("String write cannot fail");
        writeln!(output, "search_policy_checksum={:016x}", self.search_policy_checksum)
            .expect("String write cannot fail");
        writeln!(output, "weight_schema={}", self.weight_schema).expect("String write cannot fail");
        writeln!(output, "weight_identifier={:016x}", self.weight_identifier)
            .expect("String write cannot fail");
        writeln!(output, "weight_checksum={:016x}", self.weight_checksum)
            .expect("String write cannot fail");
        writeln!(output, "dataset_schema={}", self.dataset_schema).expect("String write cannot fail");
        writeln!(output, "dataset_checksum={:016x}", self.dataset_checksum)
            .expect("String write cannot fail");
        writeln!(output, "config_checksum={:016x}", self.config_checksum)
            .expect("String write cannot fail");
        writeln!(output, "opening_checksum={:016x}", self.opening_checksum)
            .expect("String write cannot fail");
        writeln!(output, "games={}", self.games).expect("String write cannot fail");
        writeln!(output, "completed_games={}", self.completed_games).expect("String write cannot fail");
        writeln!(output, "unfinished_games={}", self.unfinished_games).expect("String write cannot fail");
        writeln!(output, "seed={}", self.seed).expect("String write cannot fail");
        writeln!(output, "training_occurrences={}", self.training_occurrences)
            .expect("String write cannot fail");
        writeln!(output, "validation_occurrences={}", self.validation_occurrences)
            .expect("String write cannot fail");
        writeln!(output, "test_occurrences={}", self.test_occurrences).expect("String write cannot fail");
        writeln!(output, "checksum={:016x}", self.checksum).expect("String write cannot fail");
        output
    }

    /// Validates this sidecar against one exact dataset image.
    pub fn validate_dataset(&self, dataset: &SelfPlayDataset) -> Result<(), S3DatasetManifestError> {
        let reconstructed = Self::from_dataset(self.source_commit, dataset)?;
        if &reconstructed != self {
            return Err(S3DatasetManifestError::Dataset(
                "S3 dataset manifest does not match the supplied dataset".to_owned(),
            ));
        }
        Ok(())
    }

    /// Applies the predeclared minimum-data and unfinished-game admission policy.
    pub fn validate_for_tuning(&self) -> Result<(), S3DatasetAdmissionError> {
        if self.games < S3_MINIMUM_TUNING_GAMES {
            return Err(S3DatasetAdmissionError::TooFewGames {
                found: self.games,
                minimum: S3_MINIMUM_TUNING_GAMES,
            });
        }
        if self.completed_games < S3_MINIMUM_COMPLETED_GAMES {
            return Err(S3DatasetAdmissionError::TooFewCompletedGames {
                found: self.completed_games,
                minimum: S3_MINIMUM_COMPLETED_GAMES,
            });
        }
        let unfinished_per_mille = u64::from(self.unfinished_games) * 1_000 / u64::from(self.games);
        if unfinished_per_mille > u64::from(S3_MAXIMUM_UNFINISHED_PER_MILLE) {
            return Err(S3DatasetAdmissionError::TooManyUnfinishedGames {
                unfinished: self.unfinished_games,
                games: self.games,
                maximum_per_mille: S3_MAXIMUM_UNFINISHED_PER_MILLE,
            });
        }
        if self.training_occurrences < S3_MINIMUM_TRAINING_OCCURRENCES {
            return Err(S3DatasetAdmissionError::TooFewTrainingOccurrences {
                found: self.training_occurrences,
                minimum: S3_MINIMUM_TRAINING_OCCURRENCES,
            });
        }
        if self.validation_occurrences < S3_MINIMUM_VALIDATION_OCCURRENCES {
            return Err(S3DatasetAdmissionError::TooFewValidationOccurrences {
                found: self.validation_occurrences,
                minimum: S3_MINIMUM_VALIDATION_OCCURRENCES,
            });
        }
        Ok(())
    }

    /// Exact source commit bound by this package.
    #[must_use]
    pub const fn source_commit(&self) -> [u8; 20] {
        self.source_commit
    }

    /// Canonical Task-20 dataset checksum.
    #[must_use]
    pub const fn dataset_checksum(&self) -> u64 {
        self.dataset_checksum
    }

    /// Complete manifest checksum.
    #[must_use]
    pub const fn checksum(&self) -> u64 {
        self.checksum
    }

    /// Occurrence-weighted training count.
    #[must_use]
    pub const fn training_occurrences(&self) -> u64 {
        self.training_occurrences
    }

    /// Occurrence-weighted validation count.
    #[must_use]
    pub const fn validation_occurrences(&self) -> u64 {
        self.validation_occurrences
    }

    fn validate(&self) -> Result<(), S3DatasetManifestError> {
        if self.source_commit == [0; 20] {
            return Err(S3DatasetManifestError::ZeroSourceCommit);
        }
        let policy = SearchPolicySet::baseline();
        let weights = EvaluationWeightSet::baseline();
        if self.engine_version != env!("CARGO_PKG_VERSION")
            || self.search_policy_schema != policy.schema_version
            || self.search_policy_identifier != policy.identifier
            || self.search_policy_checksum != policy.checksum
            || self.weight_schema != weights.schema_version
            || self.weight_identifier != weights.identifier
            || self.weight_checksum != weights.checksum
            || self.dataset_schema != SELF_PLAY_DATASET_SCHEMA_VERSION
        {
            return Err(S3DatasetManifestError::Identity(
                "S3 dataset manifest does not bind the authoritative v0.1 baseline identity"
                    .to_owned(),
            ));
        }
        if self.dataset_checksum == 0 || self.config_checksum == 0 || self.opening_checksum == 0 {
            return Err(S3DatasetManifestError::Malformed(
                "S3 dataset checksums must be non-zero".to_owned(),
            ));
        }
        if self.games == 0
            || self
                .completed_games
                .checked_add(self.unfinished_games)
                .ok_or(S3DatasetManifestError::CountOverflow)?
                != self.games
        {
            return Err(S3DatasetManifestError::Malformed(
                "S3 game counts are inconsistent".to_owned(),
            ));
        }
        let expected = self.computed_checksum();
        if self.checksum != expected {
            return Err(S3DatasetManifestError::ChecksumMismatch {
                expected,
                found: self.checksum,
            });
        }
        Ok(())
    }

    fn computed_checksum(&self) -> u64 {
        let mut clone = self.clone();
        clone.checksum = 0;
        hash_bytes(FNV_OFFSET, clone.to_text().as_bytes())
    }
}

/// Strict manifest parse, identity, or binding error.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum S3DatasetManifestError {
    ZeroSourceCommit,
    CountOverflow,
    Dataset(String),
    Identity(String),
    Malformed(String),
    ChecksumMismatch { expected: u64, found: u64 },
}

impl fmt::Display for S3DatasetManifestError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::ZeroSourceCommit => formatter.write_str("S3 source commit must be non-zero"),
            Self::CountOverflow => formatter.write_str("S3 dataset count overflow"),
            Self::Dataset(message) | Self::Identity(message) | Self::Malformed(message) => {
                formatter.write_str(message)
            }
            Self::ChecksumMismatch { expected, found } => write!(
                formatter,
                "S3 dataset manifest checksum mismatch: expected {expected:016x}, found {found:016x}"
            ),
        }
    }
}

impl std::error::Error for S3DatasetManifestError {}

/// Dataset that is valid but does not meet the S3 tuning admission policy.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum S3DatasetAdmissionError {
    TooFewGames { found: u32, minimum: u32 },
    TooFewCompletedGames { found: u32, minimum: u32 },
    TooManyUnfinishedGames {
        unfinished: u32,
        games: u32,
        maximum_per_mille: u32,
    },
    TooFewTrainingOccurrences { found: u64, minimum: u64 },
    TooFewValidationOccurrences { found: u64, minimum: u64 },
}

impl fmt::Display for S3DatasetAdmissionError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match *self {
            Self::TooFewGames { found, minimum } => {
                write!(formatter, "S3 tuning requires at least {minimum} games, found {found}")
            }
            Self::TooFewCompletedGames { found, minimum } => write!(
                formatter,
                "S3 tuning requires at least {minimum} completed games, found {found}"
            ),
            Self::TooManyUnfinishedGames {
                unfinished,
                games,
                maximum_per_mille,
            } => write!(
                formatter,
                "S3 unfinished-game rate {unfinished}/{games} exceeds {maximum_per_mille} per mille"
            ),
            Self::TooFewTrainingOccurrences { found, minimum } => write!(
                formatter,
                "S3 tuning requires at least {minimum} training occurrences, found {found}"
            ),
            Self::TooFewValidationOccurrences { found, minimum } => write!(
                formatter,
                "S3 tuning requires at least {minimum} validation occurrences, found {found}"
            ),
        }
    }
}

impl std::error::Error for S3DatasetAdmissionError {}

/// Returns all predeclared existing-evaluator tuning groups and their immutable masks.
#[must_use]
pub fn evaluation_groups() -> [(EvaluationParameterGroup, usize, u64); 6] {
    EvaluationParameterGroup::ALL.map(|group| {
        let mask = group.mask();
        (group, mask.active_count(), mask.fingerprint())
    })
}

fn canonical_config_checksum(dataset: &SelfPlayDataset) -> u64 {
    let config = dataset.config();
    let splits = config.splits();
    let text = format!(
        "games={}\nseed={}\nmaximum_plies={}\nclaimable_draw={}\nopening_positions={}\nsplit_train={}\nsplit_validation={}\nsplit_test={}\nwhite_limit={}\nwhite_tt_mib={}\nwhite_check_extension={}\nblack_limit={}\nblack_tt_mib={}\nblack_check_extension={}\n",
        config.game_count(),
        config.seed(),
        config.maximum_plies(),
        config.claimable_draw_policy(),
        config.opening_position_policy(),
        splits.train(),
        splits.validation(),
        splits.test(),
        config.white().limit(),
        config.white().transposition_table_mebibytes(),
        config.white().check_extension_enabled(),
        config.black().limit(),
        config.black().transposition_table_mebibytes(),
        config.black().check_extension_enabled(),
    );
    hash_bytes(FNV_OFFSET, text.as_bytes())
}

fn canonical_opening_checksum(dataset: &SelfPlayDataset) -> u64 {
    let mut text = String::new();
    for opening in dataset.openings() {
        writeln!(
            text,
            "{}\t{}\t{}",
            opening.identifier(),
            opening.initial_fen(),
            opening.moves().join(" ")
        )
        .expect("String write cannot fail");
    }
    hash_bytes(FNV_OFFSET, text.as_bytes())
}

fn parse_commit(value: &str) -> Result<[u8; 20], S3DatasetManifestError> {
    if value.len() != 40 || !value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(S3DatasetManifestError::Malformed(
            "source_commit must be exactly 40 hexadecimal characters".to_owned(),
        ));
    }
    let mut output = [0_u8; 20];
    for (index, destination) in output.iter_mut().enumerate() {
        *destination = u8::from_str_radix(&value[index * 2..index * 2 + 2], 16).map_err(|_| {
            S3DatasetManifestError::Malformed("invalid source_commit hexadecimal".to_owned())
        })?;
    }
    Ok(output)
}

fn format_commit(commit: [u8; 20]) -> String {
    commit.iter().map(|byte| format!("{byte:02x}")).collect()
}

fn parse_hex_u64(value: &str, field: &str) -> Result<u64, S3DatasetManifestError> {
    if value.len() != 16 || !value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(S3DatasetManifestError::Malformed(format!(
            "{field} must be 16 hexadecimal characters"
        )));
    }
    u64::from_str_radix(value, 16)
        .map_err(|_| S3DatasetManifestError::Malformed(format!("invalid {field}")))
}

fn parse_number<T>(value: &str, field: &str) -> Result<T, S3DatasetManifestError>
where
    T: std::str::FromStr,
    T::Err: fmt::Display,
{
    value.parse::<T>().map_err(|error| {
        S3DatasetManifestError::Malformed(format!("invalid {field}: {error}"))
    })
}

fn hash_bytes(mut hash: u64, bytes: &[u8]) -> u64 {
    for byte in bytes {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    hash
}

/// Parses an exact forty-hex-character source commit for manifest construction.
pub fn parse_source_commit(value: &str) -> Result<[u8; 20], S3DatasetManifestError> {
    parse_commit(value)
}

/// Converts a tooling error into the S3 dataset error domain for command adapters.
pub fn dataset_tool_error(error: ToolError) -> S3DatasetManifestError {
    S3DatasetManifestError::Dataset(error.to_string())
}

#[cfg(test)]
mod tests {
    use crate::self_play::{
        generate_self_play_dataset, DatasetSplitPercentages, OpeningPositionPolicy, OpeningSuite,
        SelfPlayConfig, SelfPlayLimit, SelfPlaySideConfig,
    };

    use super::{
        evaluation_groups, parse_source_commit, S3DatasetAdmissionError, S3DatasetManifest,
        S3_MINIMUM_TUNING_GAMES,
    };

    fn small_dataset(games: u32) -> crate::self_play::SelfPlayDataset {
        let openings = OpeningSuite::from_text(concat!(
            "CHESS_SELF_PLAY_OPENINGS\t1\n",
            "king-pawn\trnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\te2e4 e7e5\n",
            "queen-pawn\trnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\td2d4 d7d5\n",
            "english\trnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\tc2c4 e7e5\n",
        ))
        .expect("opening fixture parses");
        let side = SelfPlaySideConfig::new(1, SelfPlayLimit::Depth(1));
        let config = SelfPlayConfig::new(games, 0x5333, side, side)
            .with_maximum_plies(10)
            .with_opening_position_policy(OpeningPositionPolicy::Exclude)
            .with_splits(DatasetSplitPercentages::new(60, 20, 20).expect("splits are valid"));
        generate_self_play_dataset(&config, &openings, "s3-test-dataset.tsv")
            .expect("small self-play dataset generates")
    }

    #[test]
    fn manifest_round_trip_binds_exact_dataset_and_source() {
        let dataset = small_dataset(6);
        let source = parse_source_commit("0123456789abcdef0123456789abcdef01234567")
            .expect("commit parses");
        let manifest = S3DatasetManifest::from_dataset(source, &dataset).expect("manifest builds");
        let text = manifest.to_text();
        let parsed = S3DatasetManifest::from_text(&text).expect("manifest parses");
        assert_eq!(parsed, manifest);
        parsed.validate_dataset(&dataset).expect("dataset binding validates");
        assert_ne!(parsed.dataset_checksum(), 0);
        assert_ne!(parsed.checksum(), 0);
    }

    #[test]
    fn manifest_checksum_and_dataset_binding_fail_closed() {
        let dataset = small_dataset(6);
        let source = parse_source_commit("0123456789abcdef0123456789abcdef01234567")
            .expect("commit parses");
        let manifest = S3DatasetManifest::from_dataset(source, &dataset).expect("manifest builds");
        let corrupt = manifest.to_text().replace("seed=21299", "seed=21300");
        assert!(S3DatasetManifest::from_text(&corrupt).is_err());

        let other = small_dataset(7);
        assert!(manifest.validate_dataset(&other).is_err());
    }

    #[test]
    fn small_pilot_is_valid_but_not_admitted_as_training_scale() {
        let dataset = small_dataset(6);
        let source = parse_source_commit("0123456789abcdef0123456789abcdef01234567")
            .expect("commit parses");
        let manifest = S3DatasetManifest::from_dataset(source, &dataset).expect("manifest builds");
        assert_eq!(
            manifest.validate_for_tuning(),
            Err(S3DatasetAdmissionError::TooFewGames {
                found: 6,
                minimum: S3_MINIMUM_TUNING_GAMES,
            })
        );
    }

    #[test]
    fn predeclared_groups_have_stable_nonzero_identity() {
        let groups = evaluation_groups();
        assert_eq!(groups.len(), 6);
        assert!(groups.iter().all(|(_, count, checksum)| *count > 0 && *checksum != 0));
    }
}
''')

replace_once(
    "crates/chess-tools/src/lib.rs",
    "pub mod self_play;\npub mod tuning;\n",
    "pub mod s3;\npub mod self_play;\npub mod tuning;\n",
)

Path("docs/RUST_CHESS_ENGINE_S3_PIPELINE.md").write_text(r'''# S3 evaluation-strength pipeline contract

S3 preserves the Task 20 `CHESS_SELF_PLAY_DATASET` schema instead of silently changing a completed historical format. An S3 training package is therefore two explicit artifacts:

1. the strict Task 20 dataset image; and
2. a strict `CHESS_S3_TRAINING_DATASET_MANIFEST` sidecar.

The sidecar binds the dataset checksum to an explicit 40-hex source commit, package version, exact v0.1 search-policy schema/identifier/checksum, baseline evaluation schema/identifier/checksum, deterministic self-play configuration checksum, opening-suite checksum, seed, game completion counts, and train/validation/test occurrence counts. The sidecar is itself checksummed and fail-closed. A caller must explicitly supply the source commit; no Git, environment, filesystem, or process discovery is used by the library contract.

## Dataset admission

A structurally valid pilot dataset is not automatically large enough for tuning. S3 initially requires:

- at least 16 self-play games;
- at least 12 completed games;
- at most 250 unfinished games per 1000 games;
- at least 128 occurrence-weighted eligible training positions; and
- at least 16 occurrence-weighted eligible validation positions.

These are minimum correctness/admission thresholds, not claims of statistical sufficiency for production strength. Larger S3 tasks must record their actual scale before candidate promotion.

## Existing-evaluator parameter groups

The runtime evaluator has 816 serialized scalar slots. Six structural zero slots are not tunable, leaving 810 named optimizer parameters. S3 partitions those 810 named parameters into five disjoint pre-full groups, followed by an all-parameter pass:

| Group | Named scalars |
|---|---:|
| material and piece-square | 778 |
| mobility and activity | 16 |
| pawn structure | 8 |
| king safety and space | 6 |
| endgame king activity | 2 |
| full existing evaluator | 810 |

Each group is a deterministic fixed-size bit mask with a stable FNV-1a fingerprint.

## Mask-aware SPSA

`SpsaConfig` defaults to the historical all-810-parameter mask, preserving the historical configuration fingerprint for full-mask runs. A non-full mask is explicitly bound into the configuration fingerprint and therefore into checkpoint resume validation.

Only selected parameters receive perturbation directions or optimizer updates. Inactive parameters are restored to their reference values during projection. The coupled ten material parameters may be selected as a complete group or not at all, preventing ordering projection from changing nominally inactive material values. Regularization is normalized over the selected parameter count, not diluted over all 810 values.

Validation loss remains held out from optimizer state transitions. Existing `LossDataset::calibrate_k` calibrates `K` on training data only, and SPSA reports validation MSE separately after bounded work.

No artifact described here is a production activation mechanism. v0.1 defaults remain authoritative until the distinct S3 activation gate is explicitly approved and passes.
''')
