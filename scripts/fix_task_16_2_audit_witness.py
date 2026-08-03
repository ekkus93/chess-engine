#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
path = root / "crates/chess-search/src/alpha_beta.rs"
text = path.read_text(encoding="utf-8")
old = '''    pub(crate) fn full() -> Self {
        Self {
            alpha: Score::mated_in(0).expect("zero-ply mate score is supported"),
            beta: Score::mate_in(0).expect("zero-ply mate score is supported"),
        }
    }
'''
new = '''    pub(crate) fn full() -> Self {
        let alpha = Score::mated_in(0).expect("zero-ply mate score is supported");
        let beta = Score::mate_in(0).expect("zero-ply mate score is supported");
        Self { alpha, beta }
    }
'''
if text.count(old) != 1:
    raise RuntimeError("expected exactly one full-window constructor to normalize")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Task 16.2 audit witness normalized")
