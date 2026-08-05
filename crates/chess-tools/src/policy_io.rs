use std::collections::BTreeMap;

use chess_search::{
    AlphaBetaMode, ExperimentalSearchFeatures, MoveOrderingPolicy, QuiescencePolicy,
    SearchPolicy, SearchPolicyParameters, SearchPolicySet, TranspositionPolicy,
    SEARCH_POLICY_SCHEMA_VERSION,
};

use super::ToolError;

const FORMAT_MARKER: &str = "chess-search-policy-v1";
const FIELD_COUNT: usize = 11;

/// Serializes a validated search policy into canonical explicit text.
pub fn serialize_search_policy(set: &SearchPolicySet) -> Result<String, ToolError> {
    set.validate()
        .map_err(|error| ToolError::new(error.to_string()))?;
    let parameters = set.policy.parameters();
    Ok(format!(
        concat!(
            "{FORMAT_MARKER}\n",
            "schema={}\n",
            "identifier={:016x}\n",
            "checksum={:016x}\n",
            "alpha_beta={}\n",
            "transposition={}\n",
            "move_ordering={}\n",
            "quiescence={}\n",
            "aspiration_windows={}\n",
            "aspiration_half_width_centipawns={}\n",
            "maximum_quiescence_ply={}\n",
            "maximum_check_extensions_per_line={}\n",
            "experimental_features={:016x}\n"
        ),
        set.schema_version,
        set.identifier,
        set.checksum,
        parameters.alpha_beta.name(),
        parameters.transposition.name(),
        parameters.move_ordering.name(),
        parameters.quiescence.name(),
        parameters.aspiration_windows,
        parameters.aspiration_half_width_centipawns,
        parameters.maximum_quiescence_ply,
        parameters.maximum_check_extensions_per_line,
        parameters.experimental_features.bits(),
    ))
}

/// Parses an order-independent explicit policy file and validates its canonical identity.
pub fn deserialize_search_policy(input: &str) -> Result<SearchPolicySet, ToolError> {
    let mut lines = input.lines();
    if lines.next() != Some(FORMAT_MARKER) {
        return Err(ToolError::new(format!(
            "search-policy file must begin with {FORMAT_MARKER:?}"
        )));
    }

    let mut fields = BTreeMap::new();
    for line in lines {
        let (name, value) = line.split_once('=').ok_or_else(|| {
            ToolError::new(format!("search-policy field must use name=value syntax: {line:?}"))
        })?;
        if name.is_empty() || value.is_empty() {
            return Err(ToolError::new(format!(
                "search-policy field name and value must be non-empty: {line:?}"
            )));
        }
        if !is_known_field(name) {
            return Err(ToolError::new(format!(
                "unknown search-policy field {name:?}"
            )));
        }
        if fields.insert(name, value).is_some() {
            return Err(ToolError::new(format!(
                "duplicate search-policy field {name:?}"
            )));
        }
    }
    if fields.len() != FIELD_COUNT {
        return Err(ToolError::new(format!(
            "search-policy file requires {FIELD_COUNT} fields, found {}",
            fields.len()
        )));
    }

    let schema_version = parse_u16(required(&fields, "schema")?, "schema")?;
    let identifier = parse_hex(required(&fields, "identifier")?, "identifier")?;
    let checksum = parse_hex(required(&fields, "checksum")?, "checksum")?;
    let alpha_beta = match required(&fields, "alpha_beta")? {
        "full_window_fail_soft" => AlphaBetaMode::FullWindowFailSoft,
        value => return Err(unknown_value("alpha_beta", value)),
    };
    let transposition = match required(&fields, "transposition")? {
        "clustered_full_key" => TranspositionPolicy::ClusteredFullKey,
        value => return Err(unknown_value("transposition", value)),
    };
    let move_ordering = match required(&fields, "move_ordering")? {
        "v0_1_mvv_lva_killers_history" => MoveOrderingPolicy::V0_1MvvLvaKillersHistory,
        value => return Err(unknown_value("move_ordering", value)),
    };
    let quiescence = match required(&fields, "quiescence")? {
        "captures_promotions_and_evasions" => QuiescencePolicy::CapturesPromotionsAndEvasions,
        value => return Err(unknown_value("quiescence", value)),
    };
    let aspiration_windows = parse_bool(
        required(&fields, "aspiration_windows")?,
        "aspiration_windows",
    )?;
    let aspiration_half_width_centipawns = parse_u16(
        required(&fields, "aspiration_half_width_centipawns")?,
        "aspiration_half_width_centipawns",
    )?;
    let maximum_quiescence_ply = parse_u16(
        required(&fields, "maximum_quiescence_ply")?,
        "maximum_quiescence_ply",
    )?;
    let maximum_check_extensions_per_line = parse_u16(
        required(&fields, "maximum_check_extensions_per_line")?,
        "maximum_check_extensions_per_line",
    )?;
    let experimental_bits = parse_hex(
        required(&fields, "experimental_features")?,
        "experimental_features",
    )?;
    let experimental_features = ExperimentalSearchFeatures::from_bits(experimental_bits)
        .map_err(|error| ToolError::new(error.to_string()))?;

    let policy = SearchPolicy::new(SearchPolicyParameters {
        alpha_beta,
        transposition,
        move_ordering,
        quiescence,
        aspiration_windows,
        aspiration_half_width_centipawns,
        maximum_quiescence_ply,
        maximum_check_extensions_per_line,
        experimental_features,
    });
    let set = SearchPolicySet::from_parts(schema_version, identifier, policy, checksum);
    set.validate()
        .map_err(|error| ToolError::new(error.to_string()))?;
    if set.schema_version != SEARCH_POLICY_SCHEMA_VERSION {
        return Err(ToolError::new(
            "validated search-policy schema changed unexpectedly",
        ));
    }
    Ok(set)
}

