from pathlib import Path
import runpy


runpy.run_path('.github/s2_8_core_bootstrap.py', run_name='__main__')


def replace_once(path: str, old: str, new: str, label: str) -> None:
    target = Path(path)
    text = target.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one occurrence, found {count}')
    target.write_text(text.replace(old, new, 1), encoding='utf-8')


policy = 'crates/chess-search/src/search_policy.rs'
replace_once(
    policy,
    'pub const LMR_MINIMUM_LEGAL_MOVES: u16 = 6;\n',
    'pub const LMR_MINIMUM_LEGAL_MOVES: u16 = 6;\n'
    '/// Smallest total piece count at which S2-8 may reduce a move.\n'
    'pub const LMR_MINIMUM_TOTAL_PIECES: u16 = 10;\n',
    'LMR low-material constant',
)
replace_once(
    policy,
    '            hash = hash_bytes(hash, &LMR_MINIMUM_LEGAL_MOVES.to_le_bytes());\n',
    '            hash = hash_bytes(hash, &LMR_MINIMUM_LEGAL_MOVES.to_le_bytes());\n'
    '            hash = hash_bytes(hash, &LMR_MINIMUM_TOTAL_PIECES.to_le_bytes());\n',
    'LMR low-material checksum binding',
)

search = 'crates/chess-search/src/alpha_beta.rs'
replace_once(
    search,
    '        LMR_MINIMUM_DEPTH, LMR_MINIMUM_LEGAL_MOVES, LMR_MINIMUM_MOVE_INDEX,\n'
    '        LMR_REDUCTION_TABLE,\n',
    '        LMR_MINIMUM_DEPTH, LMR_MINIMUM_LEGAL_MOVES, LMR_MINIMUM_MOVE_INDEX,\n'
    '        LMR_MINIMUM_TOTAL_PIECES, LMR_REDUCTION_TABLE,\n',
    'LMR low-material import',
)
replace_once(
    search,
    '    let legal_move_count = ordered_tokens.iter().len();\n\n',
    '    let legal_move_count = ordered_tokens.iter().len();\n'
    '    let total_piece_count = u16::try_from(position.all_occupancy().count())\n'
    '        .expect("a chess position contains at most 64 pieces");\n\n',
    'LMR node piece count',
)
replace_once(
    search,
    '                legal_move_count,\n                current,\n',
    '                legal_move_count,\n                total_piece_count,\n                current,\n',
    'LMR child request piece count',
)
replace_once(
    search,
    '    legal_move_count: usize,\n    current: Move,\n',
    '    legal_move_count: usize,\n    total_piece_count: u16,\n    current: Move,\n',
    'LMR request piece-count field',
)
replace_once(
    search,
    '        || request.protected_quiet_candidate\n        || request.current.kind().is_capture()\n',
    '        || request.protected_quiet_candidate\n'
    '        || request.total_piece_count < LMR_MINIMUM_TOTAL_PIECES\n'
    '        || request.alpha.is_mate()\n'
    '        || request.beta.is_mate()\n'
    '        || request.current.kind().is_capture()\n',
    'LMR low-material and mate-window guards',
)
replace_once(
    search,
    '            legal_move_count: 20,\n            current,\n',
    '            legal_move_count: 20,\n            total_piece_count: 32,\n            current,\n',
    'LMR unit request piece count',
)
replace_once(
    search,
    '        protected.legal_move_count = 5;\n'
    '        assert_eq!(late_move_reduction(protected, true), None);\n\n'
    '        let capture = quiet_move',
    '        protected.legal_move_count = 5;\n'
    '        assert_eq!(late_move_reduction(protected, true), None);\n'
    '        protected = request(quiet);\n'
    '        protected.total_piece_count = 3;\n'
    '        assert_eq!(late_move_reduction(protected, true), None);\n'
    '        protected = request(quiet);\n'
    '        protected.alpha = Score::mate_in(4).expect("mate score fits");\n'
    '        assert_eq!(late_move_reduction(protected, true), None);\n'
    '        protected = request(quiet);\n'
    '        protected.beta = Score::mated_in(4).expect("mate score fits");\n'
    '        assert_eq!(late_move_reduction(protected, true), None);\n\n'
    '        let capture = quiet_move',
    'LMR low-material and mate-window unit witnesses',
)

lib = 'crates/chess-search/src/lib.rs'
replace_once(
    lib,
    '    LMR_MINIMUM_LEGAL_MOVES, LMR_MINIMUM_MOVE_INDEX, LMR_REDUCTION_TABLE,\n',
    '    LMR_MINIMUM_LEGAL_MOVES, LMR_MINIMUM_MOVE_INDEX, LMR_MINIMUM_TOTAL_PIECES,\n'
    '    LMR_REDUCTION_TABLE,\n',
    'LMR low-material public export',
)

tests = 'crates/chess-search/tests/s2_8_lmr.rs'
replace_once(
    tests,
    '    LMR_MINIMUM_MOVE_INDEX, LMR_REDUCTION_TABLE,\n',
    '    LMR_MINIMUM_MOVE_INDEX, LMR_MINIMUM_TOTAL_PIECES, LMR_REDUCTION_TABLE,\n',
    'LMR low-material test import',
)
replace_once(
    tests,
    '    assert_eq!(LMR_MINIMUM_LEGAL_MOVES, 6);\n'
    '    assert_eq!(LMR_REDUCTION_TABLE, [(4, 4, 1), (7, 8, 2)]);\n',
    '    assert_eq!(LMR_MINIMUM_LEGAL_MOVES, 6);\n'
    '    assert_eq!(LMR_MINIMUM_TOTAL_PIECES, 10);\n'
    '    assert_eq!(LMR_REDUCTION_TABLE, [(4, 4, 1), (7, 8, 2)]);\n',
    'LMR low-material test assertion',
)

audit = 'scripts/task_s2_8_lmr_audit.sh'
replace_once(
    audit,
    'grep -q \'pub const LMR_MINIMUM_LEGAL_MOVES: u16 = 6\' "$policy" || fail "missing low-mobility guard"\n',
    'grep -q \'pub const LMR_MINIMUM_LEGAL_MOVES: u16 = 6\' "$policy" || fail "missing low-mobility guard"\n'
    'grep -q \'pub const LMR_MINIMUM_TOTAL_PIECES: u16 = 10\' "$policy" || fail "missing low-material guard"\n',
    'LMR low-material audit constant',
)
replace_once(
    audit,
    'grep -q \'legal_move_count\' "$search" || fail "low-mobility nodes are not protected"\n',
    'grep -q \'legal_move_count\' "$search" || fail "low-mobility nodes are not protected"\n'
    'grep -q \'total_piece_count\' "$search" || fail "low-material nodes are not protected"\n'
    'grep -q \'request.alpha.is_mate()\' "$search" || fail "mate alpha windows are not protected"\n'
    'grep -q \'request.beta.is_mate()\' "$search" || fail "mate beta windows are not protected"\n',
    'LMR low-material and mate-window audit guards',
)

Path('.github/s2_8_core_bootstrap_repair.py').unlink()
