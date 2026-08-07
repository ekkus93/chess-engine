from pathlib import Path

PLANNING_BASELINE = "bc406d78d673cc3258e8b522bcec25c4838f5e32"
IMPLEMENTATION_START = "9f5c398a70e22228454f0184225a414f1466cdf5"
SOURCE_IMPLEMENTATION = "e5b239e9c182b9f862ab6c603b0f235ee26ac7e8"
PREVALIDATION_SHA = "5d350b86ce924ea2a149312acf9e4b66e1d0251d"


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


report = f'''# Rust Chess Engine S4 Closure Hardening Implementation Report

**Status:** Closure candidate — implementation validated; final closed-SHA validation pending
**Date:** 2026-08-07
**Planning baseline SHA:** `{PLANNING_BASELINE}`
**Implementation-start SHA:** `{IMPLEMENTATION_START}`
**H0-H6 source implementation SHA:** `{SOURCE_IMPLEMENTATION}`
**Exact pre-closure validation SHA:** `{PREVALIDATION_SHA}`
**Production package/UCI version:** `0.1.0`
**Production activation:** unchanged / none

## Executive disposition

The S4 closure-hardening implementation resolves every code-review issue targeted by H0-H6 without reopening evaluator tuning or changing production chess behavior. The implementation is fully validated on exact SHA `{PREVALIDATION_SHA}`. This report is being published as part of H7 authority closure; the final closed-authority SHA must still pass the permanent matrix before H7.3 and the tracker can be marked complete.

Production identities remain unchanged:

- v0.1 search-policy identifier/checksum: `5630315f504f4c31` / `0c0769ef9d034770`;
- baseline evaluation-weight identifier/checksum: `424153454c494e45` / `d2cca7ae10ec6e34`;
- selected S4 calibration candidate value checksum: `520db5dd58086a8a`, still inactive and `rejected_strength`;
- package/UCI version: `0.1.0`;
- no ABI, JNI, Kotlin, Android, opening-default, tablebase, or production search-policy behavior change.

## H0 authority and baseline

The hardening program began from final S4 closure SHA `{PLANNING_BASELINE}`. The planning files advanced `master` to implementation-start SHA `{IMPLEMENTATION_START}`, at which point the hardening TODO became the sole active implementation tracker. Closed S2/S3/S4 tuning and strength programs remained historical and no production candidate was activated.

## H1 final S4 evidence correction

`docs/RUST_CHESS_ENGINE_S4_FINAL_VALIDATION_ADDENDUM_2026-08-07.md` now records the previously missing completed permanent matrix for original final S4 SHA `{PLANNING_BASELINE}`:

- CI `31208874474`: jobs `92966583551`, `92966583700` success;
- Performance `31208875019`: jobs `92966584891`, `92966585078` success;
- Robustness `31208875521`: jobs `92966586631`, `92966586666`, `92966586684` success;
- Android/JNI `31208874646`: jobs `92966594534`, `92966594629`, `92966594742` success;
- S4 `31208874643`: job `92966583439` success;
- report publication `31209467578`: job `92968530668` success.

Retained original final-S4 artifacts are also recorded with digests: Performance artifacts `9005860229` and `9005851414`, and Android artifact `9005947857`.

## H2 strict diagnostic-count validation

Changed `crates/chess-tune/src/diagnostics.rs` and `crates/chess-tune/src/trace.rs`.

`SpsaIterationDiagnostics::validate_counts()` now uses checked arithmetic and requires:

- positive + negative + zero gradient counts to equal the active count;
- zero-after-quantization + nonzero integer movement to be no greater than the active count;
- `changed_parameter_count == nonzero_integer_update_count`;
- clipped-update count to be no greater than the active count;
- active count to remain within `TUNABLE_PARAMETER_COUNT`.

Parser-level regressions `trace_rejects_impossible_quantization_update_partition` and `trace_rejects_changed_count_mismatch` prove malformed canonical trace rows fail closed. Existing canonical round-trip and corruption/binding tests remain green.

## H3 fail-visible staging cleanup

Changed `crates/chess-tools/src/tuning_cli.rs`.

The old discarded cleanup result was removed. A primary tuning publication failure is preserved, while a secondary failure to remove the staging directory is appended deterministically through `cleanup_staging_after_failure` / `cleanup_failure_message`. No fallback output directory, overwrite, ignored error, or retry path was introduced. `cleanup_failure_context_preserves_primary_error` covers the deterministic error-composition behavior; direct OS-level cleanup failure injection remains intentionally skipped as non-portable.

## H4 canonical source-commit parsing

Changed `crates/chess-tools/src/tuning_cli.rs`.

Tuning-config `source_commit` now requires exactly 40 lowercase hexadecimal characters, consistent with the strict S4 trace representation, and still rejects the all-zero identity. Regressions cover valid lowercase, uppercase rejection, mixed-case rejection, and short/invalid/zero inputs.

## H5 checkpoint materialization API decision

Changed `crates/chess-tune/src/optimizer.rs`.

Repository-wide caller inventory found zero callers of `SpsaCheckpoint::current_weights`; only the public method definition existed. Path B was selected: the unused method was removed rather than preserving ambiguous all-mask raw checkpoint projection. The safe `best_weights()` publication path remains, and `checkpoint_best_weights_preserve_inactive_parameters_after_masked_run` proves inactive values remain baseline-identical after a masked run. Existing resume checks continue to fail closed on config, dataset, objective, bounds, and runtime-weight mismatches.

## H6 audit/workflow integration

Updated:

- `scripts/task_post_port_review_fix_audit.sh`;
- `scripts/task_s3_evaluation_strength_audit.sh`;
- `scripts/task_s4_evaluation_tuning_calibration_audit.sh`;
- `docs/LEGACY_TODO_INDEX.md`;
- S4 hardening spec/TODO and original S4 evidence documents.

The permanent S4 workflow itself was not weakened or made write-capable. It remains `contents: read` and runs the permanent S4 audit, formatting, strict Clippy, complete `chess-tune` regressions, and complete `chess-tools` regressions.

## H0-H6 staging evidence

Temporary staging run `31212409405`, job `92978072080`, passed after the helper and workflow removed themselves from the working tree. It validated formatting, strict tuning/tooling Clippy, both regression suites, authority audit, S4 audit, and `git diff --check` before publishing `{SOURCE_IMPLEMENTATION}`.

The first staging attempt `31212279860`, job `92977651725`, failed only on generated Rust formatting and published nothing. The staging workflow was corrected to run `cargo fmt --all` before `--check`; no semantic gate was weakened.

## Exact implementation prevalidation

A normal repository write produced exact implementation-validation SHA `{PREVALIDATION_SHA}`. All required permanent workflows passed on that same SHA:

- CI run `31212586187`: x86-64 job `92978647071`, ARM64 job `92978647134` — success;
- Performance run `31212586069`: x86-64 job `92978646654`, ARM64 job `92978646729` — success;
- Robustness run `31212586338`: fuzz/corpus `92978647371`, Miri `92978647390`, sanitizers/leak `92978647427` — success;
- Android/JNI run `31212586580`: lint `92978665266`, API-35 JNI `92978665285`, host JVM JNI `92978665319` — success;
- S4 run `31212586025`, guardrails job `92978646315` — success;
- post-CI bounded report publication run `31213948156`, job `92983000347` — success.

Retained prevalidation artifacts:

- x86-64 Performance artifact `9007273737`, digest `sha256:140c626f08128b23504a44ffb331d903f0d573a365fe63814f5200bb464882c0`;
- ARM64 Performance artifact `9007261853`, digest `sha256:083cbdcbc4401db074af6d408a9c55604028af5b048b59a420bef80e0654af02`;
- Android Performance artifact `9007354662`, digest `sha256:f45d290c61b90827de212a5a113b7ea882c4c597f9ba3326ff71ca649d2721e1`.

## Source files changed

Behavioral Rust changes are limited to:

1. `crates/chess-tune/src/diagnostics.rs`;
2. `crates/chess-tune/src/trace.rs`;
3. `crates/chess-tune/src/optimizer.rs`;
4. `crates/chess-tools/src/tuning_cli.rs`.

All other hardening changes are evidence, authority, or audit documentation/scripts. No runtime search/evaluation implementation, public adapter, or Android production code was changed.

## H7 closure state

H7.1 implementation reporting and H7.2 authority cleanup are complete in this closure candidate. The hardening TODO is historical and there is no active implementation TODO. H7.3 remains pending until a normal repository write on this closed-authority state triggers and passes the permanent CI, Performance, Robustness, Android/JNI, S4, and report-publication gates. No final completion claim is made before that evidence exists.
'''
Path("docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_IMPLEMENTATION_REPORT.md").write_text(report)

