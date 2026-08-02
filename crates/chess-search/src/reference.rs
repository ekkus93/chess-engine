use core::fmt;

use chess_core::{LegalMoveError, Move, Position, SearchHistory, SearchHistoryError};

use crate::{cancellation::NeverCancelled, evaluate, Score, SearchCancellationProbe, MAX_MATE_PLY};

const CLAIMABLE_REPETITION_COUNT: usize = 3;
const CLAIMABLE_HALFMOVE_COUNT: u16 = 100;

/// Result of one correctness-first, unpruned reference search.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ReferenceSearchResult {
    score: Score,
    best_move: Option<Move>,
    nodes: u64,
}

impl ReferenceSearchResult {
    /// Returns the root score from the side-to-move perspective.
    #[must_use]
    pub const fn score(self) -> Score {
        self.score
    }

    /// Returns the first deterministic best move, or `None` at leaves and terminals.
    #[must_use]
    pub const fn best_move(self) -> Option<Move> {
        self.best_move
    }

    /// Returns the number of visited nodes, including the root.
    #[must_use]
    pub const fn nodes(self) -> u64 {
        self.nodes
    }
}

/// A fail-loud reference-search error.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ReferenceSearchError {
    /// Position rule processing failed.
    Rules(LegalMoveError),
    /// Reversible search-line history processing failed.
    History(SearchHistoryError),
    /// The supplied history is not rooted at the supplied current position.
    HistoryPositionMismatch {
        /// Current position identity.
        position_zobrist: u64,
        /// Latest history identity, if present.
        history_zobrist: Option<u64>,
    },
    /// Requested depth exceeds the supported mate-distance domain.
    DepthTooLarge {
        /// Requested depth in plies.
        depth: u16,
        /// Largest supported depth in plies.
        maximum: u16,
    },
    /// Cooperative cancellation was requested.
    Cancelled,
    /// Recursive node accumulation exceeded `u64`.
    NodeCountOverflow,
    /// A non-terminal searched node unexpectedly produced no best move.
    MissingBestMove,
}

impl fmt::Display for ReferenceSearchError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Rules(error) => error.fmt(formatter),
            Self::History(error) => error.fmt(formatter),
            Self::HistoryPositionMismatch {
                position_zobrist,
                history_zobrist,
            } => write!(
                formatter,
                "search history {history_zobrist:?} does not match position {position_zobrist:#018x}"
            ),
            Self::DepthTooLarge { depth, maximum } => write!(
                formatter,
                "reference-search depth {depth} exceeds supported maximum {maximum}"
            ),
            Self::Cancelled => formatter.write_str("reference search cancelled"),
            Self::NodeCountOverflow => formatter.write_str("reference-search node count overflow"),
            Self::MissingBestMove => {
                formatter.write_str("non-terminal reference-search node has no best move")
            }
        }
    }
}

impl std::error::Error for ReferenceSearchError {}

impl From<LegalMoveError> for ReferenceSearchError {
    fn from(value: LegalMoveError) -> Self {
        Self::Rules(value)
    }
}

impl From<SearchHistoryError> for ReferenceSearchError {
    fn from(value: SearchHistoryError) -> Self {
        Self::History(value)
    }
}

/// Searches the complete legal tree to `depth` without pruning or move ordering.
///
/// This convenience entry point never requests cancellation. Use
/// [`reference_search_with_cancellation`] when an external stop probe is
/// required.
pub fn reference_search(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
) -> Result<ReferenceSearchResult, ReferenceSearchError> {
    let mut cancellation = NeverCancelled;
    reference_search_with_cancellation(position, history, depth, &mut cancellation)
}

