from pathlib import Path

FINAL_VALIDATED_SHA = "040dbfa7d88df71380c9082d224f54b99e17c583"
CLOSURE_CANDIDATE_SHA = "c8f31b07562111034b3eb6bd0fd81e04c7185133"


def read(path: str) -> str:
    return Path(path).read_text()


def write(path: str, text: str) -> None:
    Path(path).write_text(text)


def replace_exact(path: str, old: str, new: str, count: int = 1) -> None:
    text = read(path)
    found = text.count(old)
    if found != count:
        raise SystemExit(f"{path}: expected {count} occurrence(s) of {old!r}, found {found}")
    write(path, text.replace(old, new, count))


def append_once(path: str, marker: str, body: str) -> None:
    text = read(path)
    if marker in text:
        return
    if not text.endswith("\n"):
        text += "\n"
    write(path, text + "\n" + body.rstrip() + "\n")


final_doc = f'''# Rust Chess Engine S4 Closure Hardening Final Validation — 2026-08-07

**Status:** Complete exact closed-authority validation evidence
**Closed-authority candidate SHA:** `{CLOSURE_CANDIDATE_SHA}`
**Exact validated hardening closure SHA:** `{FINAL_VALIDATED_SHA}`

## Permanent validation matrix

All required permanent workflows completed successfully on exact SHA `{FINAL_VALIDATED_SHA}`:

- CI run `31214468559`: x86-64 workspace-quality job `92984632692` success; ARM64 workspace-build job `92984632651` success.
- Performance run `31214473918`: ARM64 job `92984650575` success; x86-64 job `92984650722` success.
- Robustness run `31214467831`: native sanitizers/leak job `92984630799`, fuzz/corpus job `92984630807`, and Miri job `92984630842` all success.
- Android/JNI run `31214467810`: Android/Kotlin lint job `92984646200`, host-JVM JNI job `92984646272`, and API-35 JNI smoke job `92984646321` all success.
- S4 Evaluation Tuning Calibration run `31214467814`, guardrails job `92984630452`: success.
- Post-CI bounded report-publication run `31215644023`, report job `92988408595`: success.

CI passed the complete authority/audit chain, no-lint-suppression rule, lockfile drift check, formatting, workspace check, strict Clippy, all-target/all-feature workspace tests, authoritative release perft, documentation build, debug/release builds, UCI smoke, and pinned differential-oracle corpus/seeded playouts.

## Retained artifacts

The workflows that intentionally publish retained evidence produced:

- x86-64 Performance artifact `9007948263`, digest `sha256:4aa8e1ed737a51728b2a4edd8e98fac671be89307979c2476e45d4ac39aaf63b`;
- ARM64 Performance artifact `9007944932`, digest `sha256:a32c74557f09348a4856cc0591c798d2b472d321d958ae84eef967d13a8598cf`;
- Android Performance artifact `9008040056`, digest `sha256:48224d6b5da1d299caa9403a573f8642f4ba2b21d88847d24946f9b737f3a38a`.

CI, Robustness, S4, and report-publication intentionally retained no workflow artifacts for this run.

## Final disposition

The closure-hardening program is complete. The code-review findings were corrected without reopening tuning or changing production chess behavior. Package/UCI remains `0.1.0`; v0.1 search policy and evaluator weights remain production authority; candidate `520db5dd58086a8a` remains inactive and `rejected_strength`; no ABI/JNI/Kotlin/Android behavior, opening default, tablebase state, or production selector changed.
'''
Path("docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_FINAL_VALIDATION_2026-08-07.md").write_text(final_doc)

