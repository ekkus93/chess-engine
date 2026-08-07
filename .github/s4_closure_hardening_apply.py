from pathlib import Path

IMPLEMENTATION_START_SHA = "9f5c398a70e22228454f0184225a414f1466cdf5"
FINAL_S4_SHA = "bc406d78d673cc3258e8b522bcec25c4838f5e32"
PRE_CLOSURE_SHA = "b66b256a5b81621ba5310a749b7b93e650cc6067"


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


def append_once(path: str, marker: str, text: str) -> None:
    current = read(path)
    if marker in current:
        return
    if not current.endswith("\n"):
        current += "\n"
    write(path, current + "\n" + text.rstrip() + "\n")


# H0: register the hardening program as the sole active implementation authority.
replace_exact(
    "docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_SPEC_2026-08-07.md",
    "**Status:** Proposed planning authority; implementation not yet started",
    "**Status:** Active — closure hardening implementation in progress",
)
replace_exact(
    "docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_SPEC_2026-08-07.md",
    f"**Planning baseline SHA:** `{FINAL_S4_SHA}`\n",
    f"**Planning baseline SHA:** `{FINAL_S4_SHA}`\n**Implementation-start SHA:** `{IMPLEMENTATION_START_SHA}`\n",
)

hardening_todo = "docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_TODO_2026-08-07.md"
replace_exact(hardening_todo, "**Status:** Proposed — not yet implemented", "**Status:** Active — H0-H6 implemented; permanent validation pending")
replace_exact(
    hardening_todo,
    f"**Planning baseline SHA:** `{FINAL_S4_SHA}`\n",
    f"**Planning baseline SHA:** `{FINAL_S4_SHA}`\n**Implementation-start SHA:** `{IMPLEMENTATION_START_SHA}`\n",
)
text = read(hardening_todo)
start = text.index("# Task H0:")
end = text.index("# Task H7:")
prefix, middle, suffix = text[:start], text[start:end], text[end:]
for task in range(7):
    middle = middle.replace(f"# Task H{task}:" + middle.split(f"# Task H{task}:", 1)[1].split("\n", 1)[0], f"# Task H{task}:" + middle.split(f"# Task H{task}:", 1)[1].split("\n", 1)[0].replace("— NOT STARTED", "— COMPLETE"), 1)
middle = middle.replace("- [ ]", "- [x]")
middle = middle.replace(
    "- [x] If direct filesystem cleanup failure is impractical to test portably, document why and rely on source/audit witness for the no-silent-discard invariant.",
    "- [x] SKIPPED — direct OS-level cleanup failure injection is not portable; the pure secondary-context formatter is tested and the production cleanup call is source/audit witnessed.",
)
middle = middle.replace(
    "- [x] Path A: add or change an API to require explicit projection mask/reference values for checkpoint materialization.",
    "- [x] SKIPPED — Path A was unnecessary because repo-wide caller inventory found no caller of `SpsaCheckpoint::current_weights`.",
)
middle = middle.replace(
    "- [x] Path B: make `current_weights` private or test-only if no public caller needs it.",
    "- [x] Path B selected: remove the unused public `SpsaCheckpoint::current_weights` method entirely; no caller depends on it.",
)
middle = middle.replace(
    "- [x] Path C: document and test the current method as intentional raw full-vector projection.",
    "- [x] SKIPPED — Path C would preserve the ambiguous all-mask materialization footgun and was not selected.",
)
middle = middle.replace(
    "## H5.1 Caller inventory\n",
    "## H5.1 Caller inventory\n\nCaller inventory result: GitHub code search for `current_weights(` returned only the method definition in `crates/chess-tune/src/optimizer.rs`; there are zero production, workflow, or test callers.\n",
)
write(hardening_todo, prefix + middle + suffix)

