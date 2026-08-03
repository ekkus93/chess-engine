from pathlib import Path

IMPLEMENTATION_SHA = "d1c4a9195acfc63dc2f9af52531c4ba01e9a2dc9"
VALIDATION_RUN = "30836228692"
VALIDATION_JOB = "91761964507"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one occurrence, found {count}")
    return text.replace(old, new, 1)


def update_task_definitions() -> None:
    path = Path("docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md")
    text = path.read_text()
    start = "## 18.2 C ABI\n"
    end = "## 18.3 C ABI tests\n"
    start_index = text.index(start)
    end_index = text.index(end, start_index)
    section = text[start_index:end_index]
    open_count = section.count("- [ ]")
    if open_count != 10:
        raise SystemExit(f"Task 18.2 definitions: expected 10 open boxes, found {open_count}")
    section = section.replace("- [ ]", "- [x]")
    path.write_text(text[:start_index] + section + text[end_index:])


def task18_2_evidence() -> str:
    return f"""

### Task 18.2 completion evidence

- Implementation: `crates/chess-ffi/src/c_abi/types.rs`, `registry.rs`, `functions.rs`, and `mod.rs`, exported through `crates/chess-ffi/src/lib.rs`.
- Canonical C declarations: `crates/chess-ffi/include/chess_engine.h`; complete contract: `docs/RUST_C_ABI.md`.
- `chess-ffi` now produces `rlib`, `cdylib`, and `staticlib` artifacts without adding a dependency.
- Engine, cancellation, and output-allocation identities are opaque tagged 64-bit tokens backed by synchronized registries. Zero, stale, fabricated, destroyed, and wrong-type tokens fail before object access.
- Versioned `repr(C)` records require the exact ABI version and exact current record size. Rust engine, search, enum, vector, string, and error layouts never cross the boundary.
- FEN and move inputs use explicit `(pointer, length)` UTF-8 ranges with no `strlen`, NUL requirement, or out-of-range scanning.
- Structured result codes distinguish pointer, handle, UTF-8, ABI, rules, search, allocation, buffer, internal, and contained-panic failures. Error text is thread-local and retrieved through an owned ABI buffer.
- Output bytes are held in an allocation registry. Free operations verify token, pointer, and length; search-result cleanup validates all three owned buffers before freeing any.
- Search is synchronous and mutex-serializes one engine. A separate request-local cancellation token remains callable from another thread, and destroyed external tokens cannot invalidate an in-flight cloned reference.
- Every exported `extern \"C\"` symbol enters a `catch_unwind` boundary. The only unsafe operations are documented C pointer reads, writes, and explicit-length slice construction inside the adapter.
- Six focused Rust tests cover the shared panic boundary plus ABI versioning, construction and destruction, explicit UTF-8 position/move/status flows, typed search results, preset cancellation, stale and wrong-type handles, buffer lifecycle rejection, null pointers, and fail-closed versioned records.
- Implementation SHA: `{IMPLEMENTATION_SHA}`.
- Permanent validation: run `{VALIDATION_RUN}`, job `{VALIDATION_JOB}`.
- Results: six focused C ABI tests and 291 executed non-doc Rust tests passed; rustfmt, committed lockfile, locked all-target/all-feature compilation, strict Clippy without suppressions, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and the independent differential oracle all passed.
- Differential validation covered 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Validation correction was limited to canonical rustfmt output. No ABI behavior, safety policy, lower-layer production code, or validation gate was weakened.
- Task 18.2 is complete. Task 18.3 native C ABI lifecycle, active-cancellation, buffer, and injected-panic tests are next.
"""


def update_authoritative_todo() -> None:
    path = Path("docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md")
    text = path.read_text()
    text = replace_once(
        text,
        "- [ ] 18.2 C ABI.",
        "- [x] 18.2 C ABI.",
        "Task 18.2 checkbox",
    )
    if "### Task 18.2 completion evidence" in text:
        raise SystemExit("Task 18.2 evidence already exists")
    marker = "\n# Task 19: Opening book — NOT STARTED"
    text = replace_once(text, marker, task18_2_evidence() + marker, "Task 19 boundary")

    old_operations = """## Immediate next operations

1. Implement Task 18.2 as a narrow C ABI over the completed safe Rust facade.
2. Add opaque engine handles, ABI version query, and explicit create/destroy operations.
3. Define UTF-8 input lengths, structured result codes, and retrievable error messages.
4. Define output-buffer ownership and the matching free contract.
5. Reject null and invalid handles without exposing Rust layouts.
6. Contain every externally callable boundary with `catch_unwind`."""
    new_operations = """## Immediate next operations

1. Implement Task 18.3 as a native C or Rust-through-ABI smoke harness against the built library boundary.
2. Exercise repeated create/destroy and stale-handle rejection.
3. Cover invalid pointers, UTF-8, FEN, move, record-version, and result-code paths.
4. Run active infinite search on a worker thread and cancel it through the C token from another thread.
5. Prove buffer and search-result allocation/free lifecycles, including double-free rejection.
6. Add an exported test-only injected fault and prove panic containment without unwinding across C."""
    text = replace_once(text, old_operations, new_operations, "immediate operations")
    path.write_text(text)


