use core::fmt;

use crate::{
    SpsaIterationDiagnostics, S4_OPTIMIZER_DIAGNOSTIC_SCHEMA_VERSION, TUNABLE_PARAMETER_COUNT,
};

/// Current canonical S4 optimizer-trace schema.
pub const S4_OPTIMIZER_TRACE_SCHEMA_VERSION: u16 = 1;
/// Stable semantic identity for S4 optimizer traces.
pub const S4_OPTIMIZER_TRACE_IDENTIFIER: u64 = 0x5334_5452_4143_3031;

const TRACE_MARKER: &str = "CHESS_S4_OPTIMIZER_TRACE\t1";
const ITERATION_MARKER: &str = "iteration";
const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;

/// Exact provenance required to interpret an S4 optimizer trace.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct S4OptimizerTraceBinding {
    /// Exact source commit that ran the optimizer.
    pub source_commit: [u8; 20],
    /// Checksum of the exact tuning configuration text.
    pub tuning_config_checksum: u64,
    /// Checksum of the strict S3/S4 dataset manifest.
    pub dataset_manifest_checksum: u64,
    /// Exact selected parameter-mask fingerprint.
    pub parameter_mask_fingerprint: u64,
    /// Initial named-weight identifier.
    pub initial_weight_identifier: u64,
    /// Initial named-weight artifact checksum.
    pub initial_weight_checksum: u64,
    /// Explicit optimizer random seed.
    pub random_seed: u64,
    /// Optimizer configuration fingerprint stored by the checkpoint.
    pub config_fingerprint: u64,
    /// Loss-dataset fingerprint stored by the checkpoint.
    pub dataset_fingerprint: u64,
    /// Checksum of the checkpoint before the first traced iteration.
    pub initial_checkpoint_checksum: u64,
}

impl S4OptimizerTraceBinding {
    fn validate(self) -> Result<(), S4OptimizerTraceError> {
        if self.source_commit == [0; 20] {
            return Err(S4OptimizerTraceError::EmptyIdentity("source commit"));
        }
        for (name, value) in [
            ("tuning config checksum", self.tuning_config_checksum),
            ("dataset manifest checksum", self.dataset_manifest_checksum),
            ("parameter mask fingerprint", self.parameter_mask_fingerprint),
            ("initial weight identifier", self.initial_weight_identifier),
            ("initial weight checksum", self.initial_weight_checksum),
            ("config fingerprint", self.config_fingerprint),
            ("dataset fingerprint", self.dataset_fingerprint),
            ("initial checkpoint checksum", self.initial_checkpoint_checksum),
        ] {
            if value == 0 {
                return Err(S4OptimizerTraceError::EmptyIdentity(name));
            }
        }
        Ok(())
    }
}

/// Strict, checksummed S4 trace over one bounded optimizer advance operation.
#[derive(Clone, Debug, PartialEq)]
pub struct S4OptimizerTrace {
    binding: S4OptimizerTraceBinding,
    iterations: Vec<SpsaIterationDiagnostics>,
    checksum: u64,
}

impl S4OptimizerTrace {
    /// Builds and validates a canonical trace.
    pub fn new(
        binding: S4OptimizerTraceBinding,
        iterations: Vec<SpsaIterationDiagnostics>,
    ) -> Result<Self, S4OptimizerTraceError> {
        let mut trace = Self {
            binding,
            iterations,
            checksum: 0,
        };
        trace.validate_semantics()?;
        trace.checksum = trace.computed_checksum();
        Ok(trace)
    }

    /// Bound provenance.
    #[must_use]
    pub const fn binding(&self) -> S4OptimizerTraceBinding {
        self.binding
    }

    /// Exact iteration records.
    #[must_use]
    pub fn iterations(&self) -> &[SpsaIterationDiagnostics] {
        &self.iterations
    }

    /// Canonical semantic checksum.
    #[must_use]
    pub const fn checksum(&self) -> u64 {
        self.checksum
    }

    /// Requires the trace to match an externally expected binding exactly.
    pub fn validate_binding(
        &self,
        expected: S4OptimizerTraceBinding,
    ) -> Result<(), S4OptimizerTraceError> {
        if self.binding != expected {
            return Err(S4OptimizerTraceError::BindingMismatch);
        }
        Ok(())
    }

