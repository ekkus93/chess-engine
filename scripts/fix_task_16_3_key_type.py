#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
path = root / "crates/chess-search/src/transposition/principal_variation.rs"
text = path.read_text(encoding="utf-8")
old = "        let key = 0x1234_5678_9abc_def0;"
new = "        let key: u64 = 0x1234_5678_9abc_def0;"
count = text.count(old)
if count != 1:
    raise SystemExit(f"expected one ambiguous key literal, found {count}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Task 16.3 test key type fixed")
