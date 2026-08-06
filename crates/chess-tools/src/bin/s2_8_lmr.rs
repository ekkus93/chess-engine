use std::{
    alloc::{GlobalAlloc, Layout, System},
    collections::BTreeSet,
    env,
    error::Error,
    fmt::Write as _,
    fs,
    hint::black_box,
    path::{Path, PathBuf},
    sync::atomic::{AtomicBool, AtomicU64, Ordering},
    time::Instant,
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

const CORPUS: &str = include_str!("../../../../fixtures/search_baseline_v1.tsv");
const REPORT_SCHEMA: u16 = 1;
const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;
const TT_MEBIBYTES: usize = 1;
const FIXED_NODE_PAIRS: u32 = 8;
const FIXED_NODE_LIMIT: u64 = 2_000;
const CLOCK_PAIRS: u32 = 8;
const CLOCK_MILLISECONDS: u64 = 10;
const MAXIMUM_MATCH_PLIES: u32 = 48;
const BENCHMARK_NODE_LIMIT: u64 = 10_000;
const BENCHMARK_FENS: [&str; 4] = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10",
];

struct CountingAllocator;

static TRACK_ALLOCATIONS: AtomicBool = AtomicBool::new(false);
static ALLOCATION_CALLS: AtomicU64 = AtomicU64::new(0);
static ALLOCATED_BYTES: AtomicU64 = AtomicU64::new(0);

unsafe impl GlobalAlloc for CountingAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        let pointer = unsafe { System.alloc(layout) };
        if TRACK_ALLOCATIONS.load(Ordering::Relaxed) && !pointer.is_null() {
            ALLOCATION_CALLS.fetch_add(1, Ordering::Relaxed);
            ALLOCATED_BYTES.fetch_add(layout.size() as u64, Ordering::Relaxed);
        }
        pointer
    }

    unsafe fn alloc_zeroed(&self, layout: Layout) -> *mut u8 {
        let pointer = unsafe { System.alloc_zeroed(layout) };
        if TRACK_ALLOCATIONS.load(Ordering::Relaxed) && !pointer.is_null() {
            ALLOCATION_CALLS.fetch_add(1, Ordering::Relaxed);
            ALLOCATED_BYTES.fetch_add(layout.size() as u64, Ordering::Relaxed);
        }
        pointer
    }

    unsafe fn dealloc(&self, pointer: *mut u8, layout: Layout) {
        unsafe { System.dealloc(pointer, layout) };
    }

    unsafe fn realloc(&self, pointer: *mut u8, layout: Layout, new_size: usize) -> *mut u8 {
        let replacement = unsafe { System.realloc(pointer, layout, new_size) };
        if TRACK_ALLOCATIONS.load(Ordering::Relaxed) && !replacement.is_null() {
            ALLOCATION_CALLS.fetch_add(1, Ordering::Relaxed);
            ALLOCATED_BYTES.fetch_add(new_size as u64, Ordering::Relaxed);
        }
        replacement
    }
}

#[global_allocator]
static GLOBAL_ALLOCATOR: CountingAllocator = CountingAllocator;

#[derive(Clone, Debug, Eq, PartialEq)]
struct CorpusCase {
    identifier: String,
    fen: String,
    depth: u16,
    repetition_cycle: bool,
}

#[derive(Clone, Copy, Debug, Default)]
struct AllocationSnapshot {
    calls: u64,
    bytes: u64,
}

#[derive(Clone, Copy, Debug, Default)]
struct SearchAggregate {
    nodes: u64,
    qnodes: u64,
    selective_depth: u16,
    beta_cutoffs: u64,
    first_move_cutoffs: u64,
    lmr_reductions: u64,
    lmr_reduced_fail_highs: u64,
    lmr_verification_searches: u64,
    checksum: u64,
}

#[derive(Clone, Debug)]
struct BenchmarkSummary {
    policy: &'static str,
    samples: usize,
    median_nanos: u128,
    minimum_nanos: u128,
    maximum_nanos: u128,
    maximum_allocations: u64,
    maximum_allocated_bytes: u64,
    aggregate: SearchAggregate,
}

fn main() {
    if let Err(error) = run() {
        eprintln!("S2-8 LMR evidence failed: {error}");
        std::process::exit(1);
    }
}

