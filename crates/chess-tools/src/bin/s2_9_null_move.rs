use std::{
    collections::BTreeSet,
    env,
    error::Error,
    fmt::Write as _,
    fs,
    path::{Path, PathBuf},
};

use chess_core::{Game, Move, Position, SearchHistory, UciMove};
use chess_search::{
    iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights,
    EvaluationWeightSet, Score, SearchDiagnostics, SearchLimits, SearchPolicySet,
    TranspositionTable,
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

const CORPUS: &str = include_str!("../../../../fixtures/s2_9_null_move_validation_v1.tsv");
const REPORT_SCHEMA: u16 = 1;
const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;
const TT_MEBIBYTES: usize = 1;
const FIXED_NODE_PAIRS: u32 = 8;
const FIXED_NODE_LIMIT: u64 = 2_000;
const CLOCK_PAIRS: u32 = 8;
const CLOCK_MILLISECONDS: u64 = 10;
const MAXIMUM_MATCH_PLIES: u32 = 48;

#[derive(Clone, Debug, Eq, PartialEq)]
struct CorpusCase {
    identifier: String,
    category: String,
    fen: String,
    depth: u16,
    mode: String,
}

fn main() {
    if let Err(error) = run() {
        eprintln!("S2-9 null-move evidence failed: {error}");
        std::process::exit(1);
    }
}

fn run() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let mode = arguments
        .next()
        .ok_or("usage: s2_9_null_move deterministic OUTPUT_DIR | clock OUTPUT_DIR")?;
    let output = PathBuf::from(arguments.next().ok_or("missing output directory")?);
    if arguments.next().is_some() {
        return Err("evidence mode accepts exactly one output directory".into());
    }
    match mode.to_str() {
        Some("deterministic") => run_deterministic(&output),
        Some("clock") => run_clock(&output),
        _ => Err("usage: s2_9_null_move deterministic OUTPUT_DIR | clock OUTPUT_DIR".into()),
    }
}

fn run_deterministic(output: &Path) -> Result<(), Box<dyn Error>> {
    create_output_directory(output)?;
    let source_text = required_environment("S2_9_SOURCE_SHA")?;
    let source_commit = parse_source_commit(&source_text)?;
    let build_identity = required_environment("S2_9_BUILD_IDENTITY")?;
    let baseline_policy = SearchPolicySet::baseline();
    let candidate_policy = SearchPolicySet::null_move_pruning_candidate();
    let weights = EvaluationWeightSet::baseline();
    baseline_policy.validate()?;
    candidate_policy.validate()?;
    weights.validate()?;
    if baseline_policy.policy.null_move_pruning_enabled()
        || !candidate_policy.policy.null_move_pruning_enabled()
    {
        return Err("S2-9 policy activation boundary is inverted".into());
    }

    let parity = run_parity_corpus(&baseline_policy, &candidate_policy, &weights)?;
    write_new(&output.join("s2-9-parity.tsv"), parity.as_bytes())?;

    let openings_text = control_openings()?;
    write_new(
        &output.join("s2-9-development-openings.tsv"),
        openings_text.as_bytes(),
    )?;
    let openings = OpeningSuite::from_text(&openings_text)?;
    let report = run_development_match(
        source_commit,
        &build_identity,
        &openings,
        (&baseline_policy, &candidate_policy),
        &weights,
        EngineVariantResourceProtocol::FixedNodes(FIXED_NODE_LIMIT),
        "fixed-nodes",
    )?;
    let destination = output.join("s2-9-fixed-node-development.report");
    let temporary = output.join(".s2-9-fixed-node-development.tmp");
    write_engine_variant_validation_report_atomic(&destination, &temporary, &report)?;

    let manifest = format!(
        "S2_9_DETERMINISTIC_MANIFEST\t{REPORT_SCHEMA}\nsource_sha\t{source_text}\nbuild_identity\t{build_identity}\nbaseline_policy_identifier\t{:016x}\nbaseline_policy_checksum\t{:016x}\ncandidate_policy_identifier\t{:016x}\ncandidate_policy_checksum\t{:016x}\nweight_identifier\t{:016x}\nweight_checksum\t{:016x}\nfixed_node_pairs\t{FIXED_NODE_PAIRS}\nfixed_node_limit\t{FIXED_NODE_LIMIT}\nfixed_node_decision\t{}\nfixed_node_wins\t{}\nfixed_node_draws\t{}\nfixed_node_losses\t{}\nfixed_node_unfinished\t{}\nfixed_node_mean_bits\t{:016x}\nfixed_node_se_bits\t{:016x}\nfixed_node_lower_bits\t{:016x}\nfixed_node_checksum\t{:016x}\nactivated\tfalse\n",
        baseline_policy.identifier,
        baseline_policy.checksum,
        candidate_policy.identifier,
        candidate_policy.checksum,
        weights.identifier,
        weights.checksum,
        report.decision,
        report.candidate_wins,
        report.draws,
        report.candidate_losses,
        report.unfinished,
        report.mean_pair_score.to_bits(),
        report.pair_score_standard_error.to_bits(),
        report.lower_confidence_bound.to_bits(),
        report.checksum,
    );
    write_new(
        &output.join("s2-9-deterministic-manifest.tsv"),
        manifest.as_bytes(),
    )?;
    Ok(())
}