legacy = "docs/LEGACY_TODO_INDEX.md"
replace_exact(
    legacy,
    "| Authority index, not an implementation TODO | `docs/LEGACY_TODO_INDEX.md` | Classifies active, completed-authority, and historical TODO-named documents. |",
    "| Active S4 closure hardening program | `docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_TODO_2026-08-07.md` | Single active implementation tracker for the post-S4 closure hardening pass. |\n| Authority index, not an implementation TODO | `docs/LEGACY_TODO_INDEX.md` | Classifies active, completed-authority, and historical TODO-named documents. |",
)
replace_exact(
    legacy,
    "There is no active implementation TODO. Closed S2, S3, and S4 strength/tuning-program TODOs are historical and cannot override the completed Rust-port authority records or a future TODO explicitly registered in this table.",
    "The S4 closure-hardening TODO is the single active implementation tracker. Closed S2, S3, and S4 strength/tuning-program TODOs remain historical and cannot override the completed Rust-port authority records or this explicitly registered hardening program.",
)
replace_exact(
    legacy,
    "Apart from this authority index, every other Markdown file directly under `docs/` whose filename contains `TODO` and is not one of the two completed-authority documents above is a historical or legacy reference.",
    "Apart from this authority index, every other Markdown file directly under `docs/` whose filename contains `TODO` and is not one of the three authority documents above is a historical or legacy reference.",
)
replace_exact(
    legacy,
    "**74 TODO-named files total; 2 authority documents; 1 authority index; 71 historical.**",
    "**75 TODO-named files total; 3 authority documents; 1 authority index; 71 historical.**",
)

# H1: exact final S4 closure evidence correction.
addendum = f'''# Rust Chess Engine S4 Final Validation Addendum — 2026-08-07

**Status:** Complete evidence correction
**Final closed S4 SHA:** `{FINAL_S4_SHA}`
**Pre-closure implementation SHA:** `{PRE_CLOSURE_SHA}`

## Purpose

This addendum closes the S4-12.3 repository-evidence gap. The original S4 implementation report recorded the fully green pre-closure implementation matrix but did not persist the completed permanent matrix for the final closed SHA. The final closed SHA was validated successfully; the exact run/job evidence is recorded here without changing the S4 tuning or strength disposition.

## Final exact-SHA permanent matrix

- CI run `31208874474`: x86-64 workspace-quality job `92966583551` success; ARM64 workspace-build job `92966583700` success.
- Performance run `31208875019`: x86-64 job `92966584891` success; ARM64 job `92966585078` success.
- Robustness run `31208875521`: sanitizer/leak job `92966586631`, Miri job `92966586666`, and fuzz/corpus job `92966586684` all success.
- Android/JNI run `31208874646`: host JVM JNI job `92966594534`, API-35 JNI smoke job `92966594629`, and Android/Kotlin lint job `92966594742` all success.
- S4 Evaluation Tuning Calibration run `31208874643`, guardrails job `92966583439`: success.
- Final bounded report-publication run `31209467578`, report job `92968530668`: success.

## Final exact-SHA artifacts

The final CI, Robustness, S4, and report-publication workflows did not publish retained workflow artifacts. The final Performance and Android workflows did:

- x86-64 performance artifact `9005860229`, digest `sha256:237302e15ac2113777423f275a8aa0e1377425f5fd45fdbfd1df877aadce9614`;
- ARM64 performance artifact `9005851414`, digest `sha256:a3a3381b9383f506523efbb489e652c968f5c35d70d26a1e554785f7a6fc40d3`;
- Android performance artifact `9005947857`, digest `sha256:afc6106218a8056922c6e17c5db9b967e43aa9abe55115cf42087e2f0b720667`.

## Disposition preserved

The S4 method remains accepted only for future controlled evaluator experimentation. Candidate value checksum `520db5dd58086a8a` remains inactive and rejected by both development-strength protocols. No evaluator/search-policy activation, package/UCI version change, ABI/JNI/Kotlin/Android behavior change, opening-default change, or tablebase change occurred.
'''
Path("docs/RUST_CHESS_ENGINE_S4_FINAL_VALIDATION_ADDENDUM_2026-08-07.md").write_text(addendum)