# Tracker: H7.1/H7.2 done, H7.3 pending; tracker is a historical closure candidate, not yet final-complete evidence.
todo = "docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_TODO_2026-08-07.md"
replace_exact(todo, "**Status:** Active — H0-H6 implemented; permanent validation pending", "**Status:** Closure candidate — H0-H7.2 complete; final closed-SHA validation pending")
replace_exact(todo, "# Task H7: Final implementation report and authority cleanup — NOT STARTED", "# Task H7: Final implementation report and authority cleanup — IN PROGRESS (FINAL VALIDATION PENDING)")
text = read(todo)
start = text.index("## H7.1 Implementation report")
mid = text.index("## H7.3 Final validation")
prefix, first, rest = text[:start], text[start:mid], text[mid:]
first = first.replace("- [ ]", "- [x]")
# H7.3 remains unchecked; final checklist H0-H6 can now accurately be checked.
rest = rest.replace("- [ ] H0 authority and baseline freeze complete.", "- [x] H0 authority and baseline freeze complete.")
rest = rest.replace("- [ ] H1 final S4 validation evidence correction complete.", "- [x] H1 final S4 validation evidence correction complete.")
rest = rest.replace("- [ ] H2 strict diagnostic-count validation complete.", "- [x] H2 strict diagnostic-count validation complete.")
rest = rest.replace("- [ ] H3 fail-visible tuning-output staging cleanup complete.", "- [x] H3 fail-visible tuning-output staging cleanup complete.")
rest = rest.replace("- [ ] H4 canonical tuning source-commit parsing complete.", "- [x] H4 canonical tuning source-commit parsing complete.")
rest = rest.replace("- [ ] H5 checkpoint materialization API review complete.", "- [x] H5 checkpoint materialization API review complete.")
rest = rest.replace("- [ ] H6 permanent audit/workflow integration complete.", "- [x] H6 permanent audit/workflow integration complete.")
write(todo, prefix + first + rest)

