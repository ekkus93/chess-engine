from pathlib import Path

PRE = "b66b256a5b81621ba5310a749b7b93e650cc6067"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def write(path: str, text: str) -> None:
    Path(path).write_text(text)


todo_path = "docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_TODO_2026-08-07.md"
todo = Path(todo_path).read_text()
todo = replace_once(
    todo,
    "**Status:** Closure candidate — S4-0 through S4-11 complete; S4-12 exact final validation pending",
    "**Status:** Complete — tuning method accepted for future experimentation; no production promotion",
    "TODO status",
)
todo = replace_once(
    todo,
    "# Task S4-12: Final report and closure — IN PROGRESS (EXACT FINAL VALIDATION PENDING)",
    "# Task S4-12: Final report and closure — COMPLETE (NO PRODUCTION PROMOTION)",
    "S4-12 heading",
)
for line in [
    "- [ ] Record exact baseline and final SHAs.",
    "- [ ] Move this TODO from active authority to historical inventory when S4 closes.",
    "- [ ] Update `docs/LEGACY_TODO_INDEX.md` counts/classification.",
    "- [ ] Update permanent TODO-authority audit.",
    "- [ ] Run permanent S4 audit.",
    "- [ ] Run strict workspace CI.",
    "- [ ] Run performance validation if hot-path code changed.",
    "- [ ] Run robustness validation.",
    "- [ ] Run Android/JNI validation if adapter-facing code changed.",
    "- [ ] Run report validation.",
    "- [ ] Record exact final SHA, run IDs, job IDs, artifact IDs, and checksums.",
    "- [ ] S4 is truthfully closed with exact evidence and no production activation.",
    "- [ ] S4-12 final report and closure complete.",
]:
    todo = replace_once(todo, line, line.replace("- [ ]", "- [x]", 1), line)
marker = "## S4-12 gate\n\n"
evidence = (
    "### Exact validated pre-closure implementation evidence\n\n"
    f"- Validated implementation/closure-candidate SHA: `{PRE}`.\n"
    "- CI run/job: `31206849862` / `92960021815` (x86-64 workspace quality) and `92960021848` (ARM64 workspace build): success.\n"
    "- Performance run/jobs: `31206850107` / `92959950041`, `92959950085`: success.\n"
    "- Robustness run/jobs: `31206849667` / `92959948563`, `92959948579`, `92959948606`: success.\n"
    "- Android/JNI run/jobs: `31206849700` / `92959948648`, `92959948684`, `92959948749`: success.\n"
    "- S4 permanent gate run/job: `31206849866` / `92959950456`: success.\n"
    "- Report-master publication run/job: `31208328421` / `92964797405`: success.\n"
    "- S4-10 artifact: `9003757817`, ZIP SHA-256 `df04923ebc25fe811b5e8c945181b7ce3b1cdb02eefff5f6e1c422600b6de0f5`.\n"
    "- No S4 candidate was activated; v0.1 remains production authority.\n\n"
)
todo = replace_once(todo, marker, evidence + marker, "TODO evidence block")
write(todo_path, todo)

spec_path = "docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_SPEC_2026-08-07.md"
spec = Path(spec_path).read_text()
spec = replace_once(
    spec,
    "**Status:** Closure candidate; implementation complete through S4-11, exact final validation pending",
    "**Status:** Complete — tuning method accepted for future experimentation; no production promotion",
    "spec status",
)
write(spec_path, spec)

report_path = "docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_IMPLEMENTATION_REPORT.md"
report = Path(report_path).read_text()
report = replace_once(
    report,
    "**Status:** Closure candidate — exact final validation pending",
    "**Status:** Complete — method accepted for future experimentation; selected candidate rejected; no production promotion",
    "report status",
)
old_report_closure = """## S4-12 closure state

The technical implementation and evidence through S4-11 are complete. This report is the Phase-A closure candidate. Permanent exact-SHA CI, performance, robustness, Android/JNI, S4 audit, and report-validation evidence must pass before the tracker moves from active authority to historical and this report changes to final closed status.

This documentation-only commit is the explicit permanent-workflow validation trigger; it does not change engine behavior, evidence semantics, candidate state, or release authority.

No activation occurred anywhere in S4.
"""
new_report_closure = f"""## S4-12 closure state

S4 is closed without production promotion. The tuning method is accepted for future controlled evaluator experimentation, while the selected calibration candidate remains explicitly rejected by development chess-strength evidence.

The exact validated pre-closure implementation SHA is `{PRE}`. The permanent matrix on that same SHA is green:

- CI run `31206849862`: x86-64 workspace-quality job `92960021815` success; ARM64 workspace-build job `92960021848` success;
- Performance run `31206850107`: x86-64 job `92959950041` success; ARM64 job `92959950085` success;
- Robustness run `31206849667`: sanitizer/leak job `92959948563`, Miri job `92959948579`, and fuzz/corpus job `92959948606` all success;
- Android/JNI run `31206849700`: API-35 JNI smoke `92959948648`, Android/Kotlin lint `92959948684`, and host JVM JNI contract `92959948749` all success;
- S4 Evaluation Tuning Calibration run `31206849866`, job `92959950456`: success;
- bounded report publication run `31208328421`, job `92964797405`: success.

Closure also fixed three first-party repository defects without weakening gates: the obsolete lint suppression in `s3_candidate.rs` was removed, `fuzz/Cargo.lock` was deterministically refreshed under the existing drift check, and the saturated issue-comment reporter was converted to a serialized bounded issue-body update while retaining fail-on-error behavior.

The S4 TODO is historical after this closure. There is no active implementation TODO. The completed Rust-port authority documents and this authority index remain the standing authority until a future program is explicitly registered.

No activation occurred anywhere in S4. Package/UCI version `0.1.0`, the v0.1 evaluator/search policy, ABI/JNI/Android surface, opening default, and tablebase state remain unchanged.
"""
report = replace_once(report, old_report_closure, new_report_closure, "report closure state")
write(report_path, report)