    /// Serializes the trace canonically using integer fields and IEEE-754 bit images.
    pub fn to_text(&self) -> Result<String, S4OptimizerTraceError> {
        self.validate()?;
        let mut output = self.canonical_without_checksum();
        output.push_str(&format!("checksum={:016x}\n", self.checksum));
        Ok(output)
    }

    /// Parses strict canonical text. Unknown, duplicate, missing, reordered or noncanonical
    /// fields are rejected because the parsed trace must reproduce the input byte-for-byte.
    pub fn from_text(text: &str) -> Result<Self, S4OptimizerTraceError> {
        if !text.ends_with('\n') || text.contains("\r") {
            return Err(S4OptimizerTraceError::Malformed(
                "trace must use canonical LF-terminated lines".to_owned(),
            ));
        }
        let lines: Vec<&str> = text.lines().collect();
        if lines.first().copied() != Some(TRACE_MARKER) {
            return Err(S4OptimizerTraceError::Malformed(
                "invalid trace marker".to_owned(),
            ));
        }
        let mut cursor = 1_usize;
        let schema = parse_key_u16(&lines, &mut cursor, "schema")?;
        if schema != S4_OPTIMIZER_TRACE_SCHEMA_VERSION {
            return Err(S4OptimizerTraceError::SchemaVersion {
                expected: S4_OPTIMIZER_TRACE_SCHEMA_VERSION,
                found: schema,
            });
        }
        let identifier = parse_key_hex(&lines, &mut cursor, "identifier")?;
        if identifier != S4_OPTIMIZER_TRACE_IDENTIFIER {
            return Err(S4OptimizerTraceError::Identifier {
                expected: S4_OPTIMIZER_TRACE_IDENTIFIER,
                found: identifier,
            });
        }
        let diagnostic_schema = parse_key_u16(&lines, &mut cursor, "diagnostic_schema")?;
        if diagnostic_schema != S4_OPTIMIZER_DIAGNOSTIC_SCHEMA_VERSION {
            return Err(S4OptimizerTraceError::DiagnosticSchema {
                expected: S4_OPTIMIZER_DIAGNOSTIC_SCHEMA_VERSION,
                found: diagnostic_schema,
            });
        }
        let source_commit = parse_key_commit(&lines, &mut cursor, "source_commit")?;
        let tuning_config_checksum =
            parse_key_hex(&lines, &mut cursor, "tuning_config_checksum")?;
        let dataset_manifest_checksum =
            parse_key_hex(&lines, &mut cursor, "dataset_manifest_checksum")?;
        let parameter_mask_fingerprint =
            parse_key_hex(&lines, &mut cursor, "parameter_mask_fingerprint")?;
        let initial_weight_identifier =
            parse_key_hex(&lines, &mut cursor, "initial_weight_identifier")?;
        let initial_weight_checksum =
            parse_key_hex(&lines, &mut cursor, "initial_weight_checksum")?;
        let random_seed = parse_key_u64(&lines, &mut cursor, "random_seed")?;
        let config_fingerprint = parse_key_hex(&lines, &mut cursor, "config_fingerprint")?;
        let dataset_fingerprint = parse_key_hex(&lines, &mut cursor, "dataset_fingerprint")?;
        let initial_checkpoint_checksum =
            parse_key_hex(&lines, &mut cursor, "initial_checkpoint_checksum")?;
        let iteration_count = parse_key_usize(&lines, &mut cursor, "iteration_count")?;
        if iteration_count > 1_000_000 {
            return Err(S4OptimizerTraceError::Malformed(
                "iteration count exceeds supported trace ceiling".to_owned(),
            ));
        }
        let mut iterations = Vec::with_capacity(iteration_count);
        for _ in 0..iteration_count {
            let line = lines.get(cursor).ok_or_else(|| {
                S4OptimizerTraceError::Malformed("missing iteration row".to_owned())
            })?;
            iterations.push(parse_iteration(line)?);
            cursor += 1;
        }
        let checksum = parse_key_hex(&lines, &mut cursor, "checksum")?;
        if cursor != lines.len() {
            return Err(S4OptimizerTraceError::Malformed(
                "unexpected trailing trace fields".to_owned(),
            ));
        }
        let trace = Self {
            binding: S4OptimizerTraceBinding {
                source_commit,
                tuning_config_checksum,
                dataset_manifest_checksum,
                parameter_mask_fingerprint,
                initial_weight_identifier,
                initial_weight_checksum,
                random_seed,
                config_fingerprint,
                dataset_fingerprint,
                initial_checkpoint_checksum,
            },
            iterations,
            checksum,
        };
        trace.validate()?;
        if trace.to_text()? != text {
            return Err(S4OptimizerTraceError::NonCanonical);
        }
        Ok(trace)
    }

