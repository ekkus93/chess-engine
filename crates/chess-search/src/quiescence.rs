use chess_core::{
    static_exchange_evaluation, Move, MoveKind, PieceKind, Position, SearchHistory,
    StaticExchangeClass, StaticExchangeValue,
};

use crate::{
    alpha_beta::{AlphaBetaSearchError, AlphaBetaSearchResult},
    cancellation::NeverCancelled,
    evaluate_with_weights,
    move_ordering::{ordered_legal_moves_with_see, MoveOrdering},
    search_common::resolved_terminal_or_draw_score,
    EvaluationWeights, Score, SearchCancellationProbe, SearchDiagnosticEvent, SearchDiagnostics,
    MAX_MATE_PLY,
};

/// Default maximum number of tactical plies searched beyond an alpha-beta leaf.
pub const MAX_QUIESCENCE_PLY: u16 = 64;

/// Quiescence uses the normal alpha-beta result shape.
pub type QuiescenceSearchResult = AlphaBetaSearchResult;

/// S2-6 SEE pruning removes only captures below this strict threshold.
pub const SEE_QUIESCENCE_PRUNE_THRESHOLD_CENTIPAWNS: i32 = -100;
/// S2-6 delta-pruning margin used by the separately identified candidate.
pub const DELTA_PRUNING_MARGIN_CENTIPAWNS: i32 = 200;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct QuiescenceContext {
    pub(crate) ply: u16,
    pub(crate) quiescence_ply: u16,
    pub(crate) maximum_quiescence_ply: u16,
}

#[derive(Clone, Copy)]
pub(crate) struct QuiescenceSearchPolicy<'a> {
    alpha: Score,
    beta: Score,
    ordering: MoveOrdering,
    see_capture_ordering: bool,
    see_quiescence_pruning: bool,
    delta_pruning: bool,
    weights: &'a EvaluationWeights,
}

impl<'a> QuiescenceSearchPolicy<'a> {
    pub(crate) const fn new(
        alpha: Score,
        beta: Score,
        ordering: MoveOrdering,
        see_capture_ordering: bool,
        see_quiescence_pruning: bool,
        delta_pruning: bool,
        weights: &'a EvaluationWeights,
    ) -> Self {
        Self {
            alpha,
            beta,
            ordering,
            see_capture_ordering,
            see_quiescence_pruning,
            delta_pruning,
            weights,
        }
    }
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
    alpha: Score,
    beta: Score,
    ordering: MoveOrdering,
    cancellation: &mut Probe,
) -> Result<QuiescenceSearchResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    search_quiescence_node_with_weights(
        position,
        history,
        context,
        QuiescenceSearchPolicy::new(
            alpha,
            beta,
            ordering,
            false,
            false,
            false,
            &EvaluationWeights::DEFAULT,
        ),
        cancellation,
    )
}