spec = "docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_SPEC_2026-08-07.md"
replace_exact(spec, "**Status:** Active — closure hardening implementation in progress", "**Status:** Closure candidate — implementation complete; final closed-SHA validation pending")

# Authority index: move hardening TODO to historical inventory while final closed-state validation is pending.
legacy = "docs/LEGACY_TODO_INDEX.md"
replace_exact(legacy, "| Active S4 closure hardening program | `docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_TODO_2026-08-07.md` | Single active implementation tracker for the post-S4 closure hardening pass. |\n", "")
replace_exact(legacy, "The S4 closure-hardening TODO is the single active implementation tracker. Closed S2, S3, and S4 strength/tuning-program TODOs remain historical and cannot override the completed Rust-port authority records or this explicitly registered hardening program.", "There is no active implementation TODO. Closed S2, S3, S4 strength/tuning, and S4 closure-hardening TODOs are historical and cannot override the completed Rust-port authority records or a future TODO explicitly registered in this table.")
replace_exact(legacy, "not one of the three authority documents above", "not one of the two completed-authority documents above")
replace_exact(legacy, "**75 TODO-named files total; 3 authority documents; 1 authority index; 71 historical.**", "**75 TODO-named files total; 2 authority documents; 1 authority index; 72 historical.**")
replace_exact(legacy, "- `docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_TODO_2026-08-07.md`\n", "- `docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_TODO_2026-08-07.md`\n- `docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_TODO_2026-08-07.md`\n")

# Post-port authority audit: closed hardening candidate is historical; no active TODO.
post = "scripts/task_post_port_review_fix_audit.sh"
replace_exact(post, 'hardening_todo="docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_TODO_2026-08-07.md"\n', 'hardening_todo="docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_TODO_2026-08-07.md"\nhardening_report="docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_IMPLEMENTATION_REPORT.md"\n')
replace_exact(post, '    "$hardening_todo" \\\n    "$legacy_index" \\', '    "$hardening_todo" \\\n    "$hardening_report" \\\n    "$legacy_index" \\')
replace_exact(post, "grep -Fq '**Status:** Active — H0-H6 implemented; permanent validation pending' \"$hardening_todo\"\ngrep -Fq '**Status:** Active — closure hardening implementation in progress' \"$hardening_spec\"\n", "grep -Fq '**Status:** Closure candidate — H0-H7.2 complete; final closed-SHA validation pending' \"$hardening_todo\"\ngrep -Fq '**Status:** Closure candidate — implementation complete; final closed-SHA validation pending' \"$hardening_spec\"\ngrep -Fq '**Status:** Closure candidate — implementation validated; final closed-SHA validation pending' \"$hardening_report\"\n")
replace_exact(post, '    "$definitions"\n    "$hardening_todo"\n)', '    "$definitions"\n)')
replace_exact(post, "grep -Fq '| Active S4 closure hardening program |' \"$legacy_index\"\ngrep -Fq 'The S4 closure-hardening TODO is the single active implementation tracker.' \"$legacy_index\"\n", "if grep -Fq '| Active S4 closure hardening program |' \"$legacy_index\"; then\n    echo 'closure-candidate hardening TODO is still active' >&2\n    exit 1\nfi\ngrep -Fq 'There is no active implementation TODO.' \"$legacy_index\"\n")
replace_exact(post, 'not one of the three authority documents above', 'not one of the two completed-authority documents above')
replace_exact(post, '75 TODO-named files total; 3 authority documents; 1 authority index; 71 historical', '75 TODO-named files total; 2 authority documents; 1 authority index; 72 historical')
replace_exact(post, "grep -Fq '# Task H6: Permanent audit and workflow integration — COMPLETE' \"$hardening_todo\"\n", "grep -Fq '# Task H6: Permanent audit and workflow integration — COMPLETE' \"$hardening_todo\"\ngrep -Fq '# Task H7: Final implementation report and authority cleanup — IN PROGRESS (FINAL VALIDATION PENDING)' \"$hardening_todo\"\ngrep -Fq 'H7.1 implementation reporting and H7.2 authority cleanup are complete' \"$hardening_report\"\n")
replace_exact(post, '"$tracker"|"$definitions"|"$hardening_todo"|"$legacy_index")', '"$tracker"|"$definitions"|"$legacy_index")')

