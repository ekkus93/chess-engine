#!/usr/bin/env python3
from pathlib import Path

IMPLEMENTATION_SHA = "466c7b504832afa2bf993cb10dcc0c12aefcf1c5"
ANDROID_PROOF_SHA = "1fc49b6126ecb9faa4c0f167b272945d65aebbf1"
HOST_RUN = "30844134371"
HOST_JOB = "91788114660"
FOLLOWUP_RUN = "30844338897"
FOLLOWUP_JOB = "91788828855"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one occurrence, found {count}")
    return text.replace(old, new)


definitions_path = Path("docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md")
definitions = definitions_path.read_text()
open_block = """## 18.4 Android JNI

- [ ] Build AArch64 shared library.
- [ ] Kotlin wrapper class with deterministic native-handle ownership.
- [ ] Position setup and legal moves.
- [ ] Move application and status.
- [ ] Search from a background dispatcher/thread.
- [ ] Cancellation.
- [ ] Error mapping.
- [ ] Native resource close/finalization policy.
"""
closed_block = open_block.replace("- [ ]", "- [x]")
definitions = replace_once(
    definitions, open_block, closed_block, "Task 18.4 definition block"
)
android_harness_block = definitions.split("## 18.5 Android test harness", 1)[1].split(
    "**Task 18 gate:**", 1
)[0]
if android_harness_block.count("- [ ]") != 5 or "- [x]" in android_harness_block:
    raise SystemExit("Task 18.5 must remain entirely open")
definitions_path.write_text(definitions)


todo_path = Path("docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md")
todo = todo_path.read_text()
todo = replace_once(todo, "- [ ] 18.4 JNI.", "- [x] 18.4 JNI.", "top-level 18.4")
if todo.count("- [ ] 18.5 Android harness.") != 1:
    raise SystemExit("Task 18.5 top-level marker changed unexpectedly")
if todo.count("- [ ] Task 18 gate.") != 1:
    raise SystemExit("Task 18 gate must remain open")
if "### Task 18.4 completion evidence" in todo:
    raise SystemExit("Task 18.4 evidence already exists")

evidence = f"""

### Task 18.4 completion evidence

- Implementation: `crates/chess-jni/src/lib.rs` and `bridge.rs`, the pinned `jni = 0.21.1` dependency, `rlib` plus Android `cdylib` outputs, and the locked dependency update in `Cargo.lock`.
- Android-facing source: `crates/chess-jni/kotlin/src/main/kotlin/com/ekkus93/chessengine/ChessEngine.kt`; build entry point: `scripts/build_android_jni.sh`; contract: `docs/RUST_ANDROID_JNI.md`.
- The JNI adapter reuses the stable Task 18.2 opaque engine and cancellation tokens. It does not duplicate chess rules, search logic, handle registries, or result-code semantics.
- Sixteen exact JNI exports cover version, engine lifecycle, position reset/setup, canonical FEN, legal UCI moves, move application, game status, weight identity, cancellation lifecycle, and synchronous typed search.
- Every JNI export enters one shared panic boundary. Stable native result codes and diagnostics map to typed `ChessEngineException`; exception-construction failure falls back visibly to `RuntimeException`.
- The Kotlin `ChessEngine` is a deterministic `Closeable` owner with an idempotent close path, read/write lifecycle locking, one outstanding search, a private single-thread worker, request-local cancellation, and a phantom-reference leak fallback.
- Public Kotlin search never invokes the synchronous native call on the caller thread. `SearchOperation.cancel` uses the independent native stop token rather than Java interruption.
- Nine focused JNI tests cover opaque-token bit preservation, exact request conversion, bridge lifecycle, typed invalid-FEN preservation, active cross-thread cancellation, Kotlin/Rust symbol agreement, compact-record agreement, and ownership/background-search source contracts.
- Host implementation SHA: `{IMPLEMENTATION_SHA}`.
- Permanent host validation: run `{HOST_RUN}`, job `{HOST_JOB}`.
- Follow-up permanent validation on the Android-proof source tree: run `{FOLLOWUP_RUN}`, job `{FOLLOWUP_JOB}`.
- Results: nine focused JNI tests and 306 executed non-doc Rust tests passed; rustfmt, committed lockfile, locked all-target/all-feature compilation, strict Clippy without suppressions, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and the independent differential oracle all passed.
- Differential validation covered 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Android AArch64 proof SHA: `{ANDROID_PROOF_SHA}`. Its guarded workflow completed the locked NDK API-24 `aarch64-linux-android` release build, required a nonempty `libchess_jni.so`, verified an AArch64 ELF shared object and the exported `nativeSearch` JNI symbol, then removed itself.
- Validation corrections were limited to lockfile/rustfmt normalization, snapshotting scalar search fields before ABI-result cleanup, using the pinned `jni` crate's typed `JThrowable`, and importing one test-only result-code type. No lower-layer production behavior, safety policy, or validation gate was weakened.
- Task 18.4 is complete. Task 18.5 Android/JVM and emulator harness work is next; the overall Task 18 gate remains open.
"""
todo = replace_once(todo, "\n# Task 19: Opening book", evidence + "\n# Task 19: Opening book", "Task 19 insertion")

