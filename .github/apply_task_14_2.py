#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


move_ordering = r'''use chess_core::{
    LegalMoveToken, LegalMoveTokenList, Move, MoveKind, PieceKind, Position,
    MAX_PSEUDO_LEGAL_MOVES,
};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum MoveOrdering {
    Generation,
    Tactical,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
struct MoveOrderKey {
    transposition_table: u8,
    category: u8,
    promotion: u16,
    victim: u16,
    attacker_preference: u16,
}

impl MoveOrderKey {
    const GENERATION: Self = Self {
        transposition_table: 0,
        category: 0,
        promotion: 0,
        victim: 0,
        attacker_preference: 0,
    };
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct OrderedEntry {
    token: LegalMoveToken,
    key: MoveOrderKey,
}

pub(crate) struct OrderedLegalMoves {
    entries: [Option<OrderedEntry>; MAX_PSEUDO_LEGAL_MOVES],
    len: usize,
}

impl OrderedLegalMoves {
    fn new() -> Self {
        Self {
            entries: [None; MAX_PSEUDO_LEGAL_MOVES],
            len: 0,
        }
    }

    pub(crate) fn iter(&self) -> impl ExactSizeIterator<Item = LegalMoveToken> + '_ {
        self.entries[..self.len]
            .iter()
            .copied()
            .map(|entry| entry.expect("occupied ordered-move prefix contains entries").token)
    }
}

pub(crate) fn ordered_legal_moves(
    position: &Position,
    tokens: &LegalMoveTokenList,
    ordering: MoveOrdering,
) -> OrderedLegalMoves {
    let transposition_table_move = match ordering {
        MoveOrdering::Generation => None,
        MoveOrdering::Tactical => transposition_table_move_hook(position),
    };
    order_legal_moves_with_tt_move(position, tokens, ordering, transposition_table_move)
}

const fn transposition_table_move_hook(_position: &Position) -> Option<Move> {
    None
}

fn order_legal_moves_with_tt_move(
    position: &Position,
    tokens: &LegalMoveTokenList,
    ordering: MoveOrdering,
    transposition_table_move: Option<Move>,
) -> OrderedLegalMoves {
    let mut ordered = OrderedLegalMoves::new();

    for token in tokens.iter() {
        let current = token.move_made();
        let key = match ordering {
            MoveOrdering::Generation => MoveOrderKey::GENERATION,
            MoveOrdering::Tactical => {
                tactical_key(position, current, transposition_table_move)
            }
        };
        let entry = OrderedEntry { token, key };
        let mut insertion = ordered.len;
        while insertion > 0 {
            let previous = ordered.entries[insertion - 1]
                .expect("occupied ordered-move prefix contains entries");
            if previous.key >= entry.key {
                break;
            }
            ordered.entries[insertion] = Some(previous);
            insertion -= 1;
        }
        ordered.entries[insertion] = Some(entry);
        ordered.len += 1;
    }

    ordered
}

fn tactical_key(
    position: &Position,
    current: Move,
    transposition_table_move: Option<Move>,
) -> MoveOrderKey {
    let promotion = current.promotion();
    let capture = current.kind().is_capture();
    let category = if promotion.is_some() {
        2
    } else if capture {
        1
    } else {
        0
    };
    let victim = if capture {
        captured_piece_kind(position, current).map_or(0, piece_value)
    } else {
        0
    };
    let attacker_preference = if capture {
        let attacker = position
            .piece_at(current.source())
            .expect("a legal move source is occupied")
            .kind;
        piece_value(PieceKind::King) - piece_value(attacker)
    } else {
        0
    };

    MoveOrderKey {
        transposition_table: u8::from(transposition_table_move == Some(current)),
        category,
        promotion: promotion.map_or(0, piece_value),
        victim,
        attacker_preference,
    }
}

fn captured_piece_kind(position: &Position, current: Move) -> Option<PieceKind> {
    if current.kind() == MoveKind::EnPassant {
        Some(PieceKind::Pawn)
    } else {
        position.piece_at(current.destination()).map(|piece| piece.kind)
    }
}

const fn piece_value(kind: PieceKind) -> u16 {
    match kind {
        PieceKind::Pawn => 100,
        PieceKind::Knight => 320,
        PieceKind::Bishop => 330,
        PieceKind::Rook => 500,
        PieceKind::Queen => 900,
        PieceKind::King => 20_000,
    }
}

#[cfg(test)]
mod tests {
    use chess_core::{Move, Position};

    use super::{
        order_legal_moves_with_tt_move, ordered_legal_moves, transposition_table_move_hook,
        MoveOrdering,
    };

    fn position(fen: &str) -> Position {
        fen.parse().expect("move-ordering fixture FEN is valid")
    }

    fn ordered_moves(root: &mut Position, ordering: MoveOrdering) -> Vec<Move> {
        let tokens = root
            .legal_move_tokens()
            .expect("legal move tokens generate");
        ordered_legal_moves(root, &tokens, ordering)
            .iter()
            .map(|token| token.move_made())
            .collect()
    }

    #[test]
    fn transposition_table_hook_is_an_explicit_no_op() {
        let root = Position::starting();
        assert_eq!(transposition_table_move_hook(&root), None);
    }

    #[test]
    fn generation_policy_preserves_exact_legal_token_order() {
        let mut root = Position::starting();
        let expected: Vec<_> = root
            .legal_move_tokens()
            .expect("legal move tokens generate")
            .iter()
            .map(|token| token.move_made())
            .collect();
        let actual = ordered_moves(&mut root, MoveOrdering::Generation);
        assert_eq!(actual, expected);
    }

    #[test]
    fn tt_move_and_promotions_precede_captures_and_quiets() {
        let mut root = position("3r3k/P7/8/8/8/8/8/K2Q4 w - - 0 1");
        let tokens = root
            .legal_move_tokens()
            .expect("legal move tokens generate");
        let tt_move = tokens
            .iter()
            .map(|token| token.move_made())
            .find(|current| current.to_uci() == "a1b1")
            .expect("fixture quiet TT move exists");
        let ordered: Vec<_> = order_legal_moves_with_tt_move(
            &root,
            &tokens,
            MoveOrdering::Tactical,
            Some(tt_move),
        )
        .iter()
        .map(|token| token.move_made())
        .collect();

        assert_eq!(ordered[0], tt_move);
        let promotions: Vec<_> = ordered
            .iter()
            .copied()
            .filter(|current| current.promotion().is_some())
            .map(Move::to_uci)
            .collect();
        assert_eq!(
            promotions,
            ["a7a8q", "a7a8r", "a7a8b", "a7a8n"]
        );
        let last_promotion = ordered
            .iter()
            .rposition(|current| current.promotion().is_some())
            .expect("fixture promotions exist");
        let capture = ordered
            .iter()
            .position(|current| current.to_uci() == "d1d8")
            .expect("fixture capture exists");
        assert!(last_promotion < capture);
    }

    #[test]
    fn captures_use_mvv_lva_with_stable_equal_keys() {
        let mut victim_root = position("7k/8/8/1p2q3/2P1Q3/8/K7/8 w - - 0 1");
        let victim_order: Vec<_> = ordered_moves(&mut victim_root, MoveOrdering::Tactical)
            .into_iter()
            .filter(|current| current.kind().is_capture())
            .map(Move::to_uci)
            .collect();
        assert_eq!(&victim_order[..2], ["e4e5", "c4b5"]);

        let mut attacker_root = position("7k/8/8/3q4/2P5/8/8/K2R4 w - - 0 1");
        let attacker_order: Vec<_> = ordered_moves(&mut attacker_root, MoveOrdering::Tactical)
            .into_iter()
            .filter(|current| current.kind().is_capture())
            .map(Move::to_uci)
            .collect();
        assert_eq!(&attacker_order[..2], ["c4d5", "d1d5"]);
    }
}
'''
(root / "crates/chess-search/src/move_ordering.rs").write_text(move_ordering)

