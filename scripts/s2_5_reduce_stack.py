#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "crates/chess-search/src/move_ordering.rs"
text = PATH.read_text()


def replace_once(old: str, new: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one replacement, found {count}: {old[:160]!r}")
    text = text.replace(old, new, 1)


# Sorting keys are temporary construction state. Recursive search retains only legal tokens
# and the bounded diagnostic summary, keeping the live per-ply stack below the v0.1 layout.
replace_once(
    "pub(crate) struct OrderedLegalMoves {\n"
    "    entries: [Option<OrderedEntry>; MAX_PSEUDO_LEGAL_MOVES],\n"
    "    len: usize,\n"
    "    diagnostics: MoveOrderingDiagnostics,\n"
    "}\n\n"
    "impl OrderedLegalMoves {\n"
    "    fn new() -> Self {\n"
    "        Self {\n"
    "            entries: [None; MAX_PSEUDO_LEGAL_MOVES],\n"
    "            len: 0,\n"
    "            diagnostics: MoveOrderingDiagnostics::default(),\n"
    "        }\n"
    "    }\n\n"
    "    pub(crate) fn iter(&self) -> impl ExactSizeIterator<Item = LegalMoveToken> + '_ {\n"
    "        self.entries[..self.len].iter().copied().map(|entry| {\n"
    "            entry\n"
    "                .expect(\"occupied ordered-move prefix contains entries\")\n"
    "                .token\n"
    "        })\n"
    "    }\n",
    "pub(crate) struct OrderedLegalMoves {\n"
    "    tokens: [Option<LegalMoveToken>; MAX_PSEUDO_LEGAL_MOVES],\n"
    "    len: usize,\n"
    "    diagnostics: MoveOrderingDiagnostics,\n"
    "}\n\n"
    "impl OrderedLegalMoves {\n"
    "    fn new() -> Self {\n"
    "        Self {\n"
    "            tokens: [None; MAX_PSEUDO_LEGAL_MOVES],\n"
    "            len: 0,\n"
    "            diagnostics: MoveOrderingDiagnostics::default(),\n"
    "        }\n"
    "    }\n\n"
    "    pub(crate) fn iter(&self) -> impl ExactSizeIterator<Item = LegalMoveToken> + '_ {\n"
    "        self.tokens[..self.len].iter().copied().map(|token| {\n"
    "            token.expect(\"occupied ordered-move prefix contains legal tokens\")\n"
    "        })\n"
    "    }\n",
)
replace_once(
    "    let (transposition_table_move, previous_pv_move) = priority_moves;\n"
    "    let mut ordered = OrderedLegalMoves::new();\n"
    "    for token in tokens.iter() {\n",
    "    let (transposition_table_move, previous_pv_move) = priority_moves;\n"
    "    let mut entries: [Option<OrderedEntry>; MAX_PSEUDO_LEGAL_MOVES] =\n"
    "        [None; MAX_PSEUDO_LEGAL_MOVES];\n"
    "    let mut len = 0_usize;\n"
    "    let mut diagnostics = MoveOrderingDiagnostics::default();\n"
    "    for token in tokens.iter() {\n",
)
replace_once(
    "            ordered.diagnostics.record_class(value.class());\n",
    "            diagnostics.record_class(value.class());\n",
)
replace_once(
    "        let mut insertion = ordered.len;\n"
    "        while insertion > 0 {\n"
    "            let previous = ordered.entries[insertion - 1]\n"
    "                .expect(\"occupied ordered-move prefix contains entries\");\n"
    "            if previous.key >= entry.key {\n"
    "                break;\n"
    "            }\n"
    "            ordered.entries[insertion] = Some(previous);\n"
    "            insertion -= 1;\n"
    "        }\n"
    "        ordered.entries[insertion] = Some(entry);\n"
    "        ordered.len += 1;\n"
    "    }\n"
    "    Ok(ordered)\n",
    "        let mut insertion = len;\n"
    "        while insertion > 0 {\n"
    "            let previous = entries[insertion - 1]\n"
    "                .expect(\"occupied ordered-move prefix contains entries\");\n"
    "            if previous.key >= entry.key {\n"
    "                break;\n"
    "            }\n"
    "            entries[insertion] = Some(previous);\n"
    "            insertion -= 1;\n"
    "        }\n"
    "        entries[insertion] = Some(entry);\n"
    "        len += 1;\n"
    "    }\n\n"
    "    let mut ordered = OrderedLegalMoves::new();\n"
    "    ordered.len = len;\n"
    "    ordered.diagnostics = diagnostics;\n"
    "    for (destination, entry) in ordered.tokens[..len].iter_mut().zip(entries[..len].iter()) {\n"
    "        *destination = Some(\n"
    "            entry\n"
    "                .expect(\"occupied sorted-move prefix contains entries\")\n"
    "                .token,\n"
    "        );\n"
    "    }\n"
    "    Ok(ordered)\n",
)

# Permanent regression: the recursively retained container excludes the temporary sort keys.
replace_once(
    "    use chess_core::{Move, Position, StaticExchangeError, StaticExchangeMoveStateError};\n",
    "    use core::mem::size_of;\n\n"
    "    use chess_core::{\n"
    "        Move, Position, StaticExchangeError, StaticExchangeMoveStateError,\n"
    "        MAX_PSEUDO_LEGAL_MOVES,\n"
    "    };\n",
)
replace_once(
    "        tactical_key, transposition_table_move_hook, try_order_legal_moves_with_hints,\n"
    "        KillerMoves, MoveOrdering,\n",
    "        tactical_key, transposition_table_move_hook, try_order_legal_moves_with_hints,\n"
    "        KillerMoves, MoveOrdering, OrderedEntry, OrderedLegalMoves,\n",
)
replace_once(
    "    #[test]\n"
    "    fn transposition_table_hook_is_an_explicit_no_op() {\n",
    "    #[test]\n"
    "    fn recursively_retained_ordering_excludes_temporary_sort_keys() {\n"
    "        assert!(\n"
    "            size_of::<OrderedLegalMoves>()\n"
    "                < size_of::<[Option<OrderedEntry>; MAX_PSEUDO_LEGAL_MOVES]>()\n"
    "        );\n"
    "    }\n\n"
    "    #[test]\n"
    "    fn transposition_table_hook_is_an_explicit_no_op() {\n",
)

if "ordered.entries" in text:
    raise SystemExit("recursively retained sort-key storage remains")
PATH.write_text(text)
print("S2-5 recursive ordering stack footprint reduced")
