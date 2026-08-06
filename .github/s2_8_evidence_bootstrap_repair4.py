from pathlib import Path

path = Path('.github/s2_8_evidence_bootstrap.py')
text = path.read_text(encoding='utf-8')
old = "grep -q 'activated\\\\tfalse' \"$evidence\" || fail \"evidence omits inactive disposition\""
new = "grep -q 'activated=false' \"$evidence\" || fail \"evidence omits inactive disposition\""
count = text.count(old)
if count != 1:
    raise SystemExit(f'inactive marker repair: expected exactly one occurrence, found {count}')
path.write_text(text.replace(old, new, 1), encoding='utf-8')
Path(__file__).unlink()
