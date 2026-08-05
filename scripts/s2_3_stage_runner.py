#!/usr/bin/env python3
from pathlib import Path

path = Path("scripts/s2_3_stage.py")
text = path.read_text()
replacements = [
    (
        'replace_once("crates/chess-search/src/alpha_beta.rs", "    SearchCancellationProbe, SearchPolicy, TranspositionBound,\\n", "    SearchCancellationProbe, SearchDiagnosticEvent, SearchDiagnosticOverflow,\\n    SearchDiagnostics, SearchPolicy, TranspositionBound,\\n")',
        'replace_once("crates/chess-search/src/alpha_beta.rs", "    EvaluationWeights, Score, SearchCancellationProbe, SearchPolicy, TranspositionBound,\\n", "    EvaluationWeights, Score, SearchCancellationProbe, SearchDiagnosticEvent,\\n    SearchDiagnosticOverflow, SearchDiagnostics, SearchPolicy, TranspositionBound,\\n")',
    ),
    (
        '        let mut maximum = SearchDiagnostics::default();\n        maximum.main_nodes = u64::MAX;',
        '        let maximum = SearchDiagnostics {\n            main_nodes: u64::MAX,\n            ..SearchDiagnostics::default()\n        };',
    ),
    (
        '        let mut diagnostics = SearchDiagnostics::default();\n        diagnostics.main_nodes = u64::MAX;',
        '        let mut diagnostics = SearchDiagnostics {\n            main_nodes: u64::MAX,\n            ..SearchDiagnostics::default()\n        };',
    ),
]
for old, new in replacements:
    if text.count(old) != 1:
        raise SystemExit(f"expected one staging repair witness: {old[:80]!r}")
    text = text.replace(old, new, 1)
exec(compile(text, str(path), "exec"), {"__name__": "__main__"})
