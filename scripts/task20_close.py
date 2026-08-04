from pathlib import Path

MERGED = "333398c5913309193cb81b91c4af3deff2fd5adf"
EVIDENCE = "1fae5fa8d830a524d6ff8d36ba42ed557112c79a"
RUST_RUN = "30875333307"
RUST_JOB = "91885547979"
ANDROID_RUN = "30875333292"
HOST_JOB = "91885547947"
EMULATOR_JOB = "91885547972"


def replace_once(text: str, old: str, new: str, context: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{context}: expected one match, found {count}")
    return text.replace(old, new, 1)


def close_definitions() -> None:
    path = Path("docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md")
    text = path.read_text()
    text = replace_once(
        text,
        "- Four dedicated public-API regressions and the permanent fail-closed no-auto-discovery audit passed with the complete 332-test Rust workspace and Android adapter gates.\n- Task 19 is complete; Task 20 is next.",
        "- Four dedicated public-API regressions and the permanent fail-closed no-auto-discovery audit passed with the complete 332-test Rust workspace and Android adapter gates.\n- Task 19 is complete; Task 20 is also complete and Task 21 is next.",
        "definitions Task 19 next-operation text",
    )
    task20_start = text.index("# Task 20: Implement self-play and versioned dataset tooling")
    task21_start = text.index("# Task 21: Implement named-schema Texel-style tuning and validation")
    task20 = text[task20_start:task21_start].replace("- [ ]", "- [x]")
    old_gate = (
        "**Task 20 gate:** A seeded self-play run can be replayed and produces a "
        "validated, versioned dataset with complete provenance.\n\n---\n\n"
    )
    evidence = f"""**Task 20 gate:** A seeded self-play run can be replayed and produces a validated, versioned dataset with complete provenance. **Complete.**

### Task 20 completion evidence

- Merged implementation SHA: `{MERGED}`.
- Exact validated evidence head: `{EVIDENCE}`.
- Permanent Rust run/job: `{RUST_RUN}` / `{RUST_JOB}`; 336 non-documentation Rust tests, including four focused Task 20 integration tests, passed.
- Permanent Android run/jobs: `{ANDROID_RUN}` / `{HOST_JOB}`, `{EMULATOR_JOB}`; host JVM, ARM64/x86_64 verification, APK build, and API-35 instrumentation passed.
- Strict formatting, compilation, Clippy, release depth-four perft, rustdoc, debug/release builds, and the differential oracle passed.
- The deterministic seeded suite proved replayable games, versioned lossless records, complete provenance, explicit splitting/filtering, exact duplicate accounting, unfinished maximum-ply handling, and fail-loud empty-output rejection.
- Task 20 is complete; Task 21.1 named weight-schema integration is next.

---

"""
    task20 = replace_once(task20, old_gate, evidence, "definitions Task 20 gate")
    text = text[:task20_start] + task20 + text[task21_start:]
    if "- [ ]" in text[task20_start:text.index("# Task 21:")]:
        raise SystemExit("Task 20 detailed definitions still contain open boxes")
    path.write_text(text)


def close_live_tracker() -> None:
    path = Path("docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md")
    text = path.read_text()
    text = replace_once(
        text,
        "| 20–24 | **Not started**. |",
        "| 20 | **Complete** — deterministic offline self-play and validated versioned datasets. |\n| 21–24 | **Not started**. |",
        "live program summary",
    )
    text = replace_once(
        text,
        "- Task 20 offline self-play is next.\n- [ ] Task 19 gate.",
        "- Task 20 offline self-play is complete; Task 21 named-schema tuning is next.",
        "live stale Task 19 tail",
    )
    old_task20 = """# Task 20: Self-play and datasets — NOT STARTED
- [ ] 20.1 Configuration.
- [ ] 20.2 Records.
- [ ] 20.3 Schema.
- [ ] 20.4 Quality.
- [ ] Task 20 gate.
"""
    new_task20 = f"""# Task 20: Self-play and datasets — COMPLETE
- [x] 20.1 Configuration.
- [x] 20.2 Records.
- [x] 20.3 Schema.
- [x] 20.4 Quality.
- [x] Task 20 gate.

### Task 20 completion evidence

- Merged implementation SHA: `{MERGED}`.
- Exact validated evidence head: `{EVIDENCE}`.
- Rust run/job: `{RUST_RUN}` / `{RUST_JOB}`; 336 non-documentation tests, the four focused Task 20 regressions, release perft, documentation, builds, and differential validation passed.
- Android run/jobs: `{ANDROID_RUN}` / `{HOST_JOB}`, `{EMULATOR_JOB}`; host JVM, dual-ABI native verification, APK build, and API-35 instrumentation passed.
- `chess-tools` now provides explicit `self-play`, `self-play-validate`, and `self-play-replay` commands over strict version-1 configuration, opening, game, and position schemas.
- Seeded opening rotation, per-game seeds, independent side limits, complete engine/evaluator/search provenance, deterministic train/validation/test assignment, replay validation, duplicate occurrence accounting, and explicit opening/maximum-ply filtering are enforced.
- Task 21.1 named weight-schema integration is next.
"""
    text = replace_once(text, old_task20, new_task20, "live Task 20 block")
    text = replace_once(
        text,
        "- [ ] Self-play and tuning.",
        "- [x] Self-play and versioned datasets.\n- [ ] Tuning.",
        "live Task 25 documentation",
    )
    text = replace_once(
        text,
        "- [ ] UCI, Android, self-play, and tuning commands.",
        "- [x] Self-play generation, validation, and replay commands.\n- [ ] UCI, Android, and tuning command documentation.",
        "live Task 25 commands",
    )
    operations = """## Immediate next operations

1. Implement Task 21.1 by enumerating tunable named evaluator parameters over the validated Task 20 dataset schema.
2. Keep non-tunable structural constants separate from trainable weights.
3. Define versioned tuned-weight serialization with checksum and training metadata before optimizer work.
4. Implement Task 21.2 with explicit logistic mapping, calibrated `K`, train/validation separation, and fail-loud malformed or empty datasets.
5. Preserve explicit candidate activation: generated weights must not become defaults before Task 21.5 validation.
6. Leave Tasks 21.2–21.5 and the overall Task 21 gate open until their own implementation and exact-head evidence are complete.
"""
    operations_start = text.index("## Immediate next operations")
    text = text[:operations_start] + operations
    if "# Task 20: Self-play and datasets — COMPLETE" not in text:
        raise SystemExit("live Task 20 completion marker missing")
    if "- [x] Task 20 gate." not in text:
        raise SystemExit("live Task 20 gate marker missing")
    if "- [ ] Task 19 gate." in text:
        raise SystemExit("stale Task 19 gate remains")
    path.write_text(text)


def close_ralph_status() -> None:
    path = Path("docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md")
    text = path.read_text()
    text = replace_once(
        text,
        "**Current phase:** Task 19 opening-book support complete; Task 20 offline self-play is next",
        "**Current phase:** Task 20 offline self-play and versioned datasets complete; Task 21.1 named weight-schema integration is next",
        "Ralph current phase",
    )
    rows = text.splitlines()
    matching = [
        index for index, line in enumerate(rows) if line.startswith("| 19.5 / 19 gate |")
    ]
    if len(matching) != 1:
        raise SystemExit(f"Ralph Task 19 row: expected one match, found {len(matching)}")
    row = (
        f"| 20 / gate | `{EVIDENCE}` | Rust `{RUST_RUN}` / `{RUST_JOB}`; "
        f"Android `{ANDROID_RUN}` / `{HOST_JOB}`, `{EMULATOR_JOB}` | deterministic "
        f"offline self-play, strict version-1 game/position datasets, replay validation, "
        f"full provenance, explicit splitting/filtering, four focused regressions, 336 "
        f"Rust tests, release perft, differential oracle, host JVM, dual-ABI Android, APK, "
        f"and API-35 instrumentation green; merged `{MERGED}` |"
    )
    rows.insert(matching[0] + 1, row)
    text = "\n".join(rows) + "\n"
    if "## Task 20 completion" in text:
        raise SystemExit("Ralph Task 20 completion already exists")
    text += f"""
## Task 20 completion

Implemented and validated:

- independent fixed White and Black search configurations with depth, node, or time limits;
- explicit seed, opening source, maximum-ply policy, claimable-draw policy, output path, and train/validation/test percentages;
- strict version-1 configuration, opening, game, and position formats;
- complete game moves, result, opening identity, engine/evaluator/search provenance, termination reason, and replay command;
- lossless canonical FEN position rows with side to move, game/ply identity, split, filtering metadata, and duplicate occurrence counts;
- replay validation of every game and retained position without rerunning search;
- explicit unfinished maximum-ply outcomes, opening-position policy, fail-loud empty output, and deterministic exact duplicate handling;
- `self-play`, `self-play-validate`, and `self-play-replay` commands plus example inputs and `docs/RUST_SELF_PLAY_DATASET.md`.

Evidence:

- merged implementation SHA: `{MERGED}`;
- exact validated evidence head: `{EVIDENCE}`;
- Rust run/job: `{RUST_RUN}` / `{RUST_JOB}`;
- Android run/jobs: `{ANDROID_RUN}` / `{HOST_JOB}`, `{EMULATOR_JOB}`;
- 336 non-documentation Rust tests and all permanent quality, perft, documentation, build, differential, host JVM, dual-ABI, APK, and API-35 gates passed.

Task 20 is complete. Task 21.1 named weight-schema integration is next.
"""
    if "| 20 / gate |" not in text:
        raise SystemExit("Ralph Task 20 evidence row missing")
    path.write_text(text)


def close_contract() -> None:
    path = Path("docs/RUST_SELF_PLAY_DATASET.md")
    text = path.read_text()
    final = (
        f"\nTask 20 merged at `{MERGED}` after exact evidence head `{EVIDENCE}` passed "
        "the permanent Rust and Android workflows. Task 20 and its overall gate are "
        "complete; Task 21.1 named weight-schema integration is next.\n"
    )
    if final.strip() in text:
        raise SystemExit("Task 20 contract final status already present")
    path.write_text(text + final)


close_definitions()
close_live_tracker()
close_ralph_status()
close_contract()
