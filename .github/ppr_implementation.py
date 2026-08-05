from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def replace_once(text: str, old: str, new: str, path: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one occurrence, found {count}: {old!r}")
    return text.replace(old, new, 1)


# PPR-1: convert contradictory generated candidates from silent skips to typed failures.
legal_path = "crates/chess-core/src/position/legal.rs"
legal = read(legal_path)
legal = replace_once(
    legal,
    """impl Position {
    /// Generates every legal move for the current side to move.
""",
    """impl Position {
    fn validate_generated_candidate(
        &self,
        current: Move,
        moving_side: Color,
    ) -> Result<(), LegalMoveError> {
        let moving_piece = self
            .piece_at(current.source())
            .ok_or(LegalMoveError::InvalidGeneratedMove { current })?;
        if moving_piece.color != moving_side
            || !self.generated_move_matches_state(current, moving_piece)
        {
            return Err(LegalMoveError::InvalidGeneratedMove { current });
        }
        Ok(())
    }

    /// Generates every legal move for the current side to move.
""",
    legal_path,
)
legal = replace_once(
    legal,
    """        for current in pseudo_legal.iter() {
            let Some(moving_piece) = self.piece_at(current.source()) else {
                continue;
            };
            if moving_piece.color != moving_side
                || !self.generated_move_matches_state(current, moving_piece)
            {
                continue;
            }
""",
    """        for current in pseudo_legal.iter() {
            self.validate_generated_candidate(current, moving_side)?;
""",
    legal_path,
)
write(legal_path, legal)

tests_path = "crates/chess-core/src/position/legal_tests.rs"
tests = read(tests_path)
tests = replace_once(
    tests,
    "use crate::{Move, MoveKind, PieceKind, Position, Square};",
    "use crate::{Color, Move, MoveKind, PieceKind, Position, Square};",
    tests_path,
)
test_block = r'''
#[test]
fn empty_source_generated_candidate_fails_loudly() {
    let position = Position::starting();
    let current = Move::new(square("a3"), square("a4"), MoveKind::Quiet);
    assert_eq!(
        position.validate_generated_candidate(current, Color::White),
        Err(LegalMoveError::InvalidGeneratedMove { current })
    );
}

#[test]
fn wrong_side_generated_candidate_fails_loudly() {
    let position = Position::starting();
    let current = Move::new(square("a7"), square("a6"), MoveKind::Quiet);
    assert_eq!(
        position.validate_generated_candidate(current, Color::White),
        Err(LegalMoveError::InvalidGeneratedMove { current })
    );
}

#[test]
fn encoded_state_contradiction_fails_loudly() {
    let position = Position::starting();
    let current = Move::new(square("e2"), square("e3"), MoveKind::Capture);
    assert_eq!(
        position.validate_generated_candidate(current, Color::White),
        Err(LegalMoveError::InvalidGeneratedMove { current })
    );
}

'''
tests = replace_once(
    tests,
    "#[test]\nfn starting_position_perft_and_divide_are_exact_and_restore_state() {",
    test_block + "#[test]\nfn starting_position_perft_and_divide_are_exact_and_restore_state() {",
    tests_path,
)
write(tests_path, tests)

# PPR-2: normalize the live Task 21 detailed heading only.
tracker_path = "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
tracker = read(tracker_path)
tracker, replacements = re.subn(
    r"(?m)^(# Task 21: .+?) — IN PROGRESS$",
    r"\1 — COMPLETE",
    tracker,
    count=1,
)
if replacements != 1:
    raise RuntimeError(f"{tracker_path}: stale Task 21 heading was not found exactly once")
write(tracker_path, tracker)

# PPR-4: terminology-only clarification; parser behavior stays unchanged.
fen_path = "crates/chess-core/src/position/fen.rs"
fen = read(fen_path)
fen = replace_once(
    fen,
    "/// Strict playable FEN does not permit pawns on rank one or rank eight.",
    "/// Strict structural analysis FEN does not permit pawns on rank one or rank eight.",
    fen_path,
)
fen = replace_once(
    fen,
    "/// Materialized position failed playable-position validation.",
    "/// Materialized analysis position failed structural invariant validation.",
    fen_path,
)
fen = replace_once(
    fen,
    "    /// Parses a strict, playable six-field FEN.",
    """    /// Parses strict structural six-field FEN for safe analysis positions.
    ///
    /// Acceptance verifies syntax and internal invariants; it is not proof that
    /// the position is reachable from the standard initial position.""",
    fen_path,
)
write(fen_path, fen)

fen_doc_path = "docs/RUST_FEN_AND_UCI_NOTATION.md"
fen_doc = read(fen_doc_path)
fen_doc = replace_once(
    fen_doc,
    """Legal move generation remains fail-safe for these states: it never permits king capture, refuses castling when required pieces or safety conditions are absent, and filters moves against king attack. Zobrist repetition identity includes an en-passant file only when a legal en-passant capture exists, so accepted non-capturable targets do not create a false repetition distinction. The committed differential corpus remains restricted to positions accepted as valid by the pinned independent oracle.
""",
    """Structural acceptance is not certification of legal game reachability. Every accepted analysis position must still satisfy the engine's internal representation invariants and remain a safe input to legal move generation. Legal move generation never permits king capture, refuses castling when required pieces or safety conditions are absent, and filters moves against king attack. Zobrist repetition identity includes an en-passant file only when a legal en-passant capture exists, so accepted non-capturable targets do not create a false repetition distinction. The committed differential corpus remains restricted to positions accepted as valid by the pinned independent oracle.
""",
    fen_doc_path,
)
write(fen_doc_path, fen_doc)

# PPR-3: create an explicit authority/index file without moving or deleting history.
active_todos = [
    "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md",
    "docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md",
    "docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_TODO_2026-08-04.md",
]
all_todos = sorted(
    path.relative_to(ROOT).as_posix()
    for path in (ROOT / "docs").glob("*TODO*.md")
    if path.is_file()
)
historical_todos = [path for path in all_todos if path not in active_todos]
missing_active = [path for path in active_todos if path not in all_todos]
if missing_active:
    raise RuntimeError(f"active TODO paths missing from inventory: {missing_active}")

index_lines = [
    "# TODO Authority and Legacy Index",
    "",
    "This file prevents historical planning documents from being mistaken for current implementation instructions.",
    "",
    "## Active TODO documents",
    "",
    "| Classification | Path | Authority |",
    "|---|---|---|",
    f"| Active Rust-port tracker | `{active_todos[0]}` | Authoritative record for the completed Rust-port program. |",
    f"| Active Rust-port task definitions | `{active_todos[1]}` | Detailed definitions and evidence for the completed Rust-port program. |",
    f"| Active post-port review follow-up | `{active_todos[2]}` | Current cleanup loop until its final gate is closed. |",
    "",
    "## Exhaustive classification rule",
    "",
    "Every other Markdown file directly under `docs/` whose filename contains `TODO` is a historical or legacy reference. Those files preserve implementation history, but they are not active instructions and must not override the three documents above.",
    "",
    f"Inventory captured on 2026-08-04: **{len(all_todos)} TODO-named files total; {len(active_todos)} active; {len(historical_todos)} historical.**",
    "",
    "## Historical TODO inventory",
    "",
]
index_lines.extend(f"- `{path}`" for path in historical_todos)
index_lines.extend(
    [
        "",
        "## Maintenance rule",
        "",
        "When a new active TODO is intentionally introduced, add it to the active table and update the permanent post-port review audit. Otherwise, a newly added `docs/*TODO*.md` file is historical by default and must be listed above.",
        "",
    ]
)
write("docs/LEGACY_TODO_INDEX.md", "\n".join(index_lines))

# PPR-5: add a permanent, stable-fact audit.
audit = r'''#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

tracker="docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
definitions="docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md"
followup="docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_TODO_2026-08-04.md"
legacy_index="docs/LEGACY_TODO_INDEX.md"
fen_doc="docs/RUST_FEN_AND_UCI_NOTATION.md"
fen_source="crates/chess-core/src/position/fen.rs"

for required in \
    "$tracker" \
    "$definitions" \
    "$followup" \
    "$legacy_index" \
    "$fen_doc" \
    "$fen_source"; do
    test -f "$required"
done

grep -Eq '^# Task 21: .* — COMPLETE$' "$tracker"
if grep -Eq '^# Task 21: .* — IN PROGRESS$' "$tracker"; then
    echo "stale Task 21 IN PROGRESS heading remains" >&2
    exit 1
fi
grep -Fq 'activated=false' "$tracker"
grep -Fqi 'baseline weights remain authoritative' "$tracker"
grep -Fqi 'separate strength change' "$tracker"

active_todos=(
    "$tracker"
    "$definitions"
    "$followup"
)
for active in "${active_todos[@]}"; do
    grep -Fq "\`$active\`" "$legacy_index"
done
grep -Fq 'Every other Markdown file directly under `docs/` whose filename contains `TODO` is a historical or legacy reference.' "$legacy_index"

while IFS= read -r todo_path; do
    case "$todo_path" in
        "$tracker"|"$definitions"|"$followup")
            ;;
        *)
            grep -Fq "\`$todo_path\`" "$legacy_index" || {
                echo "legacy TODO missing from index: $todo_path" >&2
                exit 1
            }
            ;;
    esac
done < <(find docs -maxdepth 1 -type f -name '*TODO*.md' -print | sort)

grep -Fq 'strict syntax and structural **analysis-position** parser' "$fen_doc"
grep -Fq 'Structural acceptance is not certification of legal game reachability.' "$fen_doc"
grep -Fq 'remain a safe input to legal move generation' "$fen_doc"
grep -Fq 'Parses strict structural six-field FEN for safe analysis positions.' "$fen_source"
grep -Fq 'it is not proof that' "$fen_source"

for temporary in \
    ".github/ppr_implementation.py" \
    ".github/workflows/ppr-implementation.yml" \
    ".github/ppr_close.py" \
    ".github/workflows/ppr-closure.yml"; do
    if test -e "$temporary"; then
        echo "temporary post-port helper remains: $temporary" >&2
        exit 1
    fi
done

bash scripts/task_26_v0_1_audit.sh
bash scripts/task_27_full_port_audit.sh

echo "post-port review fix audit passed"
'''
write("scripts/task_post_port_review_fix_audit.sh", audit)

ci_path = ".github/workflows/ci.yml"
ci = read(ci_path)
ci = replace_once(
    ci,
    "          test -f scripts/task_27_full_port_audit.sh\n",
    """          test -f scripts/task_27_full_port_audit.sh
          test -f scripts/task_post_port_review_fix_audit.sh
""",
    ci_path,
)
ci = replace_once(
    ci,
    """            scripts/task_26_uci_smoke.sh \\
            scripts/task_27_full_port_audit.sh
""",
    """            scripts/task_26_uci_smoke.sh \\
            scripts/task_27_full_port_audit.sh \\
            scripts/task_post_port_review_fix_audit.sh
""",
    ci_path,
)
ci = replace_once(
    ci,
    """      - name: Run Task 27 full-port audit
        run: bash scripts/task_27_full_port_audit.sh

""",
    """      - name: Run Task 27 full-port audit
        run: bash scripts/task_27_full_port_audit.sh

      - name: Run post-port review fix audit
        run: bash scripts/task_post_port_review_fix_audit.sh

""",
    ci_path,
)
write(ci_path, ci)

# Cross-link the spec and record the exact baseline/reproduced findings in the live follow-up.
spec_path = "docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_SPEC_2026-08-04.md"
spec = read(spec_path)
todo_link = "`docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_TODO_2026-08-04.md`"
if todo_link not in spec:
    spec = spec.rstrip() + (
        "\n\n## Implementation tracker\n\n"
        f"Execution and exact validation evidence are recorded in {todo_link}.\n"
    )
    write(spec_path, spec)

todo_path = "docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_TODO_2026-08-04.md"
todo = read(todo_path)
todo = replace_once(todo, "**Status:** Not started", "**Status:** In progress", todo_path)
record = """## Ralph-loop implementation record

- Baseline `master` SHA: `62a80700e4bec8e297bc8899e49496d3ae71ce47`.
- Reproduced findings: legal generation silently skipped three classes of contradictory pseudo-legal candidates; the Task 21 detailed heading was stale; legacy TODO authority was ambiguous; and FEN behavior was correct but two source-level labels overclaimed playable legality.
- Policy decisions: use typed internal failures, preserve ordinary legal filtering, create a non-disruptive legacy index, and make terminology-only FEN changes.
- Validation state: implementation committed; exact-SHA permanent CI evidence pending.
- Non-issues: the existing FEN parser already intentionally accepts structurally safe analysis positions without claiming game reachability, and existing king-safety/castling/en-passant tests already cover normal filtering.
- Deviations: none.

"""
todo = replace_once(todo, "## Status rules\n", record + "## Status rules\n", todo_path)
write(todo_path, todo)
