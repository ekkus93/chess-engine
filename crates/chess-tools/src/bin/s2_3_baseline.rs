use std::{
    collections::{BTreeMap, BTreeSet},
    env,
    error::Error,
    fmt::Write as _,
    fs,
    path::{Path, PathBuf},
};

use chess_core::{Game, Move, Position, SearchHistory, UciMove};
use chess_search::{
    iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights,
    EvaluationWeightSet, Score, SearchLimits, SearchPolicySet, TranspositionTable,
};
use chess_tools::{
    engine_variant::{EngineVariantDescriptor, EngineVariantIdentity, OptionalCapabilityIdentity},
    engine_variant_validation::{
        run_engine_variant_validation, write_engine_variant_validation_report_atomic,
        EngineVariantResourceProtocol, EngineVariantRuntime, EngineVariantValidationConfig,
        EngineVariantValidationTier,
    },
    self_play::{ClaimableDrawPolicy, OpeningSuite},
    STARTING_FEN,
};

const CORPUS: &str = include_str!("../../../../fixtures/search_baseline_v1.tsv");
const CORPUS_SCHEMA: u16 = 1;
const REPORT_SCHEMA: u16 = 1;
const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;
const TT_MEBIBYTES: usize = 1;
const REQUIRED_CATEGORIES: [&str; 13] = [
    "mate_in_1",
    "mate_in_2_plus",
    "longest_survival",
    "stalemate",
    "repetition",
    "fifty_move",
    "seventy_five_move",
    "promotion_race",
    "en_passant_tactic",
    "quiet_defense",
    "zugzwang_sensitive",
    "poisoned_capture",
    "legal_pv_replay",
];

#[derive(Clone, Debug, Eq, PartialEq)]
struct CorpusCase {
    identifier: String,
    category: String,
    fen: String,
    depth: u16,
    expectation: String,
    expected: String,
}

fn main() {
    if let Err(error) = run() {
        eprintln!("s2-3 baseline failed: {error}");
        std::process::exit(1);
    }
}

