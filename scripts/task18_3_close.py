from pathlib import Path

IMPLEMENTATION_SHA = "0789ac65590ccafb55b2b86b73873edfba1c7b55"
RUN_ID = "30841137129"
JOB_ID = "91778174797"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def update_definitions() -> None:
    path = Path("docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md")
    text = path.read_text()
    old = """## 18.3 C ABI tests

- [ ] Native C or Rust-through-ABI smoke harness.
- [ ] Repeated create/destroy.
- [ ] Invalid input.
- [ ] Search and cancellation.
- [ ] Buffer lifecycle.
- [ ] Panic containment test using an injected test-only fault.
"""
    new = old.replace("- [ ]", "- [x]")
    text = replace_once(text, old, new, "Task 18.3 definition checklist")
    if text.count("## 18.4 Android JNI") != 1:
        raise SystemExit("Task 18.4 section missing or duplicated")
    task18_4 = text.split("## 18.4 Android JNI", 1)[1].split("## 18.5 Android test harness", 1)[0]
    if "- [x]" in task18_4:
        raise SystemExit("Task 18.4 was modified unexpectedly")
    path.write_text(text)


def update_todo() -> None:
    path = Path("docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md")
    text = path.read_text()
    text = replace_once(text, "- [ ] 18.3 C tests.", "- [x] 18.3 C tests.", "top-level Task 18.3 marker")

    evidence = f"""

### Task 18.3 completion evidence

- Implementation: `crates/chess-ffi/tests/c_abi_lifecycle.rs`, the non-default `ffi-test-faults` feature, `crates/chess-ffi/src/c_abi/test_faults.rs`, the guarded test declaration in `crates/chess-ffi/include/chess_engine.h`, and `docs/RUST_C_ABI_TESTS.md`.
- The Rust-through-ABI harness uses only the public `extern \"C\"` surface and covers create, position setup, legal moves, move application, status, fixed-depth search, result cleanup, reset, and destroy.
- Repeated lifecycle coverage creates and destroys 128 engines and 128 cancellation handles, requires nonzero unique tokens, and proves stale and double-destroy operations fail visibly.
- Invalid-input coverage includes null explicit-length input, invalid UTF-8, malformed FEN, malformed and illegal moves, unknown search flags, incompatible record size, null output pointers, thread-local errors, and unchanged engine state.
- Active cancellation runs infinite synchronous search on a worker thread, cancels it through an independent token, destroys the caller-visible token, and requires bounded `ExplicitStop` completion with a legal move and successful cleanup.
- Buffer tests cover tampered records, failed-validation preservation, successful original frees, stale-copy rejection, repeated empty frees, and all-or-nothing validation of the three-buffer search result.
- The non-default `ffi-test-faults` feature exports `chess_engine_test_inject_panic`; the default production surface omits it. The test requires a contained panic result and then proves the process and ABI remain usable.
- Implementation SHA: `{IMPLEMENTATION_SHA}`.
- Permanent validation: run `{RUN_ID}`, job `{JOB_ID}`.
- Results: six focused Task 18.3 lifecycle tests and 297 executed non-doc Rust tests passed; rustfmt, committed lockfile, locked all-target/all-feature compilation, strict Clippy without suppressions, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and the independent differential oracle all passed.
- Differential validation covered 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- The first validation correction was limited to canonical rustfmt output and removal of one scheduler-sensitive test assertion. No ABI behavior, safety policy, production default surface, lower-layer code, or validation gate was weakened.
- Task 18.3 is complete. Task 18.4 Android JNI integration is next.
"""
    marker = "\n# Task 19: Opening book — NOT STARTED"
    if "### Task 18.3 completion evidence" in text:
        raise SystemExit("Task 18.3 evidence already present")
    text = replace_once(text, marker, evidence + marker, "Task 19 insertion marker")

    old_ops = """## Immediate next operations

1. Implement Task 18.3 as a native C or Rust-through-ABI smoke harness against the built library boundary.
2. Exercise repeated create/destroy and stale-handle rejection.
3. Cover invalid pointers, UTF-8, FEN, move, record-version, and result-code paths.
4. Run active infinite search on a worker thread and cancel it through the C token from another thread.
5. Prove buffer and search-result allocation/free lifecycles, including double-free rejection.
6. Add an exported test-only injected fault and prove panic containment without unwinding across C."""
    new_ops = """## Immediate next operations

1. Implement Task 18.4 as an Android JNI adapter over the stable C ABI contract.
2. Build the AArch64 Android shared library with a pinned Rust target and NDK toolchain.
3. Add a Kotlin wrapper with deterministic native-handle ownership and explicit close semantics.
4. Expose position setup, legal moves, move application, game status, search, cancellation, and structured error mapping.
5. Require search execution from a background dispatcher or worker rather than the Android main thread.
6. Document native library packaging, lifecycle, and finalization policy before Task 18.5 device and JVM harness work."""
    text = replace_once(text, old_ops, new_ops, "immediate next operations")
    if "- [x] 18.4 JNI." in text or "- [x] Task 18 gate." in text:
        raise SystemExit("Task 18.4 or Task 18 gate was closed unexpectedly")
    path.write_text(text)


