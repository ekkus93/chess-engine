#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()

aspiration_path = root / "crates/chess-search/src/aspiration.rs"
aspiration = aspiration_path.read_text(encoding="utf-8")
old_fields = '''pub struct AspirationWindowAttempt {
    alpha: Score,
    beta: Score,
    outcome: AspirationWindowOutcome,
    reported_score: Score,
    nodes: u64,
    transposition_diagnostics: TranspositionTableDiagnostics,
    hash_full: TranspositionHashFull,
    transposition_generation: u8,
}

impl AspirationWindowAttempt {
    pub(crate) const fn new(
        alpha: Score,
        beta: Score,
        outcome: AspirationWindowOutcome,
        reported_score: Score,
        nodes: u64,
        transposition_diagnostics: TranspositionTableDiagnostics,
        hash_full: TranspositionHashFull,
        transposition_generation: u8,
    ) -> Self {
        Self {
            alpha,
            beta,
            outcome,
            reported_score,
            nodes,
            transposition_diagnostics,
            hash_full,
            transposition_generation,
        }
    }

'''
new_fields = '''pub struct AspirationWindowAttempt {
    pub(crate) alpha: Score,
    pub(crate) beta: Score,
    pub(crate) outcome: AspirationWindowOutcome,
    pub(crate) reported_score: Score,
    pub(crate) nodes: u64,
    pub(crate) transposition_diagnostics: TranspositionTableDiagnostics,
    pub(crate) hash_full: TranspositionHashFull,
    pub(crate) transposition_generation: u8,
}

impl AspirationWindowAttempt {
'''
if aspiration.count(old_fields) != 1:
    raise RuntimeError("expected one aspiration attempt constructor block")
aspiration_path.write_text(aspiration.replace(old_fields, new_fields, 1), encoding="utf-8")

iteration_path = root / "crates/chess-search/src/iterative_deepening.rs"
iteration = iteration_path.read_text(encoding="utf-8")
old_call = '''    let attempt = AspirationWindowAttempt::new(
        window.alpha(),
        window.beta(),
        result.outcome(),
        search_result.score(),
        search_result.nodes(),
        transposition_table.diagnostics(),
        transposition_table.hash_full(),
        transposition_table.generation(),
    );
'''
new_call = '''    let attempt = AspirationWindowAttempt {
        alpha: window.alpha(),
        beta: window.beta(),
        outcome: result.outcome(),
        reported_score: search_result.score(),
        nodes: search_result.nodes(),
        transposition_diagnostics: transposition_table.diagnostics(),
        hash_full: transposition_table.hash_full(),
        transposition_generation: transposition_table.generation(),
    };
'''
if iteration.count(old_call) != 1:
    raise RuntimeError("expected one aspiration attempt construction call")
iteration_path.write_text(iteration.replace(old_call, new_call, 1), encoding="utf-8")
print("Task 16.2 attempt construction normalized")
