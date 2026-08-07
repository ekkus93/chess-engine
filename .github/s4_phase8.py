from pathlib import Path

binary = Path('crates/chess-tools/src/bin/s4_candidate_smoke.rs')
binary.write_text(r'''use std::{env, error::Error, fmt::Write as _, fs, path::PathBuf};

use chess_core::{Game, Position};
use chess_search::{EvaluationWeightSet, SearchPolicySet};
use chess_tools::{
    engine_variant::{EngineVariantDescriptor, EngineVariantIdentity, OptionalCapabilityIdentity},
    engine_variant_validation::{
        run_engine_variant_validation, write_engine_variant_validation_report_atomic,
        EngineVariantResourceProtocol, EngineVariantRuntime, EngineVariantValidationConfig,
        EngineVariantValidationReport, EngineVariantValidationTier,
    },
    self_play::{ClaimableDrawPolicy, OpeningSuite},
    STARTING_FEN,
};
use chess_tune::NamedWeightArtifact;

const TT_MEBIBYTES: usize = 1;
const PAIR_COUNT: u32 = 16;
const MAXIMUM_PLIES: u32 = 256;
const FIXED_NODE_BUDGET: u64 = 2_000;
const CLOCK_MILLISECONDS: u64 = 10;
const BASELINE_VARIANT_IDENTIFIER: u64 = 0x5334_534d_4241_5345;
const CANDIDATE_VARIANT_IDENTIFIER: u64 = 0x5334_534d_4341_4e44;
const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;

fn main() {
    if let Err(error) = run() {
        eprintln!("S4 candidate smoke failed: {error}");
        std::process::exit(1);
    }
}

fn run() -> Result<(), Box<dyn Error>> {
    let mut args = env::args();
    let _program = args.next();
    let artifact_path = PathBuf::from(args.next().ok_or(
        "usage: s4_candidate_smoke CANDIDATE_ARTIFACT OUTPUT_DIRECTORY PROTOCOL",
    )?);
    let output_directory = PathBuf::from(args.next().ok_or(
        "usage: s4_candidate_smoke CANDIDATE_ARTIFACT OUTPUT_DIRECTORY PROTOCOL",
    )?);
    let protocol_text = args.next().ok_or(
        "usage: s4_candidate_smoke CANDIDATE_ARTIFACT OUTPUT_DIRECTORY PROTOCOL",
    )?;
    if args.next().is_some() {
        return Err(
            "usage: s4_candidate_smoke CANDIDATE_ARTIFACT OUTPUT_DIRECTORY PROTOCOL".into(),
        );
    }
    if output_directory.exists() {
        return Err(format!(
            "output directory already exists: {}",
            output_directory.display()
        )
        .into());
    }

    let source_text = required_environment("S4_SMOKE_SOURCE_SHA")?;
    let source_commit = parse_commit(&source_text)?;
    let build_identity = required_environment("S4_SMOKE_BUILD_IDENTITY")?;
    let exact_invocation = required_environment("S4_SMOKE_EXACT_INVOCATION")?;
    let expected_value_checksum = parse_hex_u64(&required_environment(
        "S4_SMOKE_EXPECTED_VALUE_CHECKSUM",
    )?)?;

    let artifact_text = fs::read_to_string(&artifact_path)?;
    let artifact = NamedWeightArtifact::deserialize(&artifact_text)?;
    artifact.validate()?;
    if artifact.metadata.source_commit != source_commit {
        return Err("candidate artifact source commit does not match smoke source".into());
    }
    let value_checksum = evaluation_value_checksum(&artifact);
    if value_checksum != expected_value_checksum {
        return Err(format!(
            "candidate value checksum mismatch: expected {expected_value_checksum:016x}, found {value_checksum:016x}"
        )
        .into());
    }

    let baseline_policy = SearchPolicySet::baseline();
    let baseline_weights = EvaluationWeightSet::baseline();
    let candidate_weights = EvaluationWeightSet::new(artifact.identifier, artifact.weights)?;
    baseline_policy.validate()?;
    baseline_weights.validate()?;
    candidate_weights.validate()?;
    if candidate_weights.checksum == baseline_weights.checksum {
        return Err("candidate evaluation-weight checksum equals baseline".into());
    }

    let baseline_identity = identity(
        BASELINE_VARIANT_IDENTIFIER,
        source_commit,
        &build_identity,
        &format!("{exact_invocation} --role baseline"),
        &baseline_policy,
        &baseline_weights,
    )?;
    let candidate_identity = identity(
        CANDIDATE_VARIANT_IDENTIFIER,
        source_commit,
        &build_identity,
        &format!("{exact_invocation} --role candidate"),
        &baseline_policy,
        &candidate_weights,
    )?;
    let baseline = EngineVariantRuntime::new(
        &baseline_identity,
        &baseline_policy,
        &baseline_weights,
    )?;
    let candidate = EngineVariantRuntime::new(
        &candidate_identity,
        &baseline_policy,
        &candidate_weights,
    )?;

    let protocol = match protocol_text.as_str() {
        "fixed_nodes" => EngineVariantResourceProtocol::FixedNodes(FIXED_NODE_BUDGET),
        "clock_ms" => EngineVariantResourceProtocol::ClockMilliseconds(CLOCK_MILLISECONDS),
        _ => return Err(format!("unsupported S4 smoke protocol {protocol_text:?}").into()),
    };
    let openings_text = deterministic_openings()?;
    let suite = OpeningSuite::from_text(&openings_text)?;
    let config = EngineVariantValidationConfig::new(
        EngineVariantValidationTier::Development,
        PAIR_COUNT,
        0x5334_534d_4f4b_4531,
        protocol,
        TT_MEBIBYTES,
    )?
    .with_maximum_plies(MAXIMUM_PLIES)?
    .with_maximum_unfinished_per_mille(1_000)?
    .with_claimable_draw_policy(ClaimableDrawPolicy::Accept);

    let report = run_engine_variant_validation(config, &suite, baseline, candidate)?;
    validate_report(&report)?;

    fs::create_dir(&output_directory)?;
    fs::write(output_directory.join("s4-smoke-openings.tsv"), openings_text)?;
    let report_name = format!("s4-development-{protocol_text}.report");
    let report_path = output_directory.join(&report_name);
    let temporary = output_directory.join(format!(".{report_name}.tmp"));
    write_engine_variant_validation_report_atomic(&report_path, &temporary, &report)?;
    let manifest = format!(
        concat!(
            "S4_CANDIDATE_SMOKE_MANIFEST\t1\n",
            "source_sha\t{}\nprotocol\t{}\npair_count\t{}\ngame_count\t{}\n",
            "baseline_policy_identifier\t{:016x}\nbaseline_policy_checksum\t{:016x}\n",
            "baseline_weight_identifier\t{:016x}\nbaseline_weight_checksum\t{:016x}\n",
            "candidate_weight_identifier\t{:016x}\ncandidate_weight_checksum\t{:016x}\n",
            "candidate_artifact_checksum\t{:016x}\ncandidate_value_checksum\t{:016x}\n",
            "baseline_variant_checksum\t{:016x}\ncandidate_variant_checksum\t{:016x}\n",
            "report_checksum\t{:016x}\ndecision\t{}\nactivated\tfalse\n"
        ),
        source_text,
        protocol_text,
        PAIR_COUNT,
        report.games.len(),
        baseline_policy.identifier,
        baseline_policy.checksum,
        baseline_weights.identifier,
        baseline_weights.checksum,
        candidate_weights.identifier,
        candidate_weights.checksum,
        artifact.checksum,
        value_checksum,
        baseline_identity.checksum(),
        candidate_identity.checksum(),
        report.checksum,
        report.decision,
    );
    fs::write(output_directory.join("s4-smoke-manifest.tsv"), manifest)?;
    println!(
        "s4_candidate_smoke\tprotocol={}\tpairs={}\tgames={}\tdecision={}\tactivated={}\tchecksum={:016x}",
        protocol_text,
        PAIR_COUNT,
        report.games.len(),
        report.decision,
        report.activated(),
        report.checksum,
    );
    Ok(())
}

fn validate_report(report: &EngineVariantValidationReport) -> Result<(), Box<dyn Error>> {
    report.validate()?;
    if !report.correctness.passed() {
        return Err("S4 development smoke correctness pre-gate failed".into());
    }
    if report.activated()
        || report.illegal_moves != 0
        || report.crashes != 0
        || report.time_forfeits != 0
        || report.infrastructure_failures != 0
    {
        return Err("S4 development smoke contains activation or infrastructure failure".into());
    }
    let expected_games = PAIR_COUNT.checked_mul(2).ok_or("game count overflow")?;
    if report.games.len() != expected_games as usize {
        return Err("S4 development smoke game count does not match paired schedule".into());
    }
    let text = report.serialize()?;
    let reparsed = EngineVariantValidationReport::deserialize(&text)?;
    if reparsed != *report {
        return Err("S4 development smoke report did not round-trip exactly".into());
    }
    Ok(())
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

fn deterministic_openings() -> Result<String, Box<dyn Error>> {
    const OPENING_COUNT: usize = 64;
    const MAXIMUM_ATTEMPTS: usize = 20_000;
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
        let mut state = splitmix64(0x5334_534d_4f50_4e31_u64 ^ attempt as u64);
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
        if complete {
            let normalized = moves.join(" ");
            if seen.insert(normalized.clone()) {
                writeln!(output, "s4-{accepted:03}\t{STARTING_FEN}\t{normalized}")?;
                accepted += 1;
            }
        }
    }
    if accepted != OPENING_COUNT {
        return Err(format!("expected {OPENING_COUNT} smoke openings, found {accepted}").into());
    }
    Ok(output)
}

fn required_environment(name: &str) -> Result<String, Box<dyn Error>> {
    let value = env::var(name).map_err(|_| format!("{name} must be supplied explicitly"))?;
    if value.trim().is_empty() {
        return Err(format!("{name} must not be empty").into());
    }
    Ok(value)
}

fn parse_commit(value: &str) -> Result<[u8; 20], Box<dyn Error>> {
    if value.len() != 40 || !value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err("source SHA must be exactly 40 hexadecimal characters".into());
    }
    let mut output = [0_u8; 20];
    for (index, byte) in output.iter_mut().enumerate() {
        *byte = u8::from_str_radix(&value[index * 2..index * 2 + 2], 16)?;
    }
    if output == [0; 20] {
        return Err("source SHA must not be zero".into());
    }
    Ok(output)
}

fn parse_hex_u64(value: &str) -> Result<u64, Box<dyn Error>> {
    if value.len() != 16
        || value
            .bytes()
            .any(|byte| !byte.is_ascii_hexdigit() || byte.is_ascii_uppercase())
    {
        return Err("expected 16 lowercase hexadecimal characters".into());
    }
    Ok(u64::from_str_radix(value, 16)?)
}

fn evaluation_value_checksum(artifact: &NamedWeightArtifact) -> u64 {
    let mut hash = FNV_OFFSET;
    for value in artifact.weights.values() {
        for byte in value.to_le_bytes() {
            hash ^= u64::from(byte);
            hash = hash.wrapping_mul(FNV_PRIME);
        }
    }
    hash
}

const fn splitmix64(mut value: u64) -> u64 {
    value = value.wrapping_add(0x9e37_79b9_7f4a_7c15);
    value = (value ^ (value >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
    value = (value ^ (value >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
    value ^ (value >> 31)
}
''')

audit = Path('scripts/task_s4_evaluation_tuning_calibration_audit.sh')
text = audit.read_text()
anchor = "require_literal 'degraded_queen_material_recovers_real_chess_loss_signal' \"$optimizer\"\n"
addition = anchor + '''require_file crates/chess-tools/src/bin/s4_candidate_smoke.rs
require_literal 'NamedWeightArtifact::deserialize' crates/chess-tools/src/bin/s4_candidate_smoke.rs
require_literal 'SearchPolicySet::baseline()' crates/chess-tools/src/bin/s4_candidate_smoke.rs
require_literal 'EvaluationWeightSet::new(artifact.identifier, artifact.weights)' crates/chess-tools/src/bin/s4_candidate_smoke.rs
require_literal 'EngineVariantValidationTier::Development' crates/chess-tools/src/bin/s4_candidate_smoke.rs
require_literal 'activated\\tfalse' crates/chess-tools/src/bin/s4_candidate_smoke.rs
'''
if text.count(anchor) != 1:
    raise SystemExit('S4 smoke audit anchor missing')
text = text.replace(anchor, addition, 1)
audit.write_text(text)