def update_status() -> None:
    path = Path("docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md")
    text = path.read_text()
    text = replace_once(
        text,
        "**Current phase:** Task 18.2 stable C ABI complete; Task 18.3 C ABI tests are next",
        "**Current phase:** Task 18.3 C ABI tests complete; Task 18.4 Android JNI is next",
        "Ralph current phase",
    )
    row18_2 = "| 18.2 | `d1c4a9195acfc63dc2f9af52531c4ba01e9a2dc9` | `30836228692` / `91761964507` | versioned opaque-token C ABI, explicit UTF-8 lengths, typed errors, verified owned buffers, synchronous search/cancellation boundary, and panic containment; 291 Rust tests green |"
    row18_3 = f"| 18.3 | `{IMPLEMENTATION_SHA}` | `{RUN_ID}` / `{JOB_ID}` | complete Rust-through-ABI lifecycle, 128× engine/cancellation churn, invalid-input preservation, active cross-thread cancellation, exact buffer ownership, and exported test-fault containment; 297 Rust tests green |"
    text = replace_once(text, row18_2, row18_2 + "\n" + row18_3, "Ralph Task 18.3 table row")

    old_tail = "Task 18.2 is complete. Task 18.3 C ABI tests are next."
    section = f"""Task 18.2 is complete. Task 18.3 C ABI tests are next.


## Task 18.3 completion

Implemented and validated:

- a dedicated Rust-through-ABI harness that imports only the public C boundary;
- complete create, position, legal-move, play, status, search, reset, cleanup, and destroy workflow coverage;
- 128 repeated engine lifecycles and 128 repeated cancellation-token lifecycles with uniqueness and stale-token rejection;
- fail-loud null, UTF-8, FEN, move, flag, versioned-record, and output-pointer tests with exact state preservation;
- active infinite search on a worker thread, cancellation through a separate token, caller-visible token destruction, and bounded retained-reference completion;
- individual and compound output-buffer validation, all-or-nothing cleanup, stale-copy rejection, and repeatable empty cleanup;
- a non-default feature-gated exported panic fault that returns the contained-panic code and leaves the process usable;
- `docs/RUST_C_ABI_TESTS.md`.

Evidence:

- implementation SHA: `{IMPLEMENTATION_SHA}`;
- permanent CI run/job: `{RUN_ID}` / `{JOB_ID}`;
- six focused Task 18.3 lifecycle tests passed;
- 297 executed non-doc Rust tests passed;
- the complete permanent workspace gate and independent differential oracle passed without lint suppression or lower-layer production changes;
- the first validation correction was canonical rustfmt plus removal of one scheduler-sensitive assertion, with no product or gate weakening.

Task 18.3 is complete. Task 18.4 Android JNI is next."""
    text = replace_once(text, old_tail, section, "Ralph Task 18.3 completion section")
    path.write_text(text)


def update_contract() -> None:
    path = Path("docs/RUST_C_ABI_TESTS.md")
    text = path.read_text()
    if "## Completion evidence" in text:
        raise SystemExit("C ABI test completion evidence already present")
    text += f"""

## Completion evidence

Implementation SHA: `{IMPLEMENTATION_SHA}`.

Permanent validation:

- PR: `#233`;
- workflow run: `{RUN_ID}`;
- job: `{JOB_ID}`;
- all six Task 18.3 lifecycle tests passed;
- 297 executed non-doc Rust tests passed across the workspace;
- formatting, committed lockfile, locked all-target/all-feature compilation, strict Clippy with warnings denied and no lint suppression, authoritative release depth-four perft, rustdoc with warnings denied, and debug/release workspace builds passed;
- differential validation passed over 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.

The first validation found only canonical rustfmt differences. The correction also removed a scheduler-sensitive assertion that was not part of the ABI contract; the rendezvous, cross-thread cancel, bounded completion, typed termination, legal result, and cleanup checks remain. No ABI behavior, default production symbol surface, safety policy, lower-layer code, or validation gate was weakened.

Task 18.3 is complete. Task 18.4 owns the Android JNI adapter and AArch64 library integration.
"""
    path.write_text(text)


def main() -> None:
    update_definitions()
    update_todo()
    update_status()
    update_contract()


if __name__ == "__main__":
    main()
