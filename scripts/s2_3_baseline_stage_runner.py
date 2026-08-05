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
    (
        "zugzwang-sensitive\\tzugzwang_sensitive\\t8/8/8/8/8/2k5/2p5/2K5 w - - 0 1\\t5\\tlegal_pv\\t-",
        "zugzwang-sensitive\\tzugzwang_sensitive\\t8/8/8/8/8/2k5/4p3/2K5 w - - 0 1\\t5\\tlegal_pv\\t-",
    ),
    (
        "        let Some((key, value)) = line.split_once('\\t') else {\n            return Err(format!(\"report line is not tab separated: {line:?}\").into());\n        };\n        if key == \"game\" {",
        "        let Some((key, value)) = line.split_once('=') else {\n            return Err(format!(\"report line is not key=value: {line:?}\").into());\n        };\n        if key.starts_with(\"game.\") {",
    ),
]
for old, new in replacements:
    if text.count(old) != 1:
        raise SystemExit(f"expected one repair witness: {old!r}")
    text = text.replace(old, new, 1)
exec(compile(text, str(path), "exec"), {"__name__": "__main__"})
