#!/usr/bin/env python3
from pathlib import Path

path = Path("scripts/s2_3_stage.py")
text = path.read_text()
old = 'replace_once("crates/chess-search/src/alpha_beta.rs", "    SearchCancellationProbe, SearchPolicy, TranspositionBound,\\n", "    SearchCancellationProbe, SearchDiagnosticEvent, SearchDiagnosticOverflow,\\n    SearchDiagnostics, SearchPolicy, TranspositionBound,\\n")'
new = 'replace_once("crates/chess-search/src/alpha_beta.rs", "    EvaluationWeights, Score, SearchCancellationProbe, SearchPolicy, TranspositionBound,\\n", "    EvaluationWeights, Score, SearchCancellationProbe, SearchDiagnosticEvent,\\n    SearchDiagnosticOverflow, SearchDiagnostics, SearchPolicy, TranspositionBound,\\n")'
if text.count(old) != 1:
    raise SystemExit("expected one alpha-beta import patch witness")
text = text.replace(old, new, 1)
exec(compile(text, str(path), "exec"), {"__name__": "__main__"})
