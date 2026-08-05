#!/usr/bin/env python3
from pathlib import Path

path = Path("scripts/s2_3_baseline_stage.py")
text = path.read_text()
replacements = [
    (
        "    EvaluationWeightSet, Score, SearchDiagnostics, SearchLimits, SearchPolicySet,\n",
        "    EvaluationWeightSet, Score, SearchLimits, SearchPolicySet,\n",
    ),
    (
        '.map_or_else(|| "-".to_owned(), |value| value.raw().to_string());',
        '.map_or_else(|| "-".to_owned(), |value| value.to_string());',
    ),
    (
        "    let root = Position::starting();\n    let mut white_moves = root.legal_moves()?.iter().collect::<Vec<_>>();",
        "    let mut root = Position::starting();\n    let mut white_moves = root.legal_moves()?.iter().collect::<Vec<_>>();",
    ),
]
for old, new in replacements:
    if text.count(old) != 1:
        raise SystemExit(f"expected one repair witness: {old!r}")
    text = text.replace(old, new, 1)
exec(compile(text, str(path), "exec"), {"__name__": "__main__"})