fn run_clock(output: &Path) -> Result<(), Box<dyn Error>> {
    create_output_directory(output)?;
    let source_text = required_environment("S2_9_SOURCE_SHA")?;
    let source_commit = parse_source_commit(&source_text)?;
    let build_identity = required_environment("S2_9_BUILD_IDENTITY")?;
    let baseline_policy = SearchPolicySet::baseline();
    let candidate_policy = SearchPolicySet::null_move_pruning_candidate();
    let weights = EvaluationWeightSet::baseline();
    let openings_text = control_openings()?;
    let openings = OpeningSuite::from_text(&openings_text)?;
    let report = run_development_match(
        source_commit,
        &build_identity,
        &openings,
        (&baseline_policy, &candidate_policy),
        &weights,
        EngineVariantResourceProtocol::ClockMilliseconds(CLOCK_MILLISECONDS),
        "clock",
    )?;
    let destination = output.join("s2-9-clock-development.report");
    let temporary = output.join(".s2-9-clock-development.tmp");
    write_engine_variant_validation_report_atomic(&destination, &temporary, &report)?;
    let summary = format!(
        "S2_9_CLOCK_SUMMARY\t{REPORT_SCHEMA}\nsource_sha\t{source_text}\nbuild_identity\t{build_identity}\npairs\t{CLOCK_PAIRS}\nclock_milliseconds\t{CLOCK_MILLISECONDS}\ndecision\t{}\nwins\t{}\ndraws\t{}\nlosses\t{}\nunfinished\t{}\nillegal_moves\t{}\ncrashes\t{}\ntime_forfeits\t{}\ninfrastructure_failures\t{}\nmean_bits\t{:016x}\nse_bits\t{:016x}\nlower_bits\t{:016x}\nchecksum\t{:016x}\nactivated\tfalse\n",
        report.decision,
        report.candidate_wins,
        report.draws,
        report.candidate_losses,
        report.unfinished,
        report.illegal_moves,
        report.crashes,
        report.time_forfeits,
        report.infrastructure_failures,
        report.mean_pair_score.to_bits(),
        report.pair_score_standard_error.to_bits(),
        report.lower_confidence_bound.to_bits(),
        report.checksum,
    );
    write_new(&output.join("s2-9-clock-summary.tsv"), summary.as_bytes())?;
    Ok(())
}

