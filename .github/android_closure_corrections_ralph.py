#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODO = ROOT / "docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md"
CLOSURE = ROOT / "docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md"
GAME_PANELS = ROOT / "android-harness/android-app/src/main/kotlin/com/ekkus93/chessapp/GamePanels.kt"
ROTATION_TEST = ROOT / "android-harness/android-app/src/androidTest/kotlin/com/ekkus93/chessapp/PortraitRotationInstrumentedTest.kt"

OLD_SOURCE = "6d9a84d910a3e6438aef390aa733a4b62a71dfdd"
FINAL_PARENT = "e9ab0fc623c22bd372ba9c8c2609dfcf74609f84"


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(args), flush=True)
    result = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout, end="", flush=True)
    if check and result.returncode != 0:
        raise SystemExit(result.returncode)
    return result


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run("git", *args, check=check)


def replace_section(path: Path, start: str, end: str, replacement: str) -> None:
    text = path.read_text()
    a = text.index(start)
    b = text.index(end, a)
    path.write_text(text[:a] + replacement.rstrip() + "\n\n" + text[b:])


def replace_exact(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    if text.count(old) != 1:
        raise RuntimeError(f"expected one occurrence in {path}: {old!r}")
    path.write_text(text.replace(old, new, 1))


def commit(message: str, *paths: Path) -> str:
    git("add", *[str(p.relative_to(ROOT)) for p in paths])
    git("diff", "--cached", "--check")
    if git("diff", "--cached", "--quiet", check=False).returncode == 0:
        raise RuntimeError(f"no staged changes for {message}")
    git("commit", "-m", message)
    sha = git("rev-parse", "HEAD").stdout.strip()
    git("push", "origin", "HEAD:master")
    print(f"COMMIT {sha} {message}", flush=True)
    return sha


def verify_historical_run(run_id: int) -> dict:
    result = run(
        "gh", "run", "view", str(run_id), "--repo", "ekkus93/chess-engine",
        "--json", "headSha,status,conclusion,jobs",
    )
    data = json.loads(result.stdout)
    if data["headSha"] != FINAL_PARENT or data["status"] != "completed" or data["conclusion"] != "success":
        raise RuntimeError(f"historical run {run_id} did not validate {FINAL_PARENT}: {data}")
    return data


def cc005() -> None:
    general = verify_historical_run(31419183264)
    android = verify_historical_run(31419183273)

    scoped = git("diff", "--exit-code", f"{OLD_SOURCE}..{FINAL_PARENT}", "--", "android-harness", "crates", check=False)
    if scoped.returncode != 0 or scoped.stdout.strip():
        raise RuntimeError("historical product/test surfaces differ unexpectedly")
    names = git("diff", "--name-only", f"{OLD_SOURCE}..{FINAL_PARENT}").stdout.strip()

    permanent = f'''## Permanent exact-source-SHA CI — corrected by closure-corrections CC-005

The original source-tree validation and the later authoritative closure-tree validation are distinct historical facts. The original source SHA remains useful supporting evidence, but the exact authoritative closure tree was `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84` and has its own permanent green runs.

### Authoritative final closure tree

- SHA: `{FINAL_PARENT}`
- General/Rust workflow `CI`: run `31419183264`
  - job `93555556721` — `Rust workspace quality` — `success`
  - job `93555556826` — `Linux ARM64 workspace build` — `success`
- Android workflow `Android JNI`: run `31419183273`
  - job `93555602583` — `Host JVM JNI contract` — `success`
  - job `93555602709` — `Android/Kotlin lint and unit tests` — `success`
  - job `93555602727` — `Android API 35 JNI and app smoke` — `success`

Both historical runs were independently re-queried during CC-005 via `gh run view`; each reported `status=completed`, `conclusion=success`, and `headSha={FINAL_PARENT}`.

### Earlier source-tree supporting evidence

The earlier permanent runs remain valid evidence for source SHA `{OLD_SOURCE}`:

- General/Rust run `31417242747`, job `93549046687` — `success`.
- Android run `31417240241`, jobs `93549039534`, `93549039574`, `93549039612` — `success`.

They are not presented as the authoritative exact-final-SHA citation.

### Product/test-surface equivalence between the two historical SHAs

This claim is supported by git comparison, not inferred from CI success:

```text
$ git diff --exit-code {OLD_SOURCE}..{FINAL_PARENT} -- android-harness crates
(exit 0; empty output)
```

The unrestricted changed-file list was:

```text
{names}
```

Therefore Android/Rust product and test surfaces were unchanged between the earlier source-validation SHA and the later closure-tree SHA, while the listed documentation/authority files changed as part of closure bookkeeping.

'''
    replace_section(CLOSURE, "## Permanent exact-source-SHA CI", "## Review-fix validation summary", permanent)
    if "**Authoritative closure-tree SHA:**" not in CLOSURE.read_text():
        replace_exact(
            CLOSURE,
            f"**Validated final source SHA:** `{OLD_SOURCE}`\n",
            f"**Validated final source SHA:** `{OLD_SOURCE}`\n**Authoritative closure-tree SHA:** `{FINAL_PARENT}`\n",
        )

    section = f'''# CC-005: Fix closure-evidence CI citation

## CC-005.1 Fix

- [x] Parent closure evidence now cites authoritative final-tree general/Rust run `31419183264` and Android run `31419183273` against `{FINAL_PARENT}`, including their job IDs and successful conclusions.
- [x] Earlier `{OLD_SOURCE[:8]}` runs remain supporting evidence only. Product/test equality is proven by the path-scoped command below, not inferred from green CI:

```text
git diff --exit-code {OLD_SOURCE}..{FINAL_PARENT} -- android-harness crates
(exit 0; empty output)
```

Supplementary unrestricted changed-file list:

```text
{names}
```

## CC-005.2 Tests

- [x] `gh run view 31419183264` and `gh run view 31419183273` independently returned completed/success on `{FINAL_PARENT}` during this task.
- [x] The recorded path-scoped diff was independently executed in this task and returned exit 0 with empty output.'''
    replace_section(TODO, "# CC-005:", "# CC-006:", section)
    run("bash", "scripts/task_post_port_review_fix_audit.sh")
    commit("docs(android): correct authoritative closure CI evidence", CLOSURE, TODO)


def cc006() -> None:
    old = """        }.collect { (scrolling, nearBottom) ->\n            // Layout growth alone cannot change follow mode; only an actual scroll does.\n            if (scrolling) {\n                followLatest = nearBottom\n            }\n        }"""
    new = """        }.collect { (scrolling, nearBottom) ->\n            // Layout growth alone cannot change follow mode; only an actual scroll does.\n            // isScrollInProgress is also true during our animateScrollToItem below. This is\n            // safe for real gameplay because history grows one row at a time, so the automatic\n            // hop stays near the bottom. A future bulk-history replacement must re-examine this\n            // assumption before relying on followLatest.\n            if (scrolling) {\n                followLatest = nearBottom\n            }\n        }"""
    replace_exact(GAME_PANELS, old, new)
    run("gradle", "-p", "android-harness", ":android-app:assembleDebugAndroidTest", "--no-daemon", "--stacktrace", "--console=plain")
    section = '''# CC-006: Document AR-006's residual auto-scroll assumption

## CC-006.1 Fix

- [x] `GamePanels.kt` now documents that `isScrollInProgress` also observes the automatic `animateScrollToItem`, that real gameplay appends one row at a time, and that a future bulk-history replacement must re-examine the assumption.

## CC-006.2 Tests

- [x] N/A — documentation-only behavior comment; Android instrumentation sources compile after the comment, and the existing two auto-scroll behavioral tests remain unchanged for the later full connected-test gate.'''
    replace_section(TODO, "# CC-006:", "# CC-007:", section)
    commit("docs(android): document move-history follow assumption", GAME_PANELS, TODO)


def cc007() -> None:
    old = '''            composeRule.onNodeWithTag("chess-board").assertExists()\n            composeRule.onNodeWithContentDescription("e4 pawn", substring = true).assertExists()'''
    new = '''            composeRule.onNodeWithTag("chess-board").assertExists()\n            composeRule.onNodeWithContentDescription("e2 pawn", substring = true).assertDoesNotExist()\n            composeRule.onNodeWithContentDescription("e4 pawn", substring = true).assertExists()'''
    replace_exact(ROTATION_TEST, old, new)
    run("gradle", "-p", "android-harness", ":android-app:assembleDebugAndroidTest", "--no-daemon", "--stacktrace", "--console=plain")
    section = '''# CC-007: Strengthen AR-020's rotation test

## CC-007.1 Fix

- [x] `PortraitRotationInstrumentedTest.kt` now asserts no `e2 pawn` node exists after rotation, alongside the existing `e4 pawn` assertion.

## CC-007.2 Tests

- [ ] The assertion compiles here and is reasoned to catch move duplication; runtime API-35 execution remains the gate before CC-008 may begin.'''
    replace_section(TODO, "# CC-007:", "# CC-008:", section)
    commit("test(android): verify rotation clears source square", ROTATION_TEST, TODO)


def stage3() -> None:
    git("status", "--short")
    cc005()
    cc006()
    cc007()
    print("STAGE3_HEAD=" + git("rev-parse", "HEAD").stdout.strip())


if __name__ == "__main__":
    os.chdir(ROOT)
    if len(sys.argv) != 2 or sys.argv[1] != "stage3":
        raise SystemExit("usage: android_closure_corrections_ralph.py stage3")
    stage3()
