from pathlib import Path

IMPLEMENTATION_SHA = "fc375ce7c35a9b8e82c83c8a0ac54e23a60986be"
VALIDATION_RUN = "30832682431"
VALIDATION_JOB = "91750223690"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one occurrence, found {count}")
    return text.replace(old, new, 1)


def update_task_definitions() -> None:
    path = Path("docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md")
    text = path.read_text()
    start = "## 18.1 Safe Rust facade\n"
    end = "## 18.2 C ABI\n"
    start_index = text.index(start)
    end_index = text.index(end, start_index)
    section = text[start_index:end_index]
    open_count = section.count("- [ ]")
    if open_count != 11:
        raise SystemExit(f"Task 18.1 definitions: expected 11 open boxes, found {open_count}")
    section = section.replace("- [ ]", "- [x]")
    path.write_text(text[:start_index] + section + text[end_index:])


def update_authoritative_todo() -> None:
    path = Path("docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md")
    text = path.read_text()
    text = replace_once(
        text,
        "# Task 18: Safe API, C ABI, and JNI — NOT STARTED",
        "# Task 18: Safe API, C ABI, and JNI — IN PROGRESS",
        "Task 18 heading",
    )
    text = replace_once(
        text,
        "- [ ] 18.1 Rust facade.",
        "- [x] 18.1 Rust facade.",
        "Task 18.1 checkbox",
    )

    marker = "\n# Task 19: Opening book — NOT STARTED"
    if "### Task 18.1 completion evidence" in text:
        raise SystemExit("Task 18.1 evidence already exists")
    evidence = f"""

### Task 18.1 completion evidence

- Implementation: `crates/chess-ffi/src/safe.rs`, public exports in `crates/chess-ffi/src/lib.rs`, direct `chess-core` and `chess-search` dependencies, and `crates/chess-ffi/tests/safe_facade.rs`.
- Public facade: `EngineConfig`, `Engine`, `SearchRequest`, `SearchCancellationHandle`, `EvaluationWeightIdentity`, `EngineError`, and `ENGINE_VERSION`.
- `Engine` owns one history-aware `Game` and one fixed-capacity transposition table. It borrows no caller memory, opens no files, starts no threads, and uses no process-global mutable state.
- Position replacement is strict and transactional. Canonical six-field FEN, deterministic legal UCI moves, legal move application, terminal rejection, and authoritative game status are exposed without duplicating chess rules.
- Search is synchronous and runs on cloned position/history state, preserving the played game on success, cancellation, and errors. Finite depth/node/time requests and explicit infinite-search cancellation use the existing typed search contract.
- Cancellation is request-local and clone-shareable across threads. `Engine: Send` and `SearchCancellationHandle: Send + Sync` are compiler-checked; no manual thread-safety implementation exists.
- Version and evaluator identity report the package version and the validated built-in baseline weight schema, identifier, and checksum. Caller-supplied weights are intentionally not claimed before the complete search path supports them.
- The safe facade module forbids unsafe code. Task 18.2 owns the separate narrow C ABI boundary.
- Contract documentation: `docs/RUST_SAFE_ENGINE_FACADE.md`.
- Implementation SHA: `{IMPLEMENTATION_SHA}`.
- Permanent validation: run `{VALIDATION_RUN}`, job `{VALIDATION_JOB}`.
- Results: nine focused facade tests and 285 executed non-doc Rust tests passed; rustfmt, committed lockfile, locked all-target/all-feature compilation, strict Clippy without suppressions, release depth-four perft, rustdoc with warnings denied, debug/release builds, and the independent differential oracle all passed.
- Differential validation covered 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Validation corrections were limited to exact rustfmt output and removing invalid `const fn` qualifiers from five fluent request builders. No semantics, safety policy, lower-layer production code, or gate was weakened.
- Task 18.1 is complete. Task 18.2 C ABI work is next.
"""
    text = replace_once(text, marker, evidence + marker, "Task 19 boundary")

    old_operations = """## Immediate next operations

1. Implement Task 17.5 process-level UCI integration tests over the real binary.
2. Cover handshake, start-position and six-field FEN setup, illegal move handling, and fixed-depth legal best move.
3. Cover mate and stalemate `bestmove 0000` behavior.
4. Prove `stop` interrupts an active search and still emits exactly one final move.
5. Prove `quit` and EOF stop and join cleanly without stale final output.
6. Prove independent sessions do not leak stdout, worker state, or mutable search control."""
    new_operations = """## Immediate next operations

1. Implement Task 18.2 as a narrow C ABI over the completed safe Rust facade.
2. Add opaque engine handles, ABI version query, and explicit create/destroy operations.
3. Define UTF-8 input lengths, structured result codes, and retrievable error messages.
4. Define output-buffer ownership and the matching free contract.
5. Reject null and invalid handles without exposing Rust layouts.
6. Contain every externally callable boundary with `catch_unwind`."""
    text = replace_once(text, old_operations, new_operations, "immediate operations")
    path.write_text(text)


def update_ralph_status() -> None:
    path = Path("docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md")
    text = path.read_text()
    text = replace_once(
        text,
        "**Current phase:** Task 17 complete; Task 18.1 Rust facade is next",
        "**Current phase:** Task 18.1 safe Rust facade complete; Task 18.2 C ABI is next",
        "Ralph current phase",
    )

    row_marker = "| 17.5 / 17 gate | `67b6c97a476e1323bc2bd96ecf14870fc2ed3139` | `30828959858` / `91737751003` | seven real subprocess workflows, bounded stop/quit, legal best moves, terminal null moves, and concurrent-session isolation; complete permanent gate green |"
    new_row = f"| 18.1 | `{IMPLEMENTATION_SHA}` | `{VALIDATION_RUN}` / `{VALIDATION_JOB}` | safe stateful facade, transactional positions, legal UCI moves, immutable synchronous search, cross-thread cancellation, identities, and ownership/thread-safety contract; 285 Rust tests green |"
    text = replace_once(text, row_marker, row_marker + "\n" + new_row, "Task 18.1 status row")

    section_marker = "\n## Task 12 completion"
    if "## Task 18.1 completion" in text:
        raise SystemExit("Task 18.1 Ralph section already exists")
    section = f"""

## Task 18.1 completion

Implemented and validated:

- `EngineConfig` with explicit fixed transposition-table capacity;
- stateful `Engine::new` owning one `Game` and one bounded table;
- transactional set/reset position and canonical FEN retrieval;
- deterministic legal UCI moves, legal move application, and game status;
- synchronous limit-controlled search on detached position/history state;
- clone-shareable request-local cancellation, including active infinite-search cancellation from another thread;
- engine version and validated baseline evaluation-weight identity;
- typed facade errors and explicit allocation failures;
- ownership and thread-safety rustdoc with compiler-derived `Send`/`Sync` assertions;
- a safe module that forbids unsafe code;
- `docs/RUST_SAFE_ENGINE_FACADE.md`.

Evidence:

- implementation SHA: `{IMPLEMENTATION_SHA}`;
- permanent CI run/job: `{VALIDATION_RUN}` / `{VALIDATION_JOB}`;
- nine focused safe-facade tests passed;
- 285 executed non-doc Rust tests passed;
- the complete permanent workspace gate and independent differential oracle passed without lint suppression or lower-layer production changes.

Task 18.1 is complete. Task 18.2 C ABI work is next.
"""
    text = replace_once(text, section_marker, section + section_marker, "Task 12 boundary")
    path.write_text(text)


def main() -> None:
    update_task_definitions()
    update_authoritative_todo()
    update_ralph_status()


if __name__ == "__main__":
    main()
