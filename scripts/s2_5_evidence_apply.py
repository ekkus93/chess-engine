#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write_new(path: str, content: str) -> None:
    target = ROOT / path
    if target.exists():
        raise SystemExit(f"refusing to replace existing path: {path}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    content = target.read_text()
    count = content.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement, found {count}: {old[:140]!r}")
    target.write_text(content.replace(old, new, 1))


write_new(
    "crates/chess-tools/src/bin/s2_5_see_ordering.rs",
    r'''use std::{
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
    beta_cutoffs: u64,
    first_move_cutoffs: u64,
    see_calls: u64,
    see_winning: u64,
    see_equal: u64,
    see_losing: u64,
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
        eprintln!("S2-5 SEE ordering evidence failed: {error}");
        std::process::exit(1);
    }
}

fn run() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let mode = arguments
        .next()
        .ok_or("usage: s2_5_see_ordering deterministic OUTPUT_DIR | clock OUTPUT_DIR | benchmark SAMPLES")?;
    match mode.to_str() {
        Some("deterministic") => {
            let output = PathBuf::from(arguments.next().ok_or("missing deterministic output directory")?);
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
        _ => Err("usage: s2_5_see_ordering deterministic OUTPUT_DIR | clock OUTPUT_DIR | benchmark SAMPLES".into()),
    }
}

fn run_deterministic(output: &Path) -> Result<(), Box<dyn Error>> {
    create_output_directory(output)?;
    let source_text = required_environment("S2_5_SOURCE_SHA")?;
    let source_commit = parse_source_commit(&source_text)?;
    let build_identity = required_environment("S2_5_BUILD_IDENTITY")?;
    let baseline_policy = SearchPolicySet::baseline();
    let candidate_policy = SearchPolicySet::see_capture_ordering_candidate();
    let weights = EvaluationWeightSet::baseline();
    baseline_policy.validate()?;
    candidate_policy.validate()?;
    weights.validate()?;
    if baseline_policy.policy.see_capture_ordering_enabled()
        || !candidate_policy.policy.see_capture_ordering_enabled()
    {
        return Err("S2-5 policy activation boundary is inverted".into());
    }

    let parity = run_parity_corpus(&baseline_policy, &candidate_policy, &weights)?;
    write_new(&output.join("s2-5-parity.tsv"), parity.as_bytes())?;

    let openings_text = control_openings()?;
    write_new(
        &output.join("s2-5-development-openings.tsv"),
        openings_text.as_bytes(),
    )?;
    let openings = OpeningSuite::from_text(&openings_text)?;
    let report = run_development_match(
        source_commit,
        &build_identity,
        &openings,
        &baseline_policy,
        &candidate_policy,
        &weights,
        EngineVariantResourceProtocol::FixedNodes(FIXED_NODE_LIMIT),
        "fixed-nodes",
    )?;
    let destination = output.join("s2-5-fixed-node-development.report");
    let temporary = output.join(".s2-5-fixed-node-development.tmp");
    write_engine_variant_validation_report_atomic(&destination, &temporary, &report)?;

    let manifest = format!(
        "S2_5_DETERMINISTIC_MANIFEST\t{REPORT_SCHEMA}\nsource_sha\t{source_text}\nbuild_identity\t{build_identity}\nbaseline_policy_identifier\t{:016x}\nbaseline_policy_checksum\t{:016x}\ncandidate_policy_identifier\t{:016x}\ncandidate_policy_checksum\t{:016x}\nweight_identifier\t{:016x}\nweight_checksum\t{:016x}\nfixed_node_pairs\t{FIXED_NODE_PAIRS}\nfixed_node_limit\t{FIXED_NODE_LIMIT}\nfixed_node_decision\t{}\nfixed_node_mean_bits\t{:016x}\nfixed_node_se_bits\t{:016x}\nfixed_node_lower_bits\t{:016x}\nfixed_node_checksum\t{:016x}\nactivated\tfalse\n",
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
        &output.join("s2-5-deterministic-manifest.tsv"),
        manifest.as_bytes(),
    )?;
    Ok(())
}

fn run_clock(output: &Path) -> Result<(), Box<dyn Error>> {
    create_output_directory(output)?;
    let source_text = required_environment("S2_5_SOURCE_SHA")?;
    let source_commit = parse_source_commit(&source_text)?;
    let build_identity = required_environment("S2_5_BUILD_IDENTITY")?;
    let baseline_policy = SearchPolicySet::baseline();
    let candidate_policy = SearchPolicySet::see_capture_ordering_candidate();
    let weights = EvaluationWeightSet::baseline();
    let openings_text = control_openings()?;
    let openings = OpeningSuite::from_text(&openings_text)?;
    let report = run_development_match(
        source_commit,
        &build_identity,
        &openings,
        &baseline_policy,
        &candidate_policy,
        &weights,
        EngineVariantResourceProtocol::ClockMilliseconds(CLOCK_MILLISECONDS),
        "clock",
    )?;
    let destination = output.join("s2-5-clock-development.report");
    let temporary = output.join(".s2-5-clock-development.tmp");
    write_engine_variant_validation_report_atomic(&destination, &temporary, &report)?;
    let summary = format!(
        "S2_5_CLOCK_SUMMARY\t{REPORT_SCHEMA}\nsource_sha\t{source_text}\nbuild_identity\t{build_identity}\npairs\t{CLOCK_PAIRS}\nclock_milliseconds\t{CLOCK_MILLISECONDS}\ndecision\t{}\nwins\t{}\ndraws\t{}\nlosses\t{}\nunfinished\t{}\nillegal_moves\t{}\ncrashes\t{}\ntime_forfeits\t{}\ninfrastructure_failures\t{}\nmean_bits\t{:016x}\nse_bits\t{:016x}\nlower_bits\t{:016x}\nchecksum\t{:016x}\nactivated\tfalse\n",
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
    write_new(&output.join("s2-5-clock-summary.tsv"), summary.as_bytes())?;
    Ok(())
}

fn run_development_match<'a>(
    source_commit: [u8; 20],
    build_identity: &str,
    openings: &OpeningSuite,
    baseline_policy: &'a SearchPolicySet,
    candidate_policy: &'a SearchPolicySet,
    weights: &'a EvaluationWeightSet,
    protocol: EngineVariantResourceProtocol,
    protocol_name: &str,
) -> Result<chess_tools::engine_variant_validation::EngineVariantValidationReport, Box<dyn Error>> {
    let baseline_identity = identity(
        0x5332_3542_4153_4531,
        source_commit,
        build_identity,
        &format!("s2_5_see_ordering {protocol_name} --role baseline"),
        baseline_policy,
        weights,
    )?;
    let candidate_identity = identity(
        0x5332_3543_414e_4431,
        source_commit,
        build_identity,
        &format!("s2_5_see_ordering {protocol_name} --role candidate"),
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
        0x5332_3544_4556_3031,
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
        "S2_5_PARITY\t{REPORT_SCHEMA}\ncorpus_checksum\t{:016x}\nbaseline_policy_checksum\t{:016x}\ncandidate_policy_checksum\t{:016x}\n",
        hash_bytes(FNV_OFFSET, CORPUS.as_bytes()),
        baseline_policy.checksum,
        candidate_policy.checksum,
    );
    let mut aggregate = FNV_OFFSET;
    let mut total_see_calls = 0_u64;
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
        total_see_calls = total_see_calls
            .checked_add(candidate_diagnostics.see_calls())
            .ok_or("SEE call total overflow")?;
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
            "case\t{}\tdepth={}\tbaseline_best={}\tcandidate_best={}\tbest_relation={}\tscore={}\tbaseline_nodes={}\tcandidate_nodes={}\tbaseline_qnodes={}\tcandidate_qnodes={}\tbaseline_cutoffs={}\tcandidate_cutoffs={}\tbaseline_first_move_cutoffs={}\tcandidate_first_move_cutoffs={}\tsee_calls={}\tsee_winning={}\tsee_equal={}\tsee_losing={}\tbaseline_diagnostics={:016x}\tcandidate_diagnostics={:016x}\tstatus=passed",
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
            candidate_diagnostics.see_calls(),
            candidate_diagnostics.see_winning_captures(),
            candidate_diagnostics.see_equal_captures(),
            candidate_diagnostics.see_losing_captures(),
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
            candidate_diagnostics.see_calls(),
            candidate_diagnostics.semantic_checksum(),
        ] {
            aggregate = hash_bytes(aggregate, &value.to_le_bytes());
        }
    }
    if total_see_calls == 0 {
        return Err("deterministic parity corpus exercised no SEE calls".into());
    }
    writeln!(output, "case_count\t{}", parse_corpus(CORPUS)?.len())?;
    writeln!(output, "differing_best_moves\t{differing_best_moves}")?;
    writeln!(output, "total_see_calls\t{total_see_calls}")?;
    writeln!(output, "aggregate_checksum\t{aggregate:016x}")?;
    writeln!(output, "activated\tfalse")?;
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
    if diagnostics.see_calls() != 0
        || diagnostics.see_winning_captures() != 0
        || diagnostics.see_equal_captures() != 0
        || diagnostics.see_losing_captures() != 0
        || diagnostics.see_prunes() != 0
        || diagnostics.quiescence_see_prunes() != 0
    {
        return Err(format!("baseline case {identifier} used SEE or pruned").into());
    }
    Ok(())
}

fn validate_candidate_diagnostics(
    diagnostics: SearchDiagnostics,
    identifier: &str,
) -> Result<(), Box<dyn Error>> {
    let classified = diagnostics
        .see_winning_captures()
        .checked_add(diagnostics.see_equal_captures())
        .and_then(|value| value.checked_add(diagnostics.see_losing_captures()))
        .ok_or("SEE classification count overflow")?;
    if diagnostics.see_calls() != classified
        || diagnostics.see_prunes() != 0
        || diagnostics.quiescence_see_prunes() != 0
    {
        return Err(format!(
            "candidate case {identifier} has inconsistent SEE classes or pruning"
        )
        .into());
    }
    Ok(())
}

fn run_benchmark(samples: usize) -> Result<(), Box<dyn Error>> {
    let baseline_policy = SearchPolicySet::baseline();
    let candidate_policy = SearchPolicySet::see_capture_ordering_candidate();
    let weights = EvaluationWeightSet::baseline();
    let baseline = benchmark_policy("baseline", samples, &baseline_policy, &weights)?;
    let candidate = benchmark_policy("candidate", samples, &candidate_policy, &weights)?;
    print_benchmark(&baseline);
    print_benchmark(&candidate);
    let ratio = candidate.median_nanos as f64 / baseline.median_nanos as f64;
    println!(
        "comparison\tmedian_time_ratio={ratio:.6}\tbaseline_nodes={}\tcandidate_nodes={}\tbaseline_qnodes={}\tcandidate_qnodes={}\tbaseline_cutoffs={}\tcandidate_cutoffs={}\tbaseline_first_move_cutoffs={}\tcandidate_first_move_cutoffs={}\tcandidate_see_calls={}\tcandidate_see_winning={}\tcandidate_see_equal={}\tcandidate_see_losing={}\tactivated=false",
        baseline.aggregate.nodes,
        candidate.aggregate.nodes,
        baseline.aggregate.qnodes,
        candidate.aggregate.qnodes,
        baseline.aggregate.beta_cutoffs,
        candidate.aggregate.beta_cutoffs,
        baseline.aggregate.first_move_cutoffs,
        candidate.aggregate.first_move_cutoffs,
        candidate.aggregate.see_calls,
        candidate.aggregate.see_winning,
        candidate.aggregate.see_equal,
        candidate.aggregate.see_losing,
    );
    if baseline.maximum_allocations != 0 || candidate.maximum_allocations != 0 {
        return Err("S2-5 search benchmark observed heap allocation".into());
    }
    if candidate.aggregate.see_calls == 0
        || candidate.aggregate.see_calls
            != candidate
                .aggregate
                .see_winning
                .checked_add(candidate.aggregate.see_equal)
                .and_then(|value| value.checked_add(candidate.aggregate.see_losing))
                .ok_or("benchmark SEE classification overflow")?
    {
        return Err("candidate benchmark did not exercise exact SEE classifications".into());
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
            let result = iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights(
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
            "sample\tpolicy={policy_name}\tindex={sample}\telapsed_nanos={elapsed_nanos}\tallocations={}\tallocated_bytes={}\tnodes={}\tqnodes={}\tcutoffs={}\tfirst_move_cutoffs={}\tsee_calls={}\tsee_winning={}\tsee_equal={}\tsee_losing={}\tchecksum={:016x}",
            snapshot.calls,
            snapshot.bytes,
            aggregate.nodes,
            aggregate.qnodes,
            aggregate.beta_cutoffs,
            aggregate.first_move_cutoffs,
            aggregate.see_calls,
            aggregate.see_winning,
            aggregate.see_equal,
            aggregate.see_losing,
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
        maximum_allocations: allocations.iter().map(|value| value.calls).max().unwrap_or(0),
        maximum_allocated_bytes: allocations.iter().map(|value| value.bytes).max().unwrap_or(0),
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
        (&mut aggregate.see_calls, diagnostics.see_calls()),
        (
            &mut aggregate.see_winning,
            diagnostics.see_winning_captures(),
        ),
        (&mut aggregate.see_equal, diagnostics.see_equal_captures()),
        (
            &mut aggregate.see_losing,
            diagnostics.see_losing_captures(),
        ),
    ] {
        *destination = destination
            .checked_add(value)
            .ok_or("benchmark aggregate counter overflow")?;
    }
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
        "summary\tpolicy={}\tsamples={}\tmedian_nanos={}\tminimum_nanos={}\tmaximum_nanos={}\tmaximum_allocations={}\tmaximum_allocated_bytes={}\tchecksum={:016x}",
        summary.policy,
        summary.samples,
        summary.median_nanos,
        summary.minimum_nanos,
        summary.maximum_nanos,
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
        return Err("invalid S2-5 parity corpus header".into());
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
        return Err("S2-5 parity corpus is empty".into());
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
            return Err(format!("principal variation contains illegal move {}", current.to_uci()).into());
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
                "s2-5-{index:03}\t{STARTING_FEN}\t{} {}",
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
        return Err("S2_5_SOURCE_SHA must be exactly 40 hexadecimal characters".into());
    }
    let mut result = [0_u8; 20];
    for (index, slot) in result.iter_mut().enumerate() {
        *slot = u8::from_str_radix(&value[index * 2..index * 2 + 2], 16)?;
    }
    if result.iter().all(|byte| *byte == 0) {
        return Err("S2_5_SOURCE_SHA must not be all zeroes".into());
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
        chess_tools::self_play::OpeningSuite::from_text(&text)
            .expect("development openings parse");
    }

    #[test]
    fn source_commit_is_exact_and_nonzero() {
        assert!(parse_source_commit("1111111111111111111111111111111111111111").is_ok());
        assert!(parse_source_commit("0000000000000000000000000000000000000000").is_err());
        assert!(parse_source_commit("abc").is_err());
    }
}
''',
)

write_new(
    "scripts/task_s2_5_see_ordering_audit.sh",
    r'''#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
policy="$root/crates/chess-search/src/search_policy.rs"
ordering="$root/crates/chess-search/src/move_ordering.rs"
diagnostics="$root/crates/chess-search/src/diagnostics.rs"
alpha_beta="$root/crates/chess-search/src/alpha_beta.rs"
quiescence="$root/crates/chess-search/src/quiescence.rs"
tests="$root/crates/chess-search/tests/s2_5_see_ordering.rs"
evidence="$root/crates/chess-tools/src/bin/s2_5_see_ordering.rs"
workflow="$root/.github/workflows/s2-5-see-ordering.yml"
doc="$root/docs/RUST_CHESS_ENGINE_V0_2_S2_5_SEE_ORDERING_2026-08-05.md"
ci="$root/.github/workflows/ci.yml"

require_file() {
  test -f "$1" || { echo "missing S2-5 asset: ${1#$root/}" >&2; exit 1; }
}

require_literal() {
  grep -Fq "$1" "$2" || {
    echo "missing S2-5 witness in ${2#$root/}: $1" >&2
    exit 1
  }
}

for path in "$policy" "$ordering" "$diagnostics" "$alpha_beta" "$quiescence" \
  "$tests" "$evidence" "$workflow" "$doc" "$ci"; do
  require_file "$path"
done

for witness in \
  'pub const SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID: u64 = 0x5332_3553_4545_4f31;' \
  'pub const SEE_CAPTURE_ORDERING: Self = Self::new' \
  'pub const fn see_capture_ordering_enabled' \
  'pub fn see_capture_ordering_candidate() -> Self'; do
  require_literal "$witness" "$policy"
done

for witness in \
  'static_exchange_evaluation(position, current)?' \
  'StaticExchangeClass::Winning => 3' \
  'StaticExchangeClass::Equal => 2' \
  'StaticExchangeClass::Losing => 1' \
  'ordered_legal_moves_with_state_and_tt_move_and_see' \
  'recursively_retained_ordering_excludes_temporary_sort_keys'; do
  require_literal "$witness" "$ordering"
done

for witness in \
  'SeeWinningCapture' \
  'SeeEqualCapture' \
  'SeeLosingCapture' \
  'see_winning_captures' \
  'see_equal_captures' \
  'see_losing_captures'; do
  require_literal "$witness" "$diagnostics"
done

require_literal 'StaticExchange(StaticExchangeError)' "$alpha_beta"
require_literal 'see_capture_ordering: policy.search_policy.see_capture_ordering_enabled()' "$alpha_beta"
require_literal 'ordered_legal_moves_with_see(position, &tokens, ordering, see_capture_ordering)?' "$quiescence"
require_literal 'candidate_preserves_exact_scores_mate_distance_and_legal_pvs' "$tests"
require_literal 'candidate_records_exact_capture_classes_without_pruning' "$tests"
require_literal 'diagnostics.see_prunes(), 0' "$tests"
require_literal 'run_engine_variant_validation' "$evidence"
require_literal 'EngineVariantResourceProtocol::FixedNodes' "$evidence"
require_literal 'EngineVariantResourceProtocol::ClockMilliseconds' "$evidence"
require_literal 'S2-5 search benchmark observed heap allocation' "$evidence"
require_literal 'contents: read' "$workflow"
require_literal 'task_s2_5_see_ordering_audit.sh' "$ci"

if grep -Eq 'contents: write|git push|git commit|s2_5_.*apply.py' "$workflow"; then
  echo 'permanent S2-5 workflow retains write or staging behavior' >&2
  exit 1
fi

if grep -R --line-number 'see_capture_ordering_candidate' \
  "$root/crates/chess-uci" "$root/crates/chess-ffi" "$root/android" 2>/dev/null; then
  echo 'S2-5 candidate leaked into a production adapter/default' >&2
  exit 1
fi

for temporary in \
  "$root/scripts/s2_5_apply.py" \
  "$root/scripts/s2_5_refine.py" \
  "$root/scripts/s2_5_fix_compile.py" \
  "$root/scripts/s2_5_reduce_stack.py" \
  "$root/scripts/s2_5_evidence_apply.py" \
  "$root/.github/workflows/s2-5-apply-temp.yml" \
  "$root/.github/workflows/s2-5-evidence-apply-temp.yml"; do
  test ! -e "$temporary" || { echo "temporary S2-5 asset remains: ${temporary#$root/}" >&2; exit 1; }
done

echo 'S2-5 SEE capture-ordering audit passed'
''',
)

write_new(
    "docs/RUST_CHESS_ENGINE_V0_2_S2_5_SEE_ORDERING_2026-08-05.md",
    r'''# Rust Chess Engine v0.2 S2-5 SEE Capture Ordering

**Status:** Implemented; inactive candidate under validation  
**Task:** S2-5  
**Starting master:** `5ccf5704ec1e1c94e03918b079be4abc4f37b038`  
**Core implementation:** `95d1917d986bc3f9ec808ba0f5f5a1a63619e5aa`

## Candidate boundary

S2-5 integrates the S2-4 Static Exchange Evaluation primitive into main-search and quiescence capture ordering only. It does not prune, reduce, extend, or omit a move. The production v0.1 policy remains the default for UCI, safe Rust, C ABI, JNI, and Android entry points.

The candidate is available only through the explicit controlled `SearchPolicySet::see_capture_ordering_candidate()` identity. Evidence reports always retain `activated=false`.

## Ordering contract

1. A valid transposition-table move remains first.
2. Previous-PV and promotion precedence remains unchanged.
3. Non-promotion captures are classified `winning > equal > losing`.
4. Captures in one class use signed SEE value, then existing MVV-LVA terms, then packed move identity as deterministic ties.
5. Quiet killer/history ordering is unchanged.
6. Every legal move remains in the ordered list.

SEE is calculated once per capture in the fixed-capacity ordering pass. The recursively retained move list contains only legal tokens and a bounded diagnostic summary; temporary sort keys are dropped before recursive search begins.

## Failure model

The ordering pass returns the existing typed `StaticExchangeError`. Alpha-beta exposes it as `AlphaBetaSearchError::StaticExchange`. Quiescence propagates the same error through the alpha-beta error boundary. Contradictory internal move state is never converted to MVV-LVA, a neutral SEE value, or an unvalidated fallback.

## Diagnostics

The candidate records exact counters for:

- SEE calls;
- winning capture classifications;
- equal capture classifications;
- losing capture classifications.

For every completed search, calls must equal the sum of the three classes. `see_prunes` and `quiescence_see_prunes` remain zero.

## Permanent evidence protocol

The focused S2-5 workflow runs on Linux x86-64 and native Linux ARM64. It provides:

- strict source audit, formatting, Clippy, and focused tests;
- full frozen S2-3 tactical-corpus baseline/candidate score parity;
- legal-PV replay and exact root position/history restoration;
- deterministic diagnostics and report checksums;
- an 8-pair fixed-node development comparison;
- an 8-pair clock-based development comparison on x86-64;
- seven-sample timing, node, qnode, cutoff, first-move-cutoff, SEE-class, and allocation evidence;
- a hard zero-allocation assertion for the measured search calls;
- read-only evidence artifacts bound to the exact source SHA and build identity.

A match result cannot activate the candidate. S2-5 records an independent disposition for later combination work; any production activation remains reserved for S2-14 and S2-15.
''',
)

write_new(
    ".github/workflows/s2-5-see-ordering.yml",
    r'''name: S2-5 SEE capture ordering validation

on:
  push:
    branches:
      - master
  pull_request:
    branches:
      - master
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: s2-5-see-ordering-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  linux-x86-64:
    name: Linux x86-64 correctness, strength, and performance
    runs-on: ubuntu-24.04
    timeout-minutes: 60
    steps:
      - uses: actions/checkout@v4

      - name: Install stable Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy

      - name: Cache Cargo data
        uses: Swatinem/rust-cache@v2
        with:
          shared-key: rust-engine-s2-5-see-ordering-x86-64

      - name: Audit S2-5 architecture
        run: bash scripts/task_s2_5_see_ordering_audit.sh

      - name: Check formatting and strict Clippy
        run: |
          cargo fmt --all -- --check
          cargo clippy --locked -p chess-search -p chess-tools --all-targets --all-features -- -D warnings

      - name: Run focused search and evidence tests
        run: |
          cargo test --locked -p chess-search --all-targets --all-features
          cargo test --locked -p chess-tools --bin s2_5_see_ordering

      - name: Build release evidence tool
        run: cargo build --locked --release -p chess-tools --bin s2_5_see_ordering

      - name: Record exact build identity
        shell: bash
        run: |
          set -euo pipefail
          build_identity="$(rustc -Vv | paste -sd '|' - | tr ' ' '_')"
          echo "S2_5_SOURCE_SHA=${GITHUB_SHA}" >> "$GITHUB_ENV"
          echo "S2_5_BUILD_IDENTITY=${build_identity}" >> "$GITHUB_ENV"

      - name: Generate byte-identical deterministic evidence twice
        run: |
          target/release/s2_5_see_ordering deterministic s2-5-deterministic-a
          target/release/s2_5_see_ordering deterministic s2-5-deterministic-b
          diff -ru s2-5-deterministic-a s2-5-deterministic-b

      - name: Generate clock development evidence
        run: target/release/s2_5_see_ordering clock s2-5-clock

      - name: Capture seven-sample x86-64 distribution
        run: target/release/s2_5_see_ordering benchmark 7 | tee s2-5-linux-x86-64.tsv

      - name: Preserve x86-64 S2-5 evidence
        uses: actions/upload-artifact@v4
        with:
          name: s2-5-see-ordering-linux-x86-64-${{ github.sha }}
          path: |
            s2-5-deterministic-a
            s2-5-clock
            s2-5-linux-x86-64.tsv
          if-no-files-found: error
          retention-days: 30

  linux-arm64:
    name: Linux ARM64 correctness and performance
    runs-on: ubuntu-24.04-arm
    timeout-minutes: 60
    steps:
      - uses: actions/checkout@v4

      - name: Install stable Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy

      - name: Cache Cargo data
        uses: Swatinem/rust-cache@v2
        with:
          shared-key: rust-engine-s2-5-see-ordering-arm64

      - name: Audit and test S2-5 on native ARM64
        run: |
          bash scripts/task_s2_5_see_ordering_audit.sh
          cargo check --locked -p chess-search -p chess-tools --all-targets --all-features
          cargo clippy --locked -p chess-search -p chess-tools --all-targets --all-features -- -D warnings
          cargo test --locked -p chess-search --all-targets --all-features
          cargo test --locked -p chess-tools --bin s2_5_see_ordering

      - name: Build release evidence tool
        run: cargo build --locked --release -p chess-tools --bin s2_5_see_ordering

      - name: Record exact build identity
        shell: bash
        run: |
          set -euo pipefail
          build_identity="$(rustc -Vv | paste -sd '|' - | tr ' ' '_')"
          echo "S2_5_SOURCE_SHA=${GITHUB_SHA}" >> "$GITHUB_ENV"
          echo "S2_5_BUILD_IDENTITY=${build_identity}" >> "$GITHUB_ENV"

      - name: Generate native ARM64 deterministic evidence
        run: target/release/s2_5_see_ordering deterministic s2-5-deterministic-arm64

      - name: Capture seven-sample ARM64 distribution
        run: target/release/s2_5_see_ordering benchmark 7 | tee s2-5-linux-arm64.tsv

      - name: Preserve ARM64 S2-5 evidence
        uses: actions/upload-artifact@v4
        with:
          name: s2-5-see-ordering-linux-arm64-${{ github.sha }}
          path: |
            s2-5-deterministic-arm64
            s2-5-linux-arm64.tsv
          if-no-files-found: error
          retention-days: 30
''',
)

replace_once(
    ".github/workflows/ci.yml",
    "          test -f scripts/task_s2_4_see_audit.sh\n",
    "          test -f scripts/task_s2_4_see_audit.sh\n"
    "          test -f scripts/task_s2_5_see_ordering_audit.sh\n",
)
replace_once(
    ".github/workflows/ci.yml",
    "          test -f docs/RUST_CHESS_ENGINE_V0_2_S2_4_SEE_2026-08-05.md\n",
    "          test -f docs/RUST_CHESS_ENGINE_V0_2_S2_4_SEE_2026-08-05.md\n"
    "          test -f docs/RUST_CHESS_ENGINE_V0_2_S2_5_SEE_ORDERING_2026-08-05.md\n",
)
replace_once(
    ".github/workflows/ci.yml",
    "          test -f crates/chess-tools/src/bin/s2_4_see_benchmark.rs\n",
    "          test -f crates/chess-tools/src/bin/s2_4_see_benchmark.rs\n"
    "          test -f crates/chess-tools/src/bin/s2_5_see_ordering.rs\n",
)
replace_once(
    ".github/workflows/ci.yml",
    "            scripts/task_s2_4_see_audit.sh\n",
    "            scripts/task_s2_4_see_audit.sh \\\n"
    "            scripts/task_s2_5_see_ordering_audit.sh\n",
)
replace_once(
    ".github/workflows/ci.yml",
    "      - name: Run standalone S2-4 SEE audit\n        run: bash scripts/task_s2_4_see_audit.sh\n\n",
    "      - name: Run standalone S2-4 SEE audit\n"
    "        run: bash scripts/task_s2_4_see_audit.sh\n\n"
    "      - name: Run S2-5 SEE capture-ordering audit\n"
    "        run: bash scripts/task_s2_5_see_ordering_audit.sh\n\n",
)

print("permanent S2-5 evidence patch applied")