# Tracker completion.
todo = "docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_TODO_2026-08-07.md"
replace_exact(todo, "**Status:** Closure candidate — H0-H7.2 complete; final closed-SHA validation pending", "**Status:** Complete — closure hardening validated; no production promotion")
replace_exact(todo, "# Task H7: Final implementation report and authority cleanup — IN PROGRESS (FINAL VALIDATION PENDING)", "# Task H7: Final implementation report and authority cleanup — COMPLETE")
text = read(todo)
h7 = text.index("## H7.3 Final validation")
end_gate = text.index("---\n\n# Final hardening completion checklist", h7)
prefix, section, suffix = text[:h7], text[h7:end_gate], text[end_gate:]
section = section.replace("- [ ]", "- [x]")
section = section.replace(
    "## H7.3 Final validation\n",
    f"## H7.3 Final validation\n\nExact validated hardening closure SHA: `{FINAL_VALIDATED_SHA}`. Evidence: `docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_FINAL_VALIDATION_2026-08-07.md`.\n\n",
)
suffix = suffix.replace("- [ ] H7 final report and authority cleanup complete.", "- [x] H7 final report and authority cleanup complete.")
write(todo, prefix + section + suffix)

spec = "docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_SPEC_2026-08-07.md"
replace_exact(spec, "**Status:** Closure candidate — implementation complete; final closed-SHA validation pending", "**Status:** Complete — closure hardening validated; no production promotion")

report = "docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_IMPLEMENTATION_REPORT.md"
replace_exact(report, "**Status:** Closure candidate — implementation validated; final closed-SHA validation pending", "**Status:** Complete — closure hardening validated; no production promotion")
append_once(
    report,
    "## H7 exact final validation",
    f'''## H7 exact final validation

The exact closed-authority hardening SHA `{FINAL_VALIDATED_SHA}` passed the complete permanent matrix. `docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_FINAL_VALIDATION_2026-08-07.md` is the authoritative detailed record.

- CI `31214468559`: jobs `92984632692`, `92984632651` success.
- Performance `31214473918`: jobs `92984650575`, `92984650722` success.
- Robustness `31214467831`: jobs `92984630799`, `92984630807`, `92984630842` success.
- Android/JNI `31214467810`: jobs `92984646200`, `92984646272`, `92984646321` success.
- S4 `31214467814`: job `92984630452` success.
- post-CI report publication `31215644023`: job `92988408595` success.

Retained final evidence artifacts are Performance `9007948263` (`sha256:4aa8e1ed737a51728b2a4edd8e98fac671be89307979c2476e45d4ac39aaf63b`), Performance ARM64 `9007944932` (`sha256:a32c74557f09348a4856cc0591c798d2b472d321d958ae84eef967d13a8598cf`), and Android `9008040056` (`sha256:48224d6b5da1d299caa9403a573f8642f4ba2b21d88847d24946f9b737f3a38a`).

H7 is complete. The hardening tracker remains historical, there is no active implementation TODO, and no production promotion occurred.''',
)

# Post-port audit final statuses.
post = "scripts/task_post_port_review_fix_audit.sh"
replace_exact(post, "grep -Fq '**Status:** Closure candidate — H0-H7.2 complete; final closed-SHA validation pending' \"$hardening_todo\"\ngrep -Fq '**Status:** Closure candidate — implementation complete; final closed-SHA validation pending' \"$hardening_spec\"\ngrep -Fq '**Status:** Closure candidate — implementation validated; final closed-SHA validation pending' \"$hardening_report\"\n", "grep -Fq '**Status:** Complete — closure hardening validated; no production promotion' \"$hardening_todo\"\ngrep -Fq '**Status:** Complete — closure hardening validated; no production promotion' \"$hardening_spec\"\ngrep -Fq '**Status:** Complete — closure hardening validated; no production promotion' \"$hardening_report\"\n")
replace_exact(post, "grep -Fq '# Task H7: Final implementation report and authority cleanup — IN PROGRESS (FINAL VALIDATION PENDING)' \"$hardening_todo\"\ngrep -Fq 'H7.1 implementation reporting and H7.2 authority cleanup are complete' \"$hardening_report\"\n", "grep -Fq '# Task H7: Final implementation report and authority cleanup — COMPLETE' \"$hardening_todo\"\ngrep -Fq 'H7 is complete.' \"$hardening_report\"\n")

