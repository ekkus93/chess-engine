from pathlib import Path

IMPLEMENTATION_SHA = "67b6c97a476e1323bc2bd96ecf14870fc2ed3139"
VALIDATION_RUN = "30828959858"
VALIDATION_JOB = "91737751003"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one occurrence, found {count}")
    return text.replace(old, new, 1)


def replace_section_checkboxes(path: Path, start: str, end: str) -> None:
    text = path.read_text()
    start_index = text.index(start)
    end_index = text.index(end, start_index)
    section = text[start_index:end_index]
    open_count = section.count("- [ ]")
    if open_count != 8:
        raise SystemExit(f"{path}: expected 8 open Task 17.5 boxes, found {open_count}")
    section = section.replace("- [ ]", "- [x]")
    path.write_text(text[:start_index] + section + text[end_index:])


def update_task_definitions() -> None:
    path = Path("docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md")
    replace_section_checkboxes(
        path,
        "## 17.5 Integration tests\n",
        "**Task 17 gate:**",
    )


def update_authoritative_todo() -> None:
    path = Path("docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md")
    text = path.read_text()
    text = replace_once(
        text,
        "# Task 17: Linux UCI executable — IN PROGRESS",
        "# Task 17: Linux UCI executable — COMPLETE",
        "Task 17 heading",
    )
    text = replace_once(
        text,
        "- [ ] 17.5 Integration tests.",
        "- [x] 17.5 Integration tests.",
        "Task 17.5 checkbox",
    )
    text = replace_once(
        text,
        "- [ ] Task 17 gate.",
        "- [x] Task 17 gate.",
        "Task 17 gate checkbox",
    )
    marker = "\n# Task 18: Safe API, C ABI, and JNI — NOT STARTED"
    if "### Task 17.5 and Task 17 gate completion evidence" in text:
        raise SystemExit("Task 17.5 evidence already exists")
    evidence = f"""

### Task 17.5 and Task 17 gate completion evidence

- Implementation: `crates/chess-uci/tests/uci_process.rs` and `docs/RUST_UCI_PROCESS_INTEGRATION.md`.
- Seven real child-process tests cover the exact handshake, readiness, start-position and six-field FEN setup, fail-visible transactional illegal input, fixed-depth legal best moves, checkmate/stalemate `bestmove 0000`, active-search `stop`, active-search `quit`, and concurrent session/stdout isolation.
- Every process read and exit is bounded. Cleanup closes stdin, terminates a stuck child, waits for it, and joins the stdout reader thread.
- The harness uses standard-library process and synchronization APIs only; it performs no stdout redirection and introduces no process-global mutable state.
- Implementation SHA: `{IMPLEMENTATION_SHA}`.
- Permanent validation: run `{VALIDATION_RUN}`, job `{VALIDATION_JOB}`.
- Results: seven subprocess tests passed; formatting, locked all-target/all-feature workspace compilation, strict Clippy without suppressions, the complete workspace tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and the independent differential oracle all passed.
- Differential validation covered 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Task 17.5 and the overall Task 17 Linux UCI executable gate are complete. Task 18.1 Rust facade work is next.
"""
    text = replace_once(text, marker, evidence + marker, "Task 18 boundary")
    path.write_text(text)


def update_ralph_status() -> None:
    path = Path("docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md")
    text = path.read_text()
    text = replace_once(text, "**Updated:** 2026-08-02", "**Updated:** 2026-08-03", "status date")
    lines = text.splitlines()
    phase_indexes = [index for index, line in enumerate(lines) if line.startswith("**Current phase:**")]
    if len(phase_indexes) != 1:
        raise SystemExit(f"status phase: expected one line, found {len(phase_indexes)}")
    lines[phase_indexes[0]] = "**Current phase:** Task 17 complete; Task 18.1 Rust facade is next"
    text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")

    row_marker = "| 17.4 | `0f0ed39b31aca077173359c5807c1afaffb3e9e4` | final permanent gate recorded in output contract | synchronized iteration info, typed scores, nodes/NPS/time/hashfull/PV, exactly-once bestmove |"
    new_row = f"| 17.5 / 17 gate | `{IMPLEMENTATION_SHA}` | `{VALIDATION_RUN}` / `{VALIDATION_JOB}` | seven real subprocess workflows, bounded stop/quit, legal best moves, terminal null moves, and concurrent-session isolation; complete permanent gate green |"
    text = replace_once(text, row_marker, row_marker + "\n" + new_row, "Task 17.5 status row")

    section_marker = "\n## Task 12 completion"
    if "## Task 17.5 and Task 17 gate completion" in text:
        raise SystemExit("Task 17.5 Ralph section already exists")
    section = f"""

## Task 17.5 and Task 17 gate completion

Implemented and validated:

- a real subprocess harness around the Cargo-built `chess-uci` executable;
- exact handshake and readiness transcripts;
- start-position replay and strict six-field FEN workflows;
- fail-visible, transactional illegal move handling;
- legal fixed-depth best moves checked against `chess-core`;
- checkmate and stalemate `bestmove 0000` behavior;
- bounded active-search `stop` and `quit` behavior;
- two concurrent engine sessions with isolated state and stdout;
- `docs/RUST_UCI_PROCESS_INTEGRATION.md`.

Evidence:

- implementation SHA: `{IMPLEMENTATION_SHA}`;
- permanent CI run/job: `{VALIDATION_RUN}` / `{VALIDATION_JOB}`;
- seven subprocess integration tests passed;
- the complete permanent workspace gate passed without lint suppression or production-code changes.

Task 17 is complete. Task 18.1 Rust facade work is next.
"""
    text = replace_once(text, section_marker, section + section_marker, "Task 12 section boundary")
    path.write_text(text)


def update_uci_contracts() -> None:
    replacements = {
        "Task 17.4 is complete. Task 17.5 process integration testing is next.":
            "Task 17.4 is complete. Task 17.5 and the overall Task 17 gate are also complete. Task 18.1 Rust facade work is next.",
        "Tasks 17.2 through 17.4 are complete. Task 17.5 process integration testing is next.":
            "Tasks 17.2 through 17.5 and the overall Task 17 gate are complete. Task 18.1 Rust facade work is next.",
    }
    changed = 0
    for path in Path("docs").glob("RUST_UCI*.md"):
        text = path.read_text()
        original = text
        for old, new in replacements.items():
            text = text.replace(old, new)
        if text != original:
            path.write_text(text)
            changed += 1
    if changed < 2:
        raise SystemExit(f"expected at least two UCI contract updates, found {changed}")


def main() -> None:
    update_task_definitions()
    update_authoritative_todo()
    update_ralph_status()
    update_uci_contracts()


if __name__ == "__main__":
    main()
