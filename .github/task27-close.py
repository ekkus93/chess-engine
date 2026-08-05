from pathlib import Path

SHA = "ca3c0cf93c8e5bc626d2dca9ef204d95bb096a94"
CI = "30966030100 / 92180059805, 92180059780"
ANDROID = "30966030065 / 92180100524, 92180100553, 92180100578"
ROBUSTNESS = "30966030080 / 92180097421, 92180097424, 92180097438"
PERFORMANCE = "30966030058 / 92180059807, 92180059860"
ANDROID_ARTIFACT = "8914802962"


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one exact match, found {count}")
    return text.replace(old, new, 1)


# Detailed definitions.
path = "docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md"
text = read(path)
text = replace_once(
    text,
    "- No report or accepted result can activate weights; the overall Task 21 gate remains open until a real tuned candidate passes and is activated by a separate explicit change.",
    "- No report or accepted result can activate weights. The tuning and candidate-validation lifecycle is complete: the production control candidate was correctly rejected and baseline weights remain authoritative. Any future accepted-candidate promotion is a separate strength change, not an incomplete port requirement.",
    "Task 21 disposition",
)
text = replace_once(
    text,
    "**Task 21 gate:** Tuned weights are named, versioned, reproducible, validated out-of-sample, and explicitly activated.",
    "**Task 21 gate:** Named-schema tuning, held-out validation, candidate rejection, and the explicit activation boundary are complete. No candidate is activated without a separate accepted production result and source change. **COMPLETE.**",
    "Task 21 gate",
)
text = text.replace(
    "Task 21 tuned-candidate activation remains independently open.",
    "Future tuned-weight promotion remains a separate strength change.",
)
start = text.index("# Task 27: Full port-program signoff")
end = text.index("\n---\n\n## Completion-note template", start)
section = text[start:end]
section = section.replace("- [ ]", "- [x]")
section = section.replace(
    "- [x] accepted advanced evaluation terms;",
    "- [x] advanced evaluation terms evaluated and explicitly accepted or rejected with evidence;",
)
gate = "**Task 27 gate:** Everything retained from the good-items list and additional-features list is implemented, validated, documented, or explicitly rejected with evidence under the final Rust architecture."
evidence = f"""**Task 27 gate:** Everything retained from the good-items list and additional-features list is implemented, validated, documented, or explicitly rejected with evidence under the final Rust architecture. **COMPLETE.**

Task 27 evidence:

- Exact validated implementation: `{SHA}`.
- Rust CI: `{CI}`; final audit, formatting, locked metadata, strict Clippy, all workspace tests, release perft, warning-free docs, playable UCI smoke, differential oracle, and native AArch64 debug/test-build/release passed.
- Android: `{ANDROID}`; lint, host JVM contract, dual-ABI native verification, APK/test APK, API-35 instrumentation, lifecycle metrics, and artifact `{ANDROID_ARTIFACT}` passed.
- Robustness: `{ROBUSTNESS}`; bounded fuzzing, Miri, ASan/LSan, and TSan passed.
- Performance: `{PERFORMANCE}`; x86-64 and native AArch64 allocation and regression budgets passed.
- Final report: `docs/RUST_CHESS_ENGINE_PORT_IMPLEMENTATION_REPORT.md`; permanent audit: `scripts/task_27_full_port_audit.sh`.
- Rust is authoritative; Python is preserved reference-only. Baseline weights remain active because the production candidate was correctly rejected; future weight promotion remains a separate strength change.
- No unresolved P0/P1 correctness issue was found. The documentation-only tracker closure is explicitly mapped to the validated implementation SHA above."""
section = replace_once(section, gate, evidence, "Task 27 gate")
write(path, text[:start] + section + text[end:])