pub(crate) fn search_quiescence_node_with_weights<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    context: QuiescenceContext,
    policy: QuiescenceSearchPolicy<'_>,
    cancellation: &mut Probe,
) -> Result<QuiescenceSearchResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    let QuiescenceSearchPolicy {
        mut alpha,
        beta,
        ordering,
        see_capture_ordering,
        see_quiescence_pruning,
        delta_pruning,
        weights,
    } = policy;
    if cancellation.on_quiescence_node(context.ply) {
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
            qnodes: 1,
            selective_depth: context.ply,
            diagnostics: SearchDiagnostics::quiescence_node(),
        });
    }

    let in_check = position.is_in_check(position.side_to_move());
    let mut best_score = None;
    let mut best_move = None;
    let mut stand_pat = None;

    if in_check {
        if context.quiescence_ply >= context.maximum_quiescence_ply {
            return Err(AlphaBetaSearchError::QuiescenceDepthLimitReachedInCheck {
                quiescence_ply: context.quiescence_ply,
                maximum: context.maximum_quiescence_ply,
            });
        }
    } else {
        let evaluated = evaluate_with_weights(position, weights);
        stand_pat = Some(evaluated);
        best_score = Some(evaluated);
        if evaluated >= beta {
            let event = SearchDiagnosticEvent::QuiescenceStandPatCutoff;
            let mut diagnostics = SearchDiagnostics::quiescence_node();
            diagnostics.record_checked(event)?;
            cancellation.on_search_diagnostic(event);
            return Ok(AlphaBetaSearchResult {
                score: evaluated,
                best_move: None,
                nodes: 1,
                qnodes: 1,
                selective_depth: context.ply,
                diagnostics,
            });
        }
        if evaluated > alpha {
            alpha = evaluated;
        }
        if context.quiescence_ply >= context.maximum_quiescence_ply {
            return Ok(AlphaBetaSearchResult {
                score: evaluated,
                best_move: None,
                nodes: 1,
                qnodes: 1,
                selective_depth: context.ply,
                diagnostics: SearchDiagnostics::quiescence_node(),
            });
        }
    }

    let ordered_tokens =
        ordered_legal_moves_with_see(position, &tokens, ordering, see_capture_ordering)?;
    let mut nodes = 1_u64;
    let mut qnodes = 1_u64;
    let mut selective_depth = context.ply;
    let mut diagnostics = SearchDiagnostics::quiescence_node();
    ordered_tokens
        .diagnostics()
        .record_into(&mut diagnostics, cancellation)?;
    let tactical_move_count = if in_check {
        0
    } else {
        tokens
            .iter()
            .filter(|token| is_tactical(token.move_made()))
            .count()
    };
    let mate_sensitive = mate_sensitive_window(alpha, beta);
    let mut searched_moves = 0_usize;
    for token in ordered_tokens.iter() {
        let current = token.move_made();
        if !in_check && !is_tactical(current) {
            continue;
        }
        if cancellation.should_cancel() {
            return Err(AlphaBetaSearchError::Cancelled);
        }

        let see_value = if see_pruning_preconditions(
            current,
            in_check,
            tactical_move_count,
            mate_sensitive,
            see_quiescence_pruning,
        ) {
            let value = static_exchange_evaluation(position, current)?;
            record_see_value(value, &mut diagnostics, cancellation)?;
            Some(value)
        } else {
            None
        };
        let delta_gain = delta_pruning_preconditions(
            current,
            in_check,
            tactical_move_count,
            mate_sensitive,
            delta_pruning,
        )
        .then(|| maximum_material_gain(position, current))
        .transpose()?;

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
        let gives_check = position.is_in_check(position.side_to_move());
        if !gives_check
            && see_value
                .is_some_and(|value| value.centipawns() < SEE_QUIESCENCE_PRUNE_THRESHOLD_CENTIPAWNS)
        {
            position.unmake_move(position_undo)?;
            record_prune(
                SearchDiagnosticEvent::QuiescenceSeePrune,
                &mut diagnostics,
                cancellation,
            )?;
            continue;
        }
        if !gives_check {
            if let (Some(evaluated), Some(gain)) = (stand_pat, delta_gain) {
                let attempt = SearchDiagnosticEvent::QuiescenceDeltaAttempt;
                diagnostics.record_checked(attempt)?;
                cancellation.on_search_diagnostic(attempt);
                if delta_bound_cannot_raise_alpha(evaluated, gain, alpha) {
                    position.unmake_move(position_undo)?;
                    record_prune(
                        SearchDiagnosticEvent::QuiescenceDeltaPrune,
                        &mut diagnostics,
                        cancellation,
                    )?;
                    continue;
                }
            }
        }
        let history_undo = history.push_position(position);
        let child = search_quiescence_node_with_weights(
            position,
            history,
            child_context,
            QuiescenceSearchPolicy::new(
                -beta,
                -alpha,
                ordering,
                see_capture_ordering,
                see_quiescence_pruning,
                delta_pruning,
                weights,
            ),
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
        qnodes = qnodes
            .checked_add(child.qnodes)
            .ok_or(AlphaBetaSearchError::NodeCountOverflow)?;
        selective_depth = selective_depth.max(child.selective_depth);
        diagnostics = diagnostics.checked_add(child.diagnostics)?;
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
            let event = SearchDiagnosticEvent::QuiescenceBetaCutoff {
                first_move: searched_moves == 0,
            };
            diagnostics.record_checked(event)?;
            cancellation.on_search_diagnostic(event);
            break;
        }
        searched_moves = searched_moves.saturating_add(1);
    }

    match best_score {
        Some(score) => Ok(AlphaBetaSearchResult {
            score,
            best_move,
            nodes,
            qnodes,
            selective_depth,
            diagnostics,
        }),
        None => Err(AlphaBetaSearchError::MissingBestMove),
    }
}