fn run_development_match<'a>(
    source_commit: [u8; 20],
    build_identity: &str,
    openings: &OpeningSuite,
    policies: (&'a SearchPolicySet, &'a SearchPolicySet),
    weights: &'a EvaluationWeightSet,
    protocol: EngineVariantResourceProtocol,
    protocol_name: &str,
) -> Result<chess_tools::engine_variant_validation::EngineVariantValidationReport, Box<dyn Error>> {
    let (baseline_policy, candidate_policy) = policies;
    let baseline_identity = identity(
        0x5332_3942_4153_4531,
        source_commit,
        build_identity,
        &format!("s2_9_null_move {protocol_name} --role baseline"),
        baseline_policy,
        weights,
    )?;
    let candidate_identity = identity(
        0x5332_3943_414e_4431,
        source_commit,
        build_identity,
        &format!("s2_9_null_move {protocol_name} --role candidate"),
        candidate_policy,
        weights,
    )?;
    let baseline = EngineVariantRuntime::new(&baseline_identity, baseline_policy, weights)?;
    let candidate = EngineVariantRuntime::new(&candidate_identity, candidate_policy, weights)?;
    let pairs = match protocol {
        EngineVariantResourceProtocol::FixedNodes(_) => FIXED_NODE_PAIRS,
        EngineVariantResourceProtocol::ClockMilliseconds(_) => CLOCK_PAIRS,
    };
    let config = EngineVariantValidationConfig::new(
        EngineVariantValidationTier::Development,
        pairs,
        0x5332_3944_4556_3031,
        protocol,
        TT_MEBIBYTES,
    )?
    .with_maximum_plies(MAXIMUM_MATCH_PLIES)?
    .with_maximum_unfinished_per_mille(1_000)?
    .with_claimable_draw_policy(ClaimableDrawPolicy::Continue);
    let report = run_engine_variant_validation(config, openings, baseline, candidate)?;
    if !report.correctness.passed()
        || report.illegal_moves != 0
        || report.crashes != 0
        || report.time_forfeits != 0
        || report.infrastructure_failures != 0
        || report.activated()
    {
        return Err(format!(
            "{protocol_name} development match failed correctness/failure/inactivity gates"
        )
        .into());
    }
    Ok(report)
}

