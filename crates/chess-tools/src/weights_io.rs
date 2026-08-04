use chess_search::{
    EvaluationWeightSet, EvaluationWeights, EVALUATION_WEIGHT_SCHEMA_VERSION, WEIGHT_VALUE_COUNT,
};

use super::ToolError;

const FORMAT_MARKER: &str = "chess-eval-weights-v1";

/// Serializes a validated weight set into the explicit canonical text format.
pub fn serialize_weight_set(set: &EvaluationWeightSet) -> Result<String, ToolError> {
    set.validate()
        .map_err(|error| ToolError::new(error.to_string()))?;
    let values = set
        .weights
        .values()
        .into_iter()
        .map(|value| value.to_string())
        .collect::<Vec<_>>()
        .join(",");
    Ok(format!(
        "{FORMAT_MARKER}\nschema={}\nidentifier={:016x}\nchecksum={:016x}\nvalues={values}\n",
        set.schema_version, set.identifier, set.checksum
    ))
}

/// Parses and validates the canonical explicit weight-set text format.
pub fn deserialize_weight_set(input: &str) -> Result<EvaluationWeightSet, ToolError> {
    let lines: Vec<_> = input.lines().collect();
    if lines.len() != 5 || lines[0] != FORMAT_MARKER {
        return Err(ToolError::new(format!(
            "weight file must contain the {FORMAT_MARKER:?} marker and exactly four fields"
        )));
    }
    let schema = parse_decimal_field(lines[1], "schema")?;
    let schema_version = u16::try_from(schema)
        .map_err(|error| ToolError::new(format!("schema is out of range: {error}")))?;
    let identifier = parse_hex_field(lines[2], "identifier")?;
    let checksum = parse_hex_field(lines[3], "checksum")?;
    let values_text = field_value(lines[4], "values")?;
    let values: Vec<_> = if values_text.is_empty() {
        Vec::new()
    } else {
        values_text
            .split(',')
            .enumerate()
            .map(|(index, value)| {
                value.parse::<i16>().map_err(|error| {
                    ToolError::new(format!("invalid weight value {index} {value:?}: {error}"))
                })
            })
            .collect::<Result<_, _>>()?
    };
    if values.len() != WEIGHT_VALUE_COUNT {
        return Err(ToolError::new(format!(
            "expected {WEIGHT_VALUE_COUNT} weight values, found {}",
            values.len()
        )));
    }
    let values: [i16; WEIGHT_VALUE_COUNT] = values
        .try_into()
        .map_err(|_| ToolError::new("weight vector length changed during conversion"))?;
    let set = EvaluationWeightSet::from_parts(
        schema_version,
        identifier,
        EvaluationWeights::from_values(values),
        checksum,
    );
    set.validate()
        .map_err(|error| ToolError::new(error.to_string()))?;
    if set.schema_version != EVALUATION_WEIGHT_SCHEMA_VERSION {
        return Err(ToolError::new(
            "validated schema version changed unexpectedly",
        ));
    }
    Ok(set)
}

fn field_value<'a>(line: &'a str, name: &str) -> Result<&'a str, ToolError> {
    line.strip_prefix(name)
        .and_then(|suffix| suffix.strip_prefix('='))
        .ok_or_else(|| ToolError::new(format!("expected {name}= field, found {line:?}")))
}

fn parse_decimal_field(line: &str, name: &str) -> Result<u64, ToolError> {
    let value = field_value(line, name)?;
    value
        .parse::<u64>()
        .map_err(|error| ToolError::new(format!("invalid {name} value {value:?}: {error}")))
}

fn parse_hex_field(line: &str, name: &str) -> Result<u64, ToolError> {
    let value = field_value(line, name)?;
    if value.len() != 16 || !value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(ToolError::new(format!(
            "{name} must contain exactly sixteen hexadecimal digits"
        )));
    }
    u64::from_str_radix(value, 16)
        .map_err(|error| ToolError::new(format!("invalid {name} value {value:?}: {error}")))
}

#[cfg(test)]
mod tests {
    use chess_search::EvaluationWeightSet;

    use super::{deserialize_weight_set, serialize_weight_set};

    #[test]
    fn baseline_round_trips_through_the_explicit_text_format() {
        let baseline = EvaluationWeightSet::baseline();
        let encoded = serialize_weight_set(&baseline).expect("baseline serializes");
        assert_eq!(
            deserialize_weight_set(&encoded).expect("baseline parses"),
            baseline
        );
    }

    #[test]
    fn incompatible_or_corrupt_files_fail_loudly() {
        let baseline = EvaluationWeightSet::baseline();
        let encoded = serialize_weight_set(&baseline).expect("baseline serializes");
        let wrong_schema = encoded.replacen("schema=1", "schema=2", 1);
        assert!(deserialize_weight_set(&wrong_schema).is_err());

        let wrong_checksum = encoded.replacen(
            &format!("checksum={:016x}", baseline.checksum),
            "checksum=0000000000000000",
            1,
        );
        assert!(deserialize_weight_set(&wrong_checksum).is_err());
        assert!(deserialize_weight_set("").is_err());
    }
}
