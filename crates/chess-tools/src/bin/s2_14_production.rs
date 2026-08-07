use std::{
    collections::BTreeMap,
    env,
    error::Error,
    fmt::Write as _,
    fs,
    path::{Path, PathBuf},
};

use chess_core::{Game, Position};
use chess_search::{EvaluationWeightSet, SearchPolicySet};
use chess_tools::{
    engine_variant::{EngineVariantDescriptor, EngineVariantIdentity, OptionalCapabilityIdentity},
    engine_variant_validation::{
        run_engine_variant_validation, write_engine_variant_validation_report_atomic,
        EngineVariantResourceProtocol, EngineVariantRuntime, EngineVariantValidationConfig,
        EngineVariantValidationReport, EngineVariantValidationTier,
        ENGINE_VARIANT_VALIDATION_IDENTIFIER, ENGINE_VARIANT_VALIDATION_SCHEMA_VERSION,
    },
    self_play::{ClaimableDrawPolicy, OpeningSuite},
    STARTING_FEN,
};

const MANIFEST_SCHEMA_VERSION: u16 = 1;
const TT_MEBIBYTES: usize = 1;
const CONTROL_MAXIMUM_PLIES: u32 = 256;
const FIXED_NODE_BUDGET: u64 = 2_000;
const CLOCK_MILLISECONDS: u64 = 10;
const BASELINE_ROLE_IDENTIFIER: u64 = 0x5332_3134_4241_5345;
const CANDIDATE_ROLE_IDENTIFIER: u64 = 0x5332_3134_4341_4e44;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct ControlPlan {
    tier: EngineVariantValidationTier,
    pair_count: u32,
    seed: u64,
}

fn main() {
    if let Err(error) = run() {
        eprintln!("s2-14 variant control failed: {error}");
        std::process::exit(1);
    }
}