# S3 audit final tracker status.
s3 = "scripts/task_s3_evaluation_strength_audit.sh"
replace_exact(s3, "require_literal '**Status:** Closure candidate — H0-H7.2 complete; final closed-SHA validation pending' \"$hardening_todo\"\n", "require_literal '**Status:** Complete — closure hardening validated; no production promotion' \"$hardening_todo\"\n")

# S4 audit final evidence and statuses.
s4 = "scripts/task_s4_evaluation_tuning_calibration_audit.sh"
replace_exact(s4, 'hardening_report=docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_IMPLEMENTATION_REPORT.md\n', 'hardening_report=docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_IMPLEMENTATION_REPORT.md\nhardening_final=docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_FINAL_VALIDATION_2026-08-07.md\n')
replace_exact(s4, '"$final_addendum" "$hardening_report" "$legacy"', '"$final_addendum" "$hardening_report" "$hardening_final" "$legacy"')
replace_exact(s4, "require_literal '**Status:** Closure candidate — H0-H7.2 complete; final closed-SHA validation pending' \"$hardening_todo\"\nrequire_literal '**Status:** Closure candidate — implementation complete; final closed-SHA validation pending' \"$hardening_spec\"\nrequire_literal '**Status:** Closure candidate — implementation validated; final closed-SHA validation pending' \"$hardening_report\"\n", "require_literal '**Status:** Complete — closure hardening validated; no production promotion' \"$hardening_todo\"\nrequire_literal '**Status:** Complete — closure hardening validated; no production promotion' \"$hardening_spec\"\nrequire_literal '**Status:** Complete — closure hardening validated; no production promotion' \"$hardening_report\"\nrequire_literal '**Status:** Complete exact closed-authority validation evidence' \"$hardening_final\"\n")
replace_exact(s4, "require_literal '# Task H7: Final implementation report and authority cleanup — IN PROGRESS (FINAL VALIDATION PENDING)' \"$hardening_todo\"\n", "require_literal '# Task H7: Final implementation report and authority cleanup — COMPLETE' \"$hardening_todo\"\n")
append_once(
    s4,
    "# Final H7 closed-SHA evidence.",
    r'''# Final H7 closed-SHA evidence.
require_literal '040dbfa7d88df71380c9082d224f54b99e17c583' "$hardening_final"
require_literal '31214468559' "$hardening_final"
require_literal '92984632692' "$hardening_final"
require_literal '92984632651' "$hardening_final"
require_literal '31214473918' "$hardening_final"
require_literal '92984650575' "$hardening_final"
require_literal '92984650722' "$hardening_final"
require_literal '31214467831' "$hardening_final"
require_literal '92984630799' "$hardening_final"
require_literal '92984630807' "$hardening_final"
require_literal '92984630842' "$hardening_final"
require_literal '31214467810' "$hardening_final"
require_literal '92984646200' "$hardening_final"
require_literal '92984646272' "$hardening_final"
require_literal '92984646321' "$hardening_final"
require_literal '31214467814' "$hardening_final"
require_literal '92984630452' "$hardening_final"
require_literal '31215644023' "$hardening_final"
require_literal '92988408595' "$hardening_final"
require_literal '9007948263' "$hardening_final"
require_literal '4aa8e1ed737a51728b2a4edd8e98fac671be89307979c2476e45d4ac39aaf63b' "$hardening_final"
require_literal '9007944932' "$hardening_final"
require_literal 'a32c74557f09348a4856cc0591c798d2b472d321d958ae84eef967d13a8598cf' "$hardening_final"
require_literal '9008040056' "$hardening_final"
require_literal '48224d6b5da1d299caa9403a573f8642f4ba2b21d88847d24946f9b737f3a38a' "$hardening_final"
''',
)
# Expand temporary-control absence check for finalizer.
replace_exact(s4, '.github/s4_closure_hardening_close.py .github/workflows/s4-closure-hardening-close.yml; do', '.github/s4_closure_hardening_close.py .github/workflows/s4-closure-hardening-close.yml .github/s4_closure_hardening_finalize.py .github/workflows/s4-closure-hardening-finalize.yml; do')

print("S4 closure hardening final evidence transformation complete")