append_once(
    "docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_IMPLEMENTATION_REPORT.md",
    "## Final post-closure validation evidence correction",
    f'''## Final post-closure validation evidence correction

`docs/RUST_CHESS_ENGINE_S4_FINAL_VALIDATION_ADDENDUM_2026-08-07.md` records the completed permanent validation matrix for final closed SHA `{FINAL_S4_SHA}`. The pre-closure matrix above remains valid implementation evidence; it is not the final closed-SHA signoff. The addendum records CI `31208874474`, Performance `31208875019`, Robustness `31208875521`, Android/JNI `31208874646`, S4 `31208874643`, and final report publication `31209467578`, all successful on the exact final closed SHA. The selected S4 candidate remains `rejected_strength`, inactive, and non-production.''',
)
append_once(
    "docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_TODO_2026-08-07.md",
    "### Final post-closure validation evidence correction",
    f'''### Final post-closure validation evidence correction

S4-12.3 final closed-SHA evidence is recorded in `docs/RUST_CHESS_ENGINE_S4_FINAL_VALIDATION_ADDENDUM_2026-08-07.md`. Final closed SHA `{FINAL_S4_SHA}` passed CI run `31208874474`, Performance run `31208875019`, Robustness run `31208875521`, Android/JNI run `31208874646`, S4 run `31208874643`, and final report-publication run `31209467578`. This supplements, rather than replaces, the pre-closure implementation evidence. No S4 candidate was activated.''',
)

# H2: checked diagnostic-count invariants.
replace_exact(
    "crates/chess-tune/src/diagnostics.rs",
    '''    pub(crate) fn validate_counts(self) -> bool {
        let active = self.active_parameter_count as usize;
        active <= TUNABLE_PARAMETER_COUNT
            && self.positive_gradient_count as usize
                + self.negative_gradient_count as usize
                + self.zero_gradient_count as usize
                == active
            && self.zero_after_quantization_count as usize <= active
            && self.nonzero_integer_update_count as usize <= active
            && self.clipped_update_count as usize <= active
            && self.changed_parameter_count as usize <= active
    }
''',
    '''    pub(crate) fn validate_counts(self) -> bool {
        let active = self.active_parameter_count;
        let gradient_count = self
            .positive_gradient_count
            .checked_add(self.negative_gradient_count)
            .and_then(|count| count.checked_add(self.zero_gradient_count));
        let movement_count = self
            .zero_after_quantization_count
            .checked_add(self.nonzero_integer_update_count);

        active as usize <= TUNABLE_PARAMETER_COUNT
            && gradient_count == Some(active)
            && movement_count.is_some_and(|count| count <= active)
            && self.changed_parameter_count == self.nonzero_integer_update_count
            && self.clipped_update_count <= active
    }
''',
)

trace_path = "crates/chess-tune/src/trace.rs"
trace = read(trace_path)
insert = r'''

    fn mutate_iteration_field(text: &str, field_index: usize, value: &str) -> String {
        let mut lines = text.lines().map(str::to_owned).collect::<Vec<_>>();
        let row = lines
            .iter_mut()
            .find(|line| line.starts_with("iteration\t"))
            .expect("fixture contains an iteration row");
        let mut fields = row.split('\t').map(str::to_owned).collect::<Vec<_>>();
        assert_eq!(fields.len(), 31);
        fields[field_index] = value.to_owned();
        *row = fields.join("\t");
        lines.join("\n") + "\n"
    }

    #[test]
    fn trace_rejects_impossible_quantization_update_partition() {
        let trace =
            S4OptimizerTrace::new(binding(), vec![diagnostic(1, 0x50)]).expect("trace is valid");
        let text = trace.to_text().expect("trace serializes");
        let text = mutate_iteration_field(&text, 24, "1");
        let text = mutate_iteration_field(&text, 26, "1");
        assert!(matches!(
            S4OptimizerTrace::from_text(&text),
            Err(S4OptimizerTraceError::ImpossibleCounts { .. })
        ));
    }

    #[test]
    fn trace_rejects_changed_count_mismatch() {
        let trace =
            S4OptimizerTrace::new(binding(), vec![diagnostic(1, 0x50)]).expect("trace is valid");
        let text = trace.to_text().expect("trace serializes");
        let text = mutate_iteration_field(&text, 26, "1");
        assert!(matches!(
            S4OptimizerTrace::from_text(&text),
            Err(S4OptimizerTraceError::ImpossibleCounts { .. })
        ));
    }
'''
if "fn trace_rejects_impossible_quantization_update_partition()" not in trace:
    pos = trace.rfind("\n}")
    if pos < 0:
        raise SystemExit("trace.rs: test module closing brace not found")
    trace = trace[:pos] + insert + trace[pos:]
    write(trace_path, trace)