fn run_parity_corpus(
    baseline_policy: &SearchPolicySet,
    candidate_policy: &SearchPolicySet,
    weights: &EvaluationWeightSet,
) -> Result<String, Box<dyn Error>> {
    let cases = parse_corpus(CORPUS)?;
    let mut output = format!(
        "S2_9_PARITY\t{REPORT_SCHEMA}\ncorpus_checksum\t{:016x}\nbaseline_policy_checksum\t{:016x}\ncandidate_policy_checksum\t{:016x}\n",
        hash_bytes(FNV_OFFSET, CORPUS.as_bytes()),
        baseline_policy.checksum,
        candidate_policy.checksum,
    );
    let mut aggregate = FNV_OFFSET;
    let mut total_attempts = 0_u64;
    let mut total_disabled = 0_u64;
    let mut total_fail_highs = 0_u64;
    let mut total_verifications = 0_u64;
    let mut total_cutoffs = 0_u64;
    let mut differing_best_moves = 0_u32;
    for case in cases {
        let (root, history) = root_for_case(&case)?;
        let baseline = search_exact(&root, &history, case.depth, baseline_policy, weights)?;
        let candidate = search_exact(&root, &history, case.depth, candidate_policy, weights)?;
        if baseline.score() != candidate.score()
            || baseline.completed_depth() != candidate.completed_depth()
        {
            return Err(format!(
                "case {} changed exact score or completed depth",
                case.identifier
            )
            .into());
        }
        replay_pv(&root, baseline.principal_variation())?;
        replay_pv(&root, candidate.principal_variation())?;
        let baseline_diagnostics = baseline.search_diagnostics();
        let candidate_diagnostics = candidate.search_diagnostics();
        validate_baseline_diagnostics(baseline_diagnostics, &case.identifier)?;
        validate_candidate_diagnostics(candidate_diagnostics, &case.identifier)?;
        for (destination, value) in [
            (
                &mut total_attempts,
                candidate_diagnostics.null_move_attempts(),
            ),
            (
                &mut total_disabled,
                candidate_diagnostics.null_move_disabled_nodes(),
            ),
            (
                &mut total_fail_highs,
                candidate_diagnostics.null_move_speculative_fail_highs(),
            ),
            (
                &mut total_verifications,
                candidate_diagnostics.null_move_verification_searches(),
            ),
            (
                &mut total_cutoffs,
                candidate_diagnostics.null_move_cutoffs(),
            ),
        ] {
            *destination = destination
                .checked_add(value)
                .ok_or("null-move aggregate counter overflow")?;
        }
        let baseline_best = display_move(baseline.best_move());
        let candidate_best = display_move(candidate.best_move());
        let best_relation = if baseline_best == candidate_best {
            "same"
        } else {
            differing_best_moves = differing_best_moves
                .checked_add(1)
                .ok_or("differing best-move count overflow")?;
            "equal_score_tie"
        };
        let score = display_score(candidate.score());
        writeln!(
            output,
            "case\t{}\tcategory={}\tdepth={}\tbaseline_best={}\tcandidate_best={}\tbest_relation={}\tscore={}\tbaseline_nodes={}\tcandidate_nodes={}\tbaseline_qnodes={}\tcandidate_qnodes={}\tnull_attempts={}\tnull_disabled={}\tnull_fail_highs={}\tnull_verifications={}\tnull_cutoffs={}\tbaseline_diagnostics={:016x}\tcandidate_diagnostics={:016x}\tstatus=passed",
            case.identifier,
            case.category,
            case.depth,
            baseline_best,
            candidate_best,
            best_relation,
            score,
            baseline.nodes(),
            candidate.nodes(),
            baseline.qnodes(),
            candidate.qnodes(),
            candidate_diagnostics.null_move_attempts(),
            candidate_diagnostics.null_move_disabled_nodes(),
            candidate_diagnostics.null_move_speculative_fail_highs(),
            candidate_diagnostics.null_move_verification_searches(),
            candidate_diagnostics.null_move_cutoffs(),
            baseline_diagnostics.semantic_checksum(),
            candidate_diagnostics.semantic_checksum(),
        )?;
        for value in [
            case.identifier.as_bytes(),
            case.category.as_bytes(),
            baseline_best.as_bytes(),
            candidate_best.as_bytes(),
            score.as_bytes(),
            best_relation.as_bytes(),
        ] {
            aggregate = hash_bytes(aggregate, value);
        }
        for value in [
            baseline.nodes(),
            candidate.nodes(),
            baseline.qnodes(),
            candidate.qnodes(),
            candidate_diagnostics.null_move_attempts(),
            candidate_diagnostics.null_move_disabled_nodes(),
            candidate_diagnostics.null_move_speculative_fail_highs(),
            candidate_diagnostics.null_move_verification_searches(),
            candidate_diagnostics.null_move_cutoffs(),
            candidate_diagnostics.semantic_checksum(),
        ] {
            aggregate = hash_bytes(aggregate, &value.to_le_bytes());
        }
    }
    if total_attempts == 0 || total_disabled == 0 {
        return Err("deterministic corpus did not exercise null-move policy guards".into());
    }
    if total_fail_highs != total_verifications {
        return Err("null speculative fail-high and verification totals differ".into());
    }
    if total_cutoffs > total_verifications {
        return Err("null cutoff total exceeds verification total".into());
    }
    writeln!(output, "case_count\t{}", parse_corpus(CORPUS)?.len())?;
    writeln!(output, "differing_best_moves\t{differing_best_moves}")?;
    writeln!(output, "total_null_attempts\t{total_attempts}")?;
    writeln!(output, "total_null_disabled\t{total_disabled}")?;
    writeln!(output, "total_null_fail_highs\t{total_fail_highs}")?;
    writeln!(output, "total_null_verifications\t{total_verifications}")?;
    writeln!(output, "total_null_cutoffs\t{total_cutoffs}")?;
    writeln!(output, "aggregate_checksum\t{aggregate:016x}")?;
    writeln!(output, "activated\tfalse")?;
    Ok(output)
}