fn run() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let output_directory = PathBuf::from(
        arguments
            .next()
            .ok_or("usage: s2_3_baseline OUTPUT_DIRECTORY")?,
    );
    if arguments.next().is_some() {
        return Err("usage: s2_3_baseline OUTPUT_DIRECTORY".into());
    }
    if output_directory.exists() {
        return Err(format!(
            "output directory already exists: {}",
            output_directory.display()
        )
        .into());
    }
    fs::create_dir(&output_directory)?;

    let source_text = env::var("S2_3_SOURCE_SHA")
        .map_err(|_| "S2_3_SOURCE_SHA must contain the exact 40-hex source commit")?;
    let source_commit = parse_source_commit(&source_text)?;
    let build_identity = env::var("S2_3_BUILD_IDENTITY")
        .map_err(|_| "S2_3_BUILD_IDENTITY must be supplied explicitly")?;
    if build_identity.trim().is_empty() {
        return Err("S2_3_BUILD_IDENTITY must not be empty".into());
    }

    let policy = SearchPolicySet::baseline();
    let weights = EvaluationWeightSet::baseline();
    policy.validate()?;
    weights.validate()?;

    let tactical = run_tactical_corpus(&policy, &weights, &source_text, &build_identity)?;
    write_new(
        &output_directory.join("s2-3-tactical-baseline.tsv"),
        tactical.as_bytes(),
    )?;

    let openings = control_openings()?;
    write_new(
        &output_directory.join("s2-3-control-openings.tsv"),
        openings.as_bytes(),
    )?;
    let suite = OpeningSuite::from_text(&openings)?;

    let baseline_identity = identity(
        0x5332_3342_4153_4531,
        source_commit,
        build_identity.clone(),
        "s2_3_baseline controls --role baseline",
        &policy,
        &weights,
    )?;
    let candidate_identity = identity(
        0x5332_3343_414e_4431,
        source_commit,
        build_identity.clone(),
        "s2_3_baseline controls --role candidate",
        &policy,
        &weights,
    )?;
    let baseline = EngineVariantRuntime::new(&baseline_identity, &policy, &weights)?;
    let candidate = EngineVariantRuntime::new(&candidate_identity, &policy, &weights)?;

    let controls = [
        (
            "smoke",
            EngineVariantValidationTier::Smoke,
            1_u32,
            0x5332_3353_4d4f_4b45_u64,
            64_u64,
            6_u32,
        ),
        (
            "development",
            EngineVariantValidationTier::Development,
            8_u32,
            0x5332_3344_4556_3031_u64,
            64_u64,
            6_u32,
        ),
        (
            "production",
            EngineVariantValidationTier::Production,
            200_u32,
            0x5332_3350_524f_4431_u64,
            1_u64,
            4_u32,
        ),
    ];
    let mut summary = String::from("S2_3_CONTROL_SUMMARY\t1\n");
    for (name, tier, pair_count, seed, nodes, maximum_plies) in controls {
        let config = EngineVariantValidationConfig::new(
            tier,
            pair_count,
            seed,
            EngineVariantResourceProtocol::FixedNodes(nodes),
            TT_MEBIBYTES,
        )?
        .with_maximum_plies(maximum_plies)?
        .with_maximum_unfinished_per_mille(1_000)?
        .with_claimable_draw_policy(ClaimableDrawPolicy::Continue);
        let report = run_engine_variant_validation(config, &suite, baseline, candidate)?;
        let serialized = report.serialize()?;
        validate_symmetric_control(&serialized, pair_count)?;
        let destination = output_directory.join(format!("s2-3-{name}-control.report"));
        let temporary = output_directory.join(format!(".s2-3-{name}-control.tmp"));
        write_engine_variant_validation_report_atomic(&destination, &temporary, &report)?;
        let fields = report_fields(&serialized)?;
        writeln!(
            summary,
            "{name}\tpairs={pair_count}\tgames={}\tdecision={}\tmean_bits={}\tse_bits={}\tlower_bits={}\tactivated={}\tchecksum={}",
            pair_count * 2,
            required(&fields, "decision")?,
            required(&fields, "mean_pair_score_bits")?,
            required(&fields, "pair_score_standard_error_bits")?,
            required(&fields, "lower_confidence_bound_bits")?,
            required(&fields, "activated")?,
            required(&fields, "checksum")?,
        )?;
    }
    write_new(
        &output_directory.join("s2-3-control-summary.tsv"),
        summary.as_bytes(),
    )?;

    let manifest = format!(
        "S2_3_BASELINE_MANIFEST\t{REPORT_SCHEMA}\nsource_sha\t{source_text}\nbuild_identity\t{build_identity}\npolicy_identifier\t{:016x}\npolicy_checksum\t{:016x}\nweight_identifier\t{:016x}\nweight_checksum\t{:016x}\ncorpus_checksum\t{:016x}\nopening_checksum\t{:016x}\nactivated\tfalse\n",
        policy.identifier,
        policy.checksum,
        weights.identifier,
        weights.checksum,
        hash_bytes(FNV_OFFSET, CORPUS.as_bytes()),
        hash_bytes(FNV_OFFSET, openings.as_bytes()),
    );
    write_new(
        &output_directory.join("s2-3-baseline-manifest.tsv"),
        manifest.as_bytes(),
    )?;
    Ok(())
}

fn parse_source_commit(value: &str) -> Result<[u8; 20], Box<dyn Error>> {
    if value.len() != 40 || !value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err("S2_3_SOURCE_SHA must be exactly 40 hexadecimal characters".into());
    }
    let mut result = [0_u8; 20];
    for (index, slot) in result.iter_mut().enumerate() {
        *slot = u8::from_str_radix(&value[index * 2..index * 2 + 2], 16)?;
    }
    if result.iter().all(|byte| *byte == 0) {
        return Err("S2_3_SOURCE_SHA must not be all zeroes".into());
    }
    Ok(result)
}

fn identity(
    identifier: u64,
    source_commit: [u8; 20],
    build_identity: String,
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
            build_identity,
            exact_invocation: exact_invocation.to_owned(),
        },
        policy,
        weights,
    )?)
}

