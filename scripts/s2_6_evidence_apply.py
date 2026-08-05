#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text()


def write_new(path: str, content: str) -> None:
    target = ROOT / path
    if target.exists():
        raise SystemExit(f"refusing to replace existing path: {path}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)


def replace_once(path: str, old: str, new: str) -> None:
    content = read(path)
    count = content.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement, found {count}: {old[:160]!r}")
    (ROOT / path).write_text(content.replace(old, new, 1))


# Add a direct narrowed-window delta-pruning regression. Full-window exact parity remains
# covered separately by the evidence binary and frozen tactical corpus.
replace_once(
    "crates/chess-search/src/quiescence.rs",
    "    #[test]\n"
    "    fn guard_exhaustion_in_check_remains_fail_loud_with_pruning_enabled() {\n",
    r'''    #[test]
    fn delta_pruning_is_exercised_only_after_see_under_a_narrow_window() {
        let mut position: Position = "3r3k/8/8/3p3p/8/8/8/K2Q4 w - - 0 1"
            .parse()
            .expect("delta-pruning fixture parses");
        let snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);
        let history_snapshot = history.clone();
        let mut cancellation = NeverCancelled;
        let result = search_quiescence_node_with_weights(
            &mut position,
            &mut history,
            QuiescenceContext {
                ply: 0,
                quiescence_ply: 0,
                maximum_quiescence_ply: MAX_QUIESCENCE_PLY,
            },
            QuiescenceSearchPolicy::new(
                Score::from_evaluation(2_000),
                Score::from_evaluation(2_100),
                MoveOrdering::Tactical,
                false,
                true,
                true,
                &EvaluationWeights::DEFAULT,
            ),
            &mut cancellation,
        )
        .expect("narrow-window delta search succeeds");
        assert!(result.score() <= Score::from_evaluation(2_000));
        assert!(result.diagnostics().quiescence_delta_attempts() > 0);
        assert!(result.diagnostics().quiescence_delta_prunes() > 0);
        assert_eq!(position, snapshot);
        assert_eq!(history, history_snapshot);
        assert_eq!(position.zobrist(), position.recomputed_zobrist());
    }

    #[test]
    fn guard_exhaustion_in_check_remains_fail_loud_with_pruning_enabled() {
''',
)

write_new(
    "crates/chess-tools/src/bin/s2_6_quiescence.rs",
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
    reference_search_with_quiescence, EvaluationWeightSet, Score, SearchDiagnostics, SearchLimits,
    SearchPolicySet, TranspositionTable,
};
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

const CORPUS: &str = include_str!("../../../../fixtures/search_baseline_v1.tsv");
const REPORT_SCHEMA: u16 = 1;
const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;
const TT_MEBIBYTES: usize = 1;
const DEVELOPMENT_PAIRS: u32 = 8;
const FIXED_NODE_LIMIT: u64 = 2_000;
const CLOCK_MILLISECONDS: u64 = 10;
const MAXIMUM_MATCH_PLIES: u32 = 48;
const BENCHMARK_NODE_LIMIT: u64 = 10_000;
const BENCHMARK_FENS: [&str; 4] = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10",
];
const PRUNE_WITNESS_FEN: &str = "3r3k/8/8/3p3p/8/8/8/K2Q4 w - - 0 1";

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
    see_prunes: u64,
    delta_attempts: u64,
    delta_prunes: u64,
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
        eprintln!("S2-6 quiescence evidence failed: {error}");
        std::process::exit(1);
    }
}

fn run() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let mode = arguments.next().ok_or(
        "usage: s2_6_quiescence deterministic OUTPUT_DIR | clock OUTPUT_DIR | benchmark SAMPLES",
    )?;
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
            "usage: s2_6_quiescence deterministic OUTPUT_DIR | clock OUTPUT_DIR | benchmark SAMPLES"
                .into(),
        ),
    }
}

