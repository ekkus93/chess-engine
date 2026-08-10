#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODO = ROOT / "docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md"
PARENT = ROOT / "docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md"
INDEX = ROOT / "docs/LEGACY_TODO_INDEX.md"
AUDIT = ROOT / "scripts/task_post_port_review_fix_audit.sh"

IMPLEMENTATION_START = "fe97117a9d5315a2ae4bff344ed8b22f52d8c86e"
FINAL_SOURCE = "a16590502279750c21ce6afa7356cf755f7efcaa"
FOCUS_SHA = "05ec27dd099fa5ad74f5e5ff0bea2ae1cc5a801c"


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(args), flush=True)
    result = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout, end="", flush=True)
    if check and result.returncode != 0:
        raise SystemExit(result.returncode)
    return result


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run("git", *args, check=check)


def replace_exact(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    if text.count(old) != 1:
        raise RuntimeError(f"expected one occurrence in {path}: {old[:160]!r}")
    path.write_text(text.replace(old, new, 1))


def replace_section(path: Path, start: str, end: str, replacement: str) -> None:
    text = path.read_text()
    a = text.index(start)
    b = text.index(end, a)
    path.write_text(text[:a] + replacement.rstrip() + "\n\n---\n\n" + text[b:])


def validate_source() -> None:
    run(
        "gradle", "-p", "android-harness",
        ":android-app:lintDebug", ":android-app:testDebugUnitTest",
        "--no-daemon", "--stacktrace", "--console=plain",
    )
    run("bash", "scripts/dev.sh", "fast")

    diff = git("diff", f"{IMPLEMENTATION_START}..HEAD", "--", "android-harness", "crates").stdout
    forbidden = re.compile(r"^\+.*(?:#\s*\[\s*(?:allow|expect)\b|@Suppress\b)", re.MULTILINE)
    match = forbidden.search(diff)
    if match:
        raise RuntimeError(f"first-party lint suppression added during correction pass: {match.group(0)}")


def correct_parent() -> None:
    ar003 = '''# AR-003: Remove internal jargon from player-facing setup copy — corrected by closure-corrections CC-001

The original AR-003 implementation correctly removed the setup-screen jargon, but the original closure overclaimed the module-wide sweep: two player-visible `ChessViewModel` error strings still contained "native". CC-001 corrected those strings and broadened the structural guard so the historical gap is explicit rather than silently rewritten away.

## AR-003.1 Fix

- [x] Original work: `SetupScreen.kt` subtitle and cleanup-required copy no longer contain architecture jargon.
- [x] CC-001 correction: `ChessViewModel` now says "A previous game is still active..." and "Initial game snapshot failed..." rather than exposing "native" to the player-facing error dialog.
- [x] CC-001 correction: all production Kotlin string literals are checked for "native"/"JNI"/"shared layer"/"architecture", with only three exact internal-only `check()`/`Log.e` sinks narrowly allowlisted and justified.

## AR-003.2 Tests

- [x] The broadened module-wide structural test passes.
- [x] Implementation-time negative sanity check proved the broadened test fails when "native" is temporarily reintroduced into the player-visible `ChessViewModel` error string, then passes again after restoration.
'''
    replace_section(PARENT, "# AR-003:", "# AR-004:", ar003)

    ar004 = f'''# AR-004: Verify and fix system-bar theming on target SDK 35 — corrected by closure-corrections CC-002

The original closure checked the verify-first/runtime-observation boxes without having recorded a genuinely diagnostic observation. CC-002 repaired the evidence rather than assuming the old flag-only test was sufficient.

## AR-004.1 Fix — verify-first evidence corrected

- [x] CC-002A added a real API-35 framebuffer diagnostic: expected product background `#0B1220`, RGB tolerance ±12/channel, and >=70% matching pixels in sampled status/navigation-bar regions. Icon-appearance flags remain supporting evidence only.
- [x] Initial permanent observation run `31431380577`, API-35 job `93595365511`, passed on exact SHA `6e5fdec216f013fae1257c67899fa26cce02d5e6`.
- [x] A later full-suite run exposed a test-order/foreground race rather than a product regression: global `UiAutomation` capture could occur after the activity lost focus. Isolated run `31434333957`, job `93604944381`, artifact `9080478963`, showed the in-test status sample at 100% `#0B1220` while a post-test launcher screencap was light/0%.
- [x] CC-002A therefore hardened the diagnostic at `{FOCUS_SHA}` to wait for `MainActivity.hasWindowFocus()` and the app package to be foreground before the global screenshot. Permanent Android run `31434848246` then passed all jobs, including API-35 job `93606568633` and the full connected suite.
- [x] **Disposition:** `remediation-not-needed`. The real rendered state is correct; no `MainActivity`/WindowCompat production change was added. Existing `styles.xml` fallback attributes remain intact.

## AR-004.2 Tests

- [x] Focus-bound API-35 framebuffer diagnostic passes in the full permanent connected suite (`31434848246` / `93606568633`).
- [x] The preserved isolated evidence distinguishes actual app rendering from the launcher/foreground race; the original flag-only evidence is no longer treated as sufficient by itself.
'''
    replace_section(PARENT, "# AR-004:", "# AR-005:", ar004)

    ar011 = '''# AR-011: Add a functional promotion-dialog test — corrected by closure-corrections CC-004

The direct `PromotionDialog` callback test from the original implementation is valid. The original closure nevertheless overclaimed the second deliverable: no end-to-end promotion test and no documented impracticality reason existed at that time. CC-004 preserves that history and supplies an empirical blocker disposition rather than inventing coverage.

## AR-011.1 Fix

- [x] Original valid evidence: instrumentation renders `PromotionDialog` with a real `onChoose` callback, taps Queen/Rook/Bishop/Knight, and checks the resulting move strings.
- [x] CC-004 correction disposition: `documented blocker`. A temporary, uncommitted host-JVM probe drove the real JNI `ChessEngine`, reproduced the app's opening-book/depth-1 opponent policy, and beam-searched legal human paths for up to 12 human turns; no deterministic promotion path was found.
- [x] The existing high-level `ChessGame` exposes no clean test-only position/FEN injection seam. Adding production/native API solely to manufacture this test was rejected as disproportionate scope expansion.

## AR-011.2 Tests

- [x] Direct promotion-dialog functional instrumentation remains the permanent executable coverage.
- [x] No end-to-end promotion execution is claimed; the bounded real-engine search above is the recorded blocker evidence.
'''
    replace_section(PARENT, "# AR-011:", "# AR-012:", ar011)

    text = PARENT.read_text()
    text = text.replace(
        "## AR-021.2 Mandatory permanent exact-SHA CI (QI-012)\n",
        "## AR-021.2 Mandatory permanent exact-SHA CI (QI-012) — citation corrected by closure-corrections CC-005\n\n"
        "The original closure recorded the earlier source-SHA runs below but omitted the later authoritative closure-tree runs. CC-005 corrected `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md` to cite the exact final closure tree `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84`: general/Rust run `31419183264` and Android run `31419183273`, all successful. The earlier `6d9a84d...` runs remain supporting source-tree evidence, and a path-scoped git diff proves `android-harness`/`crates` were unchanged between those historical SHAs.\n\n",
        1,
    )
    old_block = '''Permanent Android CI run/job IDs: run 31417240241; jobs 93549039534, 93549039574, 93549039612; all success
Permanent general/Rust CI run/job IDs: run 31417242747; job 93549046687; success'''
    new_block = '''Earlier source-SHA Android CI:       run 31417240241; jobs 93549039534, 93549039574, 93549039612; all success
Earlier source-SHA general/Rust CI:  run 31417242747; job 93549046687; success
Authoritative closure-tree SHA:      e9ab0fc623c22bd372ba9c8c2609dfcf74609f84
Authoritative Android CI:            run 31419183273; jobs 93555602583, 93555602709, 93555602727; all success
Authoritative general/Rust CI:       run 31419183264; jobs 93555556721, 93555556826; all success'''
    if old_block not in text:
        raise RuntimeError("parent AR-021 evidence block not found")
    PARENT.write_text(text.replace(old_block, new_block, 1))


def close_tracker() -> None:
    text = TODO.read_text()
    text = text.replace("**Status:** proposed / not started", "**Status:** Complete", 1)
    TODO.write_text(text)

    cc002 = f'''# CC-002: Fix AR-004 — perform the verify-first system-bar observation

**Disposition:** `remediation-not-needed`.

## CC-002A: Runtime observation

- [x] Direct API-35 framebuffer evidence was added; icon-appearance flags are supporting evidence only.
- [x] Initial permanent observation: run `31431380577`, API-35 job `93595365511`, exact SHA `6e5fdec216f013fae1257c67899fa26cce02d5e6`, success.
- [x] The later full-suite 0% status sample was investigated fail-closed rather than ignored. Corrected isolation run `31434333957`, job `93604944381`, artifact `9080478963`, proved the in-test app screenshot had a 100% `#0B1220` status sample while the post-test launcher screenshot was light/0%, identifying a foreground teardown race.
- [x] Diagnostic hardened at `{FOCUS_SHA}` to require `MainActivity` window focus and foreground package before global screenshot. Permanent Android run `31434848246` then completed all three jobs successfully; API-35 job `93606568633` passed the full connected suite.

## CC-002B: Conditional remediation

- [x] **Disposition reached:** `remediation-not-needed`; stable focus-bound rendered evidence shows the product bars are correct.

N/A — `remediation-required`: no production system-bar change was needed.

## CC-002 Tests

- [x] Final stable evidence is permanent Android run `31434848246`, API-35 job `93606568633`, success; the investigation also preserved artifact `9080478963` explaining the earlier false failure.'''
    replace_section(TODO, "# CC-002:", "# CC-003:", cc002)

    cc007 = '''# CC-007: Strengthen AR-020's rotation test

## CC-007.1 Fix

- [x] `PortraitRotationInstrumentedTest.kt` asserts no `e2 pawn` node exists after rotation, alongside the existing `e4 pawn` presence assertion.

## CC-007.2 Tests

- [x] The strengthened assertion passed in the full API-35 connected suite in permanent Android run `31434848246`, job `93606568633`. It would fail if rotation duplicated the moved pawn onto both e2 and e4.'''
    replace_section(TODO, "# CC-007:", "# CC-008:", cc007)

    cc008 = '''# CC-008: Add Resign-dialog contrast pairing

## CC-008.1 Fix

- [x] `ThemeContrastTest.kt` now includes `requireRatio("resign dialog confirm", Danger, SurfaceElevated, 4.5)`.

## CC-008.2 Tests

- [x] Android lint/app unit-test job `93608171310` in permanent Android run `31435363087` passed on source SHA `a16590502279750c21ce6afa7356cf755f7efcaa`, including the new contrast assertion.'''
    replace_section(TODO, "# CC-008:", "# CC-009:", cc008)

    cc009 = f'''# CC-009: Final validation and closure

## CC-009.1 Validation

- [x] Android app JVM/unit tests and Android lint pass in this closure run; CC-008 also passed permanent job `93608171310` / run `31435363087` on `{FINAL_SOURCE}`.
- [x] CC-004 disposition-dependent validation is complete: `documented blocker`, backed by the bounded real-JNI-engine path search; no E2E test is claimed.
- [x] CC-002A final focus-bound runtime observation and CC-002B `remediation-not-needed` disposition are recorded; permanent run `31434848246` is fully green.
- [x] `bash scripts/dev.sh fast` passes in this closure run.
- [x] Terminal permanent exact-SHA CI is an external post-commit gate per spec §2.1/FQI-001. The repository closure is complete, but the final implementation handoff is blocked until both permanent workflows are independently confirmed green on the terminal validation SHA; their run/job IDs are intentionally not written back into a new commit.

## CC-009.2 Provenance-preserving correction of the parent TODO

- [x] AR-003, AR-004, AR-007, AR-011, and AR-021/closure-CI citation history are corrected in place without pretending the original closure had the evidence supplied by CC-001/002/003/004/005.

## CC-009.3 Authority closure

- [x] This tracker's `Status:` is `Complete`.
- [x] `docs/LEGACY_TODO_INDEX.md` classifies this bounded tracker as completed; the active-implementation slot remains empty.
- [x] Permanent authority audit updated for the corrected closure state.
- [x] Temporary correction/validation helpers are removed before the closure commit is created.

## CC-009.4 Closure evidence

- [x] Parent closure evidence was corrected by CC-005 with authoritative `e9ab0fc...` runs and path-scoped historical source/test equivalence evidence.
- [x] All repository-resident correction evidence is recorded here; terminal CI metadata remains external by protocol.

```text
Review baseline SHA:          e9ab0fc623c22bd372ba9c8c2609dfcf74609f84
Implementation start SHA:     {IMPLEMENTATION_START}
Final correction source SHA:  {FINAL_SOURCE}

Android app unit/lint:        pass — closure validation plus run 31435363087/job 93608171310
CC-004 disposition/result:    documented blocker — bounded real JNI-engine promotion-path search found no deterministic path
CC-002A runtime observation:  pass — final stable run 31434848246/job 93606568633; isolation artifact 9080478963 explains prior foreground race
CC-002B disposition/result:   remediation-not-needed — no production system-bar change
bash scripts/dev.sh fast:     pass — closure validation
first-party suppressions:     none added in android-harness/crates diff from implementation-start SHA

(Terminal permanent CI run/job IDs are reported externally in the final
implementation handoff after the terminal SHA is known and both workflows finish.)
```

## CC-009 acceptance

- [x] Every CC-001 through CC-008 task has its own recorded evidence or explicit permitted `N/A` branch.
- [x] No first-party lint suppression was added anywhere in this pass.
- [x] No existing green test was weakened or deleted to obtain a green run.
- [x] Terminal exact-SHA permanent CI remains the mandatory external gate; final handoff will not declare the Ralph loop closed until it is green.
- [x] Repository closure status is `Complete`; no repository mutation will occur after the terminal validation SHA is selected.'''
    replace_section(TODO, "# CC-009:", "\0THIS_SENTINEL_DOES_NOT_EXIST", cc009) if False else None
    # CC-009 is the final section, so replace to EOF explicitly.
    text = TODO.read_text()
    a = text.index("# CC-009:")
    TODO.write_text(text[:a] + cc009.rstrip() + "\n")


def close_index() -> None:
    text = INDEX.read_text()
    old = '`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md` (in progress as of this entry — a second-order bounded review-fix tracker correcting five inaccurate closure claims found in an independent post-closure verification of the tracker immediately above)'
    new = '`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md` (completed — second-order bounded review-fix pass corrected the five inaccurate closure claims and three secondary hardening notes without reopening the parent program)'
    if old not in text:
        raise RuntimeError("in-progress correction tracker index entry not found")
    text = text.replace(old, new, 1)
    text = text.replace(
        "and updated for the Android UI/UX review-fix closure-corrections pass on 2026-08-10:",
        "updated for the Android UI/UX review-fix closure-corrections pass on 2026-08-10, and reclassified at closure-corrections completion on 2026-08-10:",
        1,
    )
    INDEX.write_text(text)


def update_audit() -> None:
    text = AUDIT.read_text()
    text = text.replace(
        'android_ui_review_fix_closure="docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md"\n',
        'android_ui_review_fix_closure="docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md"\n'
        'android_ui_review_fix_corrections_spec="docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_SPEC_2026-08-10.md"\n'
        'android_ui_review_fix_corrections_todo="docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md"\n',
        1,
    )
    text = text.replace(
        '    "$android_ui_review_fix_closure" \\\n    "$legacy_index"',
        '    "$android_ui_review_fix_closure" \\\n    "$android_ui_review_fix_corrections_spec" \\\n    "$android_ui_review_fix_corrections_todo" \\\n    "$legacy_index"',
        1,
    )
    text = text.replace(
        'grep -Fq \'**Status:** Complete — bounded review-fix implementation and permanent exact-source-SHA validation passed\' "$android_ui_review_fix_closure"\n',
        'grep -Fq \'**Status:** Complete — bounded review-fix implementation and permanent exact-source-SHA validation passed\' "$android_ui_review_fix_closure"\n'
        'grep -Fq \'**Status:** Complete\' "$android_ui_review_fix_corrections_todo"\n'
        'grep -Fq \'`claims-downgraded`\' "$android_ui_review_fix_corrections_todo"\n'
        'grep -Fq \'`documented blocker`\' "$android_ui_review_fix_corrections_todo"\n'
        'grep -Fq \'`remediation-not-needed`\' "$android_ui_review_fix_corrections_todo"\n',
        1,
    )
    text = text.replace(
        'grep -Fq "\\`$android_ui_review_fix_closure\\`" "$legacy_index"\n',
        'grep -Fq "\\`$android_ui_review_fix_closure\\`" "$legacy_index"\n'
        'grep -Fq "\\`$android_ui_review_fix_corrections_todo\\`" "$legacy_index"\n'
        'grep -Fq "\\`$android_ui_review_fix_corrections_todo\\` (completed" "$legacy_index"\n',
        1,
    )
    old_evidence = '''grep -Fq '**Validated final source SHA:** `6d9a84d910a3e6438aef390aa733a4b62a71dfdd`' "$android_ui_review_fix_closure"
grep -Fq 'Run: `31417242747`' "$android_ui_review_fix_closure"
grep -Fq 'Job: `93549046687`' "$android_ui_review_fix_closure"
grep -Fq 'Run: `31417240241`' "$android_ui_review_fix_closure"
grep -Fq 'Job `93549039534`' "$android_ui_review_fix_closure"
grep -Fq 'Job `93549039574`' "$android_ui_review_fix_closure"
grep -Fq 'Job `93549039612`' "$android_ui_review_fix_closure"'''
    new_evidence = '''grep -Fq '**Validated final source SHA:** `6d9a84d910a3e6438aef390aa733a4b62a71dfdd`' "$android_ui_review_fix_closure"
grep -Fq '**Authoritative closure-tree SHA:** `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84`' "$android_ui_review_fix_closure"
grep -Fq 'run `31419183264`' "$android_ui_review_fix_closure"
grep -Fq 'job `93555556721`' "$android_ui_review_fix_closure"
grep -Fq 'job `93555556826`' "$android_ui_review_fix_closure"
grep -Fq 'run `31419183273`' "$android_ui_review_fix_closure"
grep -Fq 'job `93555602583`' "$android_ui_review_fix_closure"
grep -Fq 'job `93555602709`' "$android_ui_review_fix_closure"
grep -Fq 'job `93555602727`' "$android_ui_review_fix_closure"
grep -Fq 'git diff --exit-code 6d9a84d910a3e6438aef390aa733a4b62a71dfdd..e9ab0fc623c22bd372ba9c8c2609dfcf74609f84 -- android-harness crates' "$android_ui_review_fix_closure"'''
    if old_evidence not in text:
        raise RuntimeError("old Android review-fix evidence audit block not found")
    text = text.replace(old_evidence, new_evidence, 1)
    text = text.replace(
        '    ".github/android_ui_gallery.py"; do',
        '    ".github/android_ui_gallery.py" \\\n    ".github/android_closure_corrections_ralph.py" \\\n    ".github/workflows/android-closure-corrections-ralph.yml" \\\n    ".github/investigate_system_bars.sh"; do',
        1,
    )
    AUDIT.write_text(text)


def remove_temporary_helpers() -> None:
    for rel in (
        ".github/android_closure_corrections_ralph.py",
        ".github/workflows/android-closure-corrections-ralph.yml",
        ".github/investigate_system_bars.sh",
    ):
        path = ROOT / rel
        if not path.exists():
            raise RuntimeError(f"temporary helper unexpectedly absent before cleanup: {rel}")
        path.unlink()


def finalize() -> None:
    git("status", "--short")
    validate_source()
    correct_parent()
    close_tracker()
    close_index()
    update_audit()
    remove_temporary_helpers()

    run("bash", "scripts/task_post_port_review_fix_audit.sh")

    git("add", "-A")
    git("diff", "--cached", "--check")
    staged = git("diff", "--cached", "--name-only").stdout
    for forbidden in (
        ".github/android_closure_corrections_ralph.py",
        ".github/workflows/android-closure-corrections-ralph.yml",
        ".github/investigate_system_bars.sh",
    ):
        if (ROOT / forbidden).exists():
            raise RuntimeError(f"temporary helper remains before closure: {forbidden}")
    print("CLOSURE_STAGED_FILES:\n" + staged, flush=True)
    git("commit", "-m", "docs(android): close closure-corrections program")
    sha = git("rev-parse", "HEAD").stdout.strip()
    tree = git("rev-parse", "HEAD^{tree}").stdout.strip()
    git("push", "origin", "HEAD:master")
    print(f"FINAL_SUBSTANTIVE_SHA={sha}")
    print(f"FINAL_SUBSTANTIVE_TREE={tree}")


if __name__ == "__main__":
    os.chdir(ROOT)
    if len(sys.argv) != 2 or sys.argv[1] != "finalize":
        raise SystemExit("usage: android_closure_corrections_ralph.py finalize")
    finalize()