fn run_tactical_corpus(
    policy: &SearchPolicySet,
    weights: &EvaluationWeightSet,
    source_sha: &str,
    build_identity: &str,
) -> Result<String, Box<dyn Error>> {
    let cases = parse_corpus(CORPUS)?;
    let mut categories = BTreeSet::new();
    let mut report = format!(
        "S2_3_TACTICAL_BASELINE\t{REPORT_SCHEMA}\nsource_sha\t{source_sha}\nbuild_identity\t{build_identity}\ncorpus_schema\t{CORPUS_SCHEMA}\ncorpus_checksum\t{:016x}\npolicy_checksum\t{:016x}\nweight_checksum\t{:016x}\n",
        hash_bytes(FNV_OFFSET, CORPUS.as_bytes()),
        policy.checksum,
        weights.checksum,
    );
    let mut aggregate_checksum = FNV_OFFSET;
    for case in &cases {
        categories.insert(case.category.as_str());
        let (mut position, mut history) = if case.expectation == "repetition_cycle" {
            repetition_root()?
        } else {
            let position = Position::from_fen(&case.fen)?;
            let history = SearchHistory::from_position(&position);
            (position, history)
        };
        let position_snapshot = position.clone();
        let history_snapshot = history.clone();
        let mut table = TranspositionTable::new(TT_MEBIBYTES)?;
        let result =
            iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights(
                &mut position,
                &mut history,
                SearchLimits::new().with_depth(case.depth),
                &mut table,
                policy,
                &weights.weights,
            )?;
        if position != position_snapshot || history != history_snapshot {
            return Err(format!("tactical case {} changed root state", case.identifier).into());
        }
        position.validate_invariants()?;
        if result.search_diagnostics().overflowed()
            || !result.search_diagnostics().reserved_counters_are_zero()
        {
            return Err(format!(
                "tactical case {} has overflowed or nonzero reserved diagnostics",
                case.identifier
            )
            .into());
        }
        replay_pv(&position_snapshot, result.principal_variation())?;
        validate_expectation(case, result.best_move(), result.score())?;
        let best = result
            .best_move()
            .map_or_else(|| "-".to_owned(), |current| current.to_uci());
        let score = result
            .score()
            .map_or_else(|| "-".to_owned(), |value| value.to_string());
        let diagnostics = result.search_diagnostics();
        writeln!(
            report,
            "case\t{}\tcategory={}\tdepth={}\tbest={}\tscore={}\tnodes={}\tqnodes={}\tselective_depth={}\tbeta_cutoffs={}\tfirst_move_cutoffs={}\tq_beta_cutoffs={}\tq_first_move_cutoffs={}\tq_stand_pat_cutoffs={}\tdiagnostics_checksum={:016x}\tstatus=passed",
            case.identifier,
            case.category,
            case.depth,
            best,
            score,
            result.nodes(),
            result.qnodes(),
            result.selective_depth(),
            diagnostics.beta_cutoffs(),
            diagnostics.first_move_beta_cutoffs(),
            diagnostics.quiescence_beta_cutoffs(),
            diagnostics.quiescence_first_move_beta_cutoffs(),
            diagnostics.quiescence_stand_pat_cutoffs(),
            diagnostics.semantic_checksum(),
        )?;
        aggregate_checksum = hash_bytes(aggregate_checksum, case.identifier.as_bytes());
        aggregate_checksum = hash_bytes(
            aggregate_checksum,
            &diagnostics.semantic_checksum().to_le_bytes(),
        );
        aggregate_checksum = hash_bytes(aggregate_checksum, best.as_bytes());
        aggregate_checksum = hash_bytes(aggregate_checksum, score.as_bytes());
    }
    let required = REQUIRED_CATEGORIES.into_iter().collect::<BTreeSet<_>>();
    if categories != required {
        return Err(format!(
            "tactical corpus categories differ: expected {required:?}, found {categories:?}"
        )
        .into());
    }
    writeln!(report, "case_count\t{}", cases.len())?;
    writeln!(report, "aggregate_checksum\t{aggregate_checksum:016x}")?;
    writeln!(report, "activated\tfalse")?;
    Ok(report)
}

