from pathlib import Path
import sys

root = Path(sys.argv[1])


def read(path: str) -> str:
    return (root / path).read_text(encoding="utf-8")


def write(path: str, content: str) -> None:
    (root / path).write_text(content, encoding="utf-8")


def replace_once(content: str, old: str, new: str, label: str) -> str:
    count = content.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one occurrence, found {count}")
    return content.replace(old, new, 1)


# Detailed task definitions.
definitions_path = "docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md"
definitions = read(definitions_path)
for item in [
    "Add a bounded check extension only after baseline tests pass.",
    "Prevent unbounded extension chains.",
    "Record extension diagnostics.",
]:
    definitions = replace_once(
        definitions,
        f"- [ ] {item}",
        f"- [x] {item}",
        f"Task 16.7 definition {item}",
    )
definitions = replace_once(
    definitions,
    "**Task 16 gate:** Fixed-depth/node searches are deterministic, timed searches cancel responsively, PVs are legal, and aspiration recovery never promotes an inexact inferior move.",
    "**Task 16 gate — COMPLETE:** Fixed-depth/node searches are deterministic, timed searches cancel responsively, PVs are legal, aspiration recovery never promotes an inexact inferior move, and the optional check extension is explicitly bounded.",
    "Task 16 gate definition",
)
write(definitions_path, definitions)

# Live TODO tracker.
todo_path = "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
todo = read(todo_path)
todo = replace_once(
    todo,
    "| 16 | **Active** — Tasks 16.1–16.6 complete; Task 16.7 optional bounded check extension next. |",
    "| 16 | **Complete** — iterative deepening, aspiration recovery, legal PVs, limits, responsive cancellation, unified results, and bounded optional check extension. |",
    "program summary",
)
todo = replace_once(
    todo,
    "# Task 16: Iterative deepening, PV, limits, cancellation — ACTIVE",
    "# Task 16: Iterative deepening, PV, limits, cancellation — COMPLETE",
    "Task 16 heading",
)
todo = replace_once(todo, "- [ ] 16.7 Optional extension.", "- [x] 16.7 Optional extension.", "16.7 checkbox")
todo = replace_once(todo, "- [ ] Task 16 gate.", "- [x] Task 16 gate.", "Task 16 gate checkbox")

# Normalize current-next statements across earlier Task 16 evidence.
for old in [
    "Tasks 16.1–16.6 are complete. Task 16.7 optional bounded check extension is next.",
    "Task 16.7 optional bounded check extension is next; Task 16.7 and the overall Task 16 gate remain open.",
    "Tasks 16.1–16.6 are complete. Task 16.7 optional bounded check extension is the next operation.",
    "Task 16.7 optional bounded check extension is next. The overall Task 16 gate remains open.",
]:
    todo = todo.replace(old, "Task 16 is complete. Task 17.1 protocol loop is next.")