index_path = "docs/LEGACY_TODO_INDEX.md"
index = Path(index_path).read_text()
index = replace_once(
    index,
    "| Active S4 evaluation tuning calibration program | `docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_TODO_2026-08-07.md` | Active implementation tracker for S4 optimizer/tuning-signal calibration. |\n",
    "",
    "remove active S4 row",
)
index = replace_once(
    index,
    "The S4 evaluation tuning calibration TODO is the single active implementation tracker. Closed S2 and S3 strength-program TODOs remain historical and cannot override S4 or the completed Rust-port authority records.",
    "There is no active implementation TODO. Closed S2, S3, and S4 strength/tuning-program TODOs are historical and cannot override the completed Rust-port authority records or a future TODO explicitly registered in this table.",
    "index active paragraph",
)
index = replace_once(
    index,
    "not one of the three authority documents above",
    "not one of the two completed-authority documents above",
    "index authority count phrase",
)
index = replace_once(
    index,
    "must not override the active S4 tracker, the completed Rust-port authority records, or any future TODO explicitly registered in the authority table.",
    "must not override the completed Rust-port authority records or any future TODO explicitly registered in the authority table.",
    "index override phrase",
)
index = replace_once(
    index,
    "Inventory captured on 2026-08-05, reclassified at S2-16 closure on 2026-08-07, activated for S3 on 2026-08-07, reclassified again at S3 closure on 2026-08-07, and activated for S4 on 2026-08-07: **74 TODO-named files total; 3 authority documents; 1 authority index; 70 historical.**",
    "Inventory captured on 2026-08-05, reclassified at S2-16 closure on 2026-08-07, activated for S3 on 2026-08-07, reclassified again at S3 closure on 2026-08-07, activated for S4 on 2026-08-07, and reclassified at S4 closure on 2026-08-07: **74 TODO-named files total; 2 authority documents; 1 authority index; 71 historical.**",
    "index inventory counts",
)
s3_line = "- `docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_TODO_2026-08-07.md`\n"
index = replace_once(
    index,
    s3_line,
    s3_line + "- `docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_TODO_2026-08-07.md`\n",
    "historical S4 insertion",
)
write(index_path, index)