def update_contract() -> None:
    path = Path("docs/RUST_C_ABI.md")
    text = path.read_text()
    if "## Completion evidence" in text:
        raise SystemExit("C ABI completion evidence already exists")
    marker = "\nTask 18.3 adds the native C/Rust-through-ABI lifecycle, active cancellation, buffer, and injected-panic smoke harness. Task 18.4 will wrap this ABI from JNI without exposing Rust layouts to Kotlin.\n"
    evidence = f"""

## Completion evidence

Implementation SHA: `{IMPLEMENTATION_SHA}`.

Permanent implementation validation:

- PR: `#232`;
- workflow run: `{VALIDATION_RUN}`;
- job: `{VALIDATION_JOB}`;
- one shared-boundary panic-containment unit test and five public Rust-through-ABI contract tests passed;
- 291 executed non-doc Rust tests passed across the workspace;
- formatting, committed lockfile, locked all-target/all-feature compilation, strict Clippy with warnings denied and no lint suppression, authoritative release depth-four perft, rustdoc with warnings denied, and debug/release workspace builds passed;
- differential validation passed over 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.

The first implementation validation found only canonical rustfmt differences. Applying exact formatter output corrected the tree without changing ABI behavior, safety policy, tests, or lower-layer production code.

Task 18.2 is complete. Task 18.3 owns the native lifecycle, active cross-thread cancellation, complete buffer lifecycle, and exported injected-panic smoke harness.
"""
    text = replace_once(text, marker, evidence + marker, "Task 18.3 contract boundary")
    path.write_text(text)


def update_ralph_status() -> None:
    path = Path("docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md")
    text = path.read_text()
    text = replace_once(
        text,
        "**Current phase:** Task 18.1 safe Rust facade complete; Task 18.2 C ABI is next",
        "**Current phase:** Task 18.2 stable C ABI complete; Task 18.3 C ABI tests are next",
        "Ralph current phase",
    )
    row_marker = "| 18.1 | `fc375ce7c35a9b8e82c83c8a0ac54e23a60986be` | `30832682431` / `91750223690` | safe stateful facade, transactional positions, legal UCI moves, immutable synchronous search, cross-thread cancellation, identities, and ownership/thread-safety contract; 285 Rust tests green |"
    row = (
        row_marker
        + "\n| 18.2 | `d1c4a9195acfc63dc2f9af52531c4ba01e9a2dc9` | `30836228692` / `91761964507` | versioned opaque-token C ABI, explicit UTF-8 lengths, typed errors, verified owned buffers, synchronous search/cancellation boundary, and panic containment; 291 Rust tests green |"
    )
    text = replace_once(text, row_marker, row, "Ralph Task 18.2 table row")

    completion_marker = "Task 18.1 is complete. Task 18.2 C ABI work is next.\n"
    if "## Task 18.2 completion" in text:
        raise SystemExit("Ralph Task 18.2 completion already exists")
    completion = f"""

## Task 18.2 completion

Implemented and validated:

- stable ABI version `1` and exact-size versioned C records;
- opaque tagged engine and cancellation tokens with synchronized registry ownership;
- explicit create, destroy, reset, position, FEN, legal move, move application, status, weight identity, search, and cancellation operations;
- explicit-length UTF-8 input with no NUL dependency;
- structured result codes and thread-local retrievable errors;
- registry-owned immutable output bytes with verified single-free contracts;
- typed search snapshots with move/PV buffers, score, depth, nodes, time, termination, and fallback;
- null, stale, destroyed, fabricated, and wrong-type handle rejection without dereferencing caller tokens;
- `catch_unwind` containment at every exported boundary;
- `rlib`, `cdylib`, and `staticlib` products plus `crates/chess-ffi/include/chess_engine.h`;
- `docs/RUST_C_ABI.md`.

Evidence:

- implementation SHA: `{IMPLEMENTATION_SHA}`;
- permanent CI run/job: `{VALIDATION_RUN}` / `{VALIDATION_JOB}`;
- six focused C ABI tests passed;
- 291 executed non-doc Rust tests passed;
- the complete permanent workspace gate and independent differential oracle passed without lint suppression or lower-layer production changes.

Task 18.2 is complete. Task 18.3 C ABI tests are next.
"""
    text = replace_once(
        text,
        completion_marker,
        completion_marker + completion,
        "Ralph Task 18.1 completion boundary",
    )
    path.write_text(text)


def main() -> None:
    update_task_definitions()
    update_authoritative_todo()
    update_contract()
    update_ralph_status()


if __name__ == "__main__":
    main()
