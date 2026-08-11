#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SECOND_CORRECTIONS_SPEC_2026-08-10.md"
TODO = ROOT / "docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SECOND_CORRECTIONS_TODO_2026-08-10.md"
CC = ROOT / "docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md"
INDEX = ROOT / "docs/LEGACY_TODO_INDEX.md"
AUDIT = ROOT / "scripts/task_post_port_review_fix_audit.sh"
IMPLEMENTATION_START = "df9155171e84b1be295bf0cd482582d10e5b3d6c"
FINAL_SOURCE = "99a5ffd277db22c8a3d383e0206dfa6c010e4506"
SC001_SHA = "92c01f33f19759c67c01aad73375084c72e3d1cb"
SC002_SHA = "343d589b2181b6b2b355b3a809516f4acd20af1e"
SC003_DOC_SHA = "e227e78bbbbf224440002d95e6dfa7993a850fc6"
VALIDATION_RUN = os.environ.get("GITHUB_RUN_ID", "unknown")

TEMPORARIES = [
    ".github/android_second_corrections_ralph.py",
    ".github/workflows/android-second-corrections-ralph.yml",
    ".github/android_second_corrections_resume.py",
    ".github/workflows/android-second-corrections-resume.yml",
    ".github/android_second_corrections_sc003_finalize.py",
    ".github/workflows/android-second-corrections-sc003-finalize.yml",
    ".github/android_second_corrections_close.py",
    ".github/workflows/android-second-corrections-close.yml",
    ".github/workflows/android-second-corrections-promotion-probe.yml",
    "android-harness/host-jvm/src/test/kotlin/com/ekkus93/chessengine/PromotionPathEvidenceTest.kt",
]


def run(*args: str) -> str:
    print("+", " ".join(args), flush=True)
    result = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout, end="", flush=True)
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    return result.stdout


def replace_section(path: Path, start: str, end: str, replacement: str) -> None:
    text = path.read_text()
    a = text.index(start)
    b = text.index(end, a)
    path.write_text(text[:a] + replacement.rstrip() + "\n\n---\n\n" + text[b:])


def validate_source_tree() -> None:
    run("cargo", "build", "--locked", "-p", "chess-jni", "--release")
    run(
        "gradle", "-p", "android-harness",
        ":android-app:lintDebug",
        ":android-app:testDebugUnitTest",
        ":host-jvm:test",
        ":android-app:assembleDebugAndroidTest",
        "--no-daemon", "--stacktrace", "--console=plain",
    )
    run("bash", "scripts/task_post_port_review_fix_audit.sh")
    run("bash", "scripts/dev.sh", "fast")

    diff = run("git", "diff", f"{IMPLEMENTATION_START}..HEAD", "--", "android-harness", "crates")
    forbidden = re.compile(r"^\+.*(?:@\s*Suppress|#\s*\[\s*(?:allow|expect)\b)", re.MULTILINE)
    match = forbidden.search(diff)
    if match:
        raise RuntimeError(f"first-party lint suppression added in second-corrections pass: {match.group(0)}")


def update_cc001_provenance() -> None:
    replacement = r'''# CC-001: Fix AR-003 — remove remaining "native" jargon — extended by second-corrections SC-001

CC-001 correctly removed the two known `ChessViewModel.kt` player-visible strings and added a blanket scanner over `android-harness/android-app/src/main/kotlin`. Independent verification later found that Gradle compiles a second production Kotlin root, `crates/chess-jni/kotlin/src/main/kotlin`, which CC-001's scanner did not cover. Second-corrections SC-001 closes that recurrence without pretending CC-001 originally covered it.

## CC-001.1 Fix and second-corrections extension

- [x] Original CC-001 work: `ChessViewModel.kt` player-visible error strings were corrected and the app-local production source root was scanned with narrow internal-only exceptions.
- [x] SC-001 correction at `92c01f33f19759c67c01aad73375084c72e3d1cb`: the scanner now covers both Gradle-compiled Kotlin production roots, including `crates/chess-jni/kotlin/src/main/kotlin`.
- [x] SC-001 reworded every newly exposed architecture-jargon exception/thread-name string in `ChessGame.kt` and `ChessEngine.kt` rather than broadly allowlisting them. Only exact ABI `System.loadLibrary("chess_jni")` literals and the previously justified internal-only ViewModel sinks remain narrowly allowlisted.
- [x] SC-001 added a mechanical Gradle-source-root invariant: every production `java.srcDir(...)` declaration in `android-app/build.gradle.kts` must be represented in the scanner configuration.

## CC-001.2 Tests added/strengthened by SC-001

- [x] The extended structural test passes across both current production roots.
- [x] Negative jargon sanity: temporarily restoring `"native Android game returned a null handle"` made the structural test fail, then pass after restoration.
- [x] Negative future-root sanity: temporarily adding a third unscanned `java.srcDir(...)` made the structural test fail, then pass after restoration.
- [x] Host-JVM JNI, Android app JVM/unit, Android lint, and instrumentation compilation all passed before SC-001 was committed.
'''
    replace_section(CC, "# CC-001:", "# CC-002:", replacement)


