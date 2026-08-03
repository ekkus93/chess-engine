#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
path = root / "crates/chess-search/src/alpha_beta.rs"
text = path.read_text(encoding="utf-8")
old = "    pub(crate) const fn new(alpha: Score, beta: Score) -> Option<Self> {\n"
new = "    pub(crate) fn new(alpha: Score, beta: Score) -> Option<Self> {\n"
if text.count(old) != 1:
    raise RuntimeError("expected exactly one const root-window constructor")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Task 16.2 root-window constructor corrected")
