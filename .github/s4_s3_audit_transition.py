from pathlib import Path

path = Path('scripts/task_s3_evaluation_strength_audit.sh')
text = path.read_text()
old = "require_literal 'if direction == 0 {' \"$optimizer\""
new = "require_literal 'if !mask.contains(tunable) {' \"$optimizer\"\nrequire_literal 'if direction != 0 {' \"$optimizer\"\nrequire_literal 'if !matches!(direction, -1 | 1) {' \"$optimizer\""
if text.count(old) != 1:
    raise SystemExit('expected exactly one stale S3 masked-direction witness')
path.write_text(text.replace(old, new, 1))