fn parse_corpus(text: &str) -> Result<Vec<CorpusCase>, Box<dyn Error>> {
    let mut lines = text.lines();
    if lines.next() != Some("CHESS_SEARCH_BASELINE\t1") {
        return Err("invalid S2-3 tactical corpus header".into());
    }
    let mut identifiers = BTreeSet::new();
    let mut result = Vec::new();
    for (index, line) in lines.enumerate() {
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let fields = line.split('\t').collect::<Vec<_>>();
        if fields.len() != 6 {
            return Err(format!("corpus row {} must contain six fields", index + 2).into());
        }
        if fields.iter().any(|field| field.is_empty()) {
            return Err(format!("corpus row {} contains an empty field", index + 2).into());
        }
        if !identifiers.insert(fields[0].to_owned()) {
            return Err(format!("duplicate corpus identifier {:?}", fields[0]).into());
        }
        let depth = fields[3].parse::<u16>()?;
        if depth == 0 {
            return Err(format!("corpus row {} has zero depth", index + 2).into());
        }
        if !matches!(
            fields[4],
            "best_set" | "terminal_zero" | "repetition_cycle" | "legal_pv"
        ) {
            return Err(format!("unsupported corpus expectation {:?}", fields[4]).into());
        }
        result.push(CorpusCase {
            identifier: fields[0].to_owned(),
            category: fields[1].to_owned(),
            fen: fields[2].to_owned(),
            depth,
            expectation: fields[4].to_owned(),
            expected: fields[5].to_owned(),
        });
    }
    if result.is_empty() {
        return Err("tactical corpus contains no cases".into());
    }
    Ok(result)
}

fn validate_expectation(
    case: &CorpusCase,
    best_move: Option<Move>,
    score: Option<Score>,
) -> Result<(), Box<dyn Error>> {
    match case.expectation.as_str() {
        "best_set" => {
            let best = best_move
                .ok_or_else(|| format!("case {} produced no best move", case.identifier))?
                .to_uci();
            if !case.expected.split(',').any(|expected| expected == best) {
                return Err(format!(
                    "case {} expected one of {}, found {best}",
                    case.identifier, case.expected
                )
                .into());
            }
        }
        "terminal_zero" | "repetition_cycle" => {
            if best_move.is_some() || score != Some(Score::ZERO) {
                return Err(format!(
                    "case {} expected terminal/draw zero with no move",
                    case.identifier
                )
                .into());
            }
        }
        "legal_pv" => {
            if best_move.is_none() || score.is_none() {
                return Err(
                    format!("case {} produced no exact search result", case.identifier).into(),
                );
            }
        }
        _ => return Err("unreachable tactical expectation".into()),
    }
    Ok(())
}

fn replay_pv(
    root: &Position,
    principal_variation: Option<&chess_search::PrincipalVariation>,
) -> Result<(), Box<dyn Error>> {
    let Some(principal_variation) = principal_variation else {
        return Ok(());
    };
    let mut game = Game::new(root.clone());
    for current in principal_variation.moves() {
        let legal = game.legal_moves()?;
        if !legal.iter().any(|candidate| candidate == *current) {
            return Err(format!(
                "principal variation contains illegal move {}",
                current.to_uci()
            )
            .into());
        }
        game.make_move(*current)?;
    }
    Ok(())
}

fn repetition_root() -> Result<(Position, SearchHistory), Box<dyn Error>> {
    let mut game = Game::new(Position::starting());
    for _ in 0..2 {
        for value in ["g1f3", "g8f6", "f3g1", "f6g8"] {
            make_uci(&mut game, value)?;
        }
    }
    let position = game.position().clone();
    let history = game.search_history();
    Ok((position, history))
}

