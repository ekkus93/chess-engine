//! S3 held-out advancement policy and strict inactive candidate registry.

use core::{fmt, str::FromStr};
use std::collections::{BTreeMap, BTreeSet};

use chess_search::{
    EvaluationWeightSet, EvaluationWeights, BASELINE_WEIGHT_SET_ID, WEIGHT_VALUE_COUNT,
};
use chess_tune::{
    EvaluationParameterGroup, NamedWeightArtifact, NamedWeightArtifactError,
    TUNABLE_PARAMETER_COUNT,
};

/// Current S3 candidate-envelope schema.
pub const S3_CANDIDATE_SCHEMA_VERSION: u16 = 1;
/// Stable semantic identifier for S3 evaluation-weight candidates.
pub const S3_CANDIDATE_FORMAT_IDENTIFIER: u64 = 0x5333_4341_4e44_3031;
/// Held-out comparison tolerance used only to absorb deterministic floating-point noise.
pub const S3_VALIDATION_LOSS_TOLERANCE: f64 = 1.0e-12;

const CANDIDATE_MARKER: &str = "CHESS_S3_EVALUATION_CANDIDATE\t1";
const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;

/// Predeclared S3 held-out-loss disposition.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum S3LossDecision {
    /// Training loss strictly improved and held-out validation did not regress beyond tolerance.
    Advance,
    /// Training loss did not strictly improve.
    RejectNoTrainingImprovement,
    /// Training improved but held-out validation regressed beyond the frozen tolerance.
    RejectValidationRegression,
}

impl S3LossDecision {
    /// Stable machine-readable name.
    #[must_use]
    pub const fn name(self) -> &'static str {
        match self {
            Self::Advance => "advance",
            Self::RejectNoTrainingImprovement => "reject_no_training_improvement",
            Self::RejectValidationRegression => "reject_validation_regression",
        }
    }
}

impl FromStr for S3LossDecision {
    type Err = S3CandidateError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        match value {
            "advance" => Ok(Self::Advance),
            "reject_no_training_improvement" => Ok(Self::RejectNoTrainingImprovement),
            "reject_validation_regression" => Ok(Self::RejectValidationRegression),
            _ => Err(S3CandidateError::UnsupportedLossDecision(value.to_owned())),
        }
    }
}

/// Exact training and held-out loss evidence for one candidate.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct S3LossEvidence {
    initial_training: f64,
    final_training: f64,
    initial_validation: f64,
    final_validation: f64,
    decision: S3LossDecision,
}

impl S3LossEvidence {
    /// Applies the frozen S3 advancement rule.
    pub fn assess(
        initial_training: f64,
        final_training: f64,
        initial_validation: f64,
        final_validation: f64,
    ) -> Result<Self, S3CandidateError> {
        for (label, value) in [
            ("initial training loss", initial_training),
            ("final training loss", final_training),
            ("initial validation loss", initial_validation),
            ("final validation loss", final_validation),
        ] {
            if !value.is_finite() || value < 0.0 {
                return Err(S3CandidateError::InvalidLoss {
                    label,
                    value_bits: value.to_bits(),
                });
            }
        }
        let decision = if final_training >= initial_training {
            S3LossDecision::RejectNoTrainingImprovement
        } else if final_validation > initial_validation + S3_VALIDATION_LOSS_TOLERANCE {
            S3LossDecision::RejectValidationRegression
        } else {
            S3LossDecision::Advance
        };
        Ok(Self {
            initial_training,
            final_training,
            initial_validation,
            final_validation,
            decision,
        })
    }

    /// Frozen disposition.
    #[must_use]
    pub const fn decision(self) -> S3LossDecision {
        self.decision
    }

    /// Candidate-minus-baseline training loss.
    #[must_use]
    pub fn training_delta(self) -> f64 {
        self.final_training - self.initial_training
    }

    /// Candidate-minus-baseline held-out validation loss.
    #[must_use]
    pub fn validation_delta(self) -> f64 {
        self.final_validation - self.initial_validation
    }
}

