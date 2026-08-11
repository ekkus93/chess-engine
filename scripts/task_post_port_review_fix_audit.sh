#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

tracker="docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
definitions="docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md"
postport_record="docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_TODO_2026-08-04.md"
v0_2_spec="docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_SPEC_2026-08-05.md"
v0_2_todo="docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md"
s3_spec="docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_SPEC_2026-08-07.md"
s3_todo="docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_TODO_2026-08-07.md"
s3_report="docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_IMPLEMENTATION_REPORT.md"
s4_spec="docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_SPEC_2026-08-07.md"
s4_todo="docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_TODO_2026-08-07.md"
hardening_spec="docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_SPEC_2026-08-07.md"
hardening_todo="docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_TODO_2026-08-07.md"
hardening_report="docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_IMPLEMENTATION_REPORT.md"
tui_todo="docs/RUST_TUI_TODO.md"
tui_coverage_spec="docs/RUST_TUI_TEST_COVERAGE_HARDENING_SPEC.md"
tui_coverage_todo="docs/RUST_TUI_TEST_COVERAGE_HARDENING_TODO.md"
tui_coverage_report="docs/RUST_TUI_TEST_COVERAGE_HARDENING_IMPLEMENTATION.md"
console_todo="docs/RUST_CONSOLE_TODO.md"
android_ui_todo="docs/RUST_ANDROID_UI_UX_REDESIGN_TODO_2026-08-10.md"
android_ui_closure="docs/RUST_ANDROID_UI_UX_REDESIGN_CLOSURE_EVIDENCE_2026-08-10.md"
android_ui_review_fix_todo="docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md"
android_ui_review_fix_closure="docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md"
android_ui_review_fix_corrections_spec="docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_SPEC_2026-08-10.md"
android_ui_review_fix_corrections_todo="docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md"
android_ui_review_fix_second_corrections_spec="docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SECOND_CORRECTIONS_SPEC_2026-08-10.md"
android_ui_review_fix_second_corrections_todo="docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SECOND_CORRECTIONS_TODO_2026-08-10.md"
legacy_index="docs/LEGACY_TODO_INDEX.md"
fen_doc="docs/RUST_FEN_AND_UCI_NOTATION.md"
fen_source="crates/chess-core/src/position/fen.rs"

for required in \
    "$tracker" \
    "$definitions" \
    "$postport_record" \
    "$v0_2_spec" \
    "$v0_2_todo" \
    "$s3_spec" \
    "$s3_todo" \
    "$s3_report" \
    "$s4_spec" \
    "$s4_todo" \
    "$hardening_spec" \
    "$hardening_todo" \
    "$hardening_report" \
    "$tui_todo" \
    "$tui_coverage_spec" \
    "$tui_coverage_todo" \
    "$tui_coverage_report" \
    "$console_todo" \
    "$android_ui_todo" \
    "$android_ui_closure" \
    "$android_ui_review_fix_todo" \
    "$android_ui_review_fix_closure" \
    "$android_ui_review_fix_corrections_spec" \
    "$android_ui_review_fix_corrections_todo" \
    "$android_ui_review_fix_second_corrections_spec" \
    "$android_ui_review_fix_second_corrections_todo" \
    "$legacy_index" \
    "$fen_doc" \
    "$fen_source"; do
    test -f "$required"
done

grep -Eq '^# Task 21: .* — COMPLETE$' "$tracker"
if grep -Eq '^# Task 21: .* — IN PROGRESS$' "$tracker"; then
    echo "stale Task 21 IN PROGRESS heading remains" >&2
    exit 1
fi
grep -Fq 'activated=false' "$tracker"
grep -Fqi 'baseline weights remain authoritative' "$tracker"
grep -Fqi 'separate strength change' "$tracker"
grep -Fq '**Status:** Complete' "$postport_record"
grep -Fq '**Status:** Complete — program closed without v0.2 promotion' "$v0_2_todo"
grep -Fq '**Status:** Complete — program closed without promotion' "$s3_todo"
grep -Fq '**Status:** Complete — program closed without promotion' "$s3_report"
grep -Fq '**Status:** Complete — tuning method accepted for future experimentation; no production promotion' "$s4_todo"
grep -Fq '**Status:** Complete — tuning method accepted for future experimentation; no production promotion' "$s4_spec"
grep -Fq '**Status:** Complete — closure hardening validated; no production promotion' "$hardening_todo"
grep -Fq '**Status:** Complete — closure hardening validated; no production promotion' "$hardening_spec"
grep -Fq '**Status:** Complete — closure hardening validated; no production promotion' "$hardening_report"
grep -Fq 'Status: automated implementation and permanent regression validation complete; manual real-terminal acceptance remains open.' "$tui_todo"
grep -Fq 'Status: complete — Rust TUI test/coverage hardening validated; coverage remains diagnostic and no engine/search/evaluation/tuning behavior changed.' "$tui_coverage_todo"
grep -Fq 'Status: complete — targeted Rust TUI hardening and diagnostic coverage integration validated.' "$tui_coverage_report"
grep -Fq '**Status:** Complete' "$android_ui_review_fix_todo"
grep -Fq '**Status:** Complete — bounded review-fix implementation and permanent exact-source-SHA validation passed' "$android_ui_review_fix_closure"
grep -Fq '**Status:** Complete' "$android_ui_review_fix_corrections_todo"
grep -Fq '`claims-downgraded`' "$android_ui_review_fix_corrections_todo"
grep -Fq '`documented blocker`' "$android_ui_review_fix_corrections_todo"
grep -Fq '`remediation-not-needed`' "$android_ui_review_fix_corrections_todo"

