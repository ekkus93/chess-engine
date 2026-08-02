from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"{path}: expected one replacement target, found {count}: {old[:120]!r}"
        )
    write(path, text.replace(old, new, 1))


tracker = "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
replace_once(
    tracker,
    "| 13 | **Active** — reference search and alpha-beta. |\n| 14–24 | **Not started**. |",
    "| 13 | **Active** — reference search and alpha-beta; implementation remains not started pending review-fix closure. |\n| 14–24 | **Not started**. |",
)
replace_once(
    tracker,
    "## 25.1 CI\n- [x] Linux rustfmt/check/Clippy/tests/rustdoc/debug/release.\n- [x] Python validation preserved separately.\n- [x] Exact-SHA status publisher and deterministic dispatcher.\n- [ ] Release tests/perft, AArch64, Android, JNI, Miri, sanitizer, fuzz, nightly perft, and scheduled strength.",
    "## 25.1 CI\n- [x] Linux rustfmt/check/Clippy/tests/rustdoc/debug/release.\n- [x] Python validation preserved separately.\n- [x] Exact-SHA status publisher and deterministic dispatcher.\n- [x] Release depth-four authoritative perft in permanent CI.\n- [x] Scheduled/manual depth-five authoritative perft.\n- [ ] AArch64 compile CI.\n- [ ] Android compile and JNI CI.\n- [ ] Miri, sanitizer, and fuzz gates.\n- [ ] Scheduled strength testing.",
)
replace_once(
    tracker,
    "- [ ] Draws, hashing, search, TT, evaluation, ABI/JNI, differential perft/fuzz, self-play, and tuning.",
    "- [x] Zobrist hashing and repetition identity.\n- [x] Game history and draw semantics.\n- [x] Authoritative perft and differential validation.\n- [x] Baseline evaluator and trace.\n- [ ] Search and transposition table.\n- [ ] ABI/JNI.\n- [ ] Differential fuzzing.\n- [ ] Self-play and tuning.",
)
replace_once(
    tracker,
    "- [x] Full Task 0/1 validation command, committed lockfile, ignored targets/worktrees.\n- [ ] Bootstrap, fast validation, perft CLI, UCI, Android, self-play, and tuning commands.\n- [ ] Versioned schema/fixture/generated-artifact policy.\n- [ ] Task 25 gate.",
    "- [x] Full Task 0/1 validation command, committed lockfile, ignored targets/worktrees.\n- [x] Perft, divide, legal, play, suite, and oracle commands.\n- [x] Evaluation trace, evaluation benchmark, weight export, and weight validation commands.\n- [ ] General bootstrap and fast-validation wrapper commands.\n- [ ] UCI, Android, self-play, and tuning commands.\n- [ ] Versioned schema/fixture/generated-artifact policy across all future artifacts.\n- [ ] Task 25 gate.",
)
replace_once(
    tracker,
    "## Immediate next operations\n\n1. Begin Task 9 deterministic Zobrist tables and versioned key contract.\n2. Implement authoritative full-position hash recomputation.\n3. Wire incremental key updates through every Task 8 make/unmake path.\n4. Canonicalize en-passant repetition identity based on whether a legal en-passant capture exists.\n5. Compare incremental and recomputed keys after every make/unmake across curated and randomized sequences.",
    "## Immediate next operations\n\n1. Complete and validate `docs/RUST_ENGINE_REVIEW_FIX_TODO_2026-08-02.md`.\n2. Confirm the search-safe legal-token API, game root replacement, divide timing, FEN policy, and tracker cleanup on an exact green SHA.\n3. Begin Task 13 reference search only after the review-fix gate passes.\n4. Implement no-prune reference search before alpha-beta.\n5. Validate terminal scoring, line repetition, and exact search immutability before Task 13 completion.",
)

status = "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"
replace_once(
    status,
    "**Updated:** 2026-08-01  \n**Branch:** `rust-engine`  \n**Authoritative TODO:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  \n**Current phase:** Task 13 reference search and alpha-beta active; implementation not started",
    "**Updated:** 2026-08-02  \n**Branch:** `rust-engine`  \n**Authoritative TODO:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  \n**Current phase:** Pre-Task-13 review-fix implementation candidate; Task 13 search remains not started",
)
replace_once(
    status,
    "## Task 13 active scope\n",
    "## Pre-Task-13 review-fix implementation candidate\n\nImplemented pending exact-head closure validation:\n\n- opaque source-bound legal-move tokens usable by `chess-search`;\n- non-mutating stale/wrong-origin token rejection;\n- explicit `Game::reset_to_starting` and `Game::set_position`;\n- stable `elapsed_nanos` divide output;\n- explicit strict structural analysis-FEN policy and safety tests;\n- corrected Task 25 coverage and Task 13 next-operation text.\n\nTask 13 itself remains not started. Completion evidence will be recorded only after the strict permanent CI gate passes on the final clean SHA.\n\n## Task 13 active scope\n",
)

spec = "docs/RUST_ENGINE_REVIEW_FIX_SPEC_2026-08-02.md"
replace_once(
    spec,
    "**Status:** Ready for implementation",
    "**Status:** Implemented; exact-head validation pending",
)

todo = "docs/RUST_ENGINE_REVIEW_FIX_TODO_2026-08-02.md"
text = read(todo)
text = text.replace(
    "**Status:** Not started",
    "**Status:** Implemented; exact-head validation pending",
    1,
)
prefix, separator, suffix = text.partition(
    "# RF-006: Review-fix validation and closure evidence"
)
if not separator:
    raise SystemExit("review TODO RF-006 marker missing")
prefix = prefix.replace("- [ ]", "- [x]")
text = prefix + separator + suffix
for item in [
    "- [ ] RF-000 baseline confirmation complete.",
    "- [ ] RF-001 search-safe generated legal move API complete.",
    "- [ ] RF-002 explicit `Game` reset/set-position APIs complete.",
    "- [ ] RF-003 divide elapsed-time output complete.",
    "- [ ] RF-004 FEN policy documentation/tests complete.",
    "- [ ] RF-005 live TODO and Task 25 cleanup complete.",
    "- [ ] Task 13 remains active/not started.",
    "- [ ] No Tasks 14–27 are marked complete by this pass.",
]:
    text = text.replace(item, item.replace("[ ]", "[x]"), 1)
text = text.replace(
    "# RF-006: Review-fix validation and closure evidence",
    "## Implementation notes\n\n"
    "- Starting code/documentation SHA: `52377d09b713541044e24c8e3559be3f12002cc1`.\n"
    "- Control-only workflow add/remove commits did not change Rust source or review documents.\n"
    "- All six reviewed issues remained valid at baseline inspection.\n"
    "- RF-001 through RF-005 are implemented in the candidate tree; RF-006 remains open until exact-head permanent CI and documentation closure complete.\n\n"
    "---\n\n"
    "# RF-006: Review-fix validation and closure evidence",
    1,
)
write(todo, text)
