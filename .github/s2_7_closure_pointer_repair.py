from pathlib import Path

path = Path('.github/s2_7_closure.py')
text = path.read_text(encoding='utf-8')
old = '''tracker = replace_once(
    tracker,
    "- Begin with S2-7 only.",
    "- Begin with S2-8 only.",
    "next-task pointer",
)'''
new = '''tracker = replace_once(
    tracker,
    "Begin with **S2-7 only**: the inactive SEE capture-ordering candidate. Do not add SEE pruning, quiescence redesign, PVS, LMR, null move, frontier pruning, or tablebases until S2-5 has isolated policy identity, exact correctness parity, diagnostics, performance evidence, and an explicit disposition.",
    "Begin with **S2-8 only**: the inactive Late Move Reductions candidate. Do not begin S2-9 or later work until S2-8 has an isolated policy identity, bounded reduction/verification semantics, exact correctness evidence, architecture-specific performance measurements, development strength evidence, and an explicit disposition.",
    "next-task pointer",
)'''
if text.count(old) != 1:
    raise SystemExit('expected one obsolete next-task replacement')
path.write_text(text.replace(old, new, 1), encoding='utf-8')
Path('.github/s2_7_closure_pointer_repair.py').unlink()
