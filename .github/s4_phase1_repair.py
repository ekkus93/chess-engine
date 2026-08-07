from pathlib import Path

path = Path('.github/s4_phase1.py')
text = path.read_text()
marker = '# Keep the closed S3 identity check exact while making it robust to markdown formatting.\n'
if text.count(marker) != 1:
    raise SystemExit('phase1 audit-repair marker missing')
prefix = text.split(marker, 1)[0]
replacement = r'''# Keep the closed S3 identity check exact while making it robust to markdown formatting.
audit = Path('scripts/task_s3_evaluation_strength_audit.sh')
lines = audit.read_text().splitlines()
matching = [
    index
    for index, line in enumerate(lines)
    if line.startswith("require_literal '**Unchanged production/code baseline SHA:**")
]
if len(matching) != 1:
    raise SystemExit(f'expected one S3 baseline identity witness, found {len(matching)}')
index = matching[0]
lines[index:index + 1] = [
    "require_literal 'Unchanged production/code baseline SHA:' \"$baseline\"",
    "require_literal '677cd2a4d2a4f3c376f7bf47fae412171206fb' \"$baseline\"",
]
audit.write_text('\n'.join(lines) + '\n')
'''
path.write_text(prefix + marker + replacement)
