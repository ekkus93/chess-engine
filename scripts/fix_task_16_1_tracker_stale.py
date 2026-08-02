#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
path = root / "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
text = path.read_text(encoding="utf-8")
old = "- Task 15 is complete. Task 16.1 iterative deepening is next."
new = "- Task 15 and Task 16.1 are complete. Task 16.2 aspiration windows is next."
count = text.count(old)
if count != 1:
    raise SystemExit(f"expected one stale Task 16.1 sentence, found {count}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Task 16.1 stale tracker sentence corrected")
