#!/usr/bin/env python3
"""Repair Task 19 summary labels after the guarded 19.1 closure."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODO = ROOT / "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"

text = TODO.read_text(encoding="utf-8")
replacements = (
    (
        "- Task 19.1 opening-book abstraction is next.",
        "- Task 19.1 opening-book abstraction is complete. Task 19.2 backend format is next.",
    ),
    (
        "# Task 19: Opening book — NOT STARTED",
        "# Task 19: Opening book — IN PROGRESS",
    ),
)

for old, new in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one occurrence of {old!r}, found {count}")
    text = text.replace(old, new, 1)

if "- [x] 19.1 Abstraction." not in text:
    raise SystemExit("Task 19.1 is not checked")
if "- [ ] 19.2 Format." not in text:
    raise SystemExit("Task 19.2 is not open")
if "- [ ] Task 19 gate." not in text:
    raise SystemExit("Task 19 gate is not open")

TODO.write_text(text, encoding="utf-8")
