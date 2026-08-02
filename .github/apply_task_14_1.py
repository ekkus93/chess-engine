#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])


def patch(relative_path: str, replacements: list[tuple[str, str]]) -> None:
    path = root / relative_path
    text = path.read_text()
    for old, new in replacements:
        count = text.count(old)
        if count != 1:
            raise SystemExit(
                f"expected one match in {relative_path}, found {count}: {old[:100]!r}"
            )
        text = text.replace(old, new, 1)
    path.write_text(text)


patch(
    "crates/chess-search/src/quiescence.rs",
    [
        (
            '''/// Quiescence uses the normal alpha-beta result shape.
pub type QuiescenceSearchResult = AlphaBetaSearchResult;
''',
            '''/// Quiescence uses the normal alpha-beta result shape.
pub type QuiescenceSearchResult = AlphaBetaSearchResult;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct QuiescenceContext {
    pub(crate) ply: u16,
    pub(crate) quiescence_ply: u16,
    pub(crate) maximum_quiescence_ply: u16,
}
''',
        ),
        (
            '''    let result = search_quiescence_node(
        position,
        history,
        0,
        0,
        maximum_quiescence_ply,
        alpha,
        beta,
        cancellation,
    );
''',
            '''    let context = QuiescenceContext {
        ply: 0,
        quiescence_ply: 0,
        maximum_quiescence_ply,
    };
    let result = search_quiescence_node(
        position,
        history,
        context,
        alpha,
        beta,
        cancellation,
    );
''',
        ),
        (
            '''pub(crate) fn search_quiescence_node<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    ply: u16,
    quiescence_ply: u16,
    maximum_quiescence_ply: u16,
    mut alpha: Score,
    beta: Score,
    cancellation: &mut Probe,
) -> Result<QuiescenceSearchResult, AlphaBetaSearchError>
''',
            '''pub(crate) fn search_quiescence_node<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    context: QuiescenceContext,
    mut alpha: Score,
    beta: Score,
    cancellation: &mut Probe,
) -> Result<QuiescenceSearchResult, AlphaBetaSearchError>
''',
        ),
        (
            '''    if let Some(score) = resolved_terminal_or_draw_score(position, history, tokens.is_empty(), ply)
''',
            '''    if let Some(score) =
        resolved_terminal_or_draw_score(position, history, tokens.is_empty(), context.ply)
''',
        ),
        (
            '''    if in_check {
        if quiescence_ply >= maximum_quiescence_ply {
            return Err(AlphaBetaSearchError::QuiescenceDepthLimitReachedInCheck {
                quiescence_ply,
                maximum: maximum_quiescence_ply,
            });
        }
''',
            '''    if in_check {
        if context.quiescence_ply >= context.maximum_quiescence_ply {
            return Err(AlphaBetaSearchError::QuiescenceDepthLimitReachedInCheck {
                quiescence_ply: context.quiescence_ply,
                maximum: context.maximum_quiescence_ply,
            });
        }
''',
        ),
        (
            '''        if quiescence_ply >= maximum_quiescence_ply {
''',
            '''        if context.quiescence_ply >= context.maximum_quiescence_ply {
''',
        ),
        (
            '''        let child_ply = ply
            .checked_add(1)
            .filter(|next| *next <= MAX_MATE_PLY)
            .ok_or(AlphaBetaSearchError::DepthTooLarge {
                depth: ply.saturating_add(1),
                maximum: MAX_MATE_PLY,
            })?;
''',
            '''        let child_ply = context
            .ply
            .checked_add(1)
            .filter(|next| *next <= MAX_MATE_PLY)
            .ok_or(AlphaBetaSearchError::DepthTooLarge {
                depth: context.ply.saturating_add(1),
                maximum: MAX_MATE_PLY,
            })?;
        let child_context = QuiescenceContext {
            ply: child_ply,
            quiescence_ply: context.quiescence_ply + 1,
            maximum_quiescence_ply: context.maximum_quiescence_ply,
        };
''',
        ),
        (
            '''        let child = search_quiescence_node(
            position,
            history,
            child_ply,
            quiescence_ply + 1,
            maximum_quiescence_ply,
            -beta,
            -alpha,
            cancellation,
        );
''',
            '''        let child = search_quiescence_node(
            position,
            history,
            child_context,
            -beta,
            -alpha,
            cancellation,
        );
''',
        ),
    ],
)

patch(
    "crates/chess-search/src/alpha_beta.rs",
    [
        (
            '''use crate::{
    cancellation::NeverCancelled, quiescence::search_quiescence_node,
    search_common::resolved_node_score, Score, SearchCancellationProbe, MAX_MATE_PLY,
    MAX_QUIESCENCE_PLY,
};
''',
            '''use crate::{
    cancellation::NeverCancelled,
    quiescence::{search_quiescence_node, QuiescenceContext},
    search_common::resolved_node_score,
    Score, SearchCancellationProbe, MAX_MATE_PLY, MAX_QUIESCENCE_PLY,
};
''',
        ),
        (
            '''        return search_quiescence_node(
            position,
            history,
            ply,
            0,
            MAX_QUIESCENCE_PLY,
            alpha,
            beta,
            cancellation,
        );
''',
            '''        let context = QuiescenceContext {
            ply,
            quiescence_ply: 0,
            maximum_quiescence_ply: MAX_QUIESCENCE_PLY,
        };
        return search_quiescence_node(position, history, context, alpha, beta, cancellation);
''',
        ),
    ],
)

print("grouped quiescence recursion state into QuiescenceContext")