fn run() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let output_directory = PathBuf::from(
        arguments
            .next()
            .ok_or("usage: s2_14_production OUTPUT_DIRECTORY TIER PROTOCOL")?,
    );
    let tier_text = arguments
        .next()
        .ok_or("usage: s2_14_production OUTPUT_DIRECTORY TIER PROTOCOL")?
        .into_string()
        .map_err(|_| "TIER must be valid UTF-8")?;
    let protocol_text = arguments
        .next()
        .ok_or("usage: s2_14_production OUTPUT_DIRECTORY TIER PROTOCOL")?
        .into_string()
        .map_err(|_| "PROTOCOL must be valid UTF-8")?;
    if arguments.next().is_some() {
        return Err("usage: s2_14_production OUTPUT_DIRECTORY TIER PROTOCOL".into());
    }
    if output_directory.exists() {
        return Err(format!(
            "output directory already exists: {}",
            output_directory.display()
        )
        .into());
    }

    let plan = control_plan(&tier_text)?;
    let protocol = control_protocol(&protocol_text)?;
    let protocol_label = protocol_label(protocol);
    let source_text = required_environment("S2_14_SOURCE_SHA")?;
    let source_commit = parse_source_commit(&source_text)?;
    let build_identity = required_environment("S2_14_BUILD_IDENTITY")?;
    let exact_invocation = required_environment("S2_14_EXACT_INVOCATION")?;

    fs::create_dir(&output_directory)?;

    let policy = SearchPolicySet::baseline();
    let candidate_policy = SearchPolicySet::principal_variation_search_candidate();
    let weights = EvaluationWeightSet::baseline();
    policy.validate()?;
    candidate_policy.validate()?;
    weights.validate()?;
    if policy.policy.principal_variation_search_enabled()
        || !candidate_policy.policy.principal_variation_search_enabled()
        || candidate_policy.policy.see_capture_ordering_enabled()
        || candidate_policy.policy.see_quiescence_pruning_enabled()
        || candidate_policy.policy.delta_pruning_enabled()
        || candidate_policy.policy.late_move_reductions_enabled()
        || candidate_policy.policy.null_move_pruning_enabled()
    {
        return Err("S2-14 PVS candidate policy boundary is invalid".into());
    }

    let openings = control_openings()?;
    let opening_path = output_directory.join("s2-14-control-openings.tsv");
    write_new(&opening_path, openings.as_bytes())?;
    let suite = OpeningSuite::from_text(&openings)?;

    let baseline_identity = identity(
        BASELINE_ROLE_IDENTIFIER,
        source_commit,
        &build_identity,
        &format!("{exact_invocation} --role baseline"),
        &policy,
        &weights,
    )?;
    let candidate_identity = identity(
        CANDIDATE_ROLE_IDENTIFIER,
        source_commit,
        &build_identity,
        &format!("{exact_invocation} --role candidate"),
        &candidate_policy,
        &weights,
    )?;
    let baseline = EngineVariantRuntime::new(&baseline_identity, &policy, &weights)?;
    let candidate = EngineVariantRuntime::new(&candidate_identity, &candidate_policy, &weights)?;

    let config = EngineVariantValidationConfig::new(
        plan.tier,
        plan.pair_count,
        plan.seed,
        protocol,
        TT_MEBIBYTES,
    )?
    .with_maximum_plies(CONTROL_MAXIMUM_PLIES)?
    .with_maximum_unfinished_per_mille(if plan.tier == EngineVariantValidationTier::Production {
        50
    } else {
        1_000
    })?
    .with_claimable_draw_policy(ClaimableDrawPolicy::Accept);

    let report = run_engine_variant_validation(config, &suite, baseline, candidate)?;
    let serialized = report.serialize()?;
    let reparsed = EngineVariantValidationReport::deserialize(&serialized)?;
    if reparsed != report {
        return Err("serialized S2-14 report did not round-trip exactly".into());
    }
    validate_control_report(&report)?;

    let report_name = format!("s2-14-{tier_text}-{protocol_label}-control.report");
    let report_path = output_directory.join(&report_name);
    let temporary_path = output_directory.join(format!(".{report_name}.tmp"));
    write_engine_variant_validation_report_atomic(&report_path, &temporary_path, &report)?;

    let manifest = format!(
        "S2_14_VARIANT_CONTROL_MANIFEST\t{MANIFEST_SCHEMA_VERSION}\nsource_sha\t{source_text}\nbuild_identity\t{build_identity}\nexact_invocation\t{exact_invocation}\ntier\t{tier_text}\nprotocol\t{protocol}\nprotocol_purpose\t{}\npair_count\t{}\ngame_count\t{}\nreport_schema\t{}\nreport_identifier\t{:016x}\npolicy_identifier\t{:016x}\npolicy_checksum\t{:016x}\nweight_identifier\t{:016x}\nweight_checksum\t{:016x}\nbaseline_variant_checksum\t{:016x}\ncandidate_variant_checksum\t{:016x}\nreport_file\t{report_name}\nreport_checksum\t{:016x}\ndecision\t{}\nactivated\tfalse\n",
        protocol.purpose(),
        plan.pair_count,
        report.games.len(),
        ENGINE_VARIANT_VALIDATION_SCHEMA_VERSION,
        ENGINE_VARIANT_VALIDATION_IDENTIFIER,
        policy.identifier,
        policy.checksum,
        weights.identifier,
        weights.checksum,
        baseline_identity.checksum(),
        candidate_identity.checksum(),
        report.checksum,
        report.decision,
    );
    let manifest = format!(
        "{manifest}candidate_policy_identifier\t{:016x}\ncandidate_policy_checksum\t{:016x}\nopening_provenance\tfirst_party_deterministic_generator_v1\nopening_license\tMIT\n",
        candidate_policy.identifier, candidate_policy.checksum
    );
    write_new(
        &output_directory.join("s2-14-control-manifest.tsv"),
        manifest.as_bytes(),
    )?;

    println!(
        "s2_14_production\ttier={tier_text}\tprotocol={protocol_label}\tpairs={}\tgames={}\tdecision={}\tactivated={}\tchecksum={:016x}",
        plan.pair_count,
        report.games.len(),
        report.decision,
        report.activated(),
        report.checksum,
    );
    Ok(())
}

fn required_environment(name: &str) -> Result<String, Box<dyn Error>> {
    let value = env::var(name).map_err(|_| format!("{name} must be supplied explicitly"))?;
    if value.trim().is_empty() {
        return Err(format!("{name} must not be empty").into());
    }
    Ok(value)
}

fn control_plan(value: &str) -> Result<ControlPlan, Box<dyn Error>> {
    match value {
        "smoke" => Ok(ControlPlan {
            tier: EngineVariantValidationTier::Smoke,
            pair_count: 1,
            seed: 0x5332_3134_534d_4f4b,
        }),
        "development" => Ok(ControlPlan {
            tier: EngineVariantValidationTier::Development,
            pair_count: 8,
            seed: 0x5332_3134_4445_5631,
        }),
        "production" => Ok(ControlPlan {
            tier: EngineVariantValidationTier::Production,
            pair_count: 1_000,
            seed: 0x5332_3134_5052_4f44,
        }),
        _ => Err(format!("unsupported S2-14 validation tier {value:?}").into()),
    }
}

