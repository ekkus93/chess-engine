from pathlib import Path

# Temporary fail-closed staging helper. Removed after the focused gate passes.
lib = Path('crates/chess-tools/src/lib.rs')
text = lib.read_text()
old = 'pub mod s3;\n'
new = 'pub mod s3;\npub mod s3_candidate;\n'
if text.count(old) != 1:
    raise SystemExit(f'expected one S3 module witness, found {text.count(old)}')
lib.write_text(text.replace(old, new, 1))

candidate = Path('crates/chess-tools/src/s3_candidate.rs')
text = candidate.read_text()
old = '''use chess_search::{
    EvaluationWeightSet, EvaluationWeights, BASELINE_WEIGHT_SET_ID, WEIGHT_VALUE_COUNT,
};
'''
new = '''use chess_search::{EvaluationWeightSet, WEIGHT_VALUE_COUNT};
'''
if text.count(old) != 1:
    raise SystemExit(f'expected one candidate import witness, found {text.count(old)}')
candidate.write_text(text.replace(old, new, 1))