evidence = """### Task 16.7 and Task 16 gate completion evidence

- Implementation: `crates/chess-search/src/check_extension.rs`, integrated through `alpha_beta.rs`, `cancellation.rs`, `limits.rs`, `iterative_deepening.rs`, `principal_variation.rs`, and transposition probing.
- Public APIs: `SearchLimits::with_check_extension`, `SearchLimits::check_extension_enabled`, `CheckExtensionDiagnostics`, `CheckExtensionEvent`, `MAX_CHECK_EXTENSIONS_PER_LINE`, and `SearchResult::check_extension_diagnostics`.
- The feature is explicitly opt-in and disabled by default. Existing fixed-depth and limit-controlled requests preserve their prior baseline behavior.
- A checking child may receive exactly one additional ply per root-to-leaf path. The remaining budget is passed by value, consumed on application, and cannot be shared or replenished by siblings or later checks.
- Later checking nodes on the same path remain at nominal depth and are recorded as budget-exhausted. The mate-score ply ceiling blocks an extension that would leave the supported score domain.
- Extension-enabled searches suppress TT score reuse and storage because remaining extension budget is path-dependent and absent from the Zobrist key. Complete-key legal TT moves remain ordering hints only.
- PV reconstruction remains legal and bounded: the searched root move is validated, while extension-enabled requests do not continue through incompatible pre-existing TT score chains.
- Request-wide diagnostics report eligible checking nodes, applied extensions, exhausted-budget nodes, and mate-domain-blocked nodes, including work from an interrupted depth.
- Three unit tests prove the one-extension budget, disabled/nonchecking behavior, and mate-domain blocking. Four integration tests prove explicit opt-in, deterministic result/PV behavior, seeded TT-score rejection, node-limited diagnostics, and exact root/history/Zobrist restoration.
- Contract documentation: `docs/RUST_CHECK_EXTENSION.md`; search-limit and result-API contracts updated through Task 16.7.
- Production implementation commit: `54d98563f253df3ef055470a5fd4b2ee8b32947a`.
- Exact clean validated implementation SHA: `836ca0563f9a8dce44eb78997e28335a9d8fcdce`.
- Permanent CI run/job: `30785853401` / `91599164384`.
- Results: permanent exclusion audit over 17 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 229 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Validation corrections were limited to fail-closed generator assertions, two mechanical policy-wiring sites, a test-only helper classification, a private argument-policy grouping required by strict Clippy, and final temporary-generator cleanup. No lint suppression, gate downgrade, or semantic relaxation was used.
- The clean implementation delta contains eight search modules, one focused integration-test file, and three contract documents. No temporary script or workflow modification remains.
- The overall Task 16 gate is complete: deterministic depth/node behavior, responsive timed/explicit cancellation, legal PVs, exact aspiration recovery, unified result accounting, and finite optional extension semantics all passed together.
- Task 17.1 protocol loop is next.

"""
todo = replace_once(
    todo,
    "# Task 17: Linux UCI executable — NOT STARTED\n",
    evidence + "# Task 17: Linux UCI executable — NOT STARTED\n",
    "Task 16.7 evidence insertion",
)

old_ops = """## Immediate next operations

1. Evaluate and implement Task 16.7 only as a bounded, explicitly optional check extension that cannot create unbounded selective depth.
2. Define exact extension eligibility, maximum extension budget, interaction with mate-distance scoring, and cancellation/limit accounting before implementation.
3. Prove the extension preserves deterministic root choice, legal PV reconstruction, TT depth semantics, and exact position/history/Zobrist restoration.
4. Add tactical witnesses showing useful horizon improvement without weakening the Task 16.5 cancellation bound or Task 16.6 result accounting.
5. Run the overall Task 16 integration gate after Task 16.7 is either implemented and validated or explicitly declined with documented rationale.
6. Keep Task 17 UCI worker/protocol integration deferred until the Task 16 gate is complete."""
new_ops = """## Immediate next operations

1. Implement Task 17.1 as a fail-loud Linux UCI protocol loop over the completed Task 16 search boundary.
2. Support `uci`, `isready`, `ucinewgame`, supported `setoption`, `position startpos`, six-field `position fen`, move replay, all specified `go` forms, `stop`, and `quit`.
3. Keep parsing, position replacement, and move replay transactional so malformed commands cannot corrupt the active game state.
4. Add deterministic protocol transcripts covering valid commands, malformed commands, terminal positions, repeated position replacement, and clean shutdown.
5. Preserve Task 16 cancellation, legal PV, best-move fallback, node/time accounting, and exact root restoration through the adapter boundary.
6. Keep the Task 17.2 worker thread and Task 17.3 time manager separate from the initial protocol-loop implementation."""
todo = replace_once(todo, old_ops, new_ops, "immediate operations")
write(todo_path, todo)