/// Searches the complete legal tree with cooperative cancellation.
///
/// Scores use the crate's side-to-move negamax convention. Checkmate and
/// stalemate are resolved before draw rules, preserving checkmate precedence on
/// a halfmove threshold. Claimable repetition and fifty-move draws are scored as
/// zero because a searching side may claim them. Fivefold repetition and the
/// seventy-five-move rule are covered by those lower thresholds and therefore
/// receive the same score. Dead positions also score zero.
///
/// The supplied history must end at `position`. Every child is applied through
/// a source-bound legal token, pushed onto the detached line history, searched,
/// then popped and unmade before the next child. Cancellation is checked at
/// node and child boundaries. A cancellation error is returned only after every
/// active child move and line-history entry has been restored. The function
/// performs no clone-per-child operation.
pub fn reference_search_with_cancellation<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    cancellation: &mut Probe,
) -> Result<ReferenceSearchResult, ReferenceSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    if depth > MAX_MATE_PLY {
        return Err(ReferenceSearchError::DepthTooLarge {
            depth,
            maximum: MAX_MATE_PLY,
        });
    }

    let history_zobrist = history.current_zobrist();
    if history_zobrist != Some(position.zobrist()) {
        return Err(ReferenceSearchError::HistoryPositionMismatch {
            position_zobrist: position.zobrist(),
            history_zobrist,
        });
    }

    let initial_history_len = history.len();
    let initial_line_len = history.line_len();
    let initial_zobrist = position.zobrist();
    let result = search_node(position, history, depth, 0, cancellation);

    debug_assert_eq!(history.len(), initial_history_len);
    debug_assert_eq!(history.line_len(), initial_line_len);
    debug_assert_eq!(history.current_zobrist(), Some(initial_zobrist));
    debug_assert_eq!(position.zobrist(), initial_zobrist);
    debug_assert_eq!(position.zobrist(), position.recomputed_zobrist());

    result
}

fn search_node<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    ply: u16,
    cancellation: &mut Probe,
) -> Result<ReferenceSearchResult, ReferenceSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    if cancellation.should_cancel() {
        return Err(ReferenceSearchError::Cancelled);
    }

    let tokens = position.legal_move_tokens()?;

    if tokens.is_empty() {
        let score = if position.is_in_check(position.side_to_move()) {
            Score::mated_in(ply).ok_or(ReferenceSearchError::DepthTooLarge {
                depth: ply,
                maximum: MAX_MATE_PLY,
            })?
        } else {
            Score::ZERO
        };
        return Ok(ReferenceSearchResult {
            score,
            best_move: None,
            nodes: 1,
        });
    }

    if is_search_draw(position, history) {
        return Ok(ReferenceSearchResult {
            score: Score::ZERO,
            best_move: None,
            nodes: 1,
        });
    }

    if depth == 0 {
        return Ok(ReferenceSearchResult {
            score: evaluate(position),
            best_move: None,
            nodes: 1,
        });
    }

    let mut nodes = 1_u64;
    let mut best_score = None;
    let mut best_move = None;

    for token in tokens.iter() {
        if cancellation.should_cancel() {
            return Err(ReferenceSearchError::Cancelled);
        }

        let current = token.move_made();
        let position_undo = position.make_legal_token(token)?;
        let history_undo = history.push_position(position);
        let child = search_node(position, history, depth - 1, ply + 1, cancellation);
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
            .ok_or(ReferenceSearchError::NodeCountOverflow)?;
        let score = -child.score;
        let replace_best = match best_score {
            Some(previous) => score > previous,
            None => true,
        };
        if replace_best {
            best_score = Some(score);
            best_move = Some(current);
        }
    }

    match (best_score, best_move) {
        (Some(score), Some(current)) => Ok(ReferenceSearchResult {
            score,
            best_move: Some(current),
            nodes,
        }),
        _ => Err(ReferenceSearchError::MissingBestMove),
    }
}

fn is_search_draw(position: &Position, history: &SearchHistory) -> bool {
    position.is_dead_position()
        || history.repetition_count(position) >= CLAIMABLE_REPETITION_COUNT
        || position.halfmove_clock().get() >= CLAIMABLE_HALFMOVE_COUNT
}

#[cfg(test)]
mod tests {
    use chess_core::{Game, Position, SearchHistory, UciMove};

    use super::{reference_search, ReferenceSearchError};
    use crate::{evaluate, Score, MAX_MATE_PLY};

    fn position(fen: &str) -> Position {
        fen.parse().expect("test FEN is valid")
    }

    fn play(game: &mut Game, text: &str) {
        let syntax = text.parse::<UciMove>().expect("test UCI is valid");
        let current = game
            .legal_moves()
            .expect("legal generation succeeds")
            .iter()
            .find(|candidate| syntax.matches(*candidate))
            .expect("test move is legal");
        let _undo = game.make_move(current).expect("test move is playable");
    }

    fn play_knight_cycle(game: &mut Game) {
        play(game, "g1f3");
        play(game, "g8f6");
        play(game, "f3g1");
        play(game, "f6g8");
    }

    #[test]
    fn depth_zero_evaluates_and_counts_only_the_root() {
        let mut position = Position::starting();
        let snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);
        let history_snapshot = history.clone();
        let expected = evaluate(&position);

        let result = reference_search(&mut position, &mut history, 0).expect("search succeeds");