def close_authority() -> None:
    SPEC.write_text(SPEC.read_text().replace("**Status:** proposed / not started", "**Status:** Complete", 1))
    TODO.write_text(TODO.read_text().replace("**Status:** proposed / not started", "**Status:** Complete", 1))

    update_cc001_provenance()

    index = INDEX.read_text()
    old = "`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SECOND_CORRECTIONS_TODO_2026-08-10.md` (in progress as of this entry — a third-order bounded review-fix pass closing three residual gaps found by an independent post-closure verification of the closure-corrections tracker immediately above)"
    new = "`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SECOND_CORRECTIONS_TODO_2026-08-10.md` (completed — third-order bounded review-fix pass closed the residual source-scope/evidence gaps and replaced the disproven promotion blocker with permanent real-flow E2E coverage)"
    if index.count(old) != 1:
        raise RuntimeError("second-corrections authority index in-progress entry not found exactly once")
    index = index.replace(old, new, 1)
    index = index.replace(
        "and updated for the Android UI/UX review-fix second-corrections pass on 2026-08-10:",
        "updated for the Android UI/UX review-fix second-corrections pass on 2026-08-10, and reclassified at second-corrections completion on 2026-08-10:",
        1,
    )
    INDEX.write_text(index)

    audit = AUDIT.read_text()
    anchor = "grep -Fq '**Status:** Complete' \"$android_ui_review_fix_corrections_todo\"\n"
    addition = anchor + (
        "grep -Fq '**Status:** Complete' \"$android_ui_review_fix_second_corrections_spec\"\n"
        "grep -Fq '**Status:** Complete' \"$android_ui_review_fix_second_corrections_todo\"\n"
        "grep -Fq '`ui-driven-path-built`' \"$android_ui_review_fix_second_corrections_todo\"\n"
        "grep -Fq '31447725972' \"$android_ui_review_fix_second_corrections_todo\"\n"
        "grep -Fq '31448304672' \"$android_ui_review_fix_second_corrections_todo\"\n"
    )
    if audit.count(anchor) != 1:
        raise RuntimeError("audit corrections-status anchor not found exactly once")
    audit = audit.replace(anchor, addition, 1)

    anchor = "grep -Fq \"\\`$android_ui_review_fix_second_corrections_todo\\`\" \"$legacy_index\"\n"
    addition = anchor + "grep -Fq \"\\`$android_ui_review_fix_second_corrections_todo\\` (completed\" \"$legacy_index\"\n"
    if audit.count(anchor) != 1:
        raise RuntimeError("audit second-corrections index anchor not found exactly once")
    audit = audit.replace(anchor, addition, 1)

    temp_anchor = '    ".github/investigate_system_bars.sh"; do\n'
    temp_add = (
        '    ".github/investigate_system_bars.sh" \\\n'
        '    ".github/android_second_corrections_ralph.py" \\\n'
        '    ".github/workflows/android-second-corrections-ralph.yml" \\\n'
        '    ".github/android_second_corrections_resume.py" \\\n'
        '    ".github/workflows/android-second-corrections-resume.yml" \\\n'
        '    ".github/android_second_corrections_sc003_finalize.py" \\\n'
        '    ".github/workflows/android-second-corrections-sc003-finalize.yml" \\\n'
        '    ".github/android_second_corrections_close.py" \\\n'
        '    ".github/workflows/android-second-corrections-close.yml" \\\n'
        '    ".github/workflows/android-second-corrections-promotion-probe.yml" \\\n'
        '    "android-harness/host-jvm/src/test/kotlin/com/ekkus93/chessengine/PromotionPathEvidenceTest.kt"; do\n'
    )
    if audit.count(temp_anchor) != 1:
        raise RuntimeError("audit temporary-helper anchor not found exactly once")
    audit = audit.replace(temp_anchor, temp_add, 1)
    AUDIT.write_text(audit)

    sc004 = f'''# SC-004: Final validation and closure

## SC-004.1 Validation

- [x] Android app JVM/unit tests and Android lint passed in bounded closure validation workflow run `{VALIDATION_RUN}` after `cargo build --locked -p chess-jni --release`.
- [x] Host-JVM JNI tests and Android instrumentation compilation passed in the same bounded closure validation run.
- [x] SC-003's real-flow promotion instrumentation test already passed in permanent Android run `31448304672`, API-35 job `93647206317`, on exact source/test SHA `{FINAL_SOURCE}`.
- [x] `bash scripts/task_post_port_review_fix_audit.sh` passed before closure edits and again against the final candidate closure tree.
- [x] `bash scripts/dev.sh fast` passed against the final candidate closure tree.
- [x] No first-party Kotlin `@Suppress` or Rust `#[allow]`/`#[expect]` addition exists in the implementation diff from `{IMPLEMENTATION_START}` across `android-harness` and `crates`.
- [x] Permanent Android CI and permanent general/Rust CI are mandatory external terminal gates under spec §2.1. Repository-resident closure is finalized without self-referential run IDs; the implementation handoff must not claim completion until both are independently confirmed green on the terminal exact-SHA tree.

## SC-004.2 Authority closure

- [x] This document's `Status:` header is `Complete`.
- [x] `docs/LEGACY_TODO_INDEX.md` classifies this bounded tracker as completed; the active-implementation slot remains empty.
- [x] `scripts/task_post_port_review_fix_audit.sh` validates the completed second-corrections tracker, its evidence, and temporary-helper absence.
- [x] All temporary second-corrections Ralph/resume/probe/finalizer/closure helpers are removed from the final tree before exact-SHA validation.

## SC-004.3 Provenance-preserving corrections

- [x] CC-001 now records that its original scanner covered only the app-local root and that SC-001 added Gradle-wide source-root coverage plus future-root detection.
- [x] CC-004 now preserves its original `documented blocker` as historical provenance, records that SC-003's artifact-backed search disproved it, and names `ui-driven-path-built` as the current disposition with permanent E2E evidence.

## SC-004.4 Closure evidence

```text
Review baseline SHA:          a943b67abf4b187f1840a790ad9372d27576c3c5
Implementation start SHA:     {IMPLEMENTATION_START}
SC-001 source/test SHA:        {SC001_SHA}
SC-002 documentation SHA:      {SC002_SHA}
Final correction source SHA:   {FINAL_SOURCE}
SC-003 provenance SHA:         {SC003_DOC_SHA}

Android source/test evidence:  permanent run 31448304672; jobs 93647206317,
                               93647206339, 93647206354; all success
SC-003 discovery evidence:     run 31447725972; job 93645421851;
                               artifact 9085181028; RESULT=FOUND; b7a8b
Bounded closure validation:    workflow run {VALIDATION_RUN}; app lint/unit,
                               host-JVM JNI, instrumentation compile, authority audit,
                               and scripts/dev.sh fast all success
Anti-suppression review:       no added @Suppress / #[allow] / #[expect]
Temporary helpers:             absent from candidate closure tree

(Terminal permanent CI run/job IDs are external metadata reported only in the
final implementation handoff per spec §2.1; no self-referential follow-up commit.)
```

## SC-004 acceptance

- [x] Every SC-001 through SC-003 task is complete with specific recorded evidence.
- [x] No first-party lint suppression was added anywhere in this pass.
- [x] No existing green test was weakened or deleted to obtain a green run.
- [x] The repository-resident closure tree is complete and immutable before terminal CI; exact-SHA permanent CI remains the external final handoff gate required by spec §2.1.
- [x] This document's Status header is `Complete`; external program closure is claimed only after both required terminal workflows are confirmed green.
'''
    text = TODO.read_text()
    a = text.index("# SC-004:")
    TODO.write_text(text[:a] + sc004.rstrip() + "\n")


