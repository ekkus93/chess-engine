use chess_core::{Move, Position, SearchHistory};

use crate::{
    alpha_beta::{AlphaBetaSearchError, AlphaBetaSearchResult}, cancellation::NeverCancelled,
    evaluate, search_common::resolved_terminal_or_draw_score, Score, SearchCancellationProbe,
    MAX_MATE_PLY,
};

/// Default maximum number of tactical plies searched beyond an alpha-beta leaf.
pub const MAX_QUIESCENCE_PLY: u16 = 64;

/// Quiescence uses the normal alpha-beta result shape.
pub type QuiescenceSearchResult = AlphaBetaSearchResult;

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
    quiescence_search_with_cancellation(
        position,
        history,
        MAX_QUIESCENCE_PLY,
        &mut cancellation,
    )
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
    let result = search_quiescence_node(
        position,
        history,
        0,
        0,
        maximum_quiescence_ply,
        alpha,
        beta,
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
    ply: u16,
    quiescence_ply: u16,
    maximum_quiescence_ply: u16,
    mut alpha: Score,
    beta: Score,
    cancellation: &mut Probe,
) -> Result<QuiescenceSearchResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    if cancellation.should_cancel() {
        return Err(AlphaBetaSearchError::Cancelled);
    }

    let tokens = position.legal_move_tokens()?;
    if let Some(score) = resolved_terminal_or_draw_score(
        position,
        history,
        tokens.is_empty(),
        ply,
    )
    .map_err(|error| AlphaBetaSearchError::DepthTooLarge {
        depth: error.ply(),
        maximum: MAX_MATE_PLY,
    })? {
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
        if quiescence_ply >= maximum_quiescence_ply {
            return Err(AlphaBetaSearchError::QuiescenceDepthLimitReachedInCheck {
                quiescence_ply,
                maximum: maximum_quiescence_ply,
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
        if quiescence_ply >= maximum_quiescence_ply {
            return Ok(AlphaBetaSearchResult {
                score: stand_pat,
                best_move: None,
                nodes: 1,
            });
        }
    }

    let mut nodes = 1_u64;
    for token in tokens.iter() {
        let current = token.move_made();
        if !in_check && !is_tactical(current) {
            continue;
        }
        if cancellation.should_cancel() {
            return Err(AlphaBetaSearchError::Cancelled);
        }

        let child_ply = ply
            .checked_add(1)
            .filter(|next| *next <= MAX_MATE_PLY)
            .ok_or(AlphaBetaSearchError::DepthTooLarge {
                depth: ply.saturating_add(1),
                maximum: MAX_MATE_PLY,
            })?;
        let position_undo = position.make_legal_token(token)?;
        let history_undo = history.push_position(position);
        let child = search_quiescence_node(
            position,
            history,
            child_ply,
            quiescence_ply + 1,
            maximum_quiescence_ply,
            -beta,
            -alpha,
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