    /// Validates semantic invariants and the checksum.
    pub fn validate(&self) -> Result<(), S4OptimizerTraceError> {
        self.validate_semantics()?;
        let expected = self.computed_checksum();
        if self.checksum != expected {
            return Err(S4OptimizerTraceError::ChecksumMismatch {
                expected,
                found: self.checksum,
            });
        }
        Ok(())
    }

    fn validate_semantics(&self) -> Result<(), S4OptimizerTraceError> {
        self.binding.validate()?;
        if self.iterations.is_empty() {
            return Err(S4OptimizerTraceError::Malformed(
                "trace requires at least one iteration".to_owned(),
            ));
        }
        let mut previous_iteration = None;
        let mut previous_checkpoint = self.binding.initial_checkpoint_checksum;
        for diagnostic in &self.iterations {
            if !diagnostic.validate_counts() {
                return Err(S4OptimizerTraceError::ImpossibleCounts {
                    iteration: diagnostic.iteration(),
                });
            }
            validate_finite(*diagnostic)?;
            if diagnostic.active_parameter_count() as usize > TUNABLE_PARAMETER_COUNT {
                return Err(S4OptimizerTraceError::ImpossibleCounts {
                    iteration: diagnostic.iteration(),
                });
            }
            if let Some(previous) = previous_iteration {
                if diagnostic.iteration() != previous + 1 {
                    return Err(S4OptimizerTraceError::IterationSequence {
                        previous,
                        found: diagnostic.iteration(),
                    });
                }
            }
            if diagnostic.checkpoint_checksum() == 0
                || diagnostic.checkpoint_checksum() == previous_checkpoint
            {
                return Err(S4OptimizerTraceError::CheckpointIdentity {
                    iteration: diagnostic.iteration(),
                });
            }
            previous_iteration = Some(diagnostic.iteration());
            previous_checkpoint = diagnostic.checkpoint_checksum();
        }
        Ok(())
    }

    fn computed_checksum(&self) -> u64 {
        hash_bytes(FNV_OFFSET, self.canonical_without_checksum().as_bytes())
    }

    fn canonical_without_checksum(&self) -> String {
        let mut output = String::new();
        output.push_str(TRACE_MARKER);
        output.push('\n');
        output.push_str(&format!("schema={}\n", S4_OPTIMIZER_TRACE_SCHEMA_VERSION));
        output.push_str(&format!(
            "identifier={:016x}\n",
            S4_OPTIMIZER_TRACE_IDENTIFIER
        ));
        output.push_str(&format!(
            "diagnostic_schema={}\n",
            S4_OPTIMIZER_DIAGNOSTIC_SCHEMA_VERSION
        ));
        output.push_str(&format!(
            "source_commit={}\n",
            format_commit(self.binding.source_commit)
        ));
        for (key, value) in [
            ("tuning_config_checksum", self.binding.tuning_config_checksum),
            ("dataset_manifest_checksum", self.binding.dataset_manifest_checksum),
            ("parameter_mask_fingerprint", self.binding.parameter_mask_fingerprint),
            ("initial_weight_identifier", self.binding.initial_weight_identifier),
            ("initial_weight_checksum", self.binding.initial_weight_checksum),
        ] {
            output.push_str(&format!("{key}={value:016x}\n"));
        }
        output.push_str(&format!("random_seed={}\n", self.binding.random_seed));
        for (key, value) in [
            ("config_fingerprint", self.binding.config_fingerprint),
            ("dataset_fingerprint", self.binding.dataset_fingerprint),
            ("initial_checkpoint_checksum", self.binding.initial_checkpoint_checksum),
        ] {
            output.push_str(&format!("{key}={value:016x}\n"));
        }
        output.push_str(&format!("iteration_count={}\n", self.iterations.len()));
        for diagnostic in &self.iterations {
            output.push_str(&format_iteration(*diagnostic));
        }
        output
    }
}

