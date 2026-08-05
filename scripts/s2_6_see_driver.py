#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).resolve().with_name("s2_6_see_apply.py")
text = path.read_text()


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one {label} block, found {count}")
    text = text.replace(old, new, 1)


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
replace_once(context_old, context_new, "S2-6 context witness")

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
replace_once(recursive_old, recursive_new, "S2-6 recursive policy witness")

invalid_error = '''    "        .ok_or_else(|| chess_core::StaticExchangeError::MoveStateContradiction(\\n"
    "            chess_core::StaticExchangeMoveStateError::MissingCapturedPiece {\\n"
    "                destination: current.destination(),\\n"
    "            },\\n"
    "        ))?;\\n"
'''
valid_error = '''    "        .ok_or_else(|| chess_core::StaticExchangeError::MoveStateContradiction(\\n"
    "            chess_core::StaticExchangeMoveStateError::InvalidTargetState {\\n"
    "                destination: current.destination(),\\n"
    "            },\\n"
    "        ))?;\\n"
'''
replace_once(invalid_error, valid_error, "typed delta target error")

count = text.count("search_diagnostics()")
if count != 4:
    raise SystemExit(f"expected four lower-level diagnostics accessor uses, found {count}")
text = text.replace("search_diagnostics()", "diagnostics()")

path.write_text(text)
print("S2-6 patch witnesses and typed APIs refined")
