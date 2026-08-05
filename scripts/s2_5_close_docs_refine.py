#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/RUST_CHESS_ENGINE_V0_2_S2_5_SEE_ORDERING_2026-08-05.md"

text = REPORT.read_text()
lines = text.splitlines()
cleaned = "\n".join(line.rstrip() for line in lines) + "\n"
if cleaned == text:
    raise SystemExit("S2-5 report contained no trailing whitespace to refine")
REPORT.write_text(cleaned)
print("S2-5 report trailing whitespace removed")