/// Strict trace parsing/validation failure.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum S4OptimizerTraceError {
    /// Unsupported trace schema.
    SchemaVersion { expected: u16, found: u16 },
    /// Unsupported trace identifier.
    Identifier { expected: u64, found: u64 },
    /// Unsupported per-iteration diagnostic schema.
    DiagnosticSchema { expected: u16, found: u16 },
    /// Required identity was zero/empty.
    EmptyIdentity(&'static str),
    /// Text was structurally invalid.
    Malformed(String),
    /// Text parsed semantically but was not the exact canonical byte image.
    NonCanonical,
    /// Semantic checksum mismatch.
    ChecksumMismatch { expected: u64, found: u64 },
    /// Caller-provided expected provenance did not match.
    BindingMismatch,
    /// Counts could not describe the selected active parameters.
    ImpossibleCounts { iteration: u64 },
    /// Iterations were not strictly consecutive.
    IterationSequence { previous: u64, found: u64 },
    /// A checkpoint identity was absent or repeated.
    CheckpointIdentity { iteration: u64 },
    /// A floating diagnostic value was NaN or infinite.
    NonFinite { iteration: u64 },
}

impl fmt::Display for S4OptimizerTraceError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::SchemaVersion { expected, found } => {
                write!(formatter, "expected S4 trace schema {expected}, found {found}")
            }
            Self::Identifier { expected, found } => write!(
                formatter,
                "expected S4 trace identifier {expected:016x}, found {found:016x}"
            ),
            Self::DiagnosticSchema { expected, found } => write!(
                formatter,
                "expected S4 diagnostic schema {expected}, found {found}"
            ),
            Self::EmptyIdentity(name) => write!(formatter, "S4 trace {name} must be non-zero"),
            Self::Malformed(message) => write!(formatter, "malformed S4 trace: {message}"),
            Self::NonCanonical => formatter.write_str("S4 trace text is not canonical"),
            Self::ChecksumMismatch { expected, found } => write!(
                formatter,
                "S4 trace checksum mismatch: expected {expected:016x}, found {found:016x}"
            ),
            Self::BindingMismatch => formatter.write_str("S4 trace provenance binding mismatch"),
            Self::ImpossibleCounts { iteration } => {
                write!(formatter, "impossible S4 diagnostic counts at iteration {iteration}")
            }
            Self::IterationSequence { previous, found } => write!(
                formatter,
                "S4 trace iteration sequence jumped from {previous} to {found}"
            ),
            Self::CheckpointIdentity { iteration } => write!(
                formatter,
                "invalid S4 checkpoint identity at iteration {iteration}"
            ),
            Self::NonFinite { iteration } => {
                write!(formatter, "non-finite S4 diagnostic at iteration {iteration}")
            }
        }
    }
}

impl std::error::Error for S4OptimizerTraceError {}

fn validate_finite(diagnostic: SpsaIterationDiagnostics) -> Result<(), S4OptimizerTraceError> {
    let values = [
        diagnostic.positive_data_loss(),
        diagnostic.negative_data_loss(),
        diagnostic.positive_regularization(),
        diagnostic.negative_regularization(),
        diagnostic.objective_difference(),
        diagnostic.gain(),
        diagnostic.perturbation(),
        diagnostic.gradient_scale(),
        diagnostic.minimum_absolute_gradient(),
        diagnostic.maximum_absolute_gradient(),
        diagnostic.mean_absolute_gradient(),
        diagnostic.minimum_proposed_update(),
        diagnostic.maximum_proposed_update(),
        diagnostic.mean_proposed_update(),
        diagnostic.resulting_training_loss(),
    ];
    if values.into_iter().any(|value| !value.is_finite())
        || diagnostic
            .resulting_validation_loss()
            .is_some_and(|value| !value.is_finite())
    {
        return Err(S4OptimizerTraceError::NonFinite {
            iteration: diagnostic.iteration(),
        });
    }
    Ok(())
}

