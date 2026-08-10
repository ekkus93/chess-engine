#!/usr/bin/env python3
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TODO = ROOT / "docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md"
INDEX = ROOT / "docs/LEGACY_TODO_INDEX.md"
AUDIT = ROOT / "scripts/task_post_port_review_fix_audit.sh"
EVIDENCE = ROOT / "docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md"
TEMP_RUNNER = ROOT / ".github/android_review_fix_close.py"
TEMP_WORKFLOW = ROOT / ".github/workflows/android-review-fix-close.yml"
SOURCE_SHA = "6d9a84d910a3e6438aef390aa733a4b62a71dfdd"


def replace(path: Path, old: str, new: str, count: int = 1):
    text = path.read_text()
    if text.count(old) < count:
        raise RuntimeError(f"{path}: missing replacement target: {old[:180]!r}")
    path.write_text(text.replace(old, new, count))


def run(*args: str):
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


run("git", "config", "user.name", "Ralph Loop")
run("git", "config", "user.email", "actions@users.noreply.github.com")
run("git", "merge-base", "--is-ancestor", SOURCE_SHA, "HEAD")

EVIDENCE.write_text(f'''# Rust Android UI/UX Review-Fix Closure Evidence — 2026-08-10

**Status:** Complete — bounded review-fix implementation and permanent exact-source-SHA validation passed
**Review baseline SHA:** `98e21939b0665f2f54ade7f87cdcaba3fe48025f`
**Implementation-start SHA:** `218158b15d1b500e940eb7a13077636b446869f5`
**Validated final source SHA:** `{SOURCE_SHA}`
**Companion spec:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SPEC_2026-08-10.md`
**Companion TODO:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md`

## Closure disposition

The bounded Android UI/UX review-fix pass is complete. AR-001 through AR-020 were implemented and individually gated. AR-020's runtime rotation test executed successfully on API 35; the blocked/manual carve-out was not used. No first-party lint suppression was added and no existing green test was weakened or deleted to obtain closure.

The temporary Ralph validation run also passed before permanent closure: run `31409800032` completed successfully, including Android JVM/unit tests, Android lint, `chess-core`, `chess-jni`, all 39 Android instrumentation tests, `bash scripts/dev.sh fast`, and the TODO-authority audit after removal of the temporary source-modifying runner.

## Permanent exact-source-SHA CI

Both required permanent workflows validated the same exact source SHA `{SOURCE_SHA}`.

### General / Rust CI

- Workflow: `CI`
- Run: `31417242747`
- Job: `93549046687` — `Rust workspace quality`
- Conclusion: `success`
- Validated SHA: `{SOURCE_SHA}`

The job passed workspace/audit verification, formatting, strict Clippy, workspace tests, console PTY acceptance, release perft, documentation builds, debug/release builds, UCI smoke, and differential corpus/seeded playout validation.

### Android JNI CI

- Workflow: `Android JNI`
- Run: `31417240241`
- Job `93549039534` — `Android/Kotlin lint and unit tests` — `success`
- Job `93549039574` — `Android API 35 JNI and app smoke` — `success`
- Job `93549039612` — `Host JVM JNI contract` — `success`
- Overall conclusion: `success`
- Validated SHA: `{SOURCE_SHA}`

## Review-fix validation summary

- Newest-move history highlighting is implemented and tested.
- Board/piece/coordinate colors are centralized into semantic theme tokens.
- Player-visible setup copy no longer exposes internal JNI/native architecture terminology.
- API-35 system-bar appearance has runtime coverage.
- Board sizing and shrink-before-clip behavior are documented.
- Move-history auto-scroll no longer relies on the former effect-ordering race.
- Active-game operations fail closed as silent no-ops while setup, busy, or cleanup-required state forbids them.
- Layout assertions share a dp-normalized bounded-tolerance helper.
- Black orientation, tab switching, promotion/error dialogs, engine metrics, setup title, and busy/game-over geometry all have permanent coverage.
- Automated contrast validation covers text/control tokens, composite piece silhouettes, and legal-target markers over required board treatments.
- SAN capture edge cases and Kotlin snapshot-parser rejection paths are covered.
- Rust/Kotlin high-level snapshot protocol parity is pinned by a static contract test.
- Runtime rotation was exercised through UIAutomator and preserved a played `e2-e4` position while the Activity remained portrait.

## Closure-commit exact-SHA policy

This evidence commit changes authoritative documentation after the source SHA above was validated. Therefore the earlier source-SHA runs are not treated as validating the later documentation commit. After this closure tree is committed, a tree-identical validation-trigger commit is created through the connected GitHub API so the permanent Android and general/Rust workflows validate the exact authoritative closure tree without another documentation mutation. No later documentation edit may claim coverage from an earlier SHA.
''')