# H5: remove unused public raw-current checkpoint materialization and add safety regression.
optimizer_path = "crates/chess-tune/src/optimizer.rs"
replace_exact(
    optimizer_path,
    '''    /// Current rounded runtime weights.
    pub fn current_weights(
        &self,
        bounds: SpsaWeightBounds,
    ) -> Result<EvaluationWeights, SpsaOptimizerError> {
        let values = project_parameters(
            &self.current_parameters,
            bounds,
            TunableParameterMask::all(),
            &self.reference_values,
        )?;
        Ok(weights_from_tunable_values(values))
    }

''',
    "",
)
optimizer = read(optimizer_path)
opt_test = r'''

    #[test]
    fn checkpoint_best_weights_preserve_inactive_parameters_after_masked_run() {
        let data = dataset(OutcomeTarget::Win);
        let mask = EvaluationParameterGroup::PawnStructure.mask();
        let masked_config = config(20)
            .with_parameter_mask(mask)
            .expect("group mask is valid");
        let baseline = tunable_values(&EvaluationWeights::DEFAULT);
        let mut optimizer = SpsaOptimizer::new(
            masked_config,
            0x5344_4841_5244_454e,
            EvaluationWeights::DEFAULT,
            &data,
            k(),
        )
        .expect("masked optimizer starts");
        optimizer.advance(&data, 20).expect("masked advance succeeds");
        let best = tunable_values(&optimizer.checkpoint().best_weights());
        for parameter in TunableParameter::all() {
            if !mask.contains(parameter) {
                assert_eq!(
                    best[parameter.index()],
                    baseline[parameter.index()],
                    "inactive checkpoint best weight changed: {}",
                    parameter.name()
                );
            }
        }
    }
'''
if "checkpoint_best_weights_preserve_inactive_parameters_after_masked_run" not in optimizer:
    anchor = "    #[test]\n    fn mask_identity_binds_checkpoint_configuration()"
    pos = optimizer.find(anchor)
    if pos < 0:
        raise SystemExit("optimizer.rs: mask identity test anchor not found")
    optimizer = optimizer[:pos] + opt_test + "\n" + optimizer[pos:]
    write(optimizer_path, optimizer)

