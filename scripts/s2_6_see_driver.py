#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).resolve().with_name("s2_6_see_apply.py")
text = path.read_text()

context_old = '''replace_once(
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
context_new = '''replace_once(
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
if text.count(context_old) != 1:
    raise SystemExit("expected one S2-6 context witness block")
text = text.replace(context_old, context_new, 1)

recursive_old = '''replace_once(
    QUIESCENCE,
    "            QuiescenceSearchPolicy::new(\\n"
    "                -beta,\\n"
    "                -alpha,\\n"
    "                ordering,\\n"
    "                see_capture_ordering,\\n"
    "                weights,\\n"
    "            ),\\n",
    "            QuiescenceSearchPolicy::new(\\n"
    "                -beta,\\n"
    "                -alpha,\\n"
    "                ordering,\\n"
    "                see_capture_ordering,\\n"
    "                see_quiescence_pruning,\\n"
    "                delta_pruning,\\n"
    "                weights,\\n"
    "            ),\\n",
)
'''
recursive_new = '''replace_once(
    QUIESCENCE,
    "            QuiescenceSearchPolicy::new(-beta, -alpha, ordering, see_capture_ordering, weights),\\n",
    "            QuiescenceSearchPolicy::new(\\n"
    "                -beta,\\n"
    "                -alpha,\\n"
    "                ordering,\\n"
    "                see_capture_ordering,\\n"
    "                see_quiescence_pruning,\\n"
    "                delta_pruning,\\n"
    "                weights,\\n"
    "            ),\\n",
)
'''
if text.count(recursive_old) != 1:
    raise SystemExit("expected one S2-6 recursive policy witness block")
text = text.replace(recursive_old, recursive_new, 1)

path.write_text(text)
print("S2-6 patch witnesses refined")
