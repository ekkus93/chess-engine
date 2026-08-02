from pathlib import Path
import sys

root = Path(sys.argv[1])

transposition = root / "crates/chess-search/src/transposition.rs"
text = transposition.read_text()
needle = "use crate::Score;\n\n"
replacement = """use crate::Score;\n\nmod probe;\npub use probe::{\n    TranspositionProbeError, TranspositionProbeRequest, TranspositionProbeResult,\n    TranspositionProbeScore, TranspositionScoreReuse,\n};\n\n"""
if replacement not in text:
    if needle not in text:
        raise SystemExit("transposition.rs insertion point not found")
    text = text.replace(needle, replacement, 1)
text = text.replace(
    "/// The tag describes how the score may eventually be reused by a probe. Task\n/// 15.4 owns the cutoff rules; this type only makes the three meanings explicit\n/// and impossible to confuse with one another.",
    "/// The tag describes how [`TranspositionTable::probe`] may reuse the score.\n/// Keeping all three meanings explicit prevents a bound from being mistaken for\n/// an exact minimax value.",
)
text = text.replace(
    "/// never grows after construction and has no unbounded map fallback. Task 15.5\n/// will define how stores choose a slot inside a cluster; Task 15.4 will define\n/// probe semantics.",
    "/// never grows after construction and has no unbounded map fallback. Probes\n/// verify complete keys and apply depth, bound, mate, and repetition safety. Task\n/// 15.5 will define how stores choose a slot inside a cluster.",
)
transposition.write_text(text)

lib = root / "crates/chess-search/src/lib.rs"
text = lib.read_text()
old = """pub use transposition::{\n    TranspositionBound, TranspositionEntry, TranspositionScore, TranspositionTable,\n    TranspositionTableAllocationError, TRANSPOSITION_CLUSTER_SIZE,\n};\n"""
new = """pub use transposition::{\n    TranspositionBound, TranspositionEntry, TranspositionProbeError, TranspositionProbeRequest,\n    TranspositionProbeResult, TranspositionProbeScore, TranspositionScore,\n    TranspositionScoreReuse, TranspositionTable, TranspositionTableAllocationError,\n    TRANSPOSITION_CLUSTER_SIZE,\n};\n"""
if old not in text and new not in text:
    raise SystemExit("lib.rs export block not found")
text = text.replace(old, new, 1)
lib.write_text(text)

doc = root / "docs/RUST_TRANSPOSITION_TABLE_PROBE_SEMANTICS.md"
doc.write_text("""# Rust transposition-table probe semantics\n\nTask 15.4 defines a storage-only probe boundary. Production alpha-beta search is not yet wired to the table, and replacement policy remains Task 15.5.\n\n## Complete-key verification\n\n`TranspositionTable::probe` selects one four-entry cluster from the complete 64-bit Zobrist key, then accepts only an entry whose stored verification key matches all 64 bits. An index collision is a miss, not a partial hit.\n\n## Depth and bound rules\n\nA verified best move is returned as an ordering hint regardless of stored depth. Score reuse additionally requires `stored_depth >= required_depth`.\n\nAfter denormalizing the stored score at the current probe ply:\n\n- `Exact` returns the score directly.\n- `Lower` returns a fail-high cutoff only when `score >= beta`.\n- `Upper` returns a fail-low cutoff only when `score <= alpha`.\n- A bound that does not cross its window edge contributes no score, while its verified best move remains available.\n\nThe request rejects `alpha >= beta` rather than assigning undefined meaning to an invalid window.\n\n## Mate-distance safety\n\nEvery reusable score passes through `TranspositionScore::denormalize(current_ply)` before comparison or return. Conversion failures remain typed `TranspositionProbeError::ScoreConversion` errors; probes never clamp or substitute a score.\n\n## Repetition-sensitive nodes\n\nA Zobrist position key does not encode the path used to reach the position. `TranspositionScoreReuse::SuppressedForRepetition` therefore disables every cached score for a node whose repetition history may affect its value. The verified best move remains an ordering hint only; it cannot terminate search or bypass legal move validation.\n\nThe search integration in a later task must choose this conservative mode before probing any repetition-sensitive node.\n\n## Deferred work\n\nTask 15.4 does not define insertion or replacement. Tests install fixtures directly into private clusters. Task 15.5 will provide deterministic same-key updates and collision replacement, and Task 15.6 will add counters, hash-full estimation, and benchmarks.\n""")
