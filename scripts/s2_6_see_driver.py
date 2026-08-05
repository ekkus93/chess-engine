#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).resolve().with_name("s2_6_see_apply.py")
text = path.read_text()
old = '''replace_once(
    ALPHA_BETA,
    "            see_capture_ordering: false,\\n"
    "            weights:",
    "            see_capture_ordering: false,\\n"
    "            see_quiescence_pruning: false,\\n"
    "            delta_pruning: false,\\n"
    "            weights:",
    expected=3,
)
'''
new = '''replace_once(
    ALPHA_BETA,
    "            see_capture_ordering: false,\\n"
    "            weights:",
    "            see_capture_ordering: false,\\n"
    "            see_quiescence_pruning: false,\\n"
    "            delta_pruning: false,\\n"
    "            weights:",
    expected=2,
)
replace_once(
    ALPHA_BETA,
    "                see_capture_ordering: false,\\n"
    "                weights:",
    "                see_capture_ordering: false,\\n"
    "                see_quiescence_pruning: false,\\n"
    "                delta_pruning: false,\\n"
    "                weights:",
)
'''
count = text.count(old)
if count != 1:
    raise SystemExit(f"expected one S2-6 context witness block, found {count}")
path.write_text(text.replace(old, new, 1))
print("S2-6 test-context witnesses refined")