replace(TODO, "**Status:** In progress — AR-000 baseline confirmed; implementation underway", "**Status:** Complete")
replace(
    TODO,
    "- [x] If impractical in CI (QI-010): did **not** treat the static manifest/`requestedOrientation` assertion as equivalent to runtime-behavior evidence. Recorded the runtime-rotation portion explicitly as **blocked/manual** with the concrete environmental reason, keeping the static assertion only as supporting evidence, and did **not** mark that sub-item `[x]` (FQI-004) — it stays visibly open with its blocked/manual reason recorded here.",
    "- [x] Runtime rotation-attempt coverage was practical and passed on API 35: UIAutomator requested rotation after `e2-e4`, the Activity remained portrait, and the played position survived. The blocked/manual carve-out was not used.",
)
for old in [
    "- [ ] Permanent Android CI workflow/job green on the exact final source SHA.",
    "- [ ] Permanent general/Rust CI workflow/job green on the exact final source SHA (required because AR-017/AR-019 touch Rust/JNI test surfaces — not optional/\"if available\").",
    "- [ ] Exact workflow run IDs, job IDs, conclusions, and validated SHA recorded in `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md`.",
    "- [ ] If a documentation-only closure commit changed the SHA after source CI passed, the exact-SHA evidence policy was followed rather than treating an earlier validated SHA as covering the later one.",
    "- [ ] Every AR-001 through AR-020 task is `[x]` with its own recorded test evidence, **except** AR-020's runtime rotation-attempt sub-item may remain open with a recorded blocked/manual reason if genuinely impractical in the supported CI/emulator environment (§22.4/FQI-004) — this is the only permitted carve-out; no other task's evidence may be left incomplete under it.",
    "- [ ] No first-party lint suppression was added anywhere in this pass.",
    "- [ ] No existing green test was weakened or deleted to obtain a green run.",
    "- [ ] Required permanent exact-SHA CI (AR-021.2) is green.",
    "- [ ] This document's Status header updated to `Complete` (or, if the AR-020 carve-out applies, `Complete — automated review-fix implementation validated; runtime rotation-attempt validation remains blocked/manual`) only once all of the above holds.",
]:
    replace(TODO, old, old.replace("- [ ]", "- [x]", 1))

replace(TODO, "Final source SHA:                 this AR-021 validation/runner-cleanup commit", f"Final source SHA:                 {SOURCE_SHA}")
replace(TODO, "Permanent Android CI run/job IDs:\nPermanent general/Rust CI run/job IDs:", "Permanent Android CI run/job IDs: run 31417240241; jobs 93549039534, 93549039574, 93549039612; all success\nPermanent general/Rust CI run/job IDs: run 31417242747; job 93549046687; success")

replace(
    INDEX,
    "| Android UI/UX redesign closure evidence | `docs/RUST_ANDROID_UI_UX_REDESIGN_CLOSURE_EVIDENCE_2026-08-10.md` | Authoritative shipped-state, exact-SHA CI, visual-evidence, anti-fallback, and manual-follow-up record for the completed Android redesign. |\n",
    "| Android UI/UX redesign closure evidence | `docs/RUST_ANDROID_UI_UX_REDESIGN_CLOSURE_EVIDENCE_2026-08-10.md` | Authoritative shipped-state, exact-SHA CI, visual-evidence, anti-fallback, and manual-follow-up record for the completed Android redesign. |\n| Android UI/UX review-fix closure evidence | `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md` | Authoritative exact-source-SHA CI and closure record for the completed bounded Android post-closure review-fix pass. |\n",
)
replace(INDEX, "`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md` (in progress as of this entry)", "`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md` (completed)")
replace(
    INDEX,
    "updated for the Android UI/UX post-closure review-fix pass on 2026-08-10: **81 TODO-named files total; 2 completed Rust-port authority documents; 0 active implementation TODOs; 1 Android closure-evidence authority; 1 authority index; 78 historical/planning TODO records including the archived Android tracker.**",
    "updated for the Android UI/UX post-closure review-fix pass on 2026-08-10, and reclassified at review-fix closure on 2026-08-10: **81 TODO-named files total; 2 completed Rust-port authority documents; 0 active implementation TODOs; 2 Android closure-evidence authorities; 1 authority index; 78 historical/planning TODO records including the archived Android tracker.**",
)