fn format_iteration(d: SpsaIterationDiagnostics) -> String {
    let validation = d
        .resulting_validation_loss()
        .map(|value| format!("{:016x}", value.to_bits()))
        .unwrap_or_else(|| "none".to_owned());
    format!(
        concat!(
            "{}\t{}\t{:016x}\t{:016x}\t{:016x}\t{:016x}\t{:016x}\t{:016x}\t{:016x}",
            "\t{:016x}\t{:016x}\t{:016x}\t{:016x}\t{}\t{}\t{}\t{}\t{:016x}\t{:016x}",
            "\t{:016x}\t{:016x}\t{:016x}\t{:016x}\t{}\t{}\t{}\t{}\t{:016x}\t{:016x}",
            "\t{}\t{:016x}\n"
        ),
        ITERATION_MARKER,
        d.iteration(),
        d.perturbation_vector_checksum(),
        d.positive_value_checksum(),
        d.negative_value_checksum(),
        d.positive_data_loss().to_bits(),
        d.negative_data_loss().to_bits(),
        d.positive_regularization().to_bits(),
        d.negative_regularization().to_bits(),
        d.objective_difference().to_bits(),
        d.gain().to_bits(),
        d.perturbation().to_bits(),
        d.gradient_scale().to_bits(),
        d.active_parameter_count(),
        d.positive_gradient_count(),
        d.negative_gradient_count(),
        d.zero_gradient_count(),
        d.minimum_absolute_gradient().to_bits(),
        d.maximum_absolute_gradient().to_bits(),
        d.mean_absolute_gradient().to_bits(),
        d.minimum_proposed_update().to_bits(),
        d.maximum_proposed_update().to_bits(),
        d.mean_proposed_update().to_bits(),
        d.zero_after_quantization_count(),
        d.nonzero_integer_update_count(),
        d.clipped_update_count(),
        d.changed_parameter_count(),
        d.resulting_value_checksum(),
        d.resulting_training_loss().to_bits(),
        validation,
        d.checkpoint_checksum(),
    )
}

fn parse_iteration(line: &str) -> Result<SpsaIterationDiagnostics, S4OptimizerTraceError> {
    let fields: Vec<&str> = line.split('\t').collect();
    if fields.len() != 31 || fields[0] != ITERATION_MARKER {
        return Err(S4OptimizerTraceError::Malformed(
            "iteration row does not match schema".to_owned(),
        ));
    }
    let validation = if fields[29] == "none" {
        None
    } else {
        Some(f64::from_bits(parse_hex(fields[29], "validation loss bits")?))
    };
    let diagnostic = SpsaIterationDiagnostics {
        iteration: parse_u64(fields[1], "iteration")?,
        perturbation_vector_checksum: parse_hex(fields[2], "perturbation checksum")?,
        positive_value_checksum: parse_hex(fields[3], "positive value checksum")?,
        negative_value_checksum: parse_hex(fields[4], "negative value checksum")?,
        positive_data_loss: f64::from_bits(parse_hex(fields[5], "positive loss bits")?),
        negative_data_loss: f64::from_bits(parse_hex(fields[6], "negative loss bits")?),
        positive_regularization: f64::from_bits(parse_hex(fields[7], "positive regularization bits")?),
        negative_regularization: f64::from_bits(parse_hex(fields[8], "negative regularization bits")?),
        objective_difference: f64::from_bits(parse_hex(fields[9], "objective difference bits")?),
        gain: f64::from_bits(parse_hex(fields[10], "gain bits")?),
        perturbation: f64::from_bits(parse_hex(fields[11], "perturbation bits")?),
        gradient_scale: f64::from_bits(parse_hex(fields[12], "gradient scale bits")?),
        active_parameter_count: parse_u32(fields[13], "active parameter count")?,
        positive_gradient_count: parse_u32(fields[14], "positive gradient count")?,
        negative_gradient_count: parse_u32(fields[15], "negative gradient count")?,
        zero_gradient_count: parse_u32(fields[16], "zero gradient count")?,
        minimum_absolute_gradient: f64::from_bits(parse_hex(fields[17], "minimum gradient bits")?),
        maximum_absolute_gradient: f64::from_bits(parse_hex(fields[18], "maximum gradient bits")?),
        mean_absolute_gradient: f64::from_bits(parse_hex(fields[19], "mean gradient bits")?),
        minimum_proposed_update: f64::from_bits(parse_hex(fields[20], "minimum update bits")?),
        maximum_proposed_update: f64::from_bits(parse_hex(fields[21], "maximum update bits")?),
        mean_proposed_update: f64::from_bits(parse_hex(fields[22], "mean update bits")?),
        zero_after_quantization_count: parse_u32(fields[23], "zero-after-quantization count")?,
        nonzero_integer_update_count: parse_u32(fields[24], "integer update count")?,
        clipped_update_count: parse_u32(fields[25], "clipped update count")?,
        changed_parameter_count: parse_u32(fields[26], "changed parameter count")?,
        resulting_value_checksum: parse_hex(fields[27], "resulting value checksum")?,
        resulting_training_loss: f64::from_bits(parse_hex(fields[28], "training loss bits")?),
        resulting_validation_loss: validation,
        checkpoint_checksum: parse_hex(fields[30], "checkpoint checksum")?,
    };
    validate_finite(diagnostic)?;
    Ok(diagnostic)
}

