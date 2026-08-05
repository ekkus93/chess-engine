#!/usr/bin/env python3
from pathlib import Path

path = Path("scripts/s2_6_closure.py")
text = path.read_text()
old = '''if section.count("- [ ]") != 21:
    raise SystemExit(f"expected 21 unchecked S2-6 tasks, found {section.count('- [ ]')}")
'''
new = '''if section.count("- [ ]") != 22:
    raise SystemExit(f"expected 22 unchecked S2-6 tasks, found {section.count('- [ ]')}")
'''
if text.count(old) != 1:
    raise SystemExit("expected one S2-6 task-count witness")
path.write_text(text.replace(old, new, 1))
print("S2-6 closure task count corrected")