fn run() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let mode = arguments
        .next()
        .ok_or("usage: s2_8_lmr deterministic OUTPUT_DIR | clock OUTPUT_DIR | benchmark SAMPLES")?;
    match mode.to_str() {
        Some("deterministic") => {
            let output = PathBuf::from(
                arguments
                    .next()
                    .ok_or("missing deterministic output directory")?,
            );
            if arguments.next().is_some() {
                return Err("deterministic mode accepts one output directory".into());
            }
            run_deterministic(&output)
        }
        Some("clock") => {
            let output = PathBuf::from(arguments.next().ok_or("missing clock output directory")?);
            if arguments.next().is_some() {
                return Err("clock mode accepts one output directory".into());
            }
            run_clock(&output)
        }
        Some("benchmark") => {
            let samples = arguments
                .next()
                .ok_or("missing benchmark sample count")?
                .to_str()
                .ok_or("benchmark sample count is not UTF-8")?
                .parse::<usize>()?;
            if samples == 0 || arguments.next().is_some() {
                return Err("benchmark mode requires one positive sample count".into());
            }
            run_benchmark(samples)
        }
        _ => Err(
            "usage: s2_8_lmr deterministic OUTPUT_DIR | clock OUTPUT_DIR | benchmark SAMPLES"
                .into(),
        ),
    }
}

