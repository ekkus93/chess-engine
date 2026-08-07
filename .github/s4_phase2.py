from pathlib import Path

lib = Path('crates/chess-tune/src/lib.rs')
text = lib.read_text()
anchor = 'mod optimizer;\n'
if text.count(anchor) != 1:
    raise SystemExit('trace module anchor missing')
text = text.replace(anchor, anchor + 'mod trace;\n', 1)
anchor = '''pub use optimizer::{\n    SpsaCheckpoint, SpsaConfig, SpsaOptimizer, SpsaOptimizerError, SpsaRunSummary, SpsaSchedule,\n    SpsaWeightBounds, MAX_SPSA_ITERATIONS, MAX_SPSA_WEIGHT_MAGNITUDE,\n    SPSA_CHECKPOINT_SCHEMA_VERSION, SPSA_OPTIMIZER_IDENTIFIER,\n};\n'''
addition = anchor + '''pub use trace::{\n    S4OptimizerTrace, S4OptimizerTraceBinding, S4OptimizerTraceError,\n    S4_OPTIMIZER_TRACE_IDENTIFIER, S4_OPTIMIZER_TRACE_SCHEMA_VERSION,\n};\n'''
if text.count(anchor) != 1:
    raise SystemExit('trace export anchor missing')
text = text.replace(anchor, addition, 1)
lib.write_text(text)

audit = Path('scripts/task_s4_evaluation_tuning_calibration_audit.sh')
text = audit.read_text()
anchor = 's3_report=docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_IMPLEMENTATION_REPORT.md\n'
addition = anchor + 'diagnostics=crates/chess-tune/src/diagnostics.rs\ntrace=crates/chess-tune/src/trace.rs\noptimizer=crates/chess-tune/src/optimizer.rs\n'
if text.count(anchor) != 1:
    raise SystemExit('S4 audit path anchor missing')
text = text.replace(anchor, addition, 1)
old = 'for path in "$spec" "$tracker" "$baseline" "$legacy" "$s3_tracker" "$s3_report"; do\n'
new = 'for path in "$spec" "$tracker" "$baseline" "$legacy" "$s3_tracker" "$s3_report" "$diagnostics" "$trace" "$optimizer"; do\n'
if text.count(old) != 1:
    raise SystemExit('S4 audit required-file anchor missing')
text = text.replace(old, new, 1)
anchor = "require_literal 'pub const S3_CANDIDATE_FORMAT_IDENTIFIER: u64 = 0x5333_4341_4e44_3031;' crates/chess-tools/src/s3_candidate.rs\n"
addition = anchor + '''\n# S4 optimizer diagnostics and strict trace contract.\nrequire_literal 'pub const S4_OPTIMIZER_DIAGNOSTIC_SCHEMA_VERSION: u16 = 1;' "$diagnostics"\nrequire_literal 'pub const S4_OPTIMIZER_DIAGNOSTIC_IDENTIFIER: u64 = 0x5334_4449_4147_3031;' "$diagnostics"\nrequire_literal 'pub const S4_OPTIMIZER_TRACE_SCHEMA_VERSION: u16 = 1;' "$trace"\nrequire_literal 'pub const S4_OPTIMIZER_TRACE_IDENTIFIER: u64 = 0x5334_5452_4143_3031;' "$trace"\nrequire_literal 'pub fn advance_with_diagnostics(' "$optimizer"\nrequire_literal 'positive_regularization' "$diagnostics"\nrequire_literal 'zero_after_quantization_count' "$diagnostics"\nrequire_literal 'clipped_update_count' "$diagnostics"\nrequire_literal 'initial_checkpoint_checksum' "$trace"\nrequire_literal 'pub fn validate_binding(' "$trace"\nrequire_literal 'if trace.to_text()? != text' "$trace"\nrequire_literal 'trace_round_trip_is_bit_canonical' "$trace"\nrequire_literal 'trace_checksum_corruption_fails_closed' "$trace"\nrequire_literal 'wrong_binding_fails_closed' "$trace"\n'''
if text.count(anchor) != 1:
    raise SystemExit('S4 audit trace witness anchor missing')
text = text.replace(anchor, addition, 1)
audit.write_text(text)
