#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "crates/chess-search/src/move_ordering.rs"
text = path.read_text()


def replace_once(old: str, new: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one replacement, found {count}: {old[:100]!r}")
    text = text.replace(old, new, 1)

# Bundle TT/PV priority hints so both hot-path helpers stay below Clippy's argument limit.
text = text.replace(
    "        transposition_table_move,\n        previous_pv_move,\n        see_capture_ordering,\n",
    "        (transposition_table_move, previous_pv_move),\n        see_capture_ordering,\n",
)
text = text.replace(
    "        transposition_table_move,\n        previous_pv_move,\n        false,\n",
    "        (transposition_table_move, previous_pv_move),\n        false,\n",
)
replace_once(
    "#[allow(clippy::too_many_arguments)]\nfn try_order_legal_moves_with_hints(\n    position: &Position,\n    tokens: &LegalMoveTokenList,\n    ordering: MoveOrdering,\n    ply: u16,\n    quiet_state: Option<&QuietOrderingState>,\n    transposition_table_move: Option<Move>,\n    previous_pv_move: Option<Move>,\n    see_capture_ordering: bool,\n) -> Result<OrderedLegalMoves, StaticExchangeError> {\n    let mut ordered = OrderedLegalMoves::new();\n",
    "fn try_order_legal_moves_with_hints(\n    position: &Position,\n    tokens: &LegalMoveTokenList,\n    ordering: MoveOrdering,\n    ply: u16,\n    quiet_state: Option<&QuietOrderingState>,\n    priority_moves: (Option<Move>, Option<Move>),\n    see_capture_ordering: bool,\n) -> Result<OrderedLegalMoves, StaticExchangeError> {\n    let (transposition_table_move, previous_pv_move) = priority_moves;\n    let mut ordered = OrderedLegalMoves::new();\n",
)
# Bundle TT/PV priority in key construction as well.
text = text.replace(
    "                transposition_table_move,\n                None,\n                KillerMoves::default(),\n",
    "                (transposition_table_move, None),\n                KillerMoves::default(),\n",
)
text = text.replace(
    "                    transposition_table_move,\n                    previous_pv_move,\n                    killers,\n",
    "                    (transposition_table_move, previous_pv_move),\n                    killers,\n",
)
text = text.replace(
    "                None,\n                None,\n                KillerMoves::default(),\n",
    "                (None, None),\n                KillerMoves::default(),\n",
)
replace_once(
    "#[allow(clippy::too_many_arguments)]\nfn tactical_key(\n    position: &Position,\n    current: Move,\n    transposition_table_move: Option<Move>,\n    previous_pv_move: Option<Move>,\n    killers: KillerMoves,\n    history: u32,\n    see_value: Option<StaticExchangeValue>,\n    encoded_tie_break: Option<Reverse<Move>>,\n) -> MoveOrderKey {\n    let promotion = current.promotion();\n",
    "fn tactical_key(\n    position: &Position,\n    current: Move,\n    priority_moves: (Option<Move>, Option<Move>),\n    killers: KillerMoves,\n    history: u32,\n    see_value: Option<StaticExchangeValue>,\n    encoded_tie_break: Option<Reverse<Move>>,\n) -> MoveOrderKey {\n    let (transposition_table_move, previous_pv_move) = priority_moves;\n    let promotion = current.promotion();\n",
)
# Test helper call uses explicit bundled priorities.
text = text.replace(
    "                None,\n                None,\n                KillerMoves::default(),\n",
    "                (None, None),\n                KillerMoves::default(),\n",
)

if "allow(clippy::too_many_arguments)" in text:
    raise SystemExit("lint suppression remained after S2-5 refinement")
path.write_text(text)
print("S2-5 lint-clean refinement applied")