# H3/H4: fail-visible cleanup and canonical lowercase source commit.
tuning_path = "crates/chess-tools/src/tuning_cli.rs"
replace_exact(
    tuning_path,
    '''    if result.is_err() {
        let _ = fs::remove_dir_all(&staging);
    }
    result
}
''',
    '''    match result {
        Ok(()) => Ok(()),
        Err(primary_error) => Err(cleanup_staging_after_failure(&staging, primary_error)),
    }
}

fn cleanup_staging_after_failure(staging: &Path, primary_error: String) -> String {
    match fs::remove_dir_all(staging) {
        Ok(()) => primary_error,
        Err(cleanup_error) => cleanup_failure_message(&primary_error, staging, &cleanup_error),
    }
}

fn cleanup_failure_message(
    primary_error: &str,
    staging: &Path,
    cleanup_error: &std::io::Error,
) -> String {
    format!(
        "{primary_error}; additionally failed to remove tuning staging directory {staging:?}: {cleanup_error}"
    )
}
''',
)
replace_exact(
    tuning_path,
    '''fn parse_source_commit(value: &str) -> Result<[u8; 20], String> {
    if value.len() != 40 || !value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err("source_commit must be exactly 40 hexadecimal characters".to_owned());
    }
''',
    '''fn parse_source_commit(value: &str) -> Result<[u8; 20], String> {
    if value.len() != 40
        || value
            .bytes()
            .any(|byte| !byte.is_ascii_hexdigit() || byte.is_ascii_uppercase())
    {
        return Err("source_commit must be exactly 40 lowercase hexadecimal characters".to_owned());
    }
''',
)
replace_exact(
    tuning_path,
    "    use super::{parse_source_commit, TuningFileConfig, CONFIG_MARKER};",
    "    use std::{io, path::Path};\n\n    use super::{cleanup_failure_message, parse_source_commit, TuningFileConfig, CONFIG_MARKER};",
)
replace_exact(
    tuning_path,
    '''    #[test]
    fn source_commit_is_exact_and_nonzero() {
        assert_eq!(
            parse_source_commit("abababababababababababababababababababab").expect("commit"),
            [0xab; 20]
        );
        assert!(parse_source_commit("00").is_err());
        assert!(parse_source_commit("0000000000000000000000000000000000000000").is_err());
    }
''',
    '''    #[test]
    fn source_commit_accepts_canonical_lowercase() {
        assert_eq!(
            parse_source_commit("abababababababababababababababababababab").expect("commit"),
            [0xab; 20]
        );
    }

    #[test]
    fn source_commit_rejects_uppercase() {
        assert!(parse_source_commit("ABABABABABABABABABABABABABABABABABABABAB").is_err());
    }

    #[test]
    fn source_commit_rejects_mixed_case() {
        assert!(parse_source_commit("abababababababababababababababababababAB").is_err());
    }

    #[test]
    fn source_commit_rejects_short_invalid_and_zero() {
        assert!(parse_source_commit("00").is_err());
        assert!(parse_source_commit("gggggggggggggggggggggggggggggggggggggggg").is_err());
        assert!(parse_source_commit("0000000000000000000000000000000000000000").is_err());
    }

    #[test]
    fn cleanup_failure_context_preserves_primary_error() {
        let cleanup = io::Error::other("permission denied");
        let message = cleanup_failure_message("primary publication failure", Path::new(".out.staging"), &cleanup);
        assert!(message.starts_with("primary publication failure; additionally failed"));
        assert!(message.contains(".out.staging"));
        assert!(message.contains("permission denied"));
    }
''',
)

