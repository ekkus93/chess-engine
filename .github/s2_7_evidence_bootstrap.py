from pathlib import Path
import re


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one occurrence, found {count}")
    return text.replace(old, new, 1)


def replace_block(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one block, found {count}")
    return updated


source_path = Path("crates/chess-tools/src/bin/s2_5_see_ordering.rs")
destination_path = Path("crates/chess-tools/src/bin/s2_7_pvs.rs")
if destination_path.exists():
    raise SystemExit(f"refusing to overwrite {destination_path}")
text = source_path.read_text(encoding="utf-8")

for old, new in [
    ("s2_5_see_ordering", "s2_7_pvs"),
    ("S2_5", "S2_7"),
    ("S2-5", "S2-7"),
    ("s2-5", "s2-7"),
    ("SEE ordering", "PVS"),
    ("see_capture_ordering_candidate", "principal_variation_search_candidate"),
    ("see_capture_ordering_enabled", "principal_variation_search_enabled"),
    ("0x5332_3542_4153_4531", "0x5332_3742_4153_4531"),
    ("0x5332_3543_414e_4431", "0x5332_3743_414e_4431"),
    ("0x5332_3544_4556_3031", "0x5332_3744_4556_3031"),
]:
    text = text.replace(old, new)

text = replace_block(
    text,
    r"#\[derive\(Clone, Copy, Debug, Default\)\]\nstruct SearchAggregate \{.*?\n\}",
    '''#[derive(Clone, Copy, Debug, Default)]
struct SearchAggregate {
    nodes: u64,
    qnodes: u64,
    beta_cutoffs: u64,
    first_move_cutoffs: u64,
    pvs_zero_window_searches: u64,
    pvs_researches: u64,
    checksum: u64,
}''',
    "search aggregate",
)

run_parity = r'''fn run_parity_corpus(
    baseline_policy: &SearchPolicySet,
    candidate_policy: &SearchPolicySet,
    weights: &EvaluationWeightSet,
) -> Result<String, Box<dyn Error>> {
    let cases = parse_corpus(CORPUS)?;
    let mut output = format!(
        "S2_7_PARITY\t{REPORT_SCHEMA}\ncorpus_checksum\t{:016x}\nbaseline_policy_checksum\t{:016x}\ncandidate_policy_checksum\t{:016x}\n",
        hash_bytes(FNV_OFFSET, CORPUS.as_bytes()),
        baseline_policy.checksum,
        candidate_policy.checksum,
    );
    let mut aggregate = FNV_OFFSET;
    let mut total_zero_window_searches = 0_u64;
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
            .checked_add(candidate_diagnostics.pvs_zero_window_searches())
            .ok_or("PVS zero-window total overflow")?;
        total_researches = total_researches
            .checked_add(candidate_diagnostics.pvs_researches())
            .ok_or("PVS re-search total overflow")?;
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
            "case\t{}\tdepth={}\tbaseline_best={}\tcandidate_best={}\tbest_relation={}\tscore={}\tbaseline_nodes={}\tcandidate_nodes={}\tbaseline_qnodes={}\tcandidate_qnodes={}\tbaseline_cutoffs={}\tcandidate_cutoffs={}\tbaseline_first_move_cutoffs={}\tcandidate_first_move_cutoffs={}\tpvs_zero_window_searches={}\tpvs_researches={}\tbaseline_diagnostics={:016x}\tcandidate_diagnostics={:016x}\tstatus=passed",
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
            candidate_diagnostics.pvs_zero_window_searches(),
            candidate_diagnostics.pvs_researches(),
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
            candidate_diagnostics.pvs_zero_window_searches(),
            candidate_diagnostics.pvs_researches(),
            candidate_diagnostics.semantic_checksum(),
        ] {
            aggregate = hash_bytes(aggregate, &value.to_le_bytes());
        }
    }
    if total_zero_window_searches == 0 {
        return Err("deterministic parity corpus exercised no PVS zero-window searches".into());
    }
    if total_researches > total_zero_window_searches {
        return Err("PVS re-search total exceeds zero-window search total".into());
    }
    writeln!(output, "case_count\t{}", parse_corpus(CORPUS)?.len())?;
    writeln!(output, "differing_best_moves\t{differing_best_moves}")?;
    writeln!(
        output,
        "total_pvs_zero_window_searches\t{total_zero_window_searches}"
    )?;
    writeln!(output, "total_pvs_researches\t{total_researches}")?;
    writeln!(output, "aggregate_checksum\t{aggregate:016x}")?;
    writeln!(output, "activated\tfalse")?;
    Ok(output)
}

fn search_exact('''
text = replace_block(
    text,
    r"fn run_parity_corpus\(.*?\nfn search_exact\(",
    run_parity,
    "parity corpus",
)

validate_diagnostics = r'''fn validate_baseline_diagnostics(
    diagnostics: SearchDiagnostics,
    identifier: &str,
) -> Result<(), Box<dyn Error>> {
    if diagnostics.pvs_zero_window_searches() != 0 || diagnostics.pvs_researches() != 0 {
        return Err(format!("baseline case {identifier} used PVS").into());
    }
    Ok(())
}

fn validate_candidate_diagnostics(
    diagnostics: SearchDiagnostics,
    identifier: &str,
) -> Result<(), Box<dyn Error>> {
    if diagnostics.pvs_researches() > diagnostics.pvs_zero_window_searches() {
        return Err(format!("candidate case {identifier} has more re-searches than probes").into());
    }
    Ok(())
}

fn run_benchmark'''
text = replace_block(
    text,
    r"fn validate_baseline_diagnostics\(.*?\nfn run_benchmark",
    validate_diagnostics,
    "diagnostic validation",
)

run_benchmark = r'''fn run_benchmark(samples: usize) -> Result<(), Box<dyn Error>> {
    let baseline_policy = SearchPolicySet::baseline();
    let candidate_policy = SearchPolicySet::principal_variation_search_candidate();
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
        "comparison\tmedian_time_ratio={ratio:.6}\tbaseline_nodes={}\tcandidate_nodes={}\tbaseline_qnodes={}\tcandidate_qnodes={}\tbaseline_cutoffs={}\tcandidate_cutoffs={}\tbaseline_first_move_cutoffs={}\tcandidate_first_move_cutoffs={}\tbaseline_maximum_allocations={}\tcandidate_maximum_allocations={}\tallocation_delta={}\tbaseline_maximum_allocated_bytes={}\tcandidate_maximum_allocated_bytes={}\tallocated_byte_delta={}\tcandidate_pvs_zero_window_searches={}\tcandidate_pvs_researches={}\tactivated=false",
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
        allocated_byte_delta,
        candidate.aggregate.pvs_zero_window_searches,
        candidate.aggregate.pvs_researches,
    );
    if baseline.aggregate.pvs_zero_window_searches != 0
        || baseline.aggregate.pvs_researches != 0
    {
        return Err("baseline benchmark unexpectedly exercised PVS".into());
    }
    if candidate.aggregate.pvs_zero_window_searches == 0
        || candidate.aggregate.pvs_researches
            > candidate.aggregate.pvs_zero_window_searches
    {
        return Err("candidate benchmark did not exercise valid PVS accounting".into());
    }
    Ok(())
}

fn benchmark_policy'''
text = replace_block(
    text,
    r"fn run_benchmark\(.*?\nfn benchmark_policy",
    run_benchmark,
    "benchmark comparison",
)

benchmark_policy = r'''fn benchmark_policy(
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
            "sample\tpolicy={policy_name}\tindex={sample}\telapsed_nanos={elapsed_nanos}\tallocations={}\tallocated_bytes={}\tnodes={}\tqnodes={}\tcutoffs={}\tfirst_move_cutoffs={}\tpvs_zero_window_searches={}\tpvs_researches={}\tchecksum={:016x}",
            snapshot.calls,
            snapshot.bytes,
            aggregate.nodes,
            aggregate.qnodes,
            aggregate.beta_cutoffs,
            aggregate.first_move_cutoffs,
            aggregate.pvs_zero_window_searches,
            aggregate.pvs_researches,
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

fn aggregate_search'''
text = replace_block(
    text,
    r"fn benchmark_policy\(.*?\nfn aggregate_search",
    benchmark_policy,
    "benchmark policy",
)

aggregate_search = r'''fn aggregate_search(
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
        (
            &mut aggregate.pvs_zero_window_searches,
            diagnostics.pvs_zero_window_searches(),
        ),
        (&mut aggregate.pvs_researches, diagnostics.pvs_researches()),
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

fn print_benchmark'''
text = replace_block(
    text,
    r"fn aggregate_search\(.*?\nfn print_benchmark",
    aggregate_search,
    "aggregate search",
)

for forbidden in [
    "see_calls",
    "see_winning",
    "see_equal",
    "see_losing",
    "see_capture_ordering",
]:
    if forbidden in text:
        raise SystemExit(f"generated S2-7 evidence tool retained {forbidden}")

destination_path.write_text(text, encoding="utf-8")

audit_path = Path("scripts/task_s2_7_pvs_audit.sh")
audit = audit_path.read_text(encoding="utf-8")
audit = replace_once(
    audit,
    'tests="crates/chess-search/tests/s2_7_pvs.rs"\n',
    'tests="crates/chess-search/tests/s2_7_pvs.rs"\n'
    'evidence="crates/chess-tools/src/bin/s2_7_pvs.rs"\n',
    "audit evidence variable",
)
audit = replace_once(
    audit,
    'for path in "$policy" "$search" "$lib" "$tests"; do\n',
    'for path in "$policy" "$search" "$lib" "$tests" "$evidence"; do\n',
    "audit path list",
)
audit = replace_once(
    audit,
    'grep -q \'PRINCIPAL_VARIATION_SEARCH_POLICY_ID\' "$lib" || fail "missing public identity export"\n',
    'grep -q \'PRINCIPAL_VARIATION_SEARCH_POLICY_ID\' "$lib" || fail "missing public identity export"\n'
    'grep -q \'principal_variation_search_candidate\' "$evidence" || fail "missing PVS evidence identity"\n'
    'grep -q \'pvs_zero_window_searches\' "$evidence" || fail "missing PVS evidence counters"\n'
    'grep -q \'activated\\\\tfalse\' "$evidence" || fail "evidence does not preserve inactivity"\n',
    "audit evidence checks",
)
audit_path.write_text(audit, encoding="utf-8")

Path(".github/s2_7_evidence_bootstrap.py").unlink()
