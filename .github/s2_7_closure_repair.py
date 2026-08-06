from pathlib import Path

path = Path('.github/s2_7_closure.py')
text = path.read_text(encoding='utf-8')
old = 'tracker = replace_once(tracker, "# Work order\\n", record + "# Work order\\n", "work-order insertion")'
new = 'tracker = replace_once(tracker, "## Program guardrails\\n", record + "## Program guardrails\\n", "implementation-record insertion")'
if text.count(old) != 1:
    raise SystemExit('expected one obsolete tracker insertion marker')
path.write_text(text.replace(old, new, 1), encoding='utf-8')
Path('.github/s2_7_closure_repair.py').unlink()