/// Currently supported S3 candidate family.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum S3CandidateType {
    /// Existing evaluator structure with a named 810-parameter weight artifact.
    ExistingEvaluationWeights,
}

impl S3CandidateType {
    /// Stable machine-readable name.
    #[must_use]
    pub const fn name(self) -> &'static str {
        match self {
            Self::ExistingEvaluationWeights => "existing_evaluation_weights",
        }
    }
}

impl FromStr for S3CandidateType {
    type Err = S3CandidateError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        match value {
            "existing_evaluation_weights" => Ok(Self::ExistingEvaluationWeights),
            _ => Err(S3CandidateError::UnsupportedCandidateType(value.to_owned())),
        }
    }
}

/// Strict checksummed S3 sidecar over one existing named-weight artifact.
#[derive(Clone, Debug, PartialEq)]
pub struct S3CandidateEnvelope {
    /// Envelope schema.
    pub schema_version: u16,
    /// Stable envelope family identifier.
    pub format_identifier: u64,
    /// Supported candidate family.
    pub candidate_type: S3CandidateType,
    /// Candidate identifier, matching the embedded named-weight artifact.
    pub candidate_identifier: u64,
    /// Exact source commit that generated the candidate.
    pub source_commit: [u8; 20],
    /// Authoritative v0.1 baseline weight identity.
    pub baseline_identifier: u64,
    /// Authoritative v0.1 baseline weight checksum.
    pub baseline_checksum: u64,
    /// Embedded named-weight artifact checksum.
    pub artifact_checksum: u64,
    /// FNV checksum of all 816 runtime scalar values.
    pub value_checksum: u64,
    /// Exact runtime vector length.
    pub dense_vector_length: u32,
    /// Exact named tunable count.
    pub tunable_parameter_count: u32,
    /// S3 group name.
    pub group: EvaluationParameterGroup,
    /// Exact group-mask fingerprint.
    pub mask_fingerprint: u64,
    /// Deterministic generation timestamp from tuning provenance.
    pub generated_at_unix_seconds: u64,
    /// Checksum of exact tuning configuration bytes.
    pub tuning_config_checksum: u64,
    /// Task-20 dataset checksum from the named artifact metadata.
    pub dataset_checksum: u64,
    /// Strict S3 dataset-manifest checksum.
    pub dataset_manifest_checksum: u64,
    /// Checksum of exact canonical tuning report text.
    pub tuning_report_checksum: u64,
    /// Exact envelope-generation invocation.
    pub exact_invocation: String,
    /// Frozen held-out loss decision.
    pub loss_decision: S3LossDecision,
    /// Candidate-minus-baseline training loss.
    pub training_loss_delta_bits: u64,
    /// Candidate-minus-baseline held-out validation loss.
    pub validation_loss_delta_bits: u64,
    /// Activation is always false in S3 candidate artifacts.
    pub activated: bool,
    /// Canonical semantic checksum.
    pub checksum: u64,
}