fn run_deterministic(output: &Path) -> Result<(), Box<dyn Error>> {
    create_output_directory(output)?;
    let source_text = required_environment("S2_6_SOURCE_SHA")?;
    let source_commit = parse_source_commit(&source_text)?;
    let build_identity = required_environment("S2_6_BUILD_IDENTITY")?;
    let baseline = SearchPolicySet::baseline();
    let see = SearchPolicySet::see_quiescence_pruning_candidate();
    let delta = SearchPolicySet::see_and_delta_quiescence_pruning_candidate();
    let weights = EvaluationWeightSet::baseline();
    for policy in [&baseline, &see, &delta] {
        policy.validate()?;
    }
    weights.validate()?;
    if baseline.policy.see_quiescence_pruning_enabled()
        || see.policy.delta_pruning_enabled()
        || !see.policy.see_quiescence_pruning_enabled()
        || !delta.policy.see_quiescence_pruning_enabled()
        || !delta.policy.delta_pruning_enabled()
    {
        return Err("S2-6 policy activation boundary is inconsistent".into());
    }

    let parity = run_parity_corpus(&baseline, &see, &delta, &weights)?;
    write_new(&output.join("s2-6-parity.tsv"), parity.as_bytes())?;

    let openings_text = control_openings()?;
    write_new(
        &output.join("s2-6-development-openings.tsv"),
        openings_text.as_bytes(),
    )?;
    let openings = OpeningSuite::from_text(&openings_text)?;
    for (name, candidate) in [("see", &see), ("delta", &delta)] {
        let report = run_development_match(
            source_commit,
            &build_identity,
            &openings,
            &baseline,
            candidate,
            &weights,
            EngineVariantResourceProtocol::FixedNodes(FIXED_NODE_LIMIT),
            &format!("fixed-nodes-{name}"),
        )?;
        persist_report(output, &format!("s2-6-{name}-fixed-node.report"), &report)?;
    }

    let manifest = format!(
        "S2_6_DETERMINISTIC_MANIFEST\t{REPORT_SCHEMA}\nsource_sha\t{source_text}\nbuild_identity\t{build_identity}\nbaseline_policy_identifier\t{:016x}\nbaseline_policy_checksum\t{:016x}\nsee_policy_identifier\t{:016x}\nsee_policy_checksum\t{:016x}\ndelta_policy_identifier\t{:016x}\ndelta_policy_checksum\t{:016x}\nweight_identifier\t{:016x}\nweight_checksum\t{:016x}\nfixed_node_pairs\t{DEVELOPMENT_PAIRS}\nfixed_node_limit\t{FIXED_NODE_LIMIT}\nactivated\tfalse\n",
        baseline.identifier,
        baseline.checksum,
        see.identifier,
        see.checksum,
        delta.identifier,
        delta.checksum,
        weights.identifier,
        weights.checksum,
    );
    write_new(
        &output.join("s2-6-deterministic-manifest.tsv"),
        manifest.as_bytes(),
    )?;
    Ok(())
}