lib_path = root / "crates/chess-search/src/lib.rs"
lib = lib_path.read_text()
lib = replace_once(
    lib,
    "mod evaluation;\nmod quiescence;",
    "mod evaluation;\nmod move_ordering;\nmod quiescence;",
    "search module declaration",
)
lib_path.write_text(lib)

alpha_path = root / "crates/chess-search/src/alpha_beta.rs"
alpha = alpha_path.read_text()
alpha = replace_once(
    alpha,
    "    cancellation::NeverCancelled,\n    quiescence::{search_quiescence_node, QuiescenceContext},",
    "    cancellation::NeverCancelled,\n    move_ordering::{ordered_legal_moves, MoveOrdering},\n    quiescence::{search_quiescence_node, QuiescenceContext},",
    "alpha-beta imports",
)
alpha = replace_once(
    alpha,
    "/// promotions, and every legal check evasion. Legal moves retain their\n/// deterministic generation order, and equal scores keep the first move. The\n/// root uses the complete supported score window, so its returned score is exact",
    "/// promotions, and every legal check evasion. Legal moves use deterministic\n/// tactical ordering: the future TT hook, promotions, MVV-LVA captures, then\n/// generation-stable quiet moves. Equal scores keep the first searched move. The\n/// root uses the complete supported score window, so its returned score is exact",
    "alpha-beta ordering documentation",
)
alpha = replace_once(
    alpha,
    "    let result = search_node(position, history, depth, 0, alpha, beta, cancellation);",
    "    let result = search_node(\n        position,\n        history,\n        depth,\n        0,\n        alpha,\n        beta,\n        MoveOrdering::Tactical,\n        cancellation,\n    );",
    "alpha-beta root ordering",
)
alpha = replace_once(
    alpha,
    "    mut alpha: Score,\n    beta: Score,\n    cancellation: &mut Probe,",
    "    mut alpha: Score,\n    beta: Score,\n    ordering: MoveOrdering,\n    cancellation: &mut Probe,",
    "alpha-beta node ordering parameter",
)
alpha = replace_once(
    alpha,
    "        return search_quiescence_node(position, history, context, alpha, beta, cancellation);",
    "        return search_quiescence_node(\n            position,\n            history,\n            context,\n            alpha,\n            beta,\n            ordering,\n            cancellation,\n        );",
    "alpha-beta quiescence ordering",
)
alpha = replace_once(
    alpha,
    "    let mut nodes = 1_u64;\n    let mut best_score = None;",
    "    let ordered_tokens = ordered_legal_moves(position, &tokens, ordering);\n    let mut nodes = 1_u64;\n    let mut best_score = None;",
    "alpha-beta ordered token construction",
)
alpha = replace_once(
    alpha,
    "    for token in tokens.iter() {",
    "    for token in ordered_tokens.iter() {",
    "alpha-beta ordered iteration",
)
alpha = replace_once(
    alpha,
    "            -beta,\n            -alpha,\n            cancellation,",
    "            -beta,\n            -alpha,\n            ordering,\n            cancellation,",
    "alpha-beta recursive ordering",
)
alpha_path.write_text(alpha)