fn is_known_field(name: &str) -> bool {
    matches!(
        name,
        "schema"
            | "identifier"
            | "checksum"
            | "alpha_beta"
            | "transposition"
            | "move_ordering"
            | "quiescence"
            | "aspiration_windows"
            | "aspiration_half_width_centipawns"
            | "maximum_quiescence_ply"
            | "maximum_check_extensions_per_line"
            | "experimental_features"
    )
}

fn required<'a>(fields: &'a BTreeMap<&str, &str>, name: &str) -> Result<&'a str, ToolError> {
    fields
        .get(name)
        .copied()
        .ok_or_else(|| ToolError::new(format!("missing search-policy field {name:?}")))
}

fn parse_bool(value: &str, name: &str) -> Result<bool, ToolError> {
    match value {
        "true" => Ok(true),
        "false" => Ok(false),
        _ => Err(ToolError::new(format!(
            "search-policy field {name} must be true or false, found {value:?}"
        ))),
    }
}

fn parse_u16(value: &str, name: &str) -> Result<u16, ToolError> {
    value.parse::<u16>().map_err(|error| {
        ToolError::new(format!(
            "invalid search-policy field {name} value {value:?}: {error}"
        ))
    })
}

fn parse_hex(value: &str, name: &str) -> Result<u64, ToolError> {
    if value.len() != 16 || !value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(ToolError::new(format!(
            "search-policy field {name} must contain exactly sixteen hexadecimal digits"
        )));
    }
    u64::from_str_radix(value, 16).map_err(|error| {
        ToolError::new(format!(
            "invalid search-policy field {name} value {value:?}: {error}"
        ))
    })
}

fn unknown_value(name: &str, value: &str) -> ToolError {
    ToolError::new(format!(
        "unsupported search-policy field {name} value {value:?}"
    ))
}

#[cfg(test)]
mod tests {
    use chess_search::SearchPolicySet;

    use super::{deserialize_search_policy, serialize_search_policy};

    #[test]
    fn baseline_round_trips_and_field_order_is_semantically_irrelevant() {
        let baseline = SearchPolicySet::baseline();
        let canonical = serialize_search_policy(&baseline).expect("baseline serializes");
        assert_eq!(
            deserialize_search_policy(&canonical).expect("canonical policy parses"),
            baseline
        );

        let mut lines: Vec<_> = canonical.lines().collect();
        let marker = lines.remove(0);
        lines.reverse();
        let reordered = format!("{marker}\n{}\n", lines.join("\n"));
        assert_eq!(
            deserialize_search_policy(&reordered).expect("reordered policy parses"),
            baseline
        );
    }

    #[test]
    fn duplicate_missing_unknown_corrupt_and_unsupported_input_fails() {
        let baseline = SearchPolicySet::baseline();
        let canonical = serialize_search_policy(&baseline).expect("baseline serializes");
        let duplicate = format!("{canonical}schema=1\n");
        assert!(deserialize_search_policy(&duplicate).is_err());

        let missing = canonical
            .lines()
            .filter(|line| !line.starts_with("quiescence="))
            .collect::<Vec<_>>()
            .join("\n");
        assert!(deserialize_search_policy(&missing).is_err());

        let unknown = format!("{canonical}surprise=true\n");
        assert!(deserialize_search_policy(&unknown).is_err());

        let corrupt = canonical.replacen(
            &format!("checksum={:016x}", baseline.checksum),
            "checksum=0000000000000000",
            1,
        );
        assert!(deserialize_search_policy(&corrupt).is_err());

        let unsupported = canonical
            .replacen("experimental_features=0000000000000000", "experimental_features=0000000000000001", 1)
            .replacen(
                &format!("checksum={:016x}", baseline.checksum),
                "checksum=0000000000000000",
                1,
            );
        assert!(deserialize_search_policy(&unsupported).is_err());
    }
}