        assert_eq!(result.score(), expected);
        assert_eq!(result.best_move(), None);
        assert_eq!(result.nodes(), 1);
        assert_eq!(position, snapshot);
        assert_eq!(history, history_snapshot);
    }

    #[test]
    fn starting_depth_two_visits_the_complete_unpruned_tree() {
        let mut position = Position::starting();
        let snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);
        let history_snapshot = history.clone();

        let result = reference_search(&mut position, &mut history, 2).expect("search succeeds");

        assert_eq!(result.nodes(), 421);
        let best_move = result.best_move().expect("non-terminal root has a move");
        assert!(position
            .legal_moves()
            .expect("legal generation succeeds")
            .iter()
            .any(|current| current == best_move));
        assert_eq!(position, snapshot);
        assert_eq!(history, history_snapshot);
        assert_eq!(position.zobrist(), position.recomputed_zobrist());
    }

    #[test]
    fn checkmate_and_stalemate_are_scored_before_static_evaluation() {
        let mut mate = position("7k/6Q1/6K1/8/8/8/8/8 b - - 150 1");
        let mut mate_history = SearchHistory::from_position(&mate);
        let mate_result =
            reference_search(&mut mate, &mut mate_history, 3).expect("mate search succeeds");
        assert_eq!(
            mate_result.score(),
            Score::mated_in(0).expect("supported ply")
        );
        assert_eq!(mate_result.best_move(), None);
        assert_eq!(mate_result.nodes(), 1);

        let mut stalemate = position("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1");
        let mut stalemate_history = SearchHistory::from_position(&stalemate);
        let stalemate_result = reference_search(&mut stalemate, &mut stalemate_history, 3)
            .expect("stalemate search succeeds");
        assert_eq!(stalemate_result.score(), Score::ZERO);
        assert_eq!(stalemate_result.best_move(), None);
        assert_eq!(stalemate_result.nodes(), 1);
    }

    #[test]
    fn mate_in_one_uses_ply_relative_terminal_scoring() {
        let mut position = position("7k/5Q2/6K1/8/8/8/8/8 w - - 0 1");
        let snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);

        let result = reference_search(&mut position, &mut history, 1).expect("search succeeds");

        assert_eq!(result.score(), Score::mate_in(1).expect("supported ply"));
        assert!(result.best_move().is_some());
        assert_eq!(position, snapshot);
    }

    #[test]
    fn dead_fifty_move_and_repetition_draws_score_zero() {
        for fen in [
            "7k/8/8/8/8/8/8/K7 w - - 0 1",
            "8/8/8/8/8/8/R3K3/7k w - - 100 1",
            "8/8/8/8/8/8/R3K3/7k w - - 150 1",
        ] {
            let mut position = position(fen);
            let mut history = SearchHistory::from_position(&position);
            let result =
                reference_search(&mut position, &mut history, 2).expect("draw search succeeds");
            assert_eq!(result.score(), Score::ZERO, "draw FEN: {fen}");
            assert_eq!(result.best_move(), None, "draw FEN: {fen}");
            assert_eq!(result.nodes(), 1, "draw FEN: {fen}");
        }

        let mut game = Game::starting();
        play_knight_cycle(&mut game);
        play_knight_cycle(&mut game);
        let mut position = game.position().clone();
        let mut history = game.search_history();
        let result =
            reference_search(&mut position, &mut history, 2).expect("repetition search succeeds");
        assert_eq!(history.repetition_count(&position), 3);
        assert_eq!(result.score(), Score::ZERO);
        assert_eq!(result.best_move(), None);
        assert_eq!(result.nodes(), 1);
    }

    #[test]
    fn mismatched_history_and_excessive_depth_fail_without_mutation() {
        let mut root = Position::starting();
        let snapshot = root.clone();
        let other = position("7k/8/8/8/8/8/8/K7 w - - 0 1");
        let mut history = SearchHistory::from_position(&other);
        let history_snapshot = history.clone();

        assert!(matches!(
            reference_search(&mut root, &mut history, 1),
            Err(ReferenceSearchError::HistoryPositionMismatch { .. })
        ));
        assert_eq!(root, snapshot);
        assert_eq!(history, history_snapshot);

        let mut history = SearchHistory::from_position(&root);
        let history_snapshot = history.clone();
        assert_eq!(
            reference_search(&mut root, &mut history, MAX_MATE_PLY + 1),
            Err(ReferenceSearchError::DepthTooLarge {
                depth: MAX_MATE_PLY + 1,
                maximum: MAX_MATE_PLY,
            })
        );
        assert_eq!(root, snapshot);
        assert_eq!(history, history_snapshot);
    }
}