fn root_for_case(case: &CorpusCase) -> Result<(Position, SearchHistory), Box<dyn Error>> {
    match case.mode.as_str() {
        "normal" => {
            let root = Position::from_fen(&case.fen)?;
            let history = SearchHistory::from_position(&root);
            Ok((root, history))
        }
        "repetition-2" => repetition_root(2),
        "repetition-4" => repetition_root(4),
        other => Err(format!("unknown corpus mode {other}").into()),
    }
}

fn search_exact(
    root: &Position,
    root_history: &SearchHistory,
    depth: u16,
    policy: &SearchPolicySet,
    weights: &EvaluationWeightSet,
) -> Result<chess_search::SearchResult, Box<dyn Error>> {
    let mut position = root.clone();
    let mut history = root_history.clone();
    let mut table = TranspositionTable::new(TT_MEBIBYTES)?;
    let result =
        iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights(
            &mut position,
            &mut history,
            SearchLimits::new().with_depth(depth),
            &mut table,
            policy,
            &weights.weights,
        )?;
    if position != *root || history != *root_history {
        return Err("search changed root position or history".into());
    }
    position.validate_invariants()?;
    if position.zobrist() != position.recomputed_zobrist() {
        return Err("search changed incremental root hash".into());
    }
    if result.search_diagnostics().overflowed() {
        return Err("search diagnostics overflowed".into());
    }
    Ok(result)
}

fn validate_baseline_diagnostics(
    diagnostics: SearchDiagnostics,
    identifier: &str,
) -> Result<(), Box<dyn Error>> {
    if diagnostics.null_move_attempts() != 0
        || diagnostics.null_move_disabled_nodes() != 0
        || diagnostics.null_move_speculative_fail_highs() != 0
        || diagnostics.null_move_verification_searches() != 0
        || diagnostics.null_move_cutoffs() != 0
    {
        return Err(format!("baseline case {identifier} used null move").into());
    }
    Ok(())
}

fn validate_candidate_diagnostics(
    diagnostics: SearchDiagnostics,
    identifier: &str,
) -> Result<(), Box<dyn Error>> {
    if diagnostics.null_move_speculative_fail_highs()
        != diagnostics.null_move_verification_searches()
    {
        return Err(format!("candidate case {identifier} has unverified fail-highs").into());
    }
    if diagnostics.null_move_cutoffs() > diagnostics.null_move_verification_searches() {
        return Err(format!("candidate case {identifier} has excess cutoffs").into());
    }
    Ok(())
}

fn parse_corpus(text: &str) -> Result<Vec<CorpusCase>, Box<dyn Error>> {
    let mut lines = text.lines();
    if lines.next() != Some("S2_9_NULL_MOVE_VALIDATION\t1") {
        return Err("invalid S2-9 validation corpus header".into());
    }
    let mut identifiers = BTreeSet::new();
    let mut cases = Vec::new();
    for (index, line) in lines.enumerate() {
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let fields = line.split('\t').collect::<Vec<_>>();
        if fields.len() != 5 || fields.iter().any(|field| field.is_empty()) {
            return Err(format!("invalid corpus row {}", index + 2).into());
        }
        if !identifiers.insert(fields[0].to_owned()) {
            return Err(format!("duplicate corpus identifier {:?}", fields[0]).into());
        }
        cases.push(CorpusCase {
            identifier: fields[0].to_owned(),
            category: fields[1].to_owned(),
            fen: fields[2].to_owned(),
            depth: fields[3].parse()?,
            mode: fields[4].to_owned(),
        });
    }
    if cases.is_empty() {
        return Err("S2-9 validation corpus is empty".into());
    }
    Ok(cases)
}