fn make_uci(game: &mut Game, value: &str) -> Result<(), Box<dyn Error>> {
    let syntax = value.parse::<UciMove>()?;
    let legal = game.legal_moves()?;
    let current = legal
        .iter()
        .find(|candidate| syntax.matches(*candidate))
        .ok_or_else(|| format!("move {value} is not legal"))?;
    game.make_move(current)?;
    Ok(())
}

fn control_openings() -> Result<String, Box<dyn Error>> {
    let mut root = Position::starting();
    let mut white_moves = root.legal_moves()?.iter().collect::<Vec<_>>();
    white_moves.sort_by_key(|current| current.to_uci());
    let mut output = String::from("CHESS_SELF_PLAY_OPENINGS\t1\n");
    let mut index = 0_usize;
    for white in white_moves {
        let mut game = Game::new(root.clone());
        game.make_move(white)?;
        let mut black_moves = game.legal_moves()?.iter().collect::<Vec<_>>();
        black_moves.sort_by_key(|current| current.to_uci());
        for black in black_moves.into_iter().take(10) {
            writeln!(
                output,
                "control-{index:03}\t{STARTING_FEN}\t{} {}",
                white.to_uci(),
                black.to_uci()
            )?;
            index += 1;
        }
    }
    if index != 200 {
        return Err(format!("expected 200 deterministic control openings, found {index}").into());
    }
    Ok(output)
}

fn validate_symmetric_control(text: &str, pair_count: u32) -> Result<(), Box<dyn Error>> {
    let fields = report_fields(text)?;
    let expected_games = pair_count.checked_mul(2).ok_or("game count overflow")?;
    if required(&fields, "decision")? != "rejected_strength"
        || required(&fields, "activated")? != "false"
        || required(&fields, "pair_count")? != pair_count.to_string()
        || required(&fields, "game_count")? != expected_games.to_string()
        || required(&fields, "candidate_wins")? != "0"
        || required(&fields, "candidate_losses")? != "0"
        || required(&fields, "draws")? != "0"
        || required(&fields, "unfinished")? != expected_games.to_string()
        || required(&fields, "illegal_moves")? != "0"
        || required(&fields, "crashes")? != "0"
        || required(&fields, "time_forfeits")? != "0"
        || required(&fields, "infrastructure_failures")? != "0"
        || required(&fields, "mean_pair_score_bits")? != format!("{:016x}", 0.5_f64.to_bits())
        || required(&fields, "pair_score_standard_error_bits")?
            != format!("{:016x}", 0.0_f64.to_bits())
        || required(&fields, "lower_confidence_bound_bits")?
            != format!("{:016x}", 0.5_f64.to_bits())
    {
        return Err("identical-policy control report is not exactly symmetric and rejected".into());
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

fn hash_bytes(mut hash: u64, bytes: &[u8]) -> u64 {
    for byte in bytes {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    hash
}

#[cfg(test)]
mod tests {
    use super::{control_openings, parse_corpus, parse_source_commit, CORPUS, REQUIRED_CATEGORIES};
    use std::collections::BTreeSet;

    #[test]
    fn corpus_is_complete_unique_and_versioned() {
        let cases = parse_corpus(CORPUS).expect("committed corpus validates");
        assert_eq!(cases.len(), REQUIRED_CATEGORIES.len());
        assert_eq!(
            cases
                .iter()
                .map(|case| case.category.as_str())
                .collect::<BTreeSet<_>>(),
            REQUIRED_CATEGORIES.into_iter().collect::<BTreeSet<_>>()
        );
    }

    #[test]
    fn control_openings_are_exactly_two_hundred_and_parse() {
        let text = control_openings().expect("control openings generate");
        assert_eq!(text.lines().skip(1).count(), 200);
        chess_tools::self_play::OpeningSuite::from_text(&text)
            .expect("generated control openings parse strictly");
    }

    #[test]
    fn source_commit_is_exact_and_nonzero() {
        assert!(parse_source_commit("1111111111111111111111111111111111111111").is_ok());
        assert!(parse_source_commit("0000000000000000000000000000000000000000").is_err());
        assert!(parse_source_commit("abc").is_err());
    }
}