def remove_temporaries() -> None:
    for relative in TEMPORARIES:
        path = ROOT / relative
        if path.exists():
            path.unlink()


def finalize() -> None:
    validate_source_tree()
    close_authority()
    remove_temporaries()

    for relative in TEMPORARIES:
        if (ROOT / relative).exists():
            raise RuntimeError(f"temporary helper still exists: {relative}")

    # Validate the actual candidate closure tree, not only the pre-closure source tree.
    run("bash", "scripts/task_post_port_review_fix_audit.sh")
    run("bash", "scripts/dev.sh", "fast")

    diff = run("git", "diff", IMPLEMENTATION_START, "--", "android-harness", "crates")
    forbidden = re.compile(r"^\+.*(?:@\s*Suppress|#\s*\[\s*(?:allow|expect)\b)", re.MULTILINE)
    match = forbidden.search(diff)
    if match:
        raise RuntimeError(f"first-party lint suppression added in closure candidate: {match.group(0)}")

    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], cwd=ROOT, check=True)
    subprocess.run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], cwd=ROOT, check=True)
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "docs(android): close second-corrections program"], cwd=ROOT, check=True)
    subprocess.run(["git", "push", "origin", "HEAD:master"], cwd=ROOT, check=True)


if __name__ == "__main__":
    finalize()