replace(AUDIT, 'android_ui_closure="docs/RUST_ANDROID_UI_UX_REDESIGN_CLOSURE_EVIDENCE_2026-08-10.md"\n', 'android_ui_closure="docs/RUST_ANDROID_UI_UX_REDESIGN_CLOSURE_EVIDENCE_2026-08-10.md"\nandroid_ui_review_fix_todo="docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md"\nandroid_ui_review_fix_closure="docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md"\n')
replace(AUDIT, '    "$android_ui_closure" \\\n    "$legacy_index"', '    "$android_ui_closure" \\\n    "$android_ui_review_fix_todo" \\\n    "$android_ui_review_fix_closure" \\\n    "$legacy_index"')
replace(AUDIT, "grep -Fq 'Status: complete — targeted Rust TUI hardening and diagnostic coverage integration validated.' \"$tui_coverage_report\"\n", "grep -Fq 'Status: complete — targeted Rust TUI hardening and diagnostic coverage integration validated.' \"$tui_coverage_report\"\ngrep -Fq '**Status:** Complete' \"$android_ui_review_fix_todo\"\ngrep -Fq '**Status:** Complete — bounded review-fix implementation and permanent exact-source-SHA validation passed' \"$android_ui_review_fix_closure\"\n")
replace(AUDIT, 'grep -Fq "\\`$android_ui_closure\\`" "$legacy_index"\n', 'grep -Fq "\\`$android_ui_closure\\`" "$legacy_index"\ngrep -Fq "\\`$android_ui_review_fix_todo\\`" "$legacy_index"\ngrep -Fq "\\`$android_ui_review_fix_closure\\`" "$legacy_index"\n')
replace(AUDIT, "grep -Fq '| Android UI/UX redesign closure evidence |' \"$legacy_index\"\n", "grep -Fq '| Android UI/UX redesign closure evidence |' \"$legacy_index\"\ngrep -Fq '| Android UI/UX review-fix closure evidence |' \"$legacy_index\"\n")
replace(AUDIT, "grep -Fq '81 TODO-named files total; 2 completed Rust-port authority documents; 0 active implementation TODOs; 1 Android closure-evidence authority; 1 authority index; 78 historical/planning TODO records including the archived Android tracker' \"$legacy_index\"", "grep -Fq '81 TODO-named files total; 2 completed Rust-port authority documents; 0 active implementation TODOs; 2 Android closure-evidence authorities; 1 authority index; 78 historical/planning TODO records including the archived Android tracker' \"$legacy_index\"")
replace(AUDIT, "grep -Fq 'A representative physical-phone UX pass was not performed' \"$android_ui_closure\"\n", "grep -Fq 'A representative physical-phone UX pass was not performed' \"$android_ui_closure\"\ngrep -Fq '**Validated final source SHA:** `6d9a84d910a3e6438aef390aa733a4b62a71dfdd`' \"$android_ui_review_fix_closure\"\ngrep -Fq 'Run: `31417242747`' \"$android_ui_review_fix_closure\"\ngrep -Fq 'Job: `93549046687`' \"$android_ui_review_fix_closure\"\ngrep -Fq 'Run: `31417240241`' \"$android_ui_review_fix_closure\"\ngrep -Fq 'Job `93549039534`' \"$android_ui_review_fix_closure\"\ngrep -Fq 'Job `93549039574`' \"$android_ui_review_fix_closure\"\ngrep -Fq 'Job `93549039612`' \"$android_ui_review_fix_closure\"\n")

run("git", "rm", str(TEMP_RUNNER.relative_to(ROOT)), str(TEMP_WORKFLOW.relative_to(ROOT)))
run("bash", "scripts/task_post_port_review_fix_audit.sh")
run("git", "diff", "--check")
run("git", "add", str(TODO.relative_to(ROOT)), str(INDEX.relative_to(ROOT)), str(AUDIT.relative_to(ROOT)), str(EVIDENCE.relative_to(ROOT)))
run("git", "commit", "-m", "docs(android): close UI review-fix program")
run("git", "push", "origin", "HEAD:master")
print(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip())
