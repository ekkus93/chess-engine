use chess_core::{Move, Position, SearchHistory};

use crate::{
    alpha_beta::{AlphaBetaSearchError, AlphaBetaSearchResult},
    cancellation::NeverCancelled,
    evaluate,
    move_ordering::{ordered_legal_moves, MoveOrdering},
    search_common::resolved_terminal_or_draw_score,
    Score, SearchCancellationProbe, MAX_MATE_PLY,
};

/// Default maximum number of tactical plies searched beyond an alpha-beta leaf.
pub const MAX_QUIESCENCE_PLY: u16 = 64;

/// Quiescence uses the normal alpha-beta result shape.
pub type QuiescenceSearchResult = AlphaBetaSearchResult;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct QuiescenceContext {
    pub(crate) ply: u16,
    pub(crate) quiescence_ply: u16,
    pub(crate) maximum_quiescence_ply: u16,
}

/// Searches the tactical continuation of `position` with the default guard.
///
/// Stand-pat is permitted only outside check. Checked nodes search every legal
/// evasion; other nodes search captures and all promotions in deterministic
/// legal-generation order.
pub fn quiescence_search(
    position: &mut Position,
    history: &mut SearchHistory,
) -> Result<QuiescenceSearchResult, AlphaBetaSearchError> {
    let mut cancellation = NeverCancelled;
    quiescence_search_with_cancellation(position, history, MAX_QUIESCENCE_PLY, &mut cancellation)
}

/// Searches the tactical continuation with a caller-selected tactical-ply guard.
pub fn quiescence_search_with_limit(
    position: &mut Position,
    history: &mut SearchHistory,
    maximum_quiescence_ply: u16,
) -> Result<QuiescenceSearchResult, AlphaBetaSearchError> {
    let mut cancellation = NeverCancelled;
    quiescence_search_with_cancellation(
        position,
        history,
        maximum_quiescence_ply,
        &mut cancellation,
    )
}

/// Searches the tactical continuation with a guard and cancellation probe.
///
/// Cancellation is checked at node and tactical-child boundaries. Errors are
/// returned only after every active history entry is popped and every active
/// move is unmade.
pub fn quiescence_search_with_cancellation<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    maximum_quiescence_ply: u16,
    cancellation: &mut Probe,
) -> Result<QuiescenceSearchResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    let history_zobrist = history.current_zobrist();
    if history_zobrist != Some(position.zobrist()) {
        return Err(AlphaBetaSearchError::HistoryPositionMismatch {
            position_zobrist: position.zobrist(),
            history_zobrist,
        });
    }

    let initial_history_len = history.len();
    let initial_line_len = history.line_len();
    let initial_zobrist = position.zobrist();
    let alpha = Score::mated_in(0).expect("zero-ply mate score is supported");
    let beta = Score::mate_in(0).expect("zero-ply mate score is supported");
    let context = QuiescenceContext {
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
        MoveOrdering::Tactical,
        cancellation,
    );

    debug_assert_eq!(history.len(), initial_history_len);
    debug_assert_eq!(history.line_len(), initial_line_len);
    debug_assert_eq!(history.current_zobrist(), Some(initial_zobrist));
    debug_assert_eq!(position.zobrist(), initial_zobrist);
    debug_assert_eq!(position.zobrist(), position.recomputed_zobrist());

    result
}

pub(crate) fn search_quiescence_node<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    context: QuiescenceContext,
    mut alpha: Score,
    beta: Score,
    ordering: MoveOrdering,
    cancellation: &mut Probe,
) -> Result<QuiescenceSearchResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    if cancellation.on_node() {
        return Err(AlphaBetaSearchError::Cancelled);
    }

    let tokens = position.legal_move_tokens()?;
    if let Some(score) =
        resolved_terminal_or_draw_score(position, history, tokens.is_empty(), context.ply).map_err(
            |error| AlphaBetaSearchError::DepthTooLarge {
                depth: error.ply(),
                maximum: MAX_MATE_PLY,
            },
        )?
    {
        return Ok(AlphaBetaSearchResult {
            score,
            best_move: None,
            nodes: 1,
        });
    }

    let in_check = position.is_in_check(position.side_to_move());
    let mut best_score = None;
    let mut best_move = None;

    if in_check {
        if context.quiescence_ply >= context.maximum_quiescence_ply {
            return Err(AlphaBetaSearchError::QuiescenceDepthLimitReachedInCheck {
                quiescence_ply: context.quiescence_ply,
                maximum: context.maximum_quiescence_ply,
            });
        }
    } else {
        let stand_pat = evaluate(position);
        best_score = Some(stand_pat);
        if stand_pat >= beta {
            return Ok(AlphaBetaSearchResult {
                score: stand_pat,
                best_move: None,
                nodes: 1,
            });
        }
        if stand_pat > alpha {
            alpha = stand_pat;
        }
        if context.quiescence_ply >= context.maximum_quiescence_ply {
            return Ok(AlphaBetaSearchResult {
                score: stand_pat,
                best_move: None,
                nodes: 1,
            });
        }
    }

    let ordered_tokens = ordered_legal_moves(position, &tokens, ordering);
    let mut nodes = 1_u64;
    for token in ordered_tokens.iter() {
        let current = token.move_made();
        if !in_check && !is_tactical(current) {
            continue;
        }
        if cancellation.should_cancel() {
            return Err(AlphaBetaSearchError::Cancelled);
        }

        let child_ply = context
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
        let position_undo = position.make_legal_token(token)?;
        let history_undo = history.push_position(position);
        let child = search_quiescence_node(
            position,
            history,
            child_context,
            -beta,
            -alpha,
            ordering,
            cancellation,
        );
        let history_restore = history.pop_position(history_undo);
        let position_restore = position.unmake_move(position_undo);

        if let Err(error) = position_restore {
            return Err(error.into());
        }
        if let Err(error) = history_restore {
            return Err(error.into());
        }

        let child = child?;
        nodes = nodes
            .checked_add(child.nodes)
            .ok_or(AlphaBetaSearchError::NodeCountOverflow)?;
        let score = -child.score;
        let replace_best = match best_score {
            Some(previous) => score > previous,
            None => true,
        };
        if replace_best {
            best_score = Some(score);
            best_move = Some(current);
        }
        if score > alpha {
            alpha = score;
        }
        if alpha >= beta {
            break;
        }
    }

    match best_score {
        Some(score) => Ok(AlphaBetaSearchResult {
            score,
            best_move,
            nodes,
        }),
        None => Err(AlphaBetaSearchError::MissingBestMove),
    }
}

const fn is_tactical(current: Move) -> bool {
    current.kind().is_capture() || current.promotion().is_some()
}

#[cfg(test)]
mod ordering_tests {
    use chess_core::{Position, SearchHistory};

    use super::{search_quiescence_node, QuiescenceContext, MAX_QUIESCENCE_PLY};
    use crate::{cancellation::NeverCancelled, move_ordering::MoveOrdering, Score};

    fn search_with_ordering(
        root: &Position,
        ordering: MoveOrdering,
    ) -> super::QuiescenceSearchResult {
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