quiescence_path = root / "crates/chess-search/src/quiescence.rs"
quiescence = quiescence_path.read_text()
quiescence = replace_once(
    quiescence,
    "    evaluate,\n    search_common::resolved_terminal_or_draw_score,",
    "    evaluate,\n    move_ordering::{ordered_legal_moves, MoveOrdering},\n    search_common::resolved_terminal_or_draw_score,",
    "quiescence imports",
)
quiescence = replace_once(
    quiescence,
    "    let result = search_quiescence_node(position, history, context, alpha, beta, cancellation);",
    "    let result = search_quiescence_node(\n        position,\n        history,\n        context,\n        alpha,\n        beta,\n        MoveOrdering::Tactical,\n        cancellation,\n    );",
    "quiescence root ordering",
)
quiescence = replace_once(
    quiescence,
    "    mut alpha: Score,\n    beta: Score,\n    cancellation: &mut Probe,",
    "    mut alpha: Score,\n    beta: Score,\n    ordering: MoveOrdering,\n    cancellation: &mut Probe,",
    "quiescence node ordering parameter",
)
quiescence = replace_once(
    quiescence,
    "    let mut nodes = 1_u64;\n    for token in tokens.iter() {",
    "    let ordered_tokens = ordered_legal_moves(position, &tokens, ordering);\n    let mut nodes = 1_u64;\n    for token in ordered_tokens.iter() {",
    "quiescence ordered iteration",
)
quiescence = replace_once(
    quiescence,
    "            -beta,\n            -alpha,\n            cancellation,",
    "            -beta,\n            -alpha,\n            ordering,\n            cancellation,",
    "quiescence recursive ordering",
)
quiescence += r'''

#[cfg(test)]
mod ordering_tests {
    use chess_core::{Position, SearchHistory};

    use super::{search_quiescence_node, QuiescenceContext, MAX_QUIESCENCE_PLY};
    use crate::{
        cancellation::NeverCancelled,
        move_ordering::MoveOrdering,
        Score,
    };

    fn search_with_ordering(root: &Position, ordering: MoveOrdering) -> super::QuiescenceSearchResult {
        let mut position = root.clone();
        let snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);
        let history_snapshot = history.clone();
        let context = QuiescenceContext {
            ply: 0,
            quiescence_ply: 0,
            maximum_quiescence_ply: MAX_QUIESCENCE_PLY,
        };
        let mut cancellation = NeverCancelled;
        let result = search_quiescence_node(
            &mut position,
            &mut history,
            context,
            Score::from_evaluation(-700),
            Score::from_evaluation(700),
            ordering,
            &mut cancellation,
        )
        .expect("ordering benchmark search succeeds");

        assert_eq!(position, snapshot);
        assert_eq!(history, history_snapshot);
        assert_eq!(position.zobrist(), position.recomputed_zobrist());
        result
    }

    #[test]
    fn tactical_ordering_reduces_a_fixed_cutoff_tree_without_changing_the_result() {
        let root: Position = "7k/8/8/1p2q3/2P1Q3/8/K7/8 w - - 0 1"
            .parse()
            .expect("ordering benchmark FEN is valid");
        let generation = search_with_ordering(&root, MoveOrdering::Generation);
        let tactical = search_with_ordering(&root, MoveOrdering::Tactical);

        assert_eq!(tactical.score(), generation.score());
        assert_eq!(tactical.best_move(), generation.best_move());
        assert_eq!(
            tactical
                .best_move()
                .expect("benchmark has a cutoff move")
                .to_uci(),
            "e4e5"
        );
        assert!(
            tactical.nodes() < generation.nodes(),
            "tactical ordering visited {} nodes versus generation order {}",
            tactical.nodes(),
            generation.nodes()
        );
    }
}
'''
quiescence_path.write_text(quiescence)