# S3 audit: require hardening historical closure-candidate state.
s3 = "scripts/task_s3_evaluation_strength_audit.sh"
replace_exact(s3, "require_literal '| Active S4 closure hardening program |' \"$legacy\"\nrequire_literal '**Status:** Active — H0-H6 implemented; permanent validation pending' \"$hardening_todo\"\n", "if grep -Fq '| Active S4 closure hardening program |' \"$legacy\"; then\n  fail 'closure-candidate hardening TODO is still active'\nfi\nrequire_literal 'There is no active implementation TODO.' \"$legacy\"\nrequire_literal '**Status:** Closure candidate — H0-H7.2 complete; final closed-SHA validation pending' \"$hardening_todo\"\n")

# S4 audit: closed hardening candidate + report, retain H1-H6 source witnesses.
s4 = "scripts/task_s4_evaluation_tuning_calibration_audit.sh"
replace_exact(s4, 'final_addendum=docs/RUST_CHESS_ENGINE_S4_FINAL_VALIDATION_ADDENDUM_2026-08-07.md\n', 'final_addendum=docs/RUST_CHESS_ENGINE_S4_FINAL_VALIDATION_ADDENDUM_2026-08-07.md\nhardening_report=docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_IMPLEMENTATION_REPORT.md\n')
replace_exact(s4, '"$hardening_spec" "$hardening_todo" "$final_addendum" "$legacy"', '"$hardening_spec" "$hardening_todo" "$final_addendum" "$hardening_report" "$legacy"')
replace_exact(s4, "require_literal '| Active S4 closure hardening program |' \"$legacy\"\nrequire_literal '75 TODO-named files total; 3 authority documents; 1 authority index; 71 historical' \"$legacy\"\nrequire_literal '**Status:** Active — H0-H6 implemented; permanent validation pending' \"$hardening_todo\"\nrequire_literal '**Status:** Active — closure hardening implementation in progress' \"$hardening_spec\"\n", "if grep -Fq '| Active S4 closure hardening program |' \"$legacy\"; then\n  fail 'closure-candidate hardening TODO is still active'\nfi\nrequire_literal 'There is no active implementation TODO.' \"$legacy\"\nrequire_literal '75 TODO-named files total; 2 authority documents; 1 authority index; 72 historical' \"$legacy\"\nrequire_literal '**Status:** Closure candidate — H0-H7.2 complete; final closed-SHA validation pending' \"$hardening_todo\"\nrequire_literal '**Status:** Closure candidate — implementation complete; final closed-SHA validation pending' \"$hardening_spec\"\nrequire_literal '**Status:** Closure candidate — implementation validated; final closed-SHA validation pending' \"$hardening_report\"\n")
# Replace end H-task witnesses to include H7/report.
replace_exact(s4, "require_literal '# Task H6: Permanent audit and workflow integration — COMPLETE' \"$hardening_todo\"\n", "require_literal '# Task H6: Permanent audit and workflow integration — COMPLETE' \"$hardening_todo\"\nrequire_literal '# Task H7: Final implementation report and authority cleanup — IN PROGRESS (FINAL VALIDATION PENDING)' \"$hardening_todo\"\nrequire_literal '31212586187' \"$hardening_report\"\nrequire_literal '31212586069' \"$hardening_report\"\nrequire_literal '31212586338' \"$hardening_report\"\nrequire_literal '31212586580' \"$hardening_report\"\nrequire_literal '31212586025' \"$hardening_report\"\nrequire_literal '31213948156' \"$hardening_report\"\n")
# Add closure temp controls to absence check.
replace_exact(s4, 'for temporary in .github/s4_closure_hardening_apply.py .github/workflows/s4-closure-hardening-apply.yml; do', 'for temporary in .github/s4_closure_hardening_apply.py .github/workflows/s4-closure-hardening-apply.yml .github/s4_closure_hardening_close.py .github/workflows/s4-closure-hardening-close.yml; do')

print("S4 closure hardening H7 closure-candidate transformation complete")