fn repetition_root(cycles: usize) -> Result<(Position, SearchHistory), Box<dyn Error>> {
    let mut game = Game::new(Position::starting());
    for _ in 0..cycles {
        for value in ["g1f3", "g8f6", "f3g1", "f6g8"] {
            make_uci(&mut game, value)?;
        }
    }
    Ok((game.position().clone(), game.search_history()))
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

fn control_openings() -> Result<String, Box<dyn Error>> {
    let root = Position::starting();
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
                "s2-9-{index:03}\t{STARTING_FEN}\t{} {}",
                white.to_uci(),
                black.to_uci()
            )?;
            index += 1;
        }
    }
    if index != 200 {
        return Err(format!("expected 200 deterministic openings, found {index}").into());
    }
    Ok(output)
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

fn parse_source_commit(value: &str) -> Result<[u8; 20], Box<dyn Error>> {
    if value.len() != 40 || !value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err("S2_9_SOURCE_SHA must be exactly 40 hexadecimal characters".into());
    }
    let mut result = [0_u8; 20];
    for (index, slot) in result.iter_mut().enumerate() {
        *slot = u8::from_str_radix(&value[index * 2..index * 2 + 2], 16)?;
    }
    if result.iter().all(|byte| *byte == 0) {
        return Err("S2_9_SOURCE_SHA must not be all zeroes".into());
    }
    Ok(result)
}

fn required_environment(name: &str) -> Result<String, Box<dyn Error>> {
    let value = env::var(name).map_err(|_| format!("{name} must be supplied explicitly"))?;
    if value.trim().is_empty() {
        return Err(format!("{name} must not be empty").into());
    }
    Ok(value)
}

fn create_output_directory(path: &Path) -> Result<(), Box<dyn Error>> {
    if path.exists() {
        return Err(format!("output directory already exists: {}", path.display()).into());
    }
    fs::create_dir(path)?;
    Ok(())
}

fn write_new(path: &Path, bytes: &[u8]) -> Result<(), Box<dyn Error>> {
    if path.exists() {
        return Err(format!("refusing to replace evidence: {}", path.display()).into());
    }
    fs::write(path, bytes)?;
    Ok(())
}

fn display_move(current: Option<Move>) -> String {
    current.map_or_else(|| "-".to_owned(), Move::to_uci)
}

fn display_score(score: Option<Score>) -> String {
    score.map_or_else(|| "-".to_owned(), |value| value.to_string())
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
    use super::{control_openings, parse_corpus, parse_source_commit, CORPUS};

    #[test]
    fn validation_corpus_is_versioned_unique_and_complete() {
        let cases = parse_corpus(CORPUS).expect("committed validation corpus validates");
        assert_eq!(cases.len(), 14);
        for category in [
            "zugzwang",
            "stalemate",
            "repetition",
            "fifty-move",
            "seventy-five-move",
            "mate-distance",
            "longest-survival",
            "midgame",
        ] {
            assert!(cases.iter().any(|case| case.category == category));
        }
    }

    #[test]
    fn development_openings_are_complete_and_strictly_parseable() {
        let text = control_openings().expect("development openings generate");
        assert_eq!(text.lines().skip(1).count(), 200);
        chess_tools::self_play::OpeningSuite::from_text(&text).expect("development openings parse");
    }

    #[test]
    fn source_commit_is_exact_and_nonzero() {
        assert!(parse_source_commit("1111111111111111111111111111111111111111").is_ok());
        assert!(parse_source_commit("0000000000000000000000000000000000000000").is_err());
        assert!(parse_source_commit("abc").is_err());
    }
}
