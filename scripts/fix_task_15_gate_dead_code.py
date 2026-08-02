#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
path = root / "crates/chess-search/src/move_ordering.rs"
text = path.read_text()
old = """pub(crate) fn ordered_legal_moves_with_state_and_tt_move(
    position: &Position,
    tokens: &LegalMoveTokenList,
    ordering: MoveOrdering,
    ply: u16,
    quiet_state: &QuietOrderingState,
    transposition_table_move: Option<Move>,
) -> OrderedLegalMoves {
    let previous_pv_move = match ordering {
"""
new = """pub(crate) fn ordered_legal_moves_with_state_and_tt_move(
    position: &Position,
    tokens: &LegalMoveTokenList,
    ordering: MoveOrdering,
    ply: u16,
    quiet_state: &QuietOrderingState,
    transposition_table_move: Option<Move>,
) -> OrderedLegalMoves {
    if transposition_table_move == transposition_table_move_hook(position) {
        return ordered_legal_moves_with_state(position, tokens, ordering, ply, quiet_state);
    }

    let previous_pv_move = match ordering {
"""
if text.count(old) != 1:
    raise SystemExit("expected explicit TT move-ordering function exactly once")
path.write_text(text.replace(old, new, 1))