fn record_see_value<Probe>(
    value: StaticExchangeValue,
    diagnostics: &mut SearchDiagnostics,
    cancellation: &mut Probe,
) -> Result<(), AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    for event in [
        SearchDiagnosticEvent::SeeCall,
        match value.class() {
            StaticExchangeClass::Winning => SearchDiagnosticEvent::SeeWinningCapture,
            StaticExchangeClass::Equal => SearchDiagnosticEvent::SeeEqualCapture,
            StaticExchangeClass::Losing => SearchDiagnosticEvent::SeeLosingCapture,
        },
    ] {
        diagnostics.record_checked(event)?;
        cancellation.on_search_diagnostic(event);
    }
    Ok(())
}

fn record_prune<Probe>(
    event: SearchDiagnosticEvent,
    diagnostics: &mut SearchDiagnostics,
    cancellation: &mut Probe,
) -> Result<(), AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    diagnostics.record_checked(event)?;
    cancellation.on_search_diagnostic(event);
    Ok(())
}

fn see_pruning_preconditions(
    current: Move,
    in_check: bool,
    tactical_move_count: usize,
    mate_sensitive: bool,
    enabled: bool,
) -> bool {
    enabled
        && !in_check
        && tactical_move_count > 1
        && !mate_sensitive
        && current.kind().is_capture()
        && current.kind() != MoveKind::EnPassant
        && current.promotion().is_none()
}

fn delta_pruning_preconditions(
    current: Move,
    in_check: bool,
    tactical_move_count: usize,
    mate_sensitive: bool,
    enabled: bool,
) -> bool {
    enabled
        && !in_check
        && tactical_move_count > 1
        && !mate_sensitive
        && current.kind().is_capture()
        && current.kind() != MoveKind::EnPassant
        && current.promotion().is_none()
}

fn mate_sensitive_window(alpha: Score, beta: Score) -> bool {
    let full_alpha = Score::mated_in(0).expect("zero-ply mate score exists");
    let full_beta = Score::mate_in(0).expect("zero-ply mate score exists");
    (alpha.is_mate() && alpha != full_alpha) || (beta.is_mate() && beta != full_beta)
}

fn maximum_material_gain(position: &Position, current: Move) -> Result<i32, AlphaBetaSearchError> {
    let captured = position.piece_at(current.destination()).ok_or_else(|| {
        chess_core::StaticExchangeError::MoveStateContradiction(
            chess_core::StaticExchangeMoveStateError::InvalidTargetState {
                destination: current.destination(),
            },
        )
    })?;
    Ok(delta_piece_value(captured.kind))
}

const fn delta_piece_value(kind: PieceKind) -> i32 {
    match kind {
        PieceKind::Pawn => 100,
        PieceKind::Knight => 320,
        PieceKind::Bishop => 330,
        PieceKind::Rook => 500,
        PieceKind::Queen => 900,
        PieceKind::King => 20_000,
    }
}

fn delta_bound_cannot_raise_alpha(stand_pat: Score, gain: i32, alpha: Score) -> bool {
    i64::from(stand_pat.centipawns()) + i64::from(gain) + i64::from(DELTA_PRUNING_MARGIN_CENTIPAWNS)
        <= i64::from(alpha.centipawns())
}

const fn is_tactical(current: Move) -> bool {
    current.kind().is_capture() || current.promotion().is_some()
}

#[cfg(test)]
mod s2_6_tests {
    use chess_core::{Position, SearchHistory};

    use super::{
        search_quiescence_node_with_weights, QuiescenceContext, QuiescenceSearchPolicy,
        MAX_QUIESCENCE_PLY,
    };
    use crate::{
        cancellation::NeverCancelled, move_ordering::MoveOrdering, AlphaBetaSearchError,
        EvaluationWeights, Score,
    };

