from pathlib import Path
import sys

root = Path(sys.argv[1])


def replace_once(path: str, old: str, new: str, label: str) -> None:
    target = root / path
    content = target.read_text(encoding="utf-8")
    count = content.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one occurrence, found {count}")
    target.write_text(content.replace(old, new, 1), encoding="utf-8")


replace_once(
    "crates/chess-search/src/iterative_deepening.rs",
    """        let iteration = search_completed_iteration(
            position,
            history,
            depth,
            center,
            DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS,
            false,
            transposition_table,
        )?;
""",
    """        let iteration = search_completed_iteration(
            position,
            history,
            depth,
            center,
            DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS,
            transposition_table,
        )?;
""",
    "baseline iterative wrapper call",
)

replace_once(
    "crates/chess-search/src/alpha_beta.rs",
    """                transposition_table: Some(&mut table),
                cancellation: &mut cancellation,
""",
    """                transposition_table: Some(&mut table),
                check_extension_enabled: false,
                cancellation: &mut cancellation,
""",
    "test TT context policy",
)

replace_once(
    "crates/chess-search/src/principal_variation.rs",
    "pub(crate) fn reconstruct_principal_variation(\n",
    "#[cfg(test)]\npub(crate) fn reconstruct_principal_variation(\n",
    "test-only legacy PV helper",
)

iterative_path = "crates/chess-search/src/iterative_deepening.rs"
replace_once(
    iterative_path,
    "fn search_completed_iteration(\n",
    """#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct IterationSearchPolicy {
    half_width_centipawns: i32,
    check_extension_enabled: bool,
}

fn search_completed_iteration(
""",
    "iteration policy declaration",
)

replace_once(
    iterative_path,
    """        half_width_centipawns,
        false,
        transposition_table,
        &mut cancellation,
""",
    """        IterationSearchPolicy {
            half_width_centipawns,
            check_extension_enabled: false,
        },
        transposition_table,
        &mut cancellation,
""",
    "baseline iteration policy",
)

replace_once(
    iterative_path,
    """            DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS,
            check_extension_enabled,
            transposition_table,
            &mut controller,
""",
    """            IterationSearchPolicy {
                half_width_centipawns: DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS,
                check_extension_enabled,
            },
            transposition_table,
            &mut controller,
""",
    "limited iteration policy",
)

replace_once(
    iterative_path,
    """    center: Option<Score>,
    half_width_centipawns: i32,
    check_extension_enabled: bool,
    transposition_table: &mut TranspositionTable,
""",
    """    center: Option<Score>,
    policy: IterationSearchPolicy,
    transposition_table: &mut TranspositionTable,
""",
    "iteration helper signature",
)

replace_once(
    iterative_path,
    "aspiration_window(score, half_width_centipawns)",
    "aspiration_window(score, policy.half_width_centipawns)",
    "aspiration policy width",
)

replace_once(
    iterative_path,
    """        initial_window,
        check_extension_enabled,
        transposition_table,
""",
    """        initial_window,
        policy.check_extension_enabled,
        transposition_table,
""",
    "initial attempt policy",
)

replace_once(
    iterative_path,
    """                AlphaBetaWindow::full(),
                check_extension_enabled,
                transposition_table,
""",
    """                AlphaBetaWindow::full(),
                policy.check_extension_enabled,
                transposition_table,
""",
    "retry attempt policy",
)

replace_once(
    iterative_path,
    "        !check_extension_enabled,\n",
    "        !policy.check_extension_enabled,\n",
    "PV table policy",
)

print("Task 16.7 generated wiring corrected")
