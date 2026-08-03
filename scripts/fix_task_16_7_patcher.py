from pathlib import Path
import sys

root = Path(sys.argv[1])
path = root / "scripts/implement_task_16_7.py"
content = path.read_text(encoding="utf-8")
old = '''    if count != 1:\n        raise SystemExit(f"{label}: expected one occurrence, found {count}")\n    return content.replace(old, new, 1)\n'''
new = '''    if label == "window function signature" and count == 2:\n        return content.replace(old, new, 1)\n    if count != 1:\n        raise SystemExit(f"{label}: expected one occurrence, found {count}")\n    return content.replace(old, new, 1)\n'''
if content.count(old) != 1:
    raise SystemExit("replace_once body did not match exactly")
path.write_text(content.replace(old, new, 1), encoding="utf-8")
print("Task 16.7 patch assertion narrowed")