    fn run(
        root: &Position,
        see_pruning: bool,
        delta_pruning: bool,
    ) -> super::QuiescenceSearchResult {
        let mut position = root.clone();
        let snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);
        let history_snapshot = history.clone();
        let mut cancellation = NeverCancelled;
        let result = search_quiescence_node_with_weights(
            &mut position,
            &mut history,
            QuiescenceContext {
                ply: 0,
                quiescence_ply: 0,
                maximum_quiescence_ply: MAX_QUIESCENCE_PLY,
            },
            QuiescenceSearchPolicy::new(
                Score::mated_in(0).expect("full alpha"),
                Score::mate_in(0).expect("full beta"),
                MoveOrdering::Tactical,
                false,
                see_pruning,
                delta_pruning,
                &EvaluationWeights::DEFAULT,
            ),
            &mut cancellation,
        )
        .expect("controlled quiescence search succeeds");
        assert_eq!(position, snapshot);
        assert_eq!(history, history_snapshot);
        assert_eq!(position.zobrist(), position.recomputed_zobrist());
        result
    }

    #[test]
    fn see_pruning_removes_a_losing_nonchecking_capture_without_changing_score() {
        let root: Position = "3r3k/8/8/3p3p/8/8/8/K2Q4 w - - 0 1"
            .parse()
            .expect("SEE-pruning fixture parses");
        let baseline = run(&root, false, false);
        let candidate = run(&root, true, false);
        assert_eq!(candidate.score(), baseline.score());
        assert!(candidate.qnodes() < baseline.qnodes());
        assert!(candidate.diagnostics().quiescence_see_prunes() > 0);
        assert_eq!(candidate.diagnostics().quiescence_delta_attempts(), 0);
        assert_eq!(candidate.diagnostics().quiescence_delta_prunes(), 0);
    }

    #[test]
    fn see_pruning_exclusions_preserve_sensitive_tactical_moves() {
        for (label, fen) in [
            ("in-check-evasion", "4r2k/8/8/8/8/8/8/4K3 w - - 0 1"),
            ("promotion", "7k/P7/8/8/8/8/8/K7 w - - 0 1"),
            ("en-passant", "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1"),
            (
                "single-tactical-response",
                "3r3k/8/8/3p4/8/8/8/K2Q4 w - - 0 1",
            ),
            ("checking-capture", "3r3k/8/8/8/8/8/8/K2Q4 w - - 0 1"),
        ] {
            let root: Position = fen
                .parse()
                .unwrap_or_else(|error| panic!("{label}: {error}"));
            let baseline = run(&root, false, false);
            let candidate = run(&root, true, false);
            assert_eq!(candidate.score(), baseline.score(), "{label}");
            assert_eq!(
                candidate.diagnostics().quiescence_see_prunes(),
                0,
                "{label}"
            );
        }
    }

    #[test]
    fn delta_pruning_is_exercised_only_after_see_under_a_narrow_window() {
        let mut position: Position = "4k3/8/8/3p4/3Q3p/8/8/4K3 w - - 0 1"
            .parse()
            .expect("delta-pruning fixture parses");
        let snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);
        let history_snapshot = history.clone();
        let mut cancellation = NeverCancelled;
        let result = search_quiescence_node_with_weights(
            &mut position,
            &mut history,
            QuiescenceContext {
                ply: 0,
                quiescence_ply: 0,
                maximum_quiescence_ply: MAX_QUIESCENCE_PLY,
            },
            QuiescenceSearchPolicy::new(
                Score::from_evaluation(2_000),
                Score::from_evaluation(2_100),
                MoveOrdering::Tactical,
                false,
                true,
                true,
                &EvaluationWeights::DEFAULT,
            ),
            &mut cancellation,
        )
        .expect("narrow-window delta search succeeds");
        assert!(result.score() <= Score::from_evaluation(2_000));
        assert!(result.diagnostics().quiescence_delta_attempts() > 0);
        assert!(result.diagnostics().quiescence_delta_prunes() > 0);
        assert_eq!(position, snapshot);
        assert_eq!(history, history_snapshot);
        assert_eq!(position.zobrist(), position.recomputed_zobrist());
    }

    #[test]
    fn guard_exhaustion_in_check_remains_fail_loud_with_pruning_enabled() {
        let mut position: Position = "4r2k/8/8/8/8/8/8/4K3 w - - 0 1"
            .parse()
            .expect("checked fixture parses");
        let snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);
        let history_snapshot = history.clone();
        let mut cancellation = NeverCancelled;
        let result = search_quiescence_node_with_weights(
            &mut position,
            &mut history,
            QuiescenceContext {
                ply: 0,
                quiescence_ply: 0,
                maximum_quiescence_ply: 0,
            },
            QuiescenceSearchPolicy::new(
                Score::mated_in(0).expect("full alpha"),
                Score::mate_in(0).expect("full beta"),
                MoveOrdering::Tactical,
                false,
                true,
                false,
                &EvaluationWeights::DEFAULT,
            ),
            &mut cancellation,
        );
        assert_eq!(
            result,
            Err(AlphaBetaSearchError::QuiescenceDepthLimitReachedInCheck {
                quiescence_ply: 0,
                maximum: 0,
            })
        );
        assert_eq!(position, snapshot);
        assert_eq!(history, history_snapshot);
    }
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