fn run_deterministic(output: &Path) -> Result<(), Box<dyn Error>> {
    create_output_directory(output)?;
    let source_text = required_environment("S2_8_SOURCE_SHA")?;
    let source_commit = parse_source_commit(&source_text)?;
    let build_identity = required_environment("S2_8_BUILD_IDENTITY")?;
    let baseline_policy = SearchPolicySet::baseline();
    let candidate_policy = SearchPolicySet::late_move_reductions_candidate();
    let weights = EvaluationWeightSet::baseline();
    baseline_policy.validate()?;
    candidate_policy.validate()?;
    weights.validate()?;
    if baseline_policy.policy.late_move_reductions_enabled()
        || !candidate_policy.policy.late_move_reductions_enabled()
    {
        return Err("S2-8 policy activation boundary is inverted".into());
    }

    let parity = run_parity_corpus(&baseline_policy, &candidate_policy, &weights)?;
    write_new(&output.join("s2-8-parity.tsv"), parity.as_bytes())?;

    let openings_text = control_openings()?;
    write_new(
        &output.join("s2-8-development-openings.tsv"),
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
    let destination = output.join("s2-8-fixed-node-development.report");
    let temporary = output.join(".s2-8-fixed-node-development.tmp");
    write_engine_variant_validation_report_atomic(&destination, &temporary, &report)?;

    let manifest = format!(
        "S2_8_DETERMINISTIC_MANIFEST\t{REPORT_SCHEMA}\nsource_sha\t{source_text}\nbuild_identity\t{build_identity}\nbaseline_policy_identifier\t{:016x}\nbaseline_policy_checksum\t{:016x}\ncandidate_policy_identifier\t{:016x}\ncandidate_policy_checksum\t{:016x}\nweight_identifier\t{:016x}\nweight_checksum\t{:016x}\nfixed_node_pairs\t{FIXED_NODE_PAIRS}\nfixed_node_limit\t{FIXED_NODE_LIMIT}\nfixed_node_decision\t{}\nfixed_node_mean_bits\t{:016x}\nfixed_node_se_bits\t{:016x}\nfixed_node_lower_bits\t{:016x}\nfixed_node_checksum\t{:016x}\nactivated\tfalse\n",
        baseline_policy.identifier,
        baseline_policy.checksum,
        candidate_policy.identifier,
        candidate_policy.checksum,
        weights.identifier,
        weights.checksum,
        report.decision,
        report.mean_pair_score.to_bits(),
        report.pair_score_standard_error.to_bits(),
        report.lower_confidence_bound.to_bits(),
        report.checksum,
    );
    write_new(
        &output.join("s2-8-deterministic-manifest.tsv"),
        manifest.as_bytes(),
    )?;
    Ok(())
}

fn run_clock(output: &Path) -> Result<(), Box<dyn Error>> {
    create_output_directory(output)?;
    let source_text = required_environment("S2_8_SOURCE_SHA")?;
    let source_commit = parse_source_commit(&source_text)?;
    let build_identity = required_environment("S2_8_BUILD_IDENTITY")?;
    let baseline_policy = SearchPolicySet::baseline();
    let candidate_policy = SearchPolicySet::late_move_reductions_candidate();
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
    let destination = output.join("s2-8-clock-development.report");
    let temporary = output.join(".s2-8-clock-development.tmp");
    write_engine_variant_validation_report_atomic(&destination, &temporary, &report)?;
    let summary = format!(
        "S2_8_CLOCK_SUMMARY\t{REPORT_SCHEMA}\nsource_sha\t{source_text}\nbuild_identity\t{build_identity}\npairs\t{CLOCK_PAIRS}\nclock_milliseconds\t{CLOCK_MILLISECONDS}\ndecision\t{}\nwins\t{}\ndraws\t{}\nlosses\t{}\nunfinished\t{}\nillegal_moves\t{}\ncrashes\t{}\ntime_forfeits\t{}\ninfrastructure_failures\t{}\nmean_bits\t{:016x}\nse_bits\t{:016x}\nlower_bits\t{:016x}\nchecksum\t{:016x}\nactivated\tfalse\n",
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
    write_new(&output.join("s2-8-clock-summary.tsv"), summary.as_bytes())?;
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
        0x5332_3842_4153_4531,
        source_commit,
        build_identity,
        &format!("s2_8_lmr {protocol_name} --role baseline"),
        baseline_policy,
        weights,
    )?;
    let candidate_identity = identity(
        0x5332_3843_414e_4431,
        source_commit,
        build_identity,
        &format!("s2_8_lmr {protocol_name} --role candidate"),
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
        0x5332_3844_4556_3031,
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
        "S2_8_PARITY	{REPORT_SCHEMA}
corpus_checksum	{:016x}
baseline_policy_checksum	{:016x}
candidate_policy_checksum	{:016x}
",
        hash_bytes(FNV_OFFSET, CORPUS.as_bytes()),
        baseline_policy.checksum,
        candidate_policy.checksum,
    );
    let mut aggregate = FNV_OFFSET;
    let mut total_zero_window_searches = 0_u64;
    let mut total_reduced_fail_highs = 0_u64;
    let mut total_researches = 0_u64;
    let mut differing_best_moves = 0_u32;
    for case in cases {
        let (root, history) = if case.repetition_cycle {
            repetition_root()?
        } else {
            let root = Position::from_fen(&case.fen)?;
            let history = SearchHistory::from_position(&root);
            (root, history)
        };
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
        total_zero_window_searches = total_zero_window_searches
            .checked_add(candidate_diagnostics.lmr_reductions())
            .ok_or("LMR zero-window total overflow")?;
        total_reduced_fail_highs = total_reduced_fail_highs
            .checked_add(candidate_diagnostics.lmr_reduced_fail_highs())
            .ok_or("LMR reduced fail-high total overflow")?;
        total_researches = total_researches
            .checked_add(candidate_diagnostics.lmr_verification_searches())
            .ok_or("LMR verification total overflow")?;
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
            "case	{}	depth={}	baseline_best={}	candidate_best={}	best_relation={}	score={}	baseline_nodes={}	candidate_nodes={}	baseline_qnodes={}	candidate_qnodes={}	baseline_cutoffs={}	candidate_cutoffs={}	baseline_first_move_cutoffs={}	candidate_first_move_cutoffs={}	lmr_reductions={}	lmr_reduced_fail_highs={}	lmr_verification_searches={}	baseline_diagnostics={:016x}	candidate_diagnostics={:016x}	status=passed",
            case.identifier,
            case.depth,
            baseline_best,
            candidate_best,
            best_relation,
            score,
            baseline.nodes(),
            candidate.nodes(),
            baseline.qnodes(),
            candidate.qnodes(),
            baseline_diagnostics.beta_cutoffs(),
            candidate_diagnostics.beta_cutoffs(),
            baseline_diagnostics.first_move_beta_cutoffs(),
            candidate_diagnostics.first_move_beta_cutoffs(),
            candidate_diagnostics.lmr_reductions(),
            candidate_diagnostics.lmr_reduced_fail_highs(),
            candidate_diagnostics.lmr_verification_searches(),
            baseline_diagnostics.semantic_checksum(),
            candidate_diagnostics.semantic_checksum(),
        )?;
        for value in [
            case.identifier.as_bytes(),
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
            candidate_diagnostics.lmr_reductions(),
            candidate_diagnostics.lmr_reduced_fail_highs(),
            candidate_diagnostics.lmr_verification_searches(),
            candidate_diagnostics.semantic_checksum(),
        ] {
            aggregate = hash_bytes(aggregate, &value.to_le_bytes());
        }
    }
    if total_zero_window_searches == 0 {
        return Err("deterministic parity corpus exercised no LMR zero-window searches".into());
    }
    if total_reduced_fail_highs != total_researches {
        return Err("LMR reduced fail-high and verification totals differ".into());
    }
    if total_researches > total_zero_window_searches {
        return Err("LMR verification total exceeds reduction total".into());
    }
    writeln!(output, "case_count	{}", parse_corpus(CORPUS)?.len())?;
    writeln!(output, "differing_best_moves	{differing_best_moves}")?;
    writeln!(output, "total_lmr_reductions	{total_zero_window_searches}")?;
    writeln!(
        output,
        "total_lmr_reduced_fail_highs	{total_reduced_fail_highs}"
    )?;
    writeln!(output, "total_lmr_verification_searches	{total_researches}")?;
    writeln!(output, "aggregate_checksum	{aggregate:016x}")?;
    writeln!(output, "activated	false")?;
    Ok(output)
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
    if result.search_diagnostics().overflowed() {
        return Err("search diagnostics overflowed".into());
    }
    Ok(result)
}