reference_path = root / "crates/chess-search/src/reference.rs"
reference = reference_path.read_text()
reference = replace_once(
    reference,
    "    cancellation::NeverCancelled, evaluate, search_common::resolved_terminal_or_draw_score, Score,\n    SearchCancellationProbe, MAX_MATE_PLY, MAX_QUIESCENCE_PLY,",
    "    cancellation::NeverCancelled, evaluate,\n    move_ordering::{ordered_legal_moves, MoveOrdering},\n    search_common::resolved_terminal_or_draw_score, Score, SearchCancellationProbe, MAX_MATE_PLY,\n    MAX_QUIESCENCE_PLY,",
    "reference imports",
)
reference = replace_once(
    reference,
    "    let mut nodes = 1_u64;\n    let mut best_score = None;\n    let mut best_move = None;\n\n    for token in tokens.iter() {",
    "    let ordered_tokens = ordered_legal_moves(position, &tokens, MoveOrdering::Generation);\n    let mut nodes = 1_u64;\n    let mut best_score = None;\n    let mut best_move = None;\n\n    for token in ordered_tokens.iter() {",
    "reference full-tree generation ordering",
)
reference = replace_once(
    reference,
    "    let mut nodes = 1_u64;\n    for token in tokens.iter() {",
    "    let ordered_tokens = ordered_legal_moves(position, &tokens, MoveOrdering::Generation);\n    let mut nodes = 1_u64;\n    for token in ordered_tokens.iter() {",
    "reference quiescence generation ordering",
)
reference_path.write_text(reference)

documentation = r'''# Rust Tactical Move Ordering

Task 14.2 adds a deterministic, bounded move-ordering layer to alpha-beta and
quiescence search without changing legal move identity or score semantics.

## Ordering pipeline

The production search order is:

1. a transposition-table move hook;
2. promotions, with higher promoted material first;
3. captures ordered by most-valuable victim, then least-valuable attacker;
4. remaining moves in their original deterministic legal-generation order.

The transposition-table hook deliberately returns `None` until Task 15 provides
bounded transposition storage. Keeping the hook explicit fixes the integration
point without introducing a fake cache or unbounded map.

Promotion captures remain in the promotion tier. Equal ordering keys are stable:
the insertion sorter does not displace an earlier legal token with an equal key.
This preserves deterministic behavior without using a strategic score as a move
override.

## Storage and state safety

`OrderedLegalMoves` is stack-backed with the same 256-entry capacity as legal
move generation. It copies opaque source-bound legal tokens into an ordered view;
it does not synthesize moves, mutate the position, allocate per node, or weaken
token origin validation. Search still applies and restores every child through
the existing token, history, and make/unmake contracts.

The unpruned reference search uses the explicit `Generation` policy, which
retains its original token order exactly. This provides a production-used
control policy and keeps reference-search semantics independent of heuristics.

## Correctness and performance evidence

Unit coverage verifies:

- the transposition-table hook is currently an explicit no-op;
- generation policy preserves the exact legal-token sequence;
- a supplied future TT move takes first priority;
- queen, rook, bishop, and knight promotions are ordered by material value;
- MVV-LVA prefers a more valuable victim and, for equal victims, a cheaper
  attacker;
- a fixed narrow-window tactical tree returns the same fail-soft score and best
  move while visiting fewer nodes than generation order;
- both searches restore the exact position, history, and Zobrist identity.

The permanent reference-equivalence, terminal, cancellation, quiescence, perft,
and differential gates continue to protect exact search semantics.

## Explicit exclusions

Task 14.2 does not add static exchange evaluation, killer moves, history
heuristics, previous-PV ordering, transposition storage, iterative deepening, or
production search limits. SEE remains optional only after the baseline ordering
is measured and correct. Quiet ordering belongs to Task 14.3, transposition
storage to Task 15, and limits/PV management to Task 16.
'''
(root / "docs/RUST_TACTICAL_MOVE_ORDERING.md").write_text(documentation)

print("Task 14.2 tactical ordering patch applied")