for stale in \
    '| Active v0.2 strength program |' \
    '| Active S3 evaluation strength program |' \
    '| Active S4 evaluation tuning calibration program |' \
    '| Active Rust console implementation |' \
    '| Active Android UI/UX redesign implementation |'; do
    if grep -Fq "$stale" "$legacy_index"; then
        echo "closed or superseded TODO is still classified as active: $stale" >&2
        exit 1
    fi
done

authority_todos=(
    "$tracker"
    "$definitions"
)
for authority in "${authority_todos[@]}"; do
    grep -Fq "\`$authority\`" "$legacy_index"
done
grep -Fq "\`$legacy_index\`" "$legacy_index"
grep -Fq "\`$postport_record\`" "$legacy_index"
grep -Fq "\`$v0_2_todo\`" "$legacy_index"
grep -Fq "\`$s3_todo\`" "$legacy_index"
grep -Fq "\`$s4_todo\`" "$legacy_index"
grep -Fq "\`$hardening_todo\`" "$legacy_index"
grep -Fq "\`$tui_todo\`" "$legacy_index"
grep -Fq "\`$tui_coverage_todo\`" "$legacy_index"
grep -Fq "\`$console_todo\`" "$legacy_index"
grep -Fq "\`$android_ui_todo\`" "$legacy_index"
grep -Fq "\`$android_ui_closure\`" "$legacy_index"
grep -Fq "\`$android_ui_review_fix_todo\`" "$legacy_index"
grep -Fq "\`$android_ui_review_fix_closure\`" "$legacy_index"
grep -Fq "\`$android_ui_review_fix_corrections_todo\`" "$legacy_index"
grep -Fq "\`$android_ui_review_fix_corrections_todo\` (completed" "$legacy_index"
grep -Fq "\`$android_ui_review_fix_second_corrections_todo\`" "$legacy_index"
if grep -Fq 'Active S4 evaluation tuning calibration program' "$legacy_index"; then
    echo 'closed S4 TODO is still active' >&2
    exit 1
fi
if grep -Fq '| Active S4 closure hardening program |' "$legacy_index"; then
    echo 'closure-candidate hardening TODO is still active' >&2
    exit 1
fi
grep -Fq '| Archived Android UI/UX redesign planning tracker |' "$legacy_index"
grep -Fq '| Android UI/UX redesign closure evidence |' "$legacy_index"
grep -Fq '| Android UI/UX review-fix closure evidence |' "$legacy_index"
grep -Fq 'There is currently **no active implementation TODO** registered by this index.' "$legacy_index"
grep -Fq 'Apart from this authority index, every other Markdown file directly under `docs/` whose filename contains `TODO`, is not one of the two completed Rust-port authority documents above, and is not explicitly registered as active in the authority table' "$legacy_index"
grep -Fq '83 TODO-named files total; 2 completed Rust-port authority documents; 0 active implementation TODOs; 2 Android closure-evidence authorities; 1 authority index; 80 historical/planning TODO records including the archived Android tracker' "$legacy_index"
grep -Fq '## Bounded review-fix trackers' "$legacy_index"
grep -Fq 'a bounded review-fix tracker being executable does not make it the active implementation authority for the program it patches' "$legacy_index"
bounded_review_fix_section="$(awk '
    /^## Bounded review-fix trackers$/ { in_section = 1; next }
    /^## Exhaustive classification rule$/ { in_section = 0 }
    in_section { print }
' "$legacy_index")"
for bounded_review_fix_tracker in \
    'docs/RUST_ENGINE_REVIEW_FIX_TODO_2026-08-02.md' \
    'docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_TODO_2026-08-04.md' \
    'docs/RUST_TUI_REVIEW_FIX_TODO_2026-08-09.md' \
    'docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md' \
    'docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md' \
    'docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SECOND_CORRECTIONS_TODO_2026-08-10.md'; do
    grep -Fq "\`$bounded_review_fix_tracker\`" <<<"$bounded_review_fix_section" || {
        echo "bounded review-fix tracker not listed under its classification: $bounded_review_fix_tracker" >&2
        exit 1
    }