fn validate_baseline_diagnostics(
    diagnostics: SearchDiagnostics,
    identifier: &str,
) -> Result<(), Box<dyn Error>> {
    if diagnostics.lmr_reductions() != 0
        || diagnostics.lmr_reduced_fail_highs() != 0
        || diagnostics.lmr_verification_searches() != 0
    {
        return Err(format!("baseline case {identifier} used LMR").into());
    }
    Ok(())
}

fn validate_candidate_diagnostics(
    diagnostics: SearchDiagnostics,
    identifier: &str,
) -> Result<(), Box<dyn Error>> {
    if diagnostics.lmr_reduced_fail_highs() != diagnostics.lmr_verification_searches() {
        return Err(
            format!("candidate case {identifier} has unverified reduced fail-highs").into(),
        );
    }
    if diagnostics.lmr_verification_searches() > diagnostics.lmr_reductions() {
        return Err(
            format!("candidate case {identifier} has more verifications than reductions").into(),
        );
    }
    Ok(())
}

fn run_benchmark(samples: usize) -> Result<(), Box<dyn Error>> {
    let baseline_policy = SearchPolicySet::baseline();
    let candidate_policy = SearchPolicySet::late_move_reductions_candidate();
    let weights = EvaluationWeightSet::baseline();
    let baseline = benchmark_policy("baseline", samples, &baseline_policy, &weights)?;
    let candidate = benchmark_policy("candidate", samples, &candidate_policy, &weights)?;
    print_benchmark(&baseline);
    print_benchmark(&candidate);
    let ratio = candidate.median_nanos as f64 / baseline.median_nanos as f64;
    let allocation_delta =
        i128::from(candidate.maximum_allocations) - i128::from(baseline.maximum_allocations);
    let allocated_byte_delta = i128::from(candidate.maximum_allocated_bytes)
        - i128::from(baseline.maximum_allocated_bytes);
    println!(
        "comparison	median_time_ratio={ratio:.6}	baseline_nodes={}	candidate_nodes={}	baseline_qnodes={}	candidate_qnodes={}\tbaseline_selective_depth={}\tcandidate_selective_depth={}	baseline_cutoffs={}	candidate_cutoffs={}	baseline_first_move_cutoffs={}	candidate_first_move_cutoffs={}	baseline_maximum_allocations={}	candidate_maximum_allocations={}	allocation_delta={}	baseline_maximum_allocated_bytes={}	candidate_maximum_allocated_bytes={}	allocated_byte_delta={}	candidate_lmr_reductions={}	candidate_lmr_reduced_fail_highs={}	candidate_lmr_verification_searches={}	activated=false",
        baseline.aggregate.nodes,
        candidate.aggregate.nodes,
        baseline.aggregate.qnodes,
        candidate.aggregate.qnodes,
        baseline.aggregate.selective_depth,
        candidate.aggregate.selective_depth,
        baseline.aggregate.beta_cutoffs,
        candidate.aggregate.beta_cutoffs,
        baseline.aggregate.first_move_cutoffs,
        candidate.aggregate.first_move_cutoffs,
        baseline.maximum_allocations,
        candidate.maximum_allocations,
        allocation_delta,
        baseline.maximum_allocated_bytes,
        candidate.maximum_allocated_bytes,
        allocated_byte_delta,
        candidate.aggregate.lmr_reductions,
        candidate.aggregate.lmr_reduced_fail_highs,
        candidate.aggregate.lmr_verification_searches,
    );
    if baseline.aggregate.lmr_reductions != 0
        || baseline.aggregate.lmr_reduced_fail_highs != 0
        || baseline.aggregate.lmr_verification_searches != 0
    {
        return Err("baseline benchmark unexpectedly exercised LMR".into());
    }
    if candidate.aggregate.lmr_reductions == 0
        || candidate.aggregate.lmr_reduced_fail_highs
            != candidate.aggregate.lmr_verification_searches
        || candidate.aggregate.lmr_verification_searches > candidate.aggregate.lmr_reductions
    {
        return Err("candidate benchmark did not exercise valid verified LMR accounting".into());
    }
    Ok(())
}