fn parse_key_value<'a>(
    lines: &'a [&str],
    cursor: &mut usize,
    expected_key: &str,
) -> Result<&'a str, S4OptimizerTraceError> {
    let line = lines.get(*cursor).ok_or_else(|| {
        S4OptimizerTraceError::Malformed(format!("missing field {expected_key}"))
    })?;
    *cursor += 1;
    let (key, value) = line.split_once('=').ok_or_else(|| {
        S4OptimizerTraceError::Malformed(format!("invalid field {line:?}"))
    })?;
    if key != expected_key || value.is_empty() || value.trim() != value {
        return Err(S4OptimizerTraceError::Malformed(format!(
            "expected field {expected_key}, found {line:?}"
        )));
    }
    Ok(value)
}

fn parse_key_u16(
    lines: &[&str],
    cursor: &mut usize,
    key: &str,
) -> Result<u16, S4OptimizerTraceError> {
    parse_key_value(lines, cursor, key)?
        .parse()
        .map_err(|_| S4OptimizerTraceError::Malformed(format!("invalid {key}")))
}

fn parse_key_u64(
    lines: &[&str],
    cursor: &mut usize,
    key: &str,
) -> Result<u64, S4OptimizerTraceError> {
    parse_u64(parse_key_value(lines, cursor, key)?, key)
}

fn parse_key_usize(
    lines: &[&str],
    cursor: &mut usize,
    key: &str,
) -> Result<usize, S4OptimizerTraceError> {
    parse_key_value(lines, cursor, key)?
        .parse()
        .map_err(|_| S4OptimizerTraceError::Malformed(format!("invalid {key}")))
}

fn parse_key_hex(
    lines: &[&str],
    cursor: &mut usize,
    key: &str,
) -> Result<u64, S4OptimizerTraceError> {
    parse_hex(parse_key_value(lines, cursor, key)?, key)
}

fn parse_key_commit(
    lines: &[&str],
    cursor: &mut usize,
    key: &str,
) -> Result<[u8; 20], S4OptimizerTraceError> {
    parse_commit(parse_key_value(lines, cursor, key)?)
}

fn parse_u64(value: &str, name: &str) -> Result<u64, S4OptimizerTraceError> {
    value
        .parse()
        .map_err(|_| S4OptimizerTraceError::Malformed(format!("invalid {name}")))
}

fn parse_u32(value: &str, name: &str) -> Result<u32, S4OptimizerTraceError> {
    value
        .parse()
        .map_err(|_| S4OptimizerTraceError::Malformed(format!("invalid {name}")))
}

fn parse_hex(value: &str, name: &str) -> Result<u64, S4OptimizerTraceError> {
    if value.len() != 16 || value.bytes().any(|byte| !byte.is_ascii_hexdigit() || byte.is_ascii_uppercase()) {
        return Err(S4OptimizerTraceError::Malformed(format!(
            "noncanonical hexadecimal {name}"
        )));
    }
    u64::from_str_radix(value, 16)
        .map_err(|_| S4OptimizerTraceError::Malformed(format!("invalid {name}")))
}

fn parse_commit(value: &str) -> Result<[u8; 20], S4OptimizerTraceError> {
    if value.len() != 40 || value.bytes().any(|byte| !byte.is_ascii_hexdigit() || byte.is_ascii_uppercase()) {
        return Err(S4OptimizerTraceError::Malformed(
            "source commit must be 40 lowercase hexadecimal characters".to_owned(),
        ));
    }
    let mut output = [0_u8; 20];
    for (index, byte) in output.iter_mut().enumerate() {
        *byte = u8::from_str_radix(&value[index * 2..index * 2 + 2], 16)
            .map_err(|_| S4OptimizerTraceError::Malformed("invalid source commit".to_owned()))?;
    }
    Ok(output)
}

