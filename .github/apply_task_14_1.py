#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
path = root / "crates/chess-search/src/alpha_beta.rs"
text = path.read_text()


def replace(old: str, new: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one alpha_beta match, found {count}: {old[:80]!r}")
    text = text.replace(old, new, 1)


replace(
    '''use crate::{
    cancellation::NeverCancelled, search_common::resolved_node_score, Score,
    SearchCancellationProbe, MAX_MATE_PLY,
};
''',
    '''use crate::{
    cancellation::NeverCancelled, quiescence::search_quiescence_node,
    search_common::resolved_node_score, Score, SearchCancellationProbe, MAX_MATE_PLY,
    MAX_QUIESCENCE_PLY,
};
''',
)
replace(
    '''pub struct AlphaBetaSearchResult {
    score: Score,
    best_move: Option<Move>,
    nodes: u64,
}
''',
    '''pub struct AlphaBetaSearchResult {
    pub(crate) score: Score,
    pub(crate) best_move: Option<Move>,
    pub(crate) nodes: u64,
}
''',
)
replace(
    '''    /// Returns the first deterministic best move, or `None` at leaves and terminals.
''',
    '''    /// Returns the first deterministic best move, or `None` when stand-pat or a terminal is best.
''',
)
replace(
    '''    /// Cooperative cancellation was requested.
    Cancelled,
    /// Recursive node accumulation exceeded `u64`.
''',
    '''    /// Cooperative cancellation was requested.
    Cancelled,
    /// The quiescence guard was reached while the side to move remained in check.
    QuiescenceDepthLimitReachedInCheck {
        /// Tactical ply at which expansion stopped.
        quiescence_ply: u16,
        /// Selected tactical-ply maximum.
        maximum: u16,
    },
    /// Recursive node accumulation exceeded `u64`.
''',
)
replace(
    '''            Self::Cancelled => formatter.write_str("alpha-beta search cancelled"),
            Self::NodeCountOverflow => formatter.write_str("alpha-beta node count overflow"),
''',
    '''            Self::Cancelled => formatter.write_str("alpha-beta search cancelled"),
            Self::QuiescenceDepthLimitReachedInCheck {
                quiescence_ply,
                maximum,
            } => write!(
                formatter,
                "quiescence depth limit {maximum} reached in check at tactical ply {quiescence_ply}"
            ),
            Self::NodeCountOverflow => formatter.write_str("alpha-beta node count overflow"),
''',
)
replace(
    '''/// The search uses the same side-to-move score, mate-distance, terminal, draw,
/// and repetition semantics as [`crate::reference_search`]. Legal moves retain
/// their deterministic generation order, and equal scores keep the first move.
/// The root uses the complete supported score window, so its returned score is
/// exact rather than a bound.
''',
    '''/// The search uses the same side-to-move score, mate-distance, terminal, draw,
/// and repetition semantics as [`crate::reference_search`]. At depth-zero
/// leaves it invokes correctness-first quiescence search over captures,
/// promotions, and every legal check evasion. Legal moves retain their
/// deterministic generation order, and equal scores keep the first move. The
/// root uses the complete supported score window, so its returned score is exact
/// rather than a bound.
''',
)
replace(
    '''    if cancellation.should_cancel() {
        return Err(AlphaBetaSearchError::Cancelled);
    }

    let tokens = position.legal_move_tokens()?;
''',
    '''    if cancellation.should_cancel() {
        return Err(AlphaBetaSearchError::Cancelled);
    }

    if depth == 0 {
        return search_quiescence_node(
            position,
            history,
            ply,
            0,
            MAX_QUIESCENCE_PLY,
            alpha,
            beta,
            cancellation,
        );
    }

    let tokens = position.legal_move_tokens()?;
''',
)
path.write_text(text)
print("alpha-beta integrated with quiescence")
