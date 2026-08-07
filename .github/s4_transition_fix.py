from pathlib import Path

path = Path('scripts/task_s3_evaluation_strength_audit.sh')
text = path.read_text()
old = "require_literal '`docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_TODO_2026-08-07.md`' \"$legacy\"\nrequire_literal 'There is currently **no active implementation TODO**.' \"$legacy\"\nif grep -Fq '| Active S3 evaluation strength program |' \"$legacy\"; then\n"
new = "require_literal '`docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_TODO_2026-08-07.md`' \"$legacy\"\nrequire_literal 'Active S4 evaluation tuning calibration program' \"$legacy\"\nrequire_literal '`docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_TODO_2026-08-07.md`' \"$legacy\"\nif grep -Fq '| Active S3 evaluation strength program |' \"$legacy\"; then\n"
if text.count(old) != 1:
    raise SystemExit('closed-program authority witness not found exactly once')
text = text.replace(old, new, 1)
old_temp = "  .github/s3_candidate_stage.py \\\n  .github/workflows/s3-candidate-stage.yml; do"
new_temp = "  .github/s3_candidate_stage.py \\\n  .github/workflows/s3-candidate-stage.yml \\\n  .github/s3_closure_docs.py \\\n  .github/workflows/s3-closure-docs-stage.yml; do"
if text.count(old_temp) != 1:
    raise SystemExit('temporary-control list witness not found exactly once')
text = text.replace(old_temp, new_temp, 1)
path.write_text(text)