post_path = "scripts/task_post_port_review_fix_audit.sh"
post = Path(post_path).read_text()
post = replace_once(
    post,
    "grep -Fq '**Status:** Closure candidate — S4-0 through S4-11 complete; S4-12 exact final validation pending' \"$s4_todo\"",
    "grep -Fq '**Status:** Complete — tuning method accepted for future experimentation; no production promotion' \"$s4_todo\"",
    "post S4 TODO status",
)
post = replace_once(
    post,
    "grep -Fq '**Status:** Closure candidate; implementation complete through S4-11, exact final validation pending' \"$s4_spec\"",
    "grep -Fq '**Status:** Complete — tuning method accepted for future experimentation; no production promotion' \"$s4_spec\"",
    "post S4 spec status",
)
post = replace_once(
    post,
    "for stale in '| Active v0.2 strength program |' '| Active S3 evaluation strength program |'; do",
    "for stale in '| Active v0.2 strength program |' '| Active S3 evaluation strength program |' '| Active S4 evaluation tuning calibration program |'; do",
    "post stale programs",
)
post = replace_once(
    post,
    'authority_todos=(\n    "$s4_todo"\n    "$tracker"\n    "$definitions"\n)',
    'authority_todos=(\n    "$tracker"\n    "$definitions"\n)',
    "post authority todos",
)
old_index_witnesses = """grep -Fq 'Active S4 evaluation tuning calibration program' "$legacy_index"
grep -Fq 'The S4 evaluation tuning calibration TODO is the single active implementation tracker.' "$legacy_index"
grep -Fq 'Apart from this authority index, every other Markdown file directly under `docs/` whose filename contains `TODO` and is not one of the three authority documents above' "$legacy_index"
grep -Fq '74 TODO-named files total; 3 authority documents; 1 authority index; 70 historical' "$legacy_index""" 
new_index_witnesses = """grep -Fq "\`$s4_todo\`" "$legacy_index"
if grep -Fq 'Active S4 evaluation tuning calibration program' "$legacy_index"; then
    echo 'closed S4 TODO is still active' >&2
    exit 1
fi
grep -Fq 'There is no active implementation TODO.' "$legacy_index"
grep -Fq 'Apart from this authority index, every other Markdown file directly under `docs/` whose filename contains `TODO` and is not one of the two completed-authority documents above' "$legacy_index"
grep -Fq '74 TODO-named files total; 2 authority documents; 1 authority index; 71 historical' "$legacy_index"""
post = replace_once(post, old_index_witnesses, new_index_witnesses, "post index witnesses")
post = replace_once(
    post,
    "grep -Fq '# Task S4-12: Final report and closure — IN PROGRESS (EXACT FINAL VALIDATION PENDING)' \"$s4_todo\"",
    "grep -Fq '# Task S4-12: Final report and closure — COMPLETE (NO PRODUCTION PROMOTION)' \"$s4_todo\"",
    "post S4-12",
)
post = replace_once(
    post,
    '"$s4_todo"|"$tracker"|"$definitions"|"$legacy_index")',
    '"$tracker"|"$definitions"|"$legacy_index")',
    "post historical case",
)
write(post_path, post)

audit_path = "scripts/task_s4_evaluation_tuning_calibration_audit.sh"
audit = Path(audit_path).read_text()
old_authority = """# S4 is the only active program; S3 remains closed and historical.
require_literal 'Active S4 evaluation tuning calibration program' "$legacy"
require_literal '`docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_TODO_2026-08-07.md`' "$legacy"
require_literal '**Status:** Closure candidate — S4-0 through S4-11 complete; S4-12 exact final validation pending' "$tracker"
require_literal '**Status:** Closure candidate; implementation complete through S4-11, exact final validation pending' "$spec"
require_literal '**Status:** Complete — program closed without promotion' "$s3_tracker"
if grep -Fq '| Active S3 evaluation strength program |' "$legacy"; then
  fail 'closed S3 tracker is active again'
fi"""
new_authority = """# S4 is closed and historical; S3 remains closed and historical.
require_literal '`docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_TODO_2026-08-07.md`' "$legacy"
require_literal 'There is no active implementation TODO.' "$legacy"
require_literal '74 TODO-named files total; 2 authority documents; 1 authority index; 71 historical' "$legacy"
require_literal '**Status:** Complete — tuning method accepted for future experimentation; no production promotion' "$tracker"
require_literal '**Status:** Complete — tuning method accepted for future experimentation; no production promotion' "$spec"
require_literal '**Status:** Complete — program closed without promotion' "$s3_tracker"
for stale in '| Active S3 evaluation strength program |' '| Active S4 evaluation tuning calibration program |'; do
  if grep -Fq "$stale" "$legacy"; then
    fail "closed program is active again: $stale"
  fi
done"""
audit = replace_once(audit, old_authority, new_authority, "S4 audit authority block")
audit = replace_once(
    audit,
    "require_literal '**Status:** Closure candidate — exact final validation pending' \"$final_report\"",
    "require_literal '**Status:** Complete — method accepted for future experimentation; selected candidate rejected; no production promotion' \"$final_report\"",
    "S4 audit final report status",
)
audit = replace_once(
    audit,
    "require_literal '# Task S4-12: Final report and closure — IN PROGRESS (EXACT FINAL VALIDATION PENDING)' \"$tracker\"",
    "require_literal '# Task S4-12: Final report and closure — COMPLETE (NO PRODUCTION PROMOTION)' \"$tracker\"\nrequire_literal 'b66b256a5b81621ba5310a749b7b93e650cc6067' \"$final_report\"\nrequire_literal '31206849862' \"$final_report\"\nrequire_literal '31206850107' \"$final_report\"\nrequire_literal '31206849667' \"$final_report\"\nrequire_literal '31206849700' \"$final_report\"\nrequire_literal '31206849866' \"$final_report\"\nrequire_literal '31208328421' \"$final_report\"",
    "S4 audit closure evidence",
)
audit = replace_once(
    audit,
    "echo 'S4 evaluation-tuning calibration closure-candidate audit passed'",
    "echo 'S4 evaluation-tuning calibration closure audit passed'",
    "S4 audit final message",
)
write(audit_path, audit)