impl S3CandidateEnvelope {
    /// Constructs a strict inactive candidate sidecar.
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        group: EvaluationParameterGroup,
        artifact: &NamedWeightArtifact,
        dataset_manifest_checksum: u64,
        tuning_config_text: &str,
        tuning_report_text: &str,
        exact_invocation: String,
        loss: S3LossEvidence,
    ) -> Result<Self, S3CandidateError> {
        artifact.validate()?;
        validate_invocation(&exact_invocation)?;
        if dataset_manifest_checksum == 0 {
            return Err(S3CandidateError::EmptyIdentity("dataset manifest checksum"));
        }
        let baseline = EvaluationWeightSet::baseline();
        baseline
            .validate()
            .map_err(|error| S3CandidateError::Weight(error.to_string()))?;
        let mut value_hash = FNV_OFFSET;
        for value in artifact.weights.values() {
            value_hash = hash_bytes(value_hash, &value.to_le_bytes());
        }
        let mut envelope = Self {
            schema_version: S3_CANDIDATE_SCHEMA_VERSION,
            format_identifier: S3_CANDIDATE_FORMAT_IDENTIFIER,
            candidate_type: S3CandidateType::ExistingEvaluationWeights,
            candidate_identifier: artifact.identifier,
            source_commit: artifact.metadata.source_commit,
            baseline_identifier: baseline.identifier,
            baseline_checksum: baseline.checksum,
            artifact_checksum: artifact.checksum,
            value_checksum: value_hash,
            dense_vector_length: u32::try_from(WEIGHT_VALUE_COUNT)
                .expect("runtime weight count fits u32"),
            tunable_parameter_count: u32::try_from(TUNABLE_PARAMETER_COUNT)
                .expect("tunable count fits u32"),
            group,
            mask_fingerprint: group.mask_fingerprint(),
            generated_at_unix_seconds: artifact.metadata.generated_at_unix_seconds,
            tuning_config_checksum: checksum_text(tuning_config_text),
            dataset_checksum: artifact.metadata.dataset_checksum,
            dataset_manifest_checksum,
            tuning_report_checksum: checksum_text(tuning_report_text),
            exact_invocation,
            loss_decision: loss.decision(),
            training_loss_delta_bits: loss.training_delta().to_bits(),
            validation_loss_delta_bits: loss.validation_delta().to_bits(),
            activated: false,
            checksum: 0,
        };
        envelope.checksum = envelope.computed_checksum();
        envelope.validate()?;
        Ok(envelope)
    }

    /// Validates structural identities without trusting caller-provided fields.
    pub fn validate(&self) -> Result<(), S3CandidateError> {
        if self.schema_version != S3_CANDIDATE_SCHEMA_VERSION {
            return Err(S3CandidateError::SchemaVersion {
                expected: S3_CANDIDATE_SCHEMA_VERSION,
                found: self.schema_version,
            });
        }
        if self.format_identifier != S3_CANDIDATE_FORMAT_IDENTIFIER {
            return Err(S3CandidateError::FormatIdentifier {
                expected: S3_CANDIDATE_FORMAT_IDENTIFIER,
                found: self.format_identifier,
            });
        }
        if self.candidate_identifier == 0 {
            return Err(S3CandidateError::EmptyIdentity("candidate identifier"));
        }
        if self.source_commit == [0; 20] {
            return Err(S3CandidateError::EmptyIdentity("source commit"));
        }
        let baseline = EvaluationWeightSet::baseline();
        if self.baseline_identifier != baseline.identifier || self.baseline_checksum != baseline.checksum
        {
            return Err(S3CandidateError::BaselineIdentityMismatch);
        }
        if self.artifact_checksum == 0
            || self.value_checksum == 0
            || self.mask_fingerprint == 0
            || self.tuning_config_checksum == 0
            || self.dataset_checksum == 0
            || self.dataset_manifest_checksum == 0
            || self.tuning_report_checksum == 0
        {
            return Err(S3CandidateError::EmptyIdentity("candidate checksum field"));
        }
        if usize::try_from(self.dense_vector_length).ok() != Some(WEIGHT_VALUE_COUNT) {
            return Err(S3CandidateError::DenseVectorLength {
                expected: WEIGHT_VALUE_COUNT,
                found: self.dense_vector_length,
            });
        }
        if usize::try_from(self.tunable_parameter_count).ok() != Some(TUNABLE_PARAMETER_COUNT) {
            return Err(S3CandidateError::TunableParameterCount {
                expected: TUNABLE_PARAMETER_COUNT,
                found: self.tunable_parameter_count,
            });
        }
        if self.mask_fingerprint != self.group.mask_fingerprint() {
            return Err(S3CandidateError::MaskIdentityMismatch);
        }
        if self.generated_at_unix_seconds == 0 {
            return Err(S3CandidateError::EmptyIdentity("generation timestamp"));
        }
        validate_invocation(&self.exact_invocation)?;
        if self.activated {
            return Err(S3CandidateError::ActivationForbidden);
        }
        let training_delta = f64::from_bits(self.training_loss_delta_bits);
        let validation_delta = f64::from_bits(self.validation_loss_delta_bits);
        if !training_delta.is_finite() || !validation_delta.is_finite() {
            return Err(S3CandidateError::InvalidDeltaBits);
        }
        let expected = self.computed_checksum();
        if self.checksum != expected {
            return Err(S3CandidateError::ChecksumMismatch {
                expected,
                found: self.checksum,
            });
        }
        Ok(())
    }

    /// Validates this envelope against the exact named-weight payload.
    pub fn validate_artifact(&self, artifact: &NamedWeightArtifact) -> Result<(), S3CandidateError> {
        artifact.validate()?;
        if artifact.identifier != self.candidate_identifier
            || artifact.checksum != self.artifact_checksum
            || artifact.metadata.source_commit != self.source_commit
            || artifact.metadata.dataset_checksum != self.dataset_checksum
            || artifact.metadata.generated_at_unix_seconds != self.generated_at_unix_seconds
        {
            return Err(S3CandidateError::ArtifactIdentityMismatch);
        }
        let mut value_hash = FNV_OFFSET;
        for value in artifact.weights.values() {
            value_hash = hash_bytes(value_hash, &value.to_le_bytes());
        }
        if value_hash != self.value_checksum {
            return Err(S3CandidateError::ArtifactValueMismatch);
        }
        Ok(())
    }

    /// Canonical line-oriented serialization.
    pub fn to_text(&self) -> Result<String, S3CandidateError> {
        self.validate()?;
        let fields = self.canonical_fields(true);
        let mut output = String::new();
        output.push_str(CANDIDATE_MARKER);
        output.push('\n');
        for (key, value) in fields {
            output.push_str(key);
            output.push('=');
            output.push_str(&value);
            output.push('\n');
        }
        Ok(output)
    }

    /// Strict canonical parser.
    pub fn from_text(text: &str) -> Result<Self, S3CandidateError> {
        let mut lines = text.lines();
        if lines.next() != Some(CANDIDATE_MARKER) {
            return Err(S3CandidateError::Malformed("invalid candidate marker".to_owned()));
        }
        let mut fields = BTreeMap::new();
        for line in lines {
            let (key, value) = line
                .split_once('=')
                .ok_or_else(|| S3CandidateError::Malformed(format!("invalid field {line:?}")))?;
            if key.is_empty() || value.is_empty() || key.trim() != key || value.trim() != value {
                return Err(S3CandidateError::Malformed(format!("non-canonical field {line:?}")));
            }
            if fields.insert(key.to_owned(), value.to_owned()).is_some() {
                return Err(S3CandidateError::Malformed(format!("duplicate field {key:?}")));
            }
        }
        const KEYS: [&str; 24] = [
            "schema", "format_identifier", "candidate_type", "candidate_identifier",
            "source_commit", "baseline_identifier", "baseline_checksum", "artifact_checksum",
            "value_checksum", "dense_vector_length", "tunable_parameter_count", "group",
            "mask_fingerprint", "generated_at_unix_seconds", "tuning_config_checksum",
            "dataset_checksum", "dataset_manifest_checksum", "tuning_report_checksum",
            "exact_invocation", "loss_decision", "training_loss_delta_bits",
            "validation_loss_delta_bits", "activated", "checksum",
        ];
        if fields.len() != KEYS.len() || KEYS.iter().any(|key| !fields.contains_key(*key)) {
            return Err(S3CandidateError::Malformed(
                "candidate fields do not match schema 1".to_owned(),
            ));
        }
        let group = parse_group(&fields["group"])?;
        let candidate = Self {
            schema_version: parse_number(&fields["schema"], "schema")?,
            format_identifier: parse_hex(&fields["format_identifier"], "format_identifier")?,
            candidate_type: fields["candidate_type"].parse()?,
            candidate_identifier: parse_hex(&fields["candidate_identifier"], "candidate_identifier")?,
            source_commit: parse_commit(&fields["source_commit"] )?,
            baseline_identifier: parse_hex(&fields["baseline_identifier"], "baseline_identifier")?,
            baseline_checksum: parse_hex(&fields["baseline_checksum"], "baseline_checksum")?,
            artifact_checksum: parse_hex(&fields["artifact_checksum"], "artifact_checksum")?,
            value_checksum: parse_hex(&fields["value_checksum"], "value_checksum")?,
            dense_vector_length: parse_number(&fields["dense_vector_length"], "dense_vector_length")?,
            tunable_parameter_count: parse_number(&fields["tunable_parameter_count"], "tunable_parameter_count")?,
            group,
            mask_fingerprint: parse_hex(&fields["mask_fingerprint"], "mask_fingerprint")?,
            generated_at_unix_seconds: parse_number(
                &fields["generated_at_unix_seconds"],
                "generated_at_unix_seconds",
            )?,
            tuning_config_checksum: parse_hex(&fields["tuning_config_checksum"], "tuning_config_checksum")?,
            dataset_checksum: parse_hex(&fields["dataset_checksum"], "dataset_checksum")?,
            dataset_manifest_checksum: parse_hex(
                &fields["dataset_manifest_checksum"],
                "dataset_manifest_checksum",
            )?,
            tuning_report_checksum: parse_hex(&fields["tuning_report_checksum"], "tuning_report_checksum")?,
            exact_invocation: fields["exact_invocation"].clone(),
            loss_decision: fields["loss_decision"].parse()?,
            training_loss_delta_bits: parse_hex(
                &fields["training_loss_delta_bits"],
                "training_loss_delta_bits",
            )?,
            validation_loss_delta_bits: parse_hex(
                &fields["validation_loss_delta_bits"],
                "validation_loss_delta_bits",
            )?,
            activated: match fields["activated"].as_str() {
                "false" => false,
                "true" => true,
                other => {
                    return Err(S3CandidateError::Malformed(format!(
                        "invalid activated value {other:?}"
                    )))
                }
            },
            checksum: parse_hex(&fields["checksum"], "checksum")?,
        };
        candidate.validate()?;
        Ok(candidate)
    }

    fn computed_checksum(&self) -> u64 {
        let mut hash = FNV_OFFSET;
        for (key, value) in self.canonical_fields(false) {
            hash = hash_bytes(hash, key.as_bytes());
            hash = hash_bytes(hash, b"=");
            hash = hash_bytes(hash, value.as_bytes());
            hash = hash_bytes(hash, b"\n");
        }
        hash
    }

    fn canonical_fields(&self, include_checksum: bool) -> Vec<(&'static str, String)> {
        let mut fields = vec![
            ("schema", self.schema_version.to_string()),
            ("format_identifier", format!("{:016x}", self.format_identifier)),
            ("candidate_type", self.candidate_type.name().to_owned()),
            ("candidate_identifier", format!("{:016x}", self.candidate_identifier)),
            ("source_commit", format_commit(self.source_commit)),
            ("baseline_identifier", format!("{:016x}", self.baseline_identifier)),
            ("baseline_checksum", format!("{:016x}", self.baseline_checksum)),
            ("artifact_checksum", format!("{:016x}", self.artifact_checksum)),
            ("value_checksum", format!("{:016x}", self.value_checksum)),
            ("dense_vector_length", self.dense_vector_length.to_string()),
            ("tunable_parameter_count", self.tunable_parameter_count.to_string()),
            ("group", self.group.name().to_owned()),
            ("mask_fingerprint", format!("{:016x}", self.mask_fingerprint)),
            ("generated_at_unix_seconds", self.generated_at_unix_seconds.to_string()),
            ("tuning_config_checksum", format!("{:016x}", self.tuning_config_checksum)),
            ("dataset_checksum", format!("{:016x}", self.dataset_checksum)),
            (
                "dataset_manifest_checksum",
                format!("{:016x}", self.dataset_manifest_checksum),
            ),
            ("tuning_report_checksum", format!("{:016x}", self.tuning_report_checksum)),
            ("exact_invocation", self.exact_invocation.clone()),
            ("loss_decision", self.loss_decision.name().to_owned()),
            (
                "training_loss_delta_bits",
                format!("{:016x}", self.training_loss_delta_bits),
            ),
            (
                "validation_loss_delta_bits",
                format!("{:016x}", self.validation_loss_delta_bits),
            ),
            ("activated", self.activated.to_string()),
        ];
        if include_checksum {
            fields.push(("checksum", format!("{:016x}", self.checksum)));
        }
        fields
    }
}