fn run_clock(output: &Path) -> Result<(), Box<dyn Error>> {
    create_output_directory(output)?;
    let source_text = required_environment("S2_6_SOURCE_SHA")?;
    let source_commit = parse_source_commit(&source_text)?;
    let build_identity = required_environment("S2_6_BUILD_IDENTITY")?;
    let baseline = SearchPolicySet::baseline();
    let see = SearchPolicySet::see_quiescence_pruning_candidate();
    let delta = SearchPolicySet::see_and_delta_quiescence_pruning_candidate();
    let weights = EvaluationWeightSet::baseline();
    let openings_text = control_openings()?;
    let openings = OpeningSuite::from_text(&openings_text)?;
    let mut summary = format!(
        "S2_6_CLOCK_SUMMARY\t{REPORT_SCHEMA}\nsource_sha\t{source_text}\nbuild_identity\t{build_identity}\n"
    );
    for (name, candidate) in [("see", &see), ("delta", &delta)] {
        let report = run_development_match(
            source_commit,
            &build_identity,
            &openings,
            &baseline,
            candidate,
            &weights,
            EngineVariantResourceProtocol::ClockMilliseconds(CLOCK_MILLISECONDS),
            &format!("clock-{name}"),
        )?;
        persist_report(output, &format!("s2-6-{name}-clock.report"), &report)?;
        writeln!(
            summary,
            "candidate\t{name}\tdecision={}\twins={}\tdraws={}\tlosses={}\tunfinished={}\tillegal_moves={}\tcrashes={}\ttime_forfeits={}\tinfrastructure_failures={}\tmean_bits={:016x}\tlower_bits={:016x}\tchecksum={:016x}\tactivated=false",
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
            report.lower_confidence_bound.to_bits(),
            report.checksum,
        )?;
    }
    write_new(&output.join("s2-6-clock-summary.tsv"), summary.as_bytes())?;
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn run_development_match<'a>(
    source_commit: [u8; 20],
    build_identity: &str,
    openings: &OpeningSuite,
    baseline_policy: &'a SearchPolicySet,
    candidate_policy: &'a SearchPolicySet,
    weights: &'a EvaluationWeightSet,
    protocol: EngineVariantResourceProtocol,
    protocol_name: &str,
) -> Result<EngineVariantValidationReport, Box<dyn Error>> {
    let baseline_identity = identity(
        0x5332_3642_4153_4531,
        source_commit,
        build_identity,
        &format!("s2_6_quiescence {protocol_name} --role baseline"),
        baseline_policy,
        weights,
    )?;
    let candidate_identity = identity(
        candidate_policy.identifier ^ 0x4341_4e44_4944_4154,
        source_commit,
        build_identity,
        &format!("s2_6_quiescence {protocol_name} --role candidate"),
        candidate_policy,
        weights,
    )?;
    let baseline = EngineVariantRuntime::new(&baseline_identity, baseline_policy, weights)?;
    let candidate = EngineVariantRuntime::new(&candidate_identity, candidate_policy, weights)?;
    let config = EngineVariantValidationConfig::new(
        EngineVariantValidationTier::Development,
        DEVELOPMENT_PAIRS,
        0x5332_3651_5549_4553 ^ candidate_policy.identifier,
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

fn persist_report(
    output: &Path,
    name: &str,
    report: &EngineVariantValidationReport,
) -> Result<(), Box<dyn Error>> {
    let destination = output.join(name);
    let temporary = output.join(format!(".{name}.tmp"));
    write_engine_variant_validation_report_atomic(&destination, &temporary, report)?;
    Ok(())
}

fn run_parity_corpus(
    baseline_policy: &SearchPolicySet,
    see_policy: &SearchPolicySet,
    delta_policy: &SearchPolicySet,
    weights: &EvaluationWeightSet,
) -> Result<String, Box<dyn Error>> {
    let cases = parse_corpus(CORPUS)?;
    let mut output = format!(
        "S2_6_PARITY\t{REPORT_SCHEMA}\ncorpus_checksum\t{:016x}\nbaseline_policy_checksum\t{:016x}\nsee_policy_checksum\t{:016x}\ndelta_policy_checksum\t{:016x}\n",
        hash_bytes(FNV_OFFSET, CORPUS.as_bytes()),
        baseline_policy.checksum,
        see_policy.checksum,
        delta_policy.checksum,
    );
    let mut aggregate = FNV_OFFSET;
    let mut total_see_prunes = 0_u64;
    let mut total_delta_attempts = 0_u64;
    let mut total_delta_prunes = 0_u64;
    for case in cases {
        let (root, history) = if case.repetition_cycle {
            repetition_root()?
        } else {
            let root = Position::from_fen(&case.fen)?;
            let history = SearchHistory::from_position(&root);
            (root, history)
        };
        let baseline = search_exact(&root, &history, case.depth, baseline_policy, weights)?;
        let see = search_exact(&root, &history, case.depth, see_policy, weights)?;
        let delta = search_exact(&root, &history, case.depth, delta_policy, weights)?;
        for (name, candidate) in [("see", &see), ("delta", &delta)] {
            if candidate.score() != baseline.score()
                || candidate.completed_depth() != baseline.completed_depth()
            {
                return Err(format!(
                    "case {} changed exact score or completed depth for {name}",
                    case.identifier
                )
                .into());
            }
            replay_pv(&root, candidate.principal_variation())?;
        }
        replay_pv(&root, baseline.principal_variation())?;

        let reference_depth = case.depth.min(1);
        let mut reference_position = root.clone();
        let mut reference_history = history.clone();
        let reference = reference_search_with_quiescence(
            &mut reference_position,
            &mut reference_history,
            reference_depth,
        )?;
        let baseline_reference = search_exact(
            &root,
            &history,
            reference_depth,
            baseline_policy,
            weights,
        )?;
        let see_reference = search_exact(&root, &history, reference_depth, see_policy, weights)?;
        let delta_reference = search_exact(&root, &history, reference_depth, delta_policy, weights)?;
        if reference.score() != baseline_reference.score()
            || reference.score() != see_reference.score()
            || reference.score() != delta_reference.score()
        {
            return Err(format!("case {} failed bounded reference parity", case.identifier).into());
        }

        let baseline_diagnostics = baseline.search_diagnostics();
        let see_diagnostics = see.search_diagnostics();
        let delta_diagnostics = delta.search_diagnostics();
        validate_baseline_diagnostics(baseline_diagnostics, &case.identifier)?;
        validate_see_diagnostics(see_diagnostics, &case.identifier)?;
        validate_delta_diagnostics(delta_diagnostics, &case.identifier)?;
        total_see_prunes = total_see_prunes
            .checked_add(see_diagnostics.quiescence_see_prunes())
            .ok_or("SEE-prune total overflow")?;
        total_delta_attempts = total_delta_attempts
            .checked_add(delta_diagnostics.quiescence_delta_attempts())
            .ok_or("delta-attempt total overflow")?;
        total_delta_prunes = total_delta_prunes
            .checked_add(delta_diagnostics.quiescence_delta_prunes())
            .ok_or("delta-prune total overflow")?;

        let baseline_best = display_move(baseline.best_move());
        let see_best = display_move(see.best_move());
        let delta_best = display_move(delta.best_move());
        let score = display_score(baseline.score());
        writeln!(
            output,
            "case\t{}\tdepth={}\tbaseline_best={}\tsee_best={}\tdelta_best={}\tscore={}\tbaseline_nodes={}\tsee_nodes={}\tdelta_nodes={}\tbaseline_qnodes={}\tsee_qnodes={}\tdelta_qnodes={}\tsee_prunes={}\tdelta_attempts={}\tdelta_prunes={}\tbaseline_diagnostics={:016x}\tsee_diagnostics={:016x}\tdelta_diagnostics={:016x}\tstatus=passed",
            case.identifier,
            case.depth,
            baseline_best,
            see_best,
            delta_best,
            score,
            baseline.nodes(),
            see.nodes(),
            delta.nodes(),
            baseline.qnodes(),
            see.qnodes(),
            delta.qnodes(),
            see_diagnostics.quiescence_see_prunes(),
            delta_diagnostics.quiescence_delta_attempts(),
            delta_diagnostics.quiescence_delta_prunes(),
            baseline_diagnostics.semantic_checksum(),
            see_diagnostics.semantic_checksum(),
            delta_diagnostics.semantic_checksum(),
        )?;
        for value in [
            case.identifier.as_bytes(),
            baseline_best.as_bytes(),
            see_best.as_bytes(),
            delta_best.as_bytes(),
            score.as_bytes(),
        ] {
            aggregate = hash_bytes(aggregate, value);
        }
        for value in [
            baseline.nodes(),
            see.nodes(),
            delta.nodes(),
            baseline.qnodes(),
            see.qnodes(),
            delta.qnodes(),
            see_diagnostics.quiescence_see_prunes(),
            delta_diagnostics.quiescence_delta_attempts(),
            delta_diagnostics.quiescence_delta_prunes(),
        ] {
            aggregate = hash_bytes(aggregate, &value.to_le_bytes());
        }
    }

    let witness_root = Position::from_fen(PRUNE_WITNESS_FEN)?;
    let witness_history = SearchHistory::from_position(&witness_root);
    let witness = search_exact(&witness_root, &witness_history, 1, see_policy, weights)?;
    let witness_prunes = witness.search_diagnostics().quiescence_see_prunes();
    if witness_prunes == 0 {
        return Err("dedicated S2-6 witness exercised no SEE prune".into());
    }
    total_see_prunes = total_see_prunes
        .checked_add(witness_prunes)
        .ok_or("SEE-prune total overflow")?;

    writeln!(output, "case_count\t{}", parse_corpus(CORPUS)?.len())?;
    writeln!(output, "witness_see_prunes\t{witness_prunes}")?;
    writeln!(output, "total_see_prunes\t{total_see_prunes}")?;
    writeln!(output, "total_delta_attempts\t{total_delta_attempts}")?;
    writeln!(output, "total_delta_prunes\t{total_delta_prunes}")?;
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
    if diagnostics.quiescence_see_prunes() != 0
        || diagnostics.quiescence_delta_attempts() != 0
        || diagnostics.quiescence_delta_prunes() != 0
    {
        return Err(format!("baseline case {identifier} used quiescence pruning").into());
    }
    Ok(())
}

fn validate_see_diagnostics(
    diagnostics: SearchDiagnostics,
    identifier: &str,
) -> Result<(), Box<dyn Error>> {
    if diagnostics.quiescence_delta_attempts() != 0
        || diagnostics.quiescence_delta_prunes() != 0
    {
        return Err(format!("SEE-only case {identifier} used delta pruning").into());
    }
    Ok(())
}

fn validate_delta_diagnostics(
    diagnostics: SearchDiagnostics,
    identifier: &str,
) -> Result<(), Box<dyn Error>> {
    if diagnostics.quiescence_delta_prunes() > diagnostics.quiescence_delta_attempts() {
        return Err(format!("delta case {identifier} pruned more moves than it attempted").into());
    }
    Ok(())
}

fn run_benchmark(samples: usize) -> Result<(), Box<dyn Error>> {
    let weights = EvaluationWeightSet::baseline();
    let policies = [
        ("baseline", SearchPolicySet::baseline()),
        ("see", SearchPolicySet::see_quiescence_pruning_candidate()),
        (
            "delta",
            SearchPolicySet::see_and_delta_quiescence_pruning_candidate(),
        ),
    ];
    let mut summaries = Vec::with_capacity(policies.len());
    for (name, policy) in &policies {
        summaries.push(benchmark_policy(name, samples, policy, &weights)?);
    }
    for summary in &summaries {
        print_benchmark(summary);
    }
    let baseline = &summaries[0];
    for candidate in &summaries[1..] {
        let ratio = candidate.median_nanos as f64 / baseline.median_nanos as f64;
        let allocation_delta = i128::from(candidate.maximum_allocations)
            - i128::from(baseline.maximum_allocations);
        let byte_delta = i128::from(candidate.maximum_allocated_bytes)
            - i128::from(baseline.maximum_allocated_bytes);
        println!(
            "comparison\tpolicy={}\tmedian_time_ratio={ratio:.6}\tbaseline_nodes={}\tcandidate_nodes={}\tbaseline_qnodes={}\tcandidate_qnodes={}\tbaseline_cutoffs={}\tcandidate_cutoffs={}\tbaseline_first_move_cutoffs={}\tcandidate_first_move_cutoffs={}\tbaseline_maximum_allocations={}\tcandidate_maximum_allocations={}\tallocation_delta={}\tbaseline_maximum_allocated_bytes={}\tcandidate_maximum_allocated_bytes={}\tallocated_byte_delta={}\tsee_calls={}\tsee_prunes={}\tdelta_attempts={}\tdelta_prunes={}\tactivated=false",
            candidate.policy,
            baseline.aggregate.nodes,
            candidate.aggregate.nodes,
            baseline.aggregate.qnodes,
            candidate.aggregate.qnodes,
            baseline.aggregate.beta_cutoffs,
            candidate.aggregate.beta_cutoffs,
            baseline.aggregate.first_move_cutoffs,
            candidate.aggregate.first_move_cutoffs,
            baseline.maximum_allocations,
            candidate.maximum_allocations,
            allocation_delta,
            baseline.maximum_allocated_bytes,
            candidate.maximum_allocated_bytes,
            byte_delta,
            candidate.aggregate.see_calls,
            candidate.aggregate.see_prunes,
            candidate.aggregate.delta_attempts,
            candidate.aggregate.delta_prunes,
        );
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
            "sample\tpolicy={policy_name}\tindex={sample}\telapsed_nanos={elapsed_nanos}\tallocations={}\tallocated_bytes={}\tnodes={}\tqnodes={}\tcutoffs={}\tfirst_move_cutoffs={}\tsee_calls={}\tsee_prunes={}\tdelta_attempts={}\tdelta_prunes={}\tchecksum={:016x}",
            snapshot.calls,
            snapshot.bytes,
            aggregate.nodes,
            aggregate.qnodes,
            aggregate.beta_cutoffs,
            aggregate.first_move_cutoffs,
            aggregate.see_calls,
            aggregate.see_prunes,
            aggregate.delta_attempts,
            aggregate.delta_prunes,
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
            &mut aggregate.see_prunes,
            diagnostics.quiescence_see_prunes(),
        ),
        (
            &mut aggregate.delta_attempts,
            diagnostics.quiescence_delta_attempts(),
        ),
        (
            &mut aggregate.delta_prunes,
            diagnostics.quiescence_delta_prunes(),
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
        return Err("invalid S2-6 parity corpus header".into());
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
        return Err("S2-6 parity corpus is empty".into());
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
    let root = Position::starting();
    let mut mutable_root = root.clone();
    let mut white_moves = mutable_root.legal_moves()?.iter().collect::<Vec<_>>();
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
                "s2-6-{index:03}\t{STARTING_FEN}\t{} {}",
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
        return Err("S2_6_SOURCE_SHA must be exactly 40 hexadecimal characters".into());
    }
    let mut result = [0_u8; 20];
    for (index, slot) in result.iter_mut().enumerate() {
        *slot = u8::from_str_radix(&value[index * 2..index * 2 + 2], 16)?;
    }
    if result.iter().all(|byte| *byte == 0) {
        return Err("S2_6_SOURCE_SHA must not be all zeroes".into());
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
    "scripts/task_s2_6_quiescence_audit.sh",
    r'''#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
policy="$root/crates/chess-search/src/search_policy.rs"
quiescence="$root/crates/chess-search/src/quiescence.rs"
diagnostics="$root/crates/chess-search/src/diagnostics.rs"
evidence="$root/crates/chess-tools/src/bin/s2_6_quiescence.rs"
doc="$root/docs/RUST_CHESS_ENGINE_V0_2_S2_6_QUIESCENCE_2026-08-05.md"
workflow="$root/.github/workflows/s2-6-quiescence.yml"
ci="$root/.github/workflows/ci.yml"

require_file() {
  test -f "$1" || { echo "missing S2-6 asset: ${1#$root/}" >&2; exit 1; }
}

require_literal() {
  grep -Fq "$1" "$2" || {
    echo "missing S2-6 witness in ${2#$root/}: $1" >&2
    exit 1
  }
}

for path in "$policy" "$quiescence" "$diagnostics" "$evidence" "$doc" "$workflow" "$ci"; do
  require_file "$path"
done

for witness in \
  'SEE_QUIESCENCE_PRUNING_SEARCH_POLICY_ID' \
  'SEE_AND_DELTA_QUIESCENCE_PRUNING_SEARCH_POLICY_ID' \
  'DeltaPruningRequiresSeePruning' \
  'see_quiescence_pruning_candidate' \
  'see_and_delta_quiescence_pruning_candidate'; do
  require_literal "$witness" "$policy"
done

for witness in \
  'SEE_QUIESCENCE_PRUNE_THRESHOLD_CENTIPAWNS: i32 = -100' \
  'DELTA_PRUNING_MARGIN_CENTIPAWNS: i32 = 200' \
  'QuiescenceDepthLimitReachedInCheck' \
  'tactical_move_count > 1' \
  'current.kind() != MoveKind::EnPassant' \
  'let gives_check = position.is_in_check(position.side_to_move())' \
  'StaticExchangeMoveStateError::InvalidTargetState' \
  'delta_pruning_is_exercised_only_after_see_under_a_narrow_window'; do
  require_literal "$witness" "$quiescence"
done

for witness in \
  'QuiescenceDeltaAttempt' \
  'quiescence_delta_attempts' \
  'QuiescenceSeePrune' \
  'QuiescenceDeltaPrune'; do
  require_literal "$witness" "$diagnostics"
done

for witness in \
  'reference_search_with_quiescence' \
  'run_engine_variant_validation' \
  'EngineVariantResourceProtocol::FixedNodes' \
  'EngineVariantResourceProtocol::ClockMilliseconds' \
  'baseline_maximum_allocations' \
  'activated=false'; do
  require_literal "$witness" "$evidence"
done

require_literal 'contents: read' "$workflow"
require_literal 'task_s2_6_quiescence_audit.sh' "$ci"

if grep -Eq 'contents: write|git push|git commit|s2_6_.*apply.py' "$workflow"; then
  echo 'permanent S2-6 workflow retains write or staging behavior' >&2
  exit 1
fi

if grep -R --line-number 'see_quiescence_pruning_candidate\|see_and_delta_quiescence_pruning_candidate' \
  "$root/crates/chess-uci" "$root/crates/chess-ffi" "$root/android" 2>/dev/null; then
  echo 'S2-6 candidate leaked into a production adapter/default' >&2
  exit 1
fi

for temporary in \
  "$root/scripts/s2_6_see_apply.py" \
  "$root/scripts/s2_6_see_driver.py" \
  "$root/scripts/s2_6_evidence_apply.py" \
  "$root/.github/workflows/s2-6-see-apply-temp.yml" \
  "$root/.github/workflows/s2-6-evidence-apply-temp.yml"; do
  test ! -e "$temporary" || { echo "temporary S2-6 asset remains: ${temporary#$root/}" >&2; exit 1; }
done

echo 'S2-6 quiescence audit passed'
''',
)

print("permanent S2-6 evidence patch applied")
