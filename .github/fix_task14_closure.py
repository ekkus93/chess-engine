#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
paths = [
    root / "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md",
    root / "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md",
]
old = "Task 13 is complete; Task 14.1 quiescence is next."
new = "Task 13 is complete; Task 14.1 quiescence is complete and Task 14.2 tactical ordering is next."
for path in paths:
    text = path.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one stale transition, found {count}")
    path.write_text(text.replace(old, new, 1))
print("Task 14.1 closure transitions corrected")