/// In-memory registry that rejects duplicate candidate identities.
#[derive(Clone, Debug, Default)]
pub struct S3CandidateRegistry {
    identifiers: BTreeSet<u64>,
    candidates: Vec<S3CandidateEnvelope>,
}

impl S3CandidateRegistry {
    /// Registers one validated candidate, rejecting duplicate identifiers.
    pub fn register(&mut self, candidate: S3CandidateEnvelope) -> Result<(), S3CandidateError> {
        candidate.validate()?;
        if !self.identifiers.insert(candidate.candidate_identifier) {
            return Err(S3CandidateError::DuplicateCandidateIdentifier(
                candidate.candidate_identifier,
            ));
        }
        self.candidates.push(candidate);
        Ok(())
    }

    /// Number of distinct registered candidates.
    #[must_use]
    pub fn len(&self) -> usize {
        self.candidates.len()
    }

    /// Whether the registry is empty.
    #[must_use]
    pub fn is_empty(&self) -> bool {
        self.candidates.is_empty()
    }
}

/// Strict candidate construction or validation error.
#[derive(Debug, PartialEq)]
pub enum S3CandidateError {
    SchemaVersion { expected: u16, found: u16 },
    FormatIdentifier { expected: u64, found: u64 },
    UnsupportedCandidateType(String),
    UnsupportedLossDecision(String),
    EmptyIdentity(&'static str),
    BaselineIdentityMismatch,
    DenseVectorLength { expected: usize, found: u32 },
    TunableParameterCount { expected: usize, found: u32 },
    MaskIdentityMismatch,
    ActivationForbidden,
    InvalidLoss { label: &'static str, value_bits: u64 },
    InvalidDeltaBits,
    ChecksumMismatch { expected: u64, found: u64 },
    ArtifactIdentityMismatch,
    ArtifactValueMismatch,
    DuplicateCandidateIdentifier(u64),
    Artifact(NamedWeightArtifactError),
    Weight(String),
    Malformed(String),
}

impl From<NamedWeightArtifactError> for S3CandidateError {
    fn from(value: NamedWeightArtifactError) -> Self {
        Self::Artifact(value)
    }
}

impl fmt::Display for S3CandidateError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::SchemaVersion { expected, found } => {
                write!(formatter, "expected S3 candidate schema {expected}, found {found}")
            }
            Self::FormatIdentifier { expected, found } => write!(
                formatter,
                "expected S3 candidate format {expected:016x}, found {found:016x}"
            ),
            Self::UnsupportedCandidateType(value) => {
                write!(formatter, "unsupported S3 candidate type {value:?}")
            }
            Self::UnsupportedLossDecision(value) => {
                write!(formatter, "unsupported S3 loss decision {value:?}")
            }
            Self::EmptyIdentity(label) => write!(formatter, "{label} must be non-zero"),
            Self::BaselineIdentityMismatch => formatter.write_str("S3 baseline identity mismatch"),
            Self::DenseVectorLength { expected, found } => {
                write!(formatter, "expected dense vector length {expected}, found {found}")
            }
            Self::TunableParameterCount { expected, found } => {
                write!(formatter, "expected tunable count {expected}, found {found}")
            }
            Self::MaskIdentityMismatch => formatter.write_str("S3 group-mask identity mismatch"),
            Self::ActivationForbidden => formatter.write_str("S3 candidate artifacts must remain inactive"),
            Self::InvalidLoss { label, value_bits } => {
                write!(formatter, "invalid {label} bits {value_bits:016x}")
            }
            Self::InvalidDeltaBits => formatter.write_str("S3 loss delta is not finite"),
            Self::ChecksumMismatch { expected, found } => write!(
                formatter,
                "S3 candidate checksum mismatch: expected {expected:016x}, found {found:016x}"
            ),
            Self::ArtifactIdentityMismatch => formatter.write_str("named-weight artifact identity mismatch"),
            Self::ArtifactValueMismatch => formatter.write_str("named-weight artifact value checksum mismatch"),
            Self::DuplicateCandidateIdentifier(identifier) => {
                write!(formatter, "duplicate S3 candidate identifier {identifier:016x}")
            }
            Self::Artifact(error) => error.fmt(formatter),
            Self::Weight(message) | Self::Malformed(message) => formatter.write_str(message),
        }
    }
}