# Authority audits: active hardening is the sole active descendant while S3/S4 remain closed.
post = "scripts/task_post_port_review_fix_audit.sh"
replace_exact(post, 's4_todo="docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_TODO_2026-08-07.md"\n', 's4_todo="docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_TODO_2026-08-07.md"\nhardening_spec="docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_SPEC_2026-08-07.md"\nhardening_todo="docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_TODO_2026-08-07.md"\n')
replace_exact(post, '    "$s4_todo" \\\n    "$legacy_index" \\', '    "$s4_todo" \\\n    "$hardening_spec" \\\n    "$hardening_todo" \\\n    "$legacy_index" \\')
replace_exact(post, "grep -Fq '**Status:** Complete — tuning method accepted for future experimentation; no production promotion' \"$s4_spec\"\n", "grep -Fq '**Status:** Complete — tuning method accepted for future experimentation; no production promotion' \"$s4_spec\"\ngrep -Fq '**Status:** Active — H0-H6 implemented; permanent validation pending' \"$hardening_todo\"\ngrep -Fq '**Status:** Active — closure hardening implementation in progress' \"$hardening_spec\"\n")
replace_exact(post, '    "$definitions"\n)', '    "$definitions"\n    "$hardening_todo"\n)')
replace_exact(post, 'grep -Fq "\\`$s4_todo\\`" "$legacy_index"\n', 'grep -Fq "\\`$s4_todo\\`" "$legacy_index"\ngrep -Fq "\\`$hardening_todo\\`" "$legacy_index"\n')
replace_exact(post, "grep -Fq 'There is no active implementation TODO.' \"$legacy_index\"\n", "grep -Fq '| Active S4 closure hardening program |' \"$legacy_index\"\ngrep -Fq 'The S4 closure-hardening TODO is the single active implementation tracker.' \"$legacy_index\"\n")
replace_exact(post, 'not one of the two completed-authority documents above', 'not one of the three authority documents above')
replace_exact(post, '74 TODO-named files total; 2 authority documents; 1 authority index; 71 historical', '75 TODO-named files total; 3 authority documents; 1 authority index; 71 historical')
replace_exact(post, 'grep -Fq "**Specification:** \\`$s4_spec\\`" "$s4_todo"\n', 'grep -Fq "**Specification:** \\`$s4_spec\\`" "$s4_todo"\ngrep -Fq "**Companion TODO:** \\`$hardening_todo\\`" "$hardening_spec"\ngrep -Fq "**Specification:** \\`$hardening_spec\\`" "$hardening_todo"\n')
replace_exact(post, 'grep -Fq \'# Task S4-12: Final report and closure — COMPLETE (NO PRODUCTION PROMOTION)\' "$s4_todo"\n', 'grep -Fq \'# Task S4-12: Final report and closure — COMPLETE (NO PRODUCTION PROMOTION)\' "$s4_todo"\ngrep -Fq \'# Task H0: Authority registration and baseline freeze — COMPLETE\' "$hardening_todo"\ngrep -Fq \'# Task H6: Permanent audit and workflow integration — COMPLETE\' "$hardening_todo"\n')
replace_exact(post, '"$tracker"|"$definitions"|"$legacy_index")', '"$tracker"|"$definitions"|"$hardening_todo"|"$legacy_index")')

s3audit = "scripts/task_s3_evaluation_strength_audit.sh"
replace_exact(s3audit, 'final_report=docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_IMPLEMENTATION_REPORT.md\n', 'final_report=docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_IMPLEMENTATION_REPORT.md\nhardening_todo=docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_TODO_2026-08-07.md\n')
replace_exact(s3audit, '"$pilot" "$final_report" "$legacy"', '"$pilot" "$final_report" "$hardening_todo" "$legacy"')
replace_exact(s3audit, "require_literal 'There is no active implementation TODO.' \"$legacy\"\n", "require_literal '`docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_TODO_2026-08-07.md`' \"$legacy\"\nrequire_literal '| Active S4 closure hardening program |' \"$legacy\"\nrequire_literal '**Status:** Active — H0-H6 implemented; permanent validation pending' \"$hardening_todo\"\n")

s4audit = "scripts/task_s4_evaluation_tuning_calibration_audit.sh"
replace_exact(s4audit, 'final_report=docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_IMPLEMENTATION_REPORT.md\n', 'final_report=docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_IMPLEMENTATION_REPORT.md\nhardening_spec=docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_SPEC_2026-08-07.md\nhardening_todo=docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_TODO_2026-08-07.md\nfinal_addendum=docs/RUST_CHESS_ENGINE_S4_FINAL_VALIDATION_ADDENDUM_2026-08-07.md\n')
replace_exact(s4audit, '"$method" "$final_report" "$legacy"', '"$method" "$final_report" "$hardening_spec" "$hardening_todo" "$final_addendum" "$legacy"')
replace_exact(s4audit, "require_literal 'There is no active implementation TODO.' \"$legacy\"\nrequire_literal '74 TODO-named files total; 2 authority documents; 1 authority index; 71 historical' \"$legacy\"\n", "require_literal '`docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_TODO_2026-08-07.md`' \"$legacy\"\nrequire_literal '| Active S4 closure hardening program |' \"$legacy\"\nrequire_literal '75 TODO-named files total; 3 authority documents; 1 authority index; 71 historical' \"$legacy\"\nrequire_literal '**Status:** Active — H0-H6 implemented; permanent validation pending' \"$hardening_todo\"\nrequire_literal '**Status:** Active — closure hardening implementation in progress' \"$hardening_spec\"\n")