# Ralph status.
status_path = "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"
status = read(status_path)
status = replace_once(
    status,
    "**Current phase:** Tasks 16.1–16.6 complete; Task 16.7 optional bounded check extension is next",
    "**Current phase:** Task 16 complete; Task 17.1 Linux UCI protocol loop is next",
    "current phase",
)
status = replace_once(
    status,
    "| 16.6 | `dcde800f4c5a08c07fe57724ed672f2abd122157` | `30783666840` / `91593059900` | unified typed result snapshot, request-wide node/qnode/seldepth/time accounting, 222 Rust tests, depth-four perft, and differential oracle green |",
    "| 16.6 | `dcde800f4c5a08c07fe57724ed672f2abd122157` | `30783666840` / `91593059900` | unified typed result snapshot, request-wide node/qnode/seldepth/time accounting, 222 Rust tests, depth-four perft, and differential oracle green |\n| 16.7 | `836ca0563f9a8dce44eb78997e28335a9d8fcdce` | `30785853401` / `91599164384` | explicit one-ply-per-line check extension, path-safe TT/PV policy, diagnostics, 229 Rust tests, depth-four perft, and differential oracle green |\n| 16 / gate | `836ca0563f9a8dce44eb78997e28335a9d8fcdce` | `30785853401` / `91599164384` | all iterative-deepening, aspiration, PV, limit, cancellation, result, and bounded-extension integration gates green |",
    "completed-gates rows",
)
for old in [
    "Task 16.7 optional bounded check extension is next; Task 16.7 and the overall Task 16 gate remain open.",
    "Task 16.7 optional bounded check extension is next. The overall Task 16 gate remains open.",
]:
    status = status.replace(old, "Task 16 is complete. Task 17.1 protocol loop is next.")

status_evidence = """## Task 16.7 and Task 16 gate completion

Implemented and validated:

- explicit opt-in through `SearchLimits::with_check_extension`, with baseline behavior unchanged by default;
- exactly one additional check ply per root-to-leaf path, enforced by a value-passed finite budget;
- budget-exhausted and mate-domain-blocked decisions that never create an extension chain;
- path-safe suppression of TT scores and stores while preserving complete-key legal move-ordering hints;
- legal bounded root-PV behavior without following incompatible selective-search table chains;
- request-wide applied/exhausted/blocked diagnostics, including interrupted partial work;
- unchanged one-node cancellation responsiveness, node/time accounting, aspiration exactness, and exact root restoration;
- three focused unit tests, four integration tests, and updated search-limit/result contracts;
- `docs/RUST_CHECK_EXTENSION.md`.

Evidence:

- Production implementation commit: `54d98563f253df3ef055470a5fd4b2ee8b32947a`.
- Exact clean validated SHA: `836ca0563f9a8dce44eb78997e28335a9d8fcdce`.
- Permanent CI run/job: `30785853401` / `91599164384`.
- Results: permanent exclusion audit over 17 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 229 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- The deterministic extension witness records applied work only when opted in; the repeat search preserves move, score, node count, diagnostics, legal PV, position, and history.
- A seeded incompatible exact TT score cannot bypass extension search. A 64-node interrupted request preserves partial extension diagnostics and restores all root invariants.
- Validation fixes addressed generator matching, mechanical policy wiring, a test-only PV helper, strict-Clippy argument grouping, and temporary-script deletion; no production warning was suppressed and no gate was weakened.
- The clean implementation delta contains eight search modules, one integration-test file, and three contract documents; permanent CI is restored byte-for-byte.
- Task 16.1–16.7 and the overall Task 16 gate are complete. Task 17.1 protocol loop is next.

"""
status = replace_once(
    status,
    "## Task 16 active scope\n",
    status_evidence + "## Task 16 completed scope\n",
    "Task 16.7 status insertion",
)
status = replace_once(
    status,
    "- [ ] Consider Task 16.7 optional bounded check extension.",
    "- [x] Implement Task 16.7 optional bounded check extension.",
    "16.7 scope checkbox",
)
status = replace_once(
    status,
    "- [ ] Pass the overall Task 16 gate.",
    "- [x] Pass the overall Task 16 gate.",
    "Task 16 scope checkbox",
)
status = replace_once(
    status,
    "No pull request has been created; work remains on `rust-engine`. Task 16.7 optional bounded check extension is the next operation.",
    "No pull request has been created; work remains on `rust-engine`. Task 17.1 Linux UCI protocol loop is the next operation.",
    "status footer",
)
write(status_path, status)

print("Task 16.7 and Task 16 tracker closure applied")
