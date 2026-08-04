from pathlib import Path

path = Path('crates/chess-tools/src/candidate_validation.rs')
text = path.read_text()
replacements = (
    ('use chess_core::{Color, Position, SearchHistory};', 'use chess_core::{Position, SearchHistory};'),
    ('    run_weighted_validation_game, ClaimableDrawPolicy, OpeningSuite, SelfPlayLimit,\n    SelfPlayResult, SelfPlaySideConfig, SelfPlayTermination, WeightedValidationGameConfig,\n',
     '    run_weighted_validation_game, ClaimableDrawPolicy, OpeningSuite, SelfPlayResult,\n    SelfPlaySideConfig, SelfPlayTermination, WeightedValidationGameConfig,\n'),
    ('    use chess_search::EvaluationWeights;\n',
     '    use chess_search::EvaluationWeights;\n\n    use crate::self_play::SelfPlayLimit;\n'),
)
for old, new in replacements:
    if text.count(old) != 1:
        raise SystemExit(f'unexpected import block: {old!r}')
    text = text.replace(old, new, 1)
path.write_text(text)
