#!/usr/bin/env python3
from pathlib import Path

path = Path("scripts/s2_6_closure.py")
text = path.read_text()
count_old = '''if section.count("- [ ]") != 21:
    raise SystemExit(f"expected 21 unchecked S2-6 tasks, found {section.count('- [ ]')}")
'''
count_new = '''if section.count("- [ ]") != 22:
    raise SystemExit(f"expected 22 unchecked S2-6 tasks, found {section.count('- [ ]')}")
'''
if text.count(count_old) != 1:
    raise SystemExit("expected one S2-6 task-count witness")
text = text.replace(count_old, count_new, 1)
next_old = '    "Begin with **S2-4 only**": "Begin with **S2-7 only**",\n'
next_new = '    "Begin with **S2-5 only**": "Begin with **S2-7 only**",\n'
if text.count(next_old) != 1:
    raise SystemExit("expected one stale S2-6 next-action witness")
text = text.replace(next_old, next_new, 1)
path.write_text(text)
print("S2-6 closure task count and next-action witness corrected")