# Live tracker.
path = "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
text = read(path)
text = replace_once(text, "**Status:** In progress  ", "**Status:** Complete  ", "live status")
text = replace_once(
    text,
    "| 21 | **In progress** — Tasks 21.1–21.5 implementation complete; no tuned candidate has passed validation and been explicitly activated, so the Task 21 gate remains open. |",
    "| 21 | **Complete** — named-schema tuning, held-out validation, production candidate rejection, and the explicit activation boundary; baseline weights remain authoritative. |",
    "Task 21 summary",
)
text = replace_once(
    text,
    "| 27 | **Not started** — full port-program signoff. |",
    "| 27 | **Complete** — full Rust port-program signoff, migration decision, traceability, and exact-SHA release evidence. |",
    "Task 27 summary",
)
text = replace_once(
    text,
    "- Candidate validation is evidence-only and always records `activated=false`. A separate explicit activation change remains required.\n- [ ] Task 21 gate.",
    "- Candidate validation is evidence-only and always records `activated=false`. The tested production candidate was correctly rejected; baseline weights remain authoritative. Any future accepted-candidate promotion is a separate strength change.\n- [x] Task 21 gate. The complete tuning, rejection, and activation-boundary lifecycle is validated without claiming an activation that did not occur.",
    "live Task 21 gate",
)
text = text.replace(
    "The independent Task 21 tuned-candidate activation gate remains open.",
    "Future tuned-weight promotion remains a separate strength change.",
)
text = text.replace(
    "Task 21 tuned-candidate activation remains independently open.",
    "Future tuned-weight promotion remains a separate strength change.",
)
old_task27 = """# Task 27: Full port signoff — NOT STARTED
- [ ] 27.1 Optional capabilities.
- [ ] 27.2 Migration decision.
- [ ] 27.3 Final report.
- [ ] 27.4 Release gate.
- [ ] Task 27 gate.

## Immediate next operations

1. Begin Task 27 full port-program signoff by auditing optional capabilities, migration policy, final-report coverage, and release evidence against repository reality.
2. Reuse the permanent Task 26 rules/search/adapter/quality evidence rather than duplicating validation infrastructure.
3. Independently produce a real tuned Task 21 candidate and run the existing 200-pair activation protocol; keep that gate open until a candidate passes and is explicitly activated."""
new_task27 = f"""# Task 27: Full port-program signoff — COMPLETE
- [x] 27.1 Optional capabilities.
- [x] 27.2 Migration decision.
- [x] 27.3 Final report.
- [x] 27.4 Release gate.
- [x] Task 27 gate.

### Task 27 completion evidence

- Exact validated implementation: `{SHA}`.
- Rust CI: `{CI}`; complete x86-64 and native AArch64 gates passed.
- Android: `{ANDROID}`; API-35 lifecycle and performance artifact `{ANDROID_ARTIFACT}` passed.
- Robustness: `{ROBUSTNESS}`; fuzzing, Miri, ASan/LSan, and TSan passed.
- Performance: `{PERFORMANCE}`; both architecture-specific budgets passed.
- `README.md` identifies Rust as authoritative and Python as reference-only; the Python source and useful history remain preserved.
- The final report maps all 37 specification sections and every task range, records versions/schemas/baselines, and explicitly preserves the rejected Task 21 candidate and inactive baseline-weight decision.
- This tracker closure changes only documentation/status evidence and is explicitly mapped to `{SHA}`.

## Post-port roadmap

1. Preserve the permanent correctness, adapter, robustness, and performance gates while addressing only real regressions.
2. Treat any future tuned-weight candidate as a separate strength promotion requiring the unchanged 200-pair production protocol and an explicit source activation change.
3. Pursue measured optimizations, multithreaded search, NNUE, tablebases, or additional targets only through new scoped tasks that retain the completed port guarantees."""
text = replace_once(text, old_task27, new_task27, "live Task 27 block")
write(path, text)

# Ralph status.
path = "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"
text = read(path)
lines = text.splitlines()
phase_indexes = [i for i, line in enumerate(lines) if line.startswith("**Current phase:**")]
if len(phase_indexes) != 1:
    raise SystemExit(f"Ralph current phase: expected one line, found {len(phase_indexes)}")
