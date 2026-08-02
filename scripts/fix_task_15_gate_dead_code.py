#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
path = root / "crates/chess-search/src/move_ordering.rs"
text = path.read_text()

wrapper_old = """pub(crate) fn ordered_legal_moves_with_state(
    position: &Position,
    tokens: &LegalMoveTokenList,
    ordering: MoveOrdering,
    ply: u16,
    quiet_state: &QuietOrderingState,
) -> OrderedLegalMoves {
    ordered_legal_moves_with_state_and_tt_move(
        position,
        tokens,
        ordering,
        ply,
        quiet_state,
        transposition_table_move_hook(position),
    )
}
"""
wrapper_new = """pub(crate) fn ordered_legal_moves_with_state(
    position: &Position,
    tokens: &LegalMoveTokenList,
    ordering: MoveOrdering,
    ply: u16,
    quiet_state: &QuietOrderingState,
) -> OrderedLegalMoves {
    let previous_pv_move = match ordering {
        MoveOrdering::Quiet => previous_pv_move_hook(ply),
        MoveOrdering::Generation | MoveOrdering::Tactical => None,
    };
    order_legal_moves_with_hints(
        position,
        tokens,
        ordering,
        ply,
        Some(quiet_state),
        transposition_table_move_hook(position),
        previous_pv_move,
    )
}
"""
if text.count(wrapper_old) != 1:
    raise SystemExit("expected delegating move-ordering wrapper exactly once")
text = text.replace(wrapper_old, wrapper_new, 1)

explicit_old = """pub(crate) fn ordered_legal_moves_with_state_and_tt_move(
    position: &Position,
    tokens: &LegalMoveTokenList,
    ordering: MoveOrdering,
    ply: u16,
    quiet_state: &QuietOrderingState,
    transposition_table_move: Option<Move>,
) -> OrderedLegalMoves {
    let previous_pv_move = match ordering {
"""
explicit_new = """pub(crate) fn ordered_legal_moves_with_state_and_tt_move(
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
if text.count(explicit_old) != 1:
    raise SystemExit("expected explicit TT move-ordering function exactly once")
path.write_text(text.replace(explicit_old, explicit_new, 1))
