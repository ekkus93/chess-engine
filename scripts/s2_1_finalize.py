import re
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"{path}: expected one replacement, found {count}: {old[:100]!r}"
        )
    file.write_text(text.replace(old, new, 1))


replace_once(
    "crates/chess-tools/src/policy_io.rs",
    '            "{FORMAT_MARKER}\\n",',
    '            "{}\\n",',
)
replace_once(
    "crates/chess-tools/src/policy_io.rs",
    "        ),\n        set.schema_version,",
    "        ),\n        FORMAT_MARKER,\n        set.schema_version,",
)
replace_once(
    "crates/chess-tools/src/policy_io.rs",
    "const FIELD_COUNT: usize = 11;",
    "const FIELD_COUNT: usize = 12;",
)
replace_once(
    "crates/chess-search/src/search_policy.rs",
    "0xcbf_29ce4_8422_2325",
    "0xcbf2_9ce4_8422_2325",
)

replace_once(
    "crates/chess-search/tests/search_policy_identity.rs",
    'SearchLimits::depth(4).expect("depth limit validates")',
    "SearchLimits::new().with_depth(4)",
)
replace_once(
    "crates/chess-search/tests/search_policy_identity.rs",
    'SearchLimits::depth(2).expect("depth limit validates")',
    "SearchLimits::new().with_depth(2)",
)
replace_once(
    "crates/chess-search/tests/search_policy_identity.rs",
    "        limits,\n        &mut default_table,",
    "        limits.clone(),\n        &mut default_table,",
)

alpha_path = Path("crates/chess-search/src/alpha_beta.rs")
alpha_text = alpha_path.read_text()
pattern = re.compile(
    r"(?P<indent>^[ ]+)check_extension_enabled: false,\n(?P=indent)weights:",
    flags=re.MULTILINE,
)
replacement = (
    r"\g<indent>check_extension_enabled: false,\n"
    r"\g<indent>maximum_check_extensions_per_line: crate::MAX_CHECK_EXTENSIONS_PER_LINE,\n"
    r"\g<indent>maximum_quiescence_ply: crate::MAX_QUIESCENCE_PLY,\n"
    r"\g<indent>weights:"
)
alpha_text, count = pattern.subn(replacement, alpha_text)
if count != 3:
    raise SystemExit(f"alpha_beta.rs: expected three internal contexts, found {count}")
alpha_path.write_text(alpha_text)

iterative_path = Path("crates/chess-search/src/iterative_deepening.rs")
iterative_text = iterative_path.read_text()
marker = (
    "fn iterative_deepening_search_with_limits_and_clock_and_observer_and_weights"
    "<Clock, Observer>(\n"
)
execution_struct = """#[derive(Clone, Copy)]
struct IterativeDeepeningExecutionPolicy<'a> {
    search_policy: &'a SearchPolicy,
    weights: &'a EvaluationWeights,
}

"""
if iterative_text.count(marker) != 1:
    raise SystemExit("iterative_deepening.rs: execution function marker mismatch")
iterative_text = iterative_text.replace(marker, execution_struct + marker, 1)

old = """        WallClock::start(),
        &search_policy.policy,
        weights,
        |_| {},
"""
new = """        WallClock::start(),
        IterativeDeepeningExecutionPolicy {
            search_policy: &search_policy.policy,
            weights,
        },
        |_| {},
"""
if iterative_text.count(old) != 1:
    raise SystemExit("iterative_deepening.rs: explicit-policy call mismatch")
iterative_text = iterative_text.replace(old, new, 1)

old = """        clock,
        &SearchPolicy::V0_1,
        &EvaluationWeights::DEFAULT,
        observer,
"""
new = """        clock,
        IterativeDeepeningExecutionPolicy {
            search_policy: &SearchPolicy::V0_1,
            weights: &EvaluationWeights::DEFAULT,
        },
        observer,
"""
if iterative_text.count(old) != 1:
    raise SystemExit("iterative_deepening.rs: default-policy call mismatch")
iterative_text = iterative_text.replace(old, new, 1)

old = """    transposition_table: &mut TranspositionTable,
    clock: Clock,
    search_policy: &SearchPolicy,
    weights: &EvaluationWeights,
    mut observer: Observer,
"""
new = """    transposition_table: &mut TranspositionTable,
    clock: Clock,
    execution_policy: IterativeDeepeningExecutionPolicy<'_>,
    mut observer: Observer,
"""
if iterative_text.count(old) != 1:
    raise SystemExit("iterative_deepening.rs: execution signature mismatch")
iterative_text = iterative_text.replace(old, new, 1)

old = """{
    let check_extension_enabled = limits.check_extension_enabled()
        && search_policy.maximum_check_extensions_per_line() > 0;
"""
new = """{
    let IterativeDeepeningExecutionPolicy {
        search_policy,
        weights,
    } = execution_policy;
    let check_extension_enabled = limits.check_extension_enabled()
        && search_policy.maximum_check_extensions_per_line() > 0;
"""
if iterative_text.count(old) != 1:
    raise SystemExit("iterative_deepening.rs: execution body mismatch")
iterative_path.write_text(iterative_text.replace(old, new, 1))