old_next = """## Immediate next operations

1. Implement Task 18.4 as an Android JNI adapter over the stable C ABI contract.
2. Build the AArch64 Android shared library with a pinned Rust target and NDK toolchain.
3. Add a Kotlin wrapper with deterministic native-handle ownership and explicit close semantics.
4. Expose position setup, legal moves, move application, game status, search, cancellation, and structured error mapping.
5. Require search execution from a background dispatcher or worker rather than the Android main thread.
6. Document native library packaging, lifecycle, and finalization policy before Task 18.5 device and JVM harness work.
"""
new_next = """## Immediate next operations

1. Implement Task 18.5 host JVM contract tests around the committed Kotlin wrapper.
2. Add a minimal Android/Gradle harness that packages the validated AArch64 `libchess_jni.so`.
3. Run an instrumented or emulator smoke path for create, position, legal moves, search, stop, and destroy.
4. Prove sample integration never invokes search on the Android main thread.
5. Exercise repeated create/search/stop/destroy lifecycles and record the exact Android target, NDK, Gradle, and emulator commands.
6. Close the overall Task 18 gate only after the Android harness is green.
"""
todo = replace_once(todo, old_next, new_next, "immediate next operations")
todo_path.write_text(todo)


ralph_path = Path("docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md")
ralph = ralph_path.read_text()
ralph = replace_once(
    ralph,
    "**Current phase:** Task 18.3 C ABI tests complete; Task 18.4 Android JNI is next",
    "**Current phase:** Task 18.4 Android JNI complete; Task 18.5 Android harness is next",
    "Ralph current phase",
)
row_anchor = "| 18.3 | `0789ac65590ccafb55b2b86b73873edfba1c7b55` | `30841137129` / `91778174797` | complete Rust-through-ABI lifecycle, 128× engine/cancellation churn, invalid-input preservation, active cross-thread cancellation, exact buffer ownership, and exported test-fault containment; 297 Rust tests green |"
new_row = row_anchor + f"\n| 18.4 | `{IMPLEMENTATION_SHA}` | `{HOST_RUN}` / `{HOST_JOB}` | Android JNI exports and typed Kotlin owner, background search, request-local cancellation, error mapping, deterministic close/reaper policy, nine focused JNI tests, 306 Rust tests, and AArch64 ELF proof `{ANDROID_PROOF_SHA}` green |"
ralph = replace_once(ralph, row_anchor, new_row, "Ralph Task 18.4 row")
if "## Task 18.4 completion" in ralph:
    raise SystemExit("Ralph Task 18.4 section already exists")
ralph_section = f"""

## Task 18.4 completion

Implemented and validated:

- an Android `cdylib` adapter over the existing stable C ABI, with no duplicate engine registry or chess/search implementation;
- sixteen JNI exports for engine lifecycle, positions, legal moves, move/status, identity, search, and cancellation;
- shared panic containment and typed Java exception construction preserving stable native result codes;
- exact opaque-token bit preservation between Rust `u64` and JVM `long`;
- a typed Kotlin `Closeable` owner with deterministic handle destruction, lifecycle locking, one outstanding search, and a phantom-reference fallback;
- a private single-thread search worker so the public Kotlin API never runs synchronous native search on the caller thread;
- request-local cross-thread cancellation and cleanup in all completion paths;
- a locked NDK API-24 AArch64 build script producing and verifying `libchess_jni.so`;
- six bridge tests and three Kotlin/Rust source-contract tests;
- `docs/RUST_ANDROID_JNI.md`.

Evidence:

- host implementation SHA: `{IMPLEMENTATION_SHA}`;
- permanent host CI run/job: `{HOST_RUN}` / `{HOST_JOB}`;
- follow-up permanent CI run/job: `{FOLLOWUP_RUN}` / `{FOLLOWUP_JOB}`;
- Android AArch64 proof and one-shot cleanup SHA: `{ANDROID_PROOF_SHA}`;
- nine focused JNI tests and 306 executed non-doc Rust tests passed;
- the complete permanent workspace gate, authoritative release perft, and independent differential oracle passed without lint suppression or lower-layer behavior changes;
- the Android proof required a nonempty AArch64 ELF shared object and the exported JNI search symbol before its temporary workflow could remove itself.

Task 18.4 is complete. Task 18.5 Android harness work is next, and the overall Task 18 gate remains open.
"""
ralph = replace_once(ralph, "\n## Task 12 completion", ralph_section + "\n## Task 12 completion", "Ralph Task 18.4 insertion")
ralph_path.write_text(ralph)


contract_path = Path("docs/RUST_ANDROID_JNI.md")
contract = contract_path.read_text()
if "## Completion evidence" in contract:
    raise SystemExit("JNI contract completion evidence already exists")
contract += f"""

## Completion evidence

- Host implementation SHA: `{IMPLEMENTATION_SHA}`.
- Permanent host validation: run `{HOST_RUN}`, job `{HOST_JOB}`.
- Follow-up permanent validation on the Android-proof source tree: run `{FOLLOWUP_RUN}`, job `{FOLLOWUP_JOB}`.
- Android AArch64 proof and one-shot cleanup SHA: `{ANDROID_PROOF_SHA}`.
- Nine focused JNI tests and 306 executed non-doc Rust tests passed.
- The locked NDK API-24 build produced a nonempty AArch64 ELF `libchess_jni.so` and exposed the exact `nativeSearch` JNI symbol before the temporary workflow removed itself.
- Formatting, lockfile verification, all-target/all-feature compilation, strict Clippy, complete workspace tests, authoritative release depth-four perft, rustdoc, debug/release builds, and differential validation all passed.
- Task 18.4 is complete. Task 18.5 owns JVM/Gradle execution, Android packaging, emulator or instrumentation evidence, main-thread exclusion, and repeated Android lifecycle coverage.
"""
contract_path.write_text(contract)