fn format_commit(commit: [u8; 20]) -> String {
    let mut output = String::with_capacity(40);
    for byte in commit {
        output.push_str(&format!("{byte:02x}"));
    }
    output
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
    use super::{
        S4OptimizerTrace, S4OptimizerTraceBinding, S4OptimizerTraceError,
    };
    use crate::SpsaIterationDiagnostics;

    fn diagnostic(iteration: u64, checkpoint_checksum: u64) -> SpsaIterationDiagnostics {
        SpsaIterationDiagnostics {
            iteration,
            perturbation_vector_checksum: 0x11 + iteration,
            positive_value_checksum: 0x21 + iteration,
            negative_value_checksum: 0x31 + iteration,
            positive_data_loss: 0.4,
            negative_data_loss: 0.5,
            positive_regularization: 0.01,
            negative_regularization: 0.02,
            objective_difference: -0.11,
            gain: 0.1,
            perturbation: 2.0,
            gradient_scale: -0.0275,
            active_parameter_count: 2,
            positive_gradient_count: 1,
            negative_gradient_count: 1,
            zero_gradient_count: 0,
            minimum_absolute_gradient: 0.0275,
            maximum_absolute_gradient: 0.0275,
            mean_absolute_gradient: 0.0275,
            minimum_proposed_update: 0.00275,
            maximum_proposed_update: 0.00275,
            mean_proposed_update: 0.00275,
            zero_after_quantization_count: 2,
            nonzero_integer_update_count: 0,
            clipped_update_count: 0,
            changed_parameter_count: 0,
            resulting_value_checksum: 0x41 + iteration,
            resulting_training_loss: 0.45,
            resulting_validation_loss: Some(0.46),
            checkpoint_checksum,
        }
    }

    fn binding() -> S4OptimizerTraceBinding {
        S4OptimizerTraceBinding {
            source_commit: [0x11; 20],
            tuning_config_checksum: 0x12,
            dataset_manifest_checksum: 0x13,
            parameter_mask_fingerprint: 0x14,
            initial_weight_identifier: 0x15,
            initial_weight_checksum: 0x16,
            random_seed: 23,
            config_fingerprint: 0x18,
            dataset_fingerprint: 0x19,
            initial_checkpoint_checksum: 0x1a,
        }
    }

    #[test]
    fn trace_round_trip_is_bit_canonical() {
        let trace = S4OptimizerTrace::new(
            binding(),
            vec![diagnostic(1, 0x50), diagnostic(2, 0x51)],
        )
        .expect("trace is valid");
        let text = trace.to_text().expect("trace serializes");
        let parsed = S4OptimizerTrace::from_text(&text).expect("trace parses");
        assert_eq!(parsed, trace);
        assert_eq!(parsed.to_text().expect("reserializes"), text);
    }

    #[test]
    fn trace_checksum_corruption_fails_closed() {
        let trace = S4OptimizerTrace::new(binding(), vec![diagnostic(1, 0x50)])
            .expect("trace is valid");
        let text = trace.to_text().expect("trace serializes");
        let corrupted = text.replacen("positive", "positive", 0).replace(
            "initial_weight_checksum=0000000000000016",
            "initial_weight_checksum=0000000000000017",
        );
        assert!(matches!(
            S4OptimizerTrace::from_text(&corrupted),
            Err(S4OptimizerTraceError::ChecksumMismatch { .. })
        ));
    }

    #[test]
    fn wrong_binding_fails_closed() {
        let trace = S4OptimizerTrace::new(binding(), vec![diagnostic(1, 0x50)])
            .expect("trace is valid");
        let mut wrong = binding();
        wrong.dataset_manifest_checksum += 1;
        assert_eq!(
            trace.validate_binding(wrong),
            Err(S4OptimizerTraceError::BindingMismatch)
        );
    }

    #[test]
    fn malformed_or_impossible_trace_is_rejected() {
        let trace = S4OptimizerTrace::new(binding(), vec![diagnostic(1, 0x50)])
            .expect("trace is valid");
        let text = trace.to_text().expect("trace serializes");
        assert!(S4OptimizerTrace::from_text(&text.replace("schema=1", "schema=2")).is_err());
        assert!(S4OptimizerTrace::from_text(&text.replace(
            "iteration_count=1",
            "iteration_count=1\nunknown=1"
        ))
        .is_err());

        let mut impossible = diagnostic(1, 0x50);
        impossible.positive_gradient_count = 3;
        assert!(matches!(
            S4OptimizerTrace::new(binding(), vec![impossible]),
            Err(S4OptimizerTraceError::ImpossibleCounts { .. })
        ));
    }
}