impl std::error::Error for S3CandidateError {}

/// Stable FNV checksum for exact text input.
#[must_use]
pub fn checksum_text(text: &str) -> u64 {
    hash_bytes(FNV_OFFSET, text.as_bytes())
}

fn parse_group(value: &str) -> Result<EvaluationParameterGroup, S3CandidateError> {
    EvaluationParameterGroup::ALL
        .into_iter()
        .find(|group| group.name() == value)
        .ok_or_else(|| S3CandidateError::Malformed(format!("unknown S3 group {value:?}")))
}

fn validate_invocation(value: &str) -> Result<(), S3CandidateError> {
    if value.is_empty()
        || value.trim() != value
        || value.bytes().any(|byte| matches!(byte, b'\n' | b'\r' | b'\0'))
    {
        return Err(S3CandidateError::Malformed(
            "exact invocation must be non-empty canonical single-line text".to_owned(),
        ));
    }
    Ok(())
}

fn parse_commit(value: &str) -> Result<[u8; 20], S3CandidateError> {
    if value.len() != 40 || !value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(S3CandidateError::Malformed(
            "source commit must be exactly forty hexadecimal digits".to_owned(),
        ));
    }
    let mut output = [0_u8; 20];
    for (index, destination) in output.iter_mut().enumerate() {
        *destination = u8::from_str_radix(&value[index * 2..index * 2 + 2], 16)
            .map_err(|error| S3CandidateError::Malformed(error.to_string()))?;
    }
    Ok(output)
}

