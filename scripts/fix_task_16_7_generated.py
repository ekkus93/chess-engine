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

print("Task 16.7 generated wiring corrected")