fn control_protocol(value: &str) -> Result<EngineVariantResourceProtocol, Box<dyn Error>> {
    match value {
        "fixed_nodes" => Ok(EngineVariantResourceProtocol::FixedNodes(FIXED_NODE_BUDGET)),
        "clock_ms" => Ok(EngineVariantResourceProtocol::ClockMilliseconds(
            CLOCK_MILLISECONDS,
        )),
        _ => Err(format!("unsupported S2-14 resource protocol {value:?}").into()),
    }
}

const fn protocol_label(protocol: EngineVariantResourceProtocol) -> &'static str {
    match protocol {
        EngineVariantResourceProtocol::FixedNodes(_) => "fixed-nodes",
        EngineVariantResourceProtocol::ClockMilliseconds(_) => "clock-ms",
    }
}

fn parse_source_commit(value: &str) -> Result<[u8; 20], Box<dyn Error>> {
    if value.len() != 40 || !value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err("S2_14_SOURCE_SHA must be exactly 40 hexadecimal characters".into());
    }
    let mut result = [0_u8; 20];
    for (index, slot) in result.iter_mut().enumerate() {
        *slot = u8::from_str_radix(&value[index * 2..index * 2 + 2], 16)?;
    }
    if result.iter().all(|byte| *byte == 0) {
        return Err("S2_14_SOURCE_SHA must not be all zeroes".into());
    }
    Ok(result)
}

fn identity(
    identifier: u64,
    source_commit: [u8; 20],
    build_identity: &str,
    exact_invocation: &str,
    policy: &SearchPolicySet,
    weights: &EvaluationWeightSet,
) -> Result<EngineVariantIdentity, Box<dyn Error>> {
    Ok(EngineVariantIdentity::new(
        EngineVariantDescriptor {
            identifier,
            source_commit,
            engine_version: env!("CARGO_PKG_VERSION").to_owned(),
            opening_book: OptionalCapabilityIdentity::Disabled,
            tablebase: OptionalCapabilityIdentity::Disabled,
            transposition_table_mebibytes: TT_MEBIBYTES as u64,
            build_identity: build_identity.to_owned(),
            exact_invocation: exact_invocation.to_owned(),
        },
        policy,
        weights,
    )?)
}

fn control_openings() -> Result<String, Box<dyn Error>> {
    const OPENING_COUNT: usize = 1_200;
    const MAXIMUM_ATTEMPTS: usize = 100_000;
    let mut output = String::from("CHESS_SELF_PLAY_OPENINGS\t1\n");
    let mut seen = std::collections::BTreeSet::new();
    let mut accepted = 0_usize;

    for attempt in 0..MAXIMUM_ATTEMPTS {
        if accepted == OPENING_COUNT {
            break;
        }
        let target_plies = 6 + ((attempt + accepted * 7) % 15);
        let mut game = Game::new(Position::starting());
        let mut moves = Vec::with_capacity(target_plies);
        let mut state = splitmix64(0x5332_3134_4f50_4e31_u64 ^ attempt as u64);
        let mut complete = true;

        for ply in 0..target_plies {
            let mut legal = game.legal_moves()?.iter().collect::<Vec<_>>();
            if legal.is_empty() {
                complete = false;
                break;
            }
            legal.sort_by_key(|current| current.to_uci());
            state = splitmix64(state ^ (ply as u64).wrapping_mul(0x9e37_79b9_7f4a_7c15));
            let selected = legal[(state as usize) % legal.len()];
            game.make_move(selected)?;
            moves.push(selected.to_uci());
        }
        if !complete {
            continue;
        }
        let normalized = moves.join(" ");
        if !seen.insert(normalized.clone()) {
            continue;
        }
        writeln!(
            output,
            "production-{accepted:04}\t{STARTING_FEN}\t{normalized}"
        )?;
        accepted += 1;
    }

    if accepted != OPENING_COUNT {
        return Err(format!(
            "expected {OPENING_COUNT} deterministic production openings, found {accepted}"
        )
        .into());
    }
    Ok(output)
}