fn format_commit(commit: [u8; 20]) -> String {
    commit.iter().map(|byte| format!("{byte:02x}")).collect()
}

fn parse_hex(value: &str, field: &str) -> Result<u64, S3CandidateError> {
    if value.len() != 16 || !value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(S3CandidateError::Malformed(format!(
            "{field} must contain sixteen hexadecimal digits"
        )));
    }
    u64::from_str_radix(value, 16).map_err(|error| S3CandidateError::Malformed(error.to_string()))
}

fn parse_number<T>(value: &str, field: &str) -> Result<T, S3CandidateError>
where
    T: FromStr,
    T::Err: fmt::Display,
{
    value
        .parse::<T>()
        .map_err(|error| S3CandidateError::Malformed(format!("invalid {field}: {error}")))
}

fn hash_bytes(mut hash: u64, bytes: &[u8]) -> u64 {
    for byte in bytes {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    hash
}

#[cfg(test)]
mod tests {
    use chess_search::{EvaluationWeights, BASELINE_WEIGHT_SET_ID};
    use chess_tune::{
        EvaluationParameterGroup, NamedWeightArtifact, TrainingDatasetProvenance, TrainingMetadata,
        TrainingRunProvenance,
    };

    use super::{
        S3CandidateEnvelope, S3CandidateError, S3CandidateRegistry, S3LossDecision,
        S3LossEvidence, S3_VALIDATION_LOSS_TOLERANCE,
    };

    fn artifact(identifier: u64) -> NamedWeightArtifact {
        NamedWeightArtifact::new(
            identifier,
            TrainingMetadata::new(
                TrainingRunProvenance::new(
                    0x5333_5455_4e45_3031,
                    [0x22; 20],
                    7,
                    8,
                    1_786_110_300,
                ),
                TrainingDatasetProvenance::new(1, 0x1111_2222_3333_4444, 128, 32),
            ),
            EvaluationWeights::DEFAULT,
        )
        .expect("artifact is valid")
    }

    fn envelope(identifier: u64, loss: S3LossEvidence) -> S3CandidateEnvelope {
        S3CandidateEnvelope::new(
            EvaluationParameterGroup::PawnStructure,
            &artifact(identifier),
            0x9999_8888_7777_6666,
            "config=canonical\n",
            "report=canonical\n",
            "chess-tools s3-candidate-register pawn_structure".to_owned(),
            loss,
        )
        .expect("candidate envelope is valid")
    }

    #[test]
    fn held_out_rule_requires_strict_training_improvement() {
        let unchanged = S3LossEvidence::assess(0.1, 0.1, 0.2, 0.2).expect("finite losses");
        assert_eq!(
            unchanged.decision(),
            S3LossDecision::RejectNoTrainingImprovement
        );
        let improved = S3LossEvidence::assess(
            0.1,
            0.09,
            0.2,
            0.2 + S3_VALIDATION_LOSS_TOLERANCE,
        )
        .expect("finite losses");
        assert_eq!(improved.decision(), S3LossDecision::Advance);
        let regressed = S3LossEvidence::assess(
            0.1,
            0.09,
            0.2,
            0.2 + S3_VALIDATION_LOSS_TOLERANCE * 2.0,
        )
        .expect("finite losses");
        assert_eq!(
            regressed.decision(),
            S3LossDecision::RejectValidationRegression
        );
    }

    #[test]
    fn candidate_round_trip_binds_artifact_and_remains_inactive() {
        let loss = S3LossEvidence::assess(0.1, 0.1, 0.2, 0.2).expect("finite losses");
        let candidate = envelope(0x5333_4341_4e44_3031, loss);
        assert_eq!(candidate.baseline_identifier, BASELINE_WEIGHT_SET_ID);
        assert!(!candidate.activated);
        let text = candidate.to_text().expect("candidate serializes");
        let parsed = S3CandidateEnvelope::from_text(&text).expect("candidate parses");
        assert_eq!(parsed, candidate);
        parsed
            .validate_artifact(&artifact(candidate.candidate_identifier))
            .expect("artifact binding validates");
    }

    #[test]
    fn schema_checksum_baseline_type_and_length_fail_closed() {
        let loss = S3LossEvidence::assess(0.1, 0.1, 0.2, 0.2).expect("finite losses");
        let candidate = envelope(0x5333_4341_4e44_3032, loss);
        let text = candidate.to_text().expect("candidate serializes");
        assert!(S3CandidateEnvelope::from_text(&text.replace("schema=1", "schema=2")).is_err());
        assert!(S3CandidateEnvelope::from_text(
            &text.replace("candidate_type=existing_evaluation_weights", "candidate_type=nnue")
        )
        .is_err());
        assert!(S3CandidateEnvelope::from_text(
            &text.replace("dense_vector_length=816", "dense_vector_length=815")
        )
        .is_err());
        assert!(S3CandidateEnvelope::from_text(
            &text.replace(
                &format!("baseline_identifier={BASELINE_WEIGHT_SET_ID:016x}"),
                "baseline_identifier=0000000000000001",
            )
        )
        .is_err());
        let mut corrupt = text;
        let checksum_position = corrupt.rfind("checksum=").expect("checksum field exists");
        corrupt.replace_range(checksum_position + 9..checksum_position + 25, "0000000000000001");
        assert!(matches!(
            S3CandidateEnvelope::from_text(&corrupt),
            Err(S3CandidateError::ChecksumMismatch { .. })
        ));
    }

    #[test]
    fn artifact_corruption_and_duplicate_ids_fail_closed() {
        let loss = S3LossEvidence::assess(0.1, 0.1, 0.2, 0.2).expect("finite losses");
        let candidate = envelope(0x5333_4341_4e44_3033, loss);
        let mut wrong = artifact(candidate.candidate_identifier);
        wrong.weights.passed_pawn.mg += 1;
        assert!(candidate.validate_artifact(&wrong).is_err());

        let mut registry = S3CandidateRegistry::default();
        registry.register(candidate.clone()).expect("first registration");
        assert_eq!(registry.len(), 1);
        assert!(matches!(
            registry.register(candidate),
            Err(S3CandidateError::DuplicateCandidateIdentifier(_))
        ));
    }
}