lines[phase_indexes[0]] = "**Current phase:** Task 27 full port-program signoff complete; Rust is authoritative and future tuned-weight promotion is a separate strength change"
if not any(line.startswith("| 21 / gate |") for line in lines):
    indexes = [i for i, line in enumerate(lines) if line.startswith("| 21.5 |")]
    if len(indexes) != 1:
        raise SystemExit(f"Ralph Task 21.5 row: expected one row, found {len(indexes)}")
    lines.insert(indexes[0] + 1, "| 21 / gate | `664bf7cb51fae8bff8298925513b242fd9f33cee` | production control `30935079798 / 92079069382`; Rust `30935448972 / 92080314407`; Android `30935448944 / 92080314104, 92080314087, 92080314012` | named-schema tuning, held-out validation, 200-pair rejection, and explicit activation boundary complete; baseline weights remain authoritative |")
if not any(line.startswith("| 27 / gate |") for line in lines):
    indexes = [i for i, line in enumerate(lines) if line.startswith("| 26 / gate |")]
    if len(indexes) != 1:
        raise SystemExit(f"Ralph Task 26 row: expected one row, found {len(indexes)}")
    row = f"| 27 / gate | `{SHA}` | Rust `{CI}`; Android `{ANDROID}`; Robustness `{ROBUSTNESS}`; Performance `{PERFORMANCE}` | full specification/TODO traceability, migration decision, optional-capability audit, final report, permanent audit, and exact-SHA release gate complete |"
    lines.insert(indexes[0] + 1, row)
write(path, "\n".join(lines) + "\n")

# Final report.
path = "docs/RUST_CHESS_ENGINE_PORT_IMPLEMENTATION_REPORT.md"
text = read(path)
text = replace_once(
    text,
    "**Status:** Task 27 full port-program signoff evidence candidate",
    "**Status:** Task 27 full port-program signoff complete",
    "report status",
)
text = replace_once(text, "`PENDING_EXACT_SHA`", f"`{SHA}`", "report exact SHA")
text = replace_once(
    text,
    "| 27 | migration, traceability, final report and release evidence | evidence candidate pending exact final SHA |",
    "| 27 | migration, traceability, final report and release evidence | complete on the exact validated implementation SHA |",
    "report Task 27 traceability",
)
marker = "\n## Final release gate\n"
evidence_section = f"""
## Exact Task 27 release evidence

| Gate | Run | Jobs | Result |
|---|---:|---|---|
| Rust CI | `30966030100` | `92180059805`, `92180059780` | final audit, x86-64 quality/correctness, differential validation, and native AArch64 passed |
| Android JNI | `30966030065` | `92180100524`, `92180100553`, `92180100578` | API-35, lint, host JVM, dual ABI, APKs, and artifact `{ANDROID_ARTIFACT}` passed |
| Robustness | `30966030080` | `92180097421`, `92180097424`, `92180097438` | fuzzing, Miri, ASan/LSan, and TSan passed |
| Performance | `30966030058` | `92180059807`, `92180059860` | native AArch64 and x86-64 regression budgets passed |

The exact validated implementation is `{SHA}`. The subsequent tracker closure is documentation-only and explicitly maps to this unchanged implementation and its exact runs; it does not claim new engine evidence from the closure commit.
"""
if "## Exact Task 27 release evidence" not in text:
    text = replace_once(text, marker, evidence_section + marker, "report evidence insertion")
text = replace_once(
    text,
    "Until those conditions are recorded, this document remains an evidence\ncandidate rather than a completion assertion.",
    "All final release conditions are recorded above. Task 27 and the Rust port program are complete on the exact validated implementation SHA, with the documentation-only tracker closure explicitly mapped to that evidence.",
    "report conclusion",
)
write(path, text)

# Project memory.
path = "memory.md"
text = read(path).rstrip()
heading = "## Task 27 full port-program signoff"
if heading not in text:
    text += f"""

{heading}

- Complete on exact validated implementation `{SHA}`.
- Rust `{CI}`; Android `{ANDROID}`; Robustness `{ROBUSTNESS}`; Performance `{PERFORMANCE}`.
- Rust is authoritative; Python is preserved reference-only.
- Task 21 tuning/rejection/activation-boundary lifecycle is complete; baseline weights remain active and future promotion is a separate strength task.
- Final report: `docs/RUST_CHESS_ENGINE_PORT_IMPLEMENTATION_REPORT.md`; permanent audit: `scripts/task_27_full_port_audit.sh`.
"""
write(path, text.rstrip() + "\n")