done
grep -Fq '**Final product/evidence source SHA:** `a93c282699f380d604b214e0950372fd88e33585`' "$android_ui_closure"
grep -Fq '**Run:** `31383610431`' "$android_ui_closure"
grep -Fq '**Artifact ID:** `9060954512`' "$android_ui_closure"
grep -Fq 'A representative physical-phone UX pass was not performed' "$android_ui_closure"
grep -Fq '**Validated final source SHA:** `6d9a84d910a3e6438aef390aa733a4b62a71dfdd`' "$android_ui_review_fix_closure"
grep -Fq '**Authoritative closure-tree SHA:** `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84`' "$android_ui_review_fix_closure"
grep -Fq 'run `31419183264`' "$android_ui_review_fix_closure"
grep -Fq 'job `93555556721`' "$android_ui_review_fix_closure"
grep -Fq 'job `93555556826`' "$android_ui_review_fix_closure"
grep -Fq 'run `31419183273`' "$android_ui_review_fix_closure"
grep -Fq 'job `93555602583`' "$android_ui_review_fix_closure"
grep -Fq 'job `93555602709`' "$android_ui_review_fix_closure"
grep -Fq 'job `93555602727`' "$android_ui_review_fix_closure"
grep -Fq 'git diff --exit-code 6d9a84d910a3e6438aef390aa733a4b62a71dfdd..e9ab0fc623c22bd372ba9c8c2609dfcf74609f84 -- android-harness crates' "$android_ui_review_fix_closure"
grep -Fq "**Companion TODO:** \`$v0_2_todo\`" "$v0_2_spec"
grep -Fq "**Specification:** \`$v0_2_spec\`" "$v0_2_todo"
grep -Fq "**Companion TODO:** \`$s3_todo\`" "$s3_spec"
grep -Fq "**Specification:** \`$s3_spec\`" "$s3_todo"
grep -Fq "**Companion TODO:** \`$s4_todo\`" "$s4_spec"
grep -Fq "**Specification:** \`$s4_spec\`" "$s4_todo"
grep -Fq "**Companion TODO:** \`$hardening_todo\`" "$hardening_spec"
grep -Fq "**Specification:** \`$hardening_spec\`" "$hardening_todo"
grep -Fq "Companion TODO: \`$tui_coverage_todo\`" "$tui_coverage_spec"
grep -Fq "Companion specification: \`$tui_coverage_spec\`" "$tui_coverage_todo"
grep -Fq '# Task S3-7: Development strength validation — SKIPPED (NO ADVANCING CANDIDATE)' "$s3_todo"
grep -Fq '# Task S3-8: Optional new evaluation feature candidates — DEFERRED' "$s3_todo"
grep -Fq '# Task S3-10: Production candidate validation — SKIPPED (NO ELIGIBLE CANDIDATE)' "$s3_todo"
grep -Fq '# Task S3-11: Separate activation and release gate — SKIPPED (NO ACCEPTED CANDIDATE)' "$s3_todo"
grep -Fq '# Task S3-12: Final report, audit, cleanup, and closure — COMPLETE (NO PROMOTION)' "$s3_todo"
grep -Fq '# Task S4-0: Authority registration and baseline freeze — COMPLETE' "$s4_todo"
grep -Fq '# Task S4-12: Final report and closure — COMPLETE (NO PRODUCTION PROMOTION)' "$s4_todo"
grep -Fq '# Task H0: Authority registration and baseline freeze — COMPLETE' "$hardening_todo"
grep -Fq '# Task H6: Permanent audit and workflow integration — COMPLETE' "$hardening_todo"
grep -Fq '# Task H7: Final implementation report and authority cleanup — COMPLETE' "$hardening_todo"
grep -Fq 'H7 is complete.' "$hardening_report"

while IFS= read -r todo_path; do
    case "$todo_path" in
        "$tracker"|"$definitions"|"$legacy_index")
            ;;
        *)
            grep -Fq "\`$todo_path\`" "$legacy_index" || {
                echo "historical TODO missing from index: $todo_path" >&2
                exit 1
            }
            ;;
    esac
done < <(find docs -maxdepth 1 -type f -name '*TODO*.md' -print | sort)

grep -Fq 'strict syntax and structural **analysis-position** parser' "$fen_doc"
grep -Fq 'Structural acceptance is not certification of legal game reachability.' "$fen_doc"
grep -Fq 'remain a safe input to legal move generation' "$fen_doc"
grep -Fq 'Parses strict structural six-field FEN for safe analysis positions.' "$fen_source"
grep -Fq 'it is not proof that' "$fen_source"

for temporary in \
    ".github/ppr_implementation.py" \
    ".github/workflows/ppr-implementation.yml" \
    ".github/ppr_close.py" \
    ".github/workflows/ppr-closure.yml" \
    ".github/tui_coverage_hardening_patch.py" \
    ".github/tui_coverage_hardening_fix.py" \
    ".github/workflows/tui-coverage-hardening-implementation.yml" \
    ".github/tui_coverage_checklist_patch.py" \
    ".github/workflows/tui-coverage-checklist-validation.yml" \
    ".github/workflows/android-ui-gallery.yml" \
    ".github/android_ui_gallery.py" \
    ".github/android_closure_corrections_ralph.py" \
    ".github/workflows/android-closure-corrections-ralph.yml" \
    ".github/investigate_system_bars.sh"; do
    if test -e "$temporary"; then
        echo "temporary post-port helper remains: $temporary" >&2
        exit 1
    fi
done

bash scripts/task_26_v0_1_audit.sh
bash scripts/task_27_full_port_audit.sh

echo "post-port review fix and TODO-authority audit passed"