const fn splitmix64(mut value: u64) -> u64 {
    value = value.wrapping_add(0x9e37_79b9_7f4a_7c15);
    value = (value ^ (value >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
    value = (value ^ (value >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
    value ^ (value >> 31)
}

fn validate_control_report(report: &EngineVariantValidationReport) -> Result<(), Box<dyn Error>> {
    report.validate()?;
    if !report.correctness.passed() {
        return Err("S2-14 control correctness pre-gate did not pass".into());
    }
    if report.activated()
        || report.illegal_moves != 0
        || report.crashes != 0
        || report.time_forfeits != 0
        || report.infrastructure_failures != 0
    {
        return Err(
            "S2-14 control report contains activation or game infrastructure failure".into(),
        );
    }
    let expected_games = report
        .config
        .pair_count()
        .checked_mul(2)
        .ok_or("S2-14 control game count overflow")?;
    if report.games.len() != expected_games as usize {
        return Err("S2-14 control report game count does not match paired schedule".into());
    }

    let fields = report_fields(&report.serialize()?)?;
    if required(&fields, "activated")? != "false"
        || required(&fields, "pair_count")? != report.config.pair_count().to_string()
        || required(&fields, "game_count")? != expected_games.to_string()
        || required(&fields, "checksum")? != format!("{:016x}", report.checksum)
    {
        return Err("S2-14 serialized control report does not match validated structure".into());
    }
    Ok(())
}

fn report_fields(text: &str) -> Result<BTreeMap<String, String>, Box<dyn Error>> {
    let mut fields = BTreeMap::new();
    for line in text.lines().skip(1) {
        let Some((key, value)) = line.split_once('=') else {
            return Err(format!("report line is not key=value: {line:?}").into());
        };
        if key.starts_with("game.") {
            continue;
        }
        if fields.insert(key.to_owned(), value.to_owned()).is_some() {
            return Err(format!("duplicate report field {key:?}").into());
        }
    }
    Ok(fields)
}

fn required<'a>(
    fields: &'a BTreeMap<String, String>,
    key: &str,
) -> Result<&'a str, Box<dyn Error>> {
    fields
        .get(key)
        .map(String::as_str)
        .ok_or_else(|| format!("missing report field {key:?}").into())
}

fn write_new(path: &Path, bytes: &[u8]) -> Result<(), Box<dyn Error>> {
    if path.exists() {
        return Err(format!("refusing to replace existing evidence {}", path.display()).into());
    }
    fs::write(path, bytes)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::{control_openings, control_plan, control_protocol, parse_source_commit};
    use chess_tools::{
        engine_variant_validation::{EngineVariantResourceProtocol, EngineVariantValidationTier},
        self_play::OpeningSuite,
    };

    #[test]
    fn plans_are_bounded_and_tier_correct() {
        let smoke = control_plan("smoke").expect("smoke plan");
        let development = control_plan("development").expect("development plan");
        let production = control_plan("production").expect("production plan");
        assert_eq!(smoke.tier, EngineVariantValidationTier::Smoke);
        assert_eq!(smoke.pair_count, 1);
        assert_eq!(development.tier, EngineVariantValidationTier::Development);
        assert_eq!(development.pair_count, 8);
        assert_eq!(production.tier, EngineVariantValidationTier::Production);
        assert_eq!(production.pair_count, 1_000);
        assert!(control_plan("unknown").is_err());
    }

    #[test]
    fn protocols_are_explicit_and_bounded() {
        assert_eq!(
            control_protocol("fixed_nodes").expect("fixed-node protocol"),
            EngineVariantResourceProtocol::FixedNodes(2_000)
        );
        assert_eq!(
            control_protocol("clock_ms").expect("clock protocol"),
            EngineVariantResourceProtocol::ClockMilliseconds(10)
        );
        assert!(control_protocol("depth").is_err());
    }

    #[test]
    fn generated_openings_are_versioned_unique_and_complete() {
        let text = control_openings().expect("control openings generate");
        assert_eq!(text.lines().skip(1).count(), 1_200);
        OpeningSuite::from_text(&text).expect("generated openings parse strictly");
    }

    #[test]
    fn source_commit_is_exact_and_nonzero() {
        assert!(parse_source_commit("1111111111111111111111111111111111111111").is_ok());
        assert!(parse_source_commit("0000000000000000000000000000000000000000").is_err());
        assert!(parse_source_commit("abc").is_err());
    }
}