append_once(
    s4audit,
    "# S4 closure hardening H1-H6 witnesses.",
    r'''# S4 closure hardening H1-H6 witnesses.
require_literal '**Status:** Complete evidence correction' "$final_addendum"
require_literal 'bc406d78d673cc3258e8b522bcec25c4838f5e32' "$final_addendum"
require_literal '31208874474' "$final_addendum"
require_literal '31208875019' "$final_addendum"
require_literal '31208875521' "$final_addendum"
require_literal '31208874646' "$final_addendum"
require_literal '31208874643' "$final_addendum"
require_literal '31209467578' "$final_addendum"
require_literal '9005860229' "$final_addendum"
require_literal '9005851414' "$final_addendum"
require_literal '9005947857' "$final_addendum"
require_literal '.checked_add(self.negative_gradient_count)' "$diagnostics"
require_literal '.checked_add(self.nonzero_integer_update_count)' "$diagnostics"
require_literal 'gradient_count == Some(active)' "$diagnostics"
require_literal 'self.changed_parameter_count == self.nonzero_integer_update_count' "$diagnostics"
require_literal 'trace_rejects_impossible_quantization_update_partition' "$trace"
require_literal 'trace_rejects_changed_count_mismatch' "$trace"
require_literal 'cleanup_staging_after_failure' crates/chess-tools/src/tuning_cli.rs
require_literal 'cleanup_failure_message' crates/chess-tools/src/tuning_cli.rs
if grep -Fq 'let _ = fs::remove_dir_all(&staging);' crates/chess-tools/src/tuning_cli.rs; then
  fail 'silent tuning staging cleanup discard returned'
fi
require_literal 'source_commit must be exactly 40 lowercase hexadecimal characters' crates/chess-tools/src/tuning_cli.rs
require_literal 'source_commit_rejects_uppercase' crates/chess-tools/src/tuning_cli.rs
require_literal 'source_commit_rejects_mixed_case' crates/chess-tools/src/tuning_cli.rs
if grep -Fq 'pub fn current_weights(' "$optimizer"; then
  fail 'unused public raw checkpoint materializer returned'
fi
require_literal 'checkpoint_best_weights_preserve_inactive_parameters_after_masked_run' "$optimizer"
require_literal '# Task H0: Authority registration and baseline freeze — COMPLETE' "$hardening_todo"
require_literal '# Task H6: Permanent audit and workflow integration — COMPLETE' "$hardening_todo"
for temporary in .github/s4_closure_hardening_apply.py .github/workflows/s4-closure-hardening-apply.yml; do
  test ! -e "$temporary" || fail "temporary S4 hardening control remains: $temporary"
done
''',
)

# Ensure the H6 workflow assumptions remain true without modifying the permanent workflow.
workflow = read(".github/workflows/s4-evaluation-tuning-calibration.yml")
for required in [
    "contents: read",
    "cargo clippy --locked -p chess-tune -p chess-tools --all-targets --all-features -- -D warnings",
    "cargo test --locked -p chess-tune --all-targets --all-features",
    "cargo test --locked -p chess-tools --all-targets --all-features",
]:
    if required not in workflow:
        raise SystemExit(f"permanent S4 workflow missing required witness: {required}")
if "contents: write" in workflow:
    raise SystemExit("permanent S4 workflow unexpectedly write-capable")

print("S4 closure hardening H0-H6 source/doc transformation complete")