fn benchmark_policy(
    policy_name: &'static str,
    samples: usize,
    policy: &SearchPolicySet,
    weights: &EvaluationWeightSet,
) -> Result<BenchmarkSummary, Box<dyn Error>> {
    let mut elapsed = Vec::with_capacity(samples);
    let mut allocations = Vec::with_capacity(samples);
    let mut final_aggregate = SearchAggregate::default();
    for sample in 0..samples {
        let roots = BENCHMARK_FENS
            .iter()
            .map(|fen| Position::from_fen(fen))
            .collect::<Result<Vec<_>, _>>()?;
        let histories = roots
            .iter()
            .map(SearchHistory::from_position)
            .collect::<Vec<_>>();
        let mut tables = (0..roots.len())
            .map(|_| TranspositionTable::new(TT_MEBIBYTES))
            .collect::<Result<Vec<_>, _>>()?;
        let mut positions = roots.clone();
        let mut working_histories = histories.clone();
        start_allocation_tracking();
        let started = Instant::now();
        let mut aggregate = SearchAggregate::default();
        for index in 0..positions.len() {
            let result =
                iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights(
                    &mut positions[index],
                    &mut working_histories[index],
                    SearchLimits::new().with_nodes(BENCHMARK_NODE_LIMIT),
                    &mut tables[index],
                    policy,
                    &weights.weights,
                );
            let result = match result {
                Ok(result) => result,
                Err(error) => {
                    let snapshot = stop_allocation_tracking();
                    return Err(format!(
                        "benchmark search failed after {} allocations and {} bytes: {error}",
                        snapshot.calls, snapshot.bytes
                    )
                    .into());
                }
            };
            if positions[index] != roots[index] || working_histories[index] != histories[index] {
                let snapshot = stop_allocation_tracking();
                return Err(format!(
                    "benchmark search changed root after {} allocations and {} bytes",
                    snapshot.calls, snapshot.bytes
                )
                .into());
            }
            aggregate_search(&mut aggregate, &result)?;
            black_box(result.score());
        }
        let elapsed_nanos = started.elapsed().as_nanos();
        let snapshot = stop_allocation_tracking();
        println!(
            "sample	policy={policy_name}	index={sample}	elapsed_nanos={elapsed_nanos}	allocations={}	allocated_bytes={}	nodes={}	qnodes={}\tselective_depth={}	cutoffs={}	first_move_cutoffs={}	lmr_reductions={}	lmr_reduced_fail_highs={}	lmr_verification_searches={}	checksum={:016x}",
            snapshot.calls,
            snapshot.bytes,
            aggregate.nodes,
            aggregate.qnodes,
            aggregate.selective_depth,
            aggregate.beta_cutoffs,
            aggregate.first_move_cutoffs,
            aggregate.lmr_reductions,
            aggregate.lmr_reduced_fail_highs,
            aggregate.lmr_verification_searches,
            aggregate.checksum,
        );
        elapsed.push(elapsed_nanos);
        allocations.push(snapshot);
        final_aggregate = aggregate;
    }
    elapsed.sort_unstable();
    Ok(BenchmarkSummary {
        policy: policy_name,
        samples,
        median_nanos: elapsed[elapsed.len() / 2],
        minimum_nanos: *elapsed.first().ok_or("benchmark has no elapsed samples")?,
        maximum_nanos: *elapsed.last().ok_or("benchmark has no elapsed samples")?,
        maximum_allocations: allocations
            .iter()
            .map(|value| value.calls)
            .max()
            .unwrap_or(0),
        maximum_allocated_bytes: allocations
            .iter()
            .map(|value| value.bytes)
            .max()
            .unwrap_or(0),
        aggregate: final_aggregate,
    })
}

