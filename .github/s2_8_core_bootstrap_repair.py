from pathlib import Path


path = Path('.github/s2_8_core_bootstrap.py')
text = path.read_text(encoding='utf-8')


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one occurrence, found {count}')
    text = text.replace(old, new, 1)


replace_once(
    '    "    \\\"pub const LMR_MINIMUM_LEGAL_MOVES: u16 = 6;\\\\n\\\"\n"\n'
    '    "    \\\"/// Ordered `(minimum depth, minimum zero-based move index, reduction)` rules.\\\\n\\\"\n"',
    '    "    \\\"pub const LMR_MINIMUM_LEGAL_MOVES: u16 = 6;\\\\n\\\"\n"\n'
    '    "    \\\"/// Smallest total piece count at which S2-8 may reduce a move.\\\\n\\\"\n"\n'
    '    "    \\\"pub const LMR_MINIMUM_TOTAL_PIECES: u16 = 10;\\\\n\\\"\n"\n'
    '    "    \\\"/// Ordered `(minimum depth, minimum zero-based move index, reduction)` rules.\\\\n\\\"\n"',
    'policy total-piece constant',
)
replace_once(
    '    "            hash = hash_bytes(hash, &LMR_MINIMUM_LEGAL_MOVES.to_le_bytes());\\\\n\\\"\n"\n'
    '    "            for (minimum_depth, minimum_move_index, reduction) in LMR_REDUCTION_TABLE {\\\\n\\\"\n"',
    '    "            hash = hash_bytes(hash, &LMR_MINIMUM_LEGAL_MOVES.to_le_bytes());\\\\n\\\"\n"\n'
    '    "            hash = hash_bytes(hash, &LMR_MINIMUM_TOTAL_PIECES.to_le_bytes());\\\\n\\\"\n"\n'
    '    "            for (minimum_depth, minimum_move_index, reduction) in LMR_REDUCTION_TABLE {\\\\n\\\"\n"',
    'policy total-piece checksum',
)
replace_once(
    '    "        LMR_MINIMUM_DEPTH, LMR_MINIMUM_LEGAL_MOVES, LMR_MINIMUM_MOVE_INDEX,\\\\n\\\"\n"\n'
    '    "        LMR_REDUCTION_TABLE,\\\\n\\\"\n"',
    '    "        LMR_MINIMUM_DEPTH, LMR_MINIMUM_LEGAL_MOVES, LMR_MINIMUM_MOVE_INDEX,\\\\n\\\"\n"\n'
    '    "        LMR_MINIMUM_TOTAL_PIECES, LMR_REDUCTION_TABLE,\\\\n\\\"\n"',
    'search total-piece import',
)
replace_once(
    '    "    let legal_move_count = ordered_tokens.iter().len();\\\\n\\\\n\\\"\n"\n'
    '    "    for (move_index, token) in ordered_tokens.iter().enumerate() {\\\\n\\\"\n"',
    '    "    let legal_move_count = ordered_tokens.iter().len();\\\\n\\\"\n"\n'
    '    "    let total_piece_count = u16::try_from(position.all_occupancy().count())\\\\n\\\"\n"\n'
    '    "        .expect(\\\"a chess position contains at most 64 pieces\\\");\\\\n\\\\n\\\"\n"\n'
    '    "    for (move_index, token) in ordered_tokens.iter().enumerate() {\\\\n\\\"\n"',
    'search total-piece metadata',
)
replace_once(
    '    "                legal_move_count,\\\\n\\\"\n"\n'
    '    "                current,\\\\n\\\"\n"',
    '    "                legal_move_count,\\\\n\\\"\n"\n'
    '    "                total_piece_count,\\\\n\\\"\n"\n'
    '    "                current,\\\\n\\\"\n"',
    'child request total-piece field',
)
replace_once(
    '    legal_move_count: usize,\n    current: Move,\n',
    '    legal_move_count: usize,\n    total_piece_count: u16,\n    current: Move,\n',
    'child struct total-piece field',
)
replace_once(
    '        || request.protected_quiet_candidate\n        || request.current.kind().is_capture()\n',
    '        || request.protected_quiet_candidate\n        || request.total_piece_count < LMR_MINIMUM_TOTAL_PIECES\n        || request.current.kind().is_capture()\n',
    'total-piece reduction guard',
)
replace_once(
    '            legal_move_count: 20,\n            current,\n',
    '            legal_move_count: 20,\n            total_piece_count: 32,\n            current,\n',
    'unit request total-piece field',
)
replace_once(
    '        protected.legal_move_count = 5;\n        assert_eq!(late_move_reduction(protected, true), None);\n\n'
    '        let capture = quiet_move',
    '        protected.legal_move_count = 5;\n        assert_eq!(late_move_reduction(protected, true), None);\n'
    '        protected = request(quiet);\n        protected.total_piece_count = 3;\n'
    '        assert_eq!(late_move_reduction(protected, true), None);\n\n'
    '        let capture = quiet_move',
    'unit low-material witness',
)
replace_once(
    '    "    LMR_MINIMUM_LEGAL_MOVES, LMR_MINIMUM_MOVE_INDEX, LMR_REDUCTION_TABLE,\\\\n\\\"\n"\n',
    '    "    LMR_MINIMUM_LEGAL_MOVES, LMR_MINIMUM_MOVE_INDEX, LMR_MINIMUM_TOTAL_PIECES,\\\\n\\\"\n"\n'
    '    "    LMR_REDUCTION_TABLE,\\\\n\\\"\n"\n',
    'public total-piece export',
)
replace_once(
    '    LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID, LMR_MINIMUM_DEPTH, LMR_MINIMUM_LEGAL_MOVES,\n'
    '    LMR_MINIMUM_MOVE_INDEX, LMR_REDUCTION_TABLE,\n',
    '    LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID, LMR_MINIMUM_DEPTH, LMR_MINIMUM_LEGAL_MOVES,\n'
    '    LMR_MINIMUM_MOVE_INDEX, LMR_MINIMUM_TOTAL_PIECES, LMR_REDUCTION_TABLE,\n',
    'integration total-piece import',
)
replace_once(
    '    assert_eq!(LMR_MINIMUM_LEGAL_MOVES, 6);\n    assert_eq!(LMR_REDUCTION_TABLE, [(4, 4, 1), (7, 8, 2)]);\n',
    '    assert_eq!(LMR_MINIMUM_LEGAL_MOVES, 6);\n    assert_eq!(LMR_MINIMUM_TOTAL_PIECES, 10);\n'
    '    assert_eq!(LMR_REDUCTION_TABLE, [(4, 4, 1), (7, 8, 2)]);\n',
    'integration total-piece assertion',
)
replace_once(
    "grep -q 'pub const LMR_MINIMUM_LEGAL_MOVES: u16 = 6' \"$policy\" || fail \"missing low-mobility guard\"\n",
    "grep -q 'pub const LMR_MINIMUM_LEGAL_MOVES: u16 = 6' \"$policy\" || fail \"missing low-mobility guard\"\n"
    "grep -q 'pub const LMR_MINIMUM_TOTAL_PIECES: u16 = 10' \"$policy\" || fail \"missing low-material guard\"\n",
    'audit total-piece constant',
)
replace_once(
    "grep -q 'legal_move_count' \"$search\" || fail \"low-mobility nodes are not protected\"\n",
    "grep -q 'legal_move_count' \"$search\" || fail \"low-mobility nodes are not protected\"\n"
    "grep -q 'total_piece_count' \"$search\" || fail \"low-material nodes are not protected\"\n",
    'audit total-piece protection',
)
replace_once(
    'Path(".github/s2_8_core_bootstrap.py").unlink()\n',
    'Path(".github/s2_8_core_bootstrap.py").unlink()\n'
    'Path(".github/s2_8_core_bootstrap_repair.py").unlink()\n',
    'repair cleanup',
)

path.write_text(text, encoding='utf-8')
Path(__file__).unlink()