fn aggregate_search(
    aggregate: &mut SearchAggregate,
    result: &chess_search::SearchResult,
) -> Result<(), Box<dyn Error>> {
    let diagnostics = result.search_diagnostics();
    for (destination, value) in [
        (&mut aggregate.nodes, result.nodes()),
        (&mut aggregate.qnodes, result.qnodes()),
        (&mut aggregate.beta_cutoffs, diagnostics.beta_cutoffs()),
        (
            &mut aggregate.first_move_cutoffs,
            diagnostics.first_move_beta_cutoffs(),
        ),
        (&mut aggregate.lmr_reductions, diagnostics.lmr_reductions()),
        (
            &mut aggregate.lmr_reduced_fail_highs,
            diagnostics.lmr_reduced_fail_highs(),
        ),
        (
            &mut aggregate.lmr_verification_searches,
            diagnostics.lmr_verification_searches(),
        ),
    ] {
        *destination = destination
            .checked_add(value)
            .ok_or("benchmark aggregate counter overflow")?;
    }
    aggregate.selective_depth = aggregate.selective_depth.max(result.selective_depth());
    aggregate.checksum = aggregate
        .checksum
        .rotate_left(7)
        .wrapping_add(result.nodes())
        .wrapping_add(result.qnodes().rotate_left(13))
        .wrapping_add(diagnostics.semantic_checksum().rotate_left(29));
    Ok(())
}

fn print_benchmark(summary: &BenchmarkSummary) {
    println!(
        "summary\tpolicy={}\tsamples={}\tmedian_nanos={}\tminimum_nanos={}\tmaximum_nanos={}\tselective_depth={}\tmaximum_allocations={}\tmaximum_allocated_bytes={}\tchecksum={:016x}",
        summary.policy,
        summary.samples,
        summary.median_nanos,
        summary.minimum_nanos,
        summary.maximum_nanos,
        summary.aggregate.selective_depth,
        summary.maximum_allocations,
        summary.maximum_allocated_bytes,
        summary.aggregate.checksum,
    );
}

fn start_allocation_tracking() {
    ALLOCATION_CALLS.store(0, Ordering::Relaxed);
    ALLOCATED_BYTES.store(0, Ordering::Relaxed);
    TRACK_ALLOCATIONS.store(true, Ordering::SeqCst);
}

fn stop_allocation_tracking() -> AllocationSnapshot {
    TRACK_ALLOCATIONS.store(false, Ordering::SeqCst);
    AllocationSnapshot {
        calls: ALLOCATION_CALLS.load(Ordering::Relaxed),
        bytes: ALLOCATED_BYTES.load(Ordering::Relaxed),
    }
}

fn parse_corpus(text: &str) -> Result<Vec<CorpusCase>, Box<dyn Error>> {
    let mut lines = text.lines();
    if lines.next() != Some("CHESS_SEARCH_BASELINE\t1") {
        return Err("invalid S2-8 parity corpus header".into());
    }
    let mut identifiers = BTreeSet::new();
    let mut cases = Vec::new();
    for (index, line) in lines.enumerate() {
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let fields = line.split('\t').collect::<Vec<_>>();
        if fields.len() != 6 || fields.iter().any(|field| field.is_empty()) {
            return Err(format!("invalid corpus row {}", index + 2).into());
        }
        if !identifiers.insert(fields[0].to_owned()) {
            return Err(format!("duplicate corpus identifier {:?}", fields[0]).into());
        }
        cases.push(CorpusCase {
            identifier: fields[0].to_owned(),
            fen: fields[2].to_owned(),
            depth: fields[3].parse()?,
            repetition_cycle: fields[4] == "repetition_cycle",
        });
    }
    if cases.is_empty() {
        return Err("S2-8 parity corpus is empty".into());
    }
    Ok(cases)
}

fn repetition_root() -> Result<(Position, SearchHistory), Box<dyn Error>> {
    let mut game = Game::new(Position::starting());
    for _ in 0..2 {
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
                "s2-8-{index:03}\t{STARTING_FEN}\t{} {}",
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
        return Err("S2_8_SOURCE_SHA must be exactly 40 hexadecimal characters".into());
    }
    let mut result = [0_u8; 20];
    for (index, slot) in result.iter_mut().enumerate() {
        *slot = u8::from_str_radix(&value[index * 2..index * 2 + 2], 16)?;
    }
    if result.iter().all(|byte| *byte == 0) {
        return Err("S2_8_SOURCE_SHA must not be all zeroes".into());
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
    fn parity_corpus_is_versioned_unique_and_nonempty() {
        let cases = parse_corpus(CORPUS).expect("committed parity corpus validates");
        assert!(!cases.is_empty());
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
