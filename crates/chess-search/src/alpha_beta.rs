use core::fmt;

use chess_core::{LegalMoveError, Move, Position, SearchHistory, SearchHistoryError};

use crate::{search_common::resolved_node_score, Score, MAX_MATE_PLY};

/// Result of one full-window negamax alpha-beta search.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct AlphaBetaSearchResult {
    score: Score,
    best_move: Option<Move>,
    nodes: u64,
}

impl AlphaBetaSearchResult {
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

/// A fail-loud alpha-beta search error.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum AlphaBetaSearchError {
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
    /// Recursive node accumulation exceeded `u64`.
    NodeCountOverflow,
    /// A non-terminal searched node unexpectedly produced no best move.
    MissingBestMove,
}

impl fmt::Display for AlphaBetaSearchError {
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
                "alpha-beta depth {depth} exceeds supported maximum {maximum}"
            ),
            Self::NodeCountOverflow => formatter.write_str("alpha-beta node count overflow"),
            Self::MissingBestMove => {
                formatter.write_str("non-terminal alpha-beta node has no best move")
            }
        }
    }
}

impl std::error::Error for AlphaBetaSearchError {}

impl From<LegalMoveError> for AlphaBetaSearchError {
    fn from(value: LegalMoveError) -> Self {
        Self::Rules(value)
    }
}

impl From<SearchHistoryError> for AlphaBetaSearchError {
    fn from(value: SearchHistoryError) -> Self {
        Self::History(value)
    }
}

/// Searches to `depth` with recursive fail-soft negamax alpha-beta pruning.
///
/// The search uses the same side-to-move score, mate-distance, terminal, draw,
/// and repetition semantics as [`crate::reference_search`]. Legal moves retain
/// their deterministic generation order, and equal scores keep the first move.
/// The root uses the complete supported score window, so its returned score is
/// exact rather than a bound.
///
/// The supplied history must end at `position`. Every child is applied through
/// a source-bound legal token, pushed onto the detached line history, searched,
/// then popped and unmade before the next child. The function performs no
/// clone-per-child operation.
pub fn alpha_beta_search(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError> {
    if depth > MAX_MATE_PLY {
        return Err(AlphaBetaSearchError::DepthTooLarge {
            depth,
            maximum: MAX_MATE_PLY,
        });
    }

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
    let result = search_node(position, history, depth, 0, alpha, beta);

    debug_assert_eq!(history.len(), initial_history_len);
    debug_assert_eq!(history.line_len(), initial_line_len);
    debug_assert_eq!(history.current_zobrist(), Some(initial_zobrist));
    debug_assert_eq!(position.zobrist(), initial_zobrist);
    debug_assert_eq!(position.zobrist(), position.recomputed_zobrist());

    result
}

fn search_node(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    ply: u16,
    mut alpha: Score,
    beta: Score,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError> {
    let tokens = position.legal_move_tokens()?;
    if let Some(score) = resolved_node_score(position, history, tokens.is_empty(), depth, ply)
        .map_err(|error| AlphaBetaSearchError::DepthTooLarge {
            depth: error.ply(),
            maximum: MAX_MATE_PLY,
        })?
    {
        return Ok(AlphaBetaSearchResult {
            score,
            best_move: None,
            nodes: 1,
        });
    }

    let mut nodes = 1_u64;
    let mut best_score = None;
    let mut best_move = None;

    for token in tokens.iter() {
        let current = token.move_made();
        let position_undo = position.make_legal_token(token)?;
        let history_undo = history.push_position(position);
        let child = search_node(position, history, depth - 1, ply + 1, -beta, -alpha);
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

    match (best_score, best_move) {
        (Some(score), Some(current)) => Ok(AlphaBetaSearchResult {
            score,
            best_move: Some(current),
            nodes,
        }),
        _ => Err(AlphaBetaSearchError::MissingBestMove),
    }
}

#[cfg(test)]
mod tests {
    use chess_core::{Game, Position, SearchHistory, UciMove};

    use super::{alpha_beta_search, AlphaBetaSearchError};
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

        let result =
            alpha_beta_search(&mut position, &mut history, 0).expect("search succeeds");

        assert_eq!(result.score(), expected);
        assert_eq!(result.best_move(), None);
        assert_eq!(result.nodes(), 1);
        assert_eq!(position, snapshot);
        assert_eq!(history, history_snapshot);
    }

    #[test]
    fn starting_depth_three_prunes_and_restores_exactly() {
        const COMPLETE_DEPTH_THREE_TREE: u64 = 1 + 20 + 400 + 8_902;

        let mut position = Position::starting();
        let snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);
        let history_snapshot = history.clone();

        let result =
            alpha_beta_search(&mut position, &mut history, 3).expect("search succeeds");

        assert!(result.nodes() < COMPLETE_DEPTH_THREE_TREE);
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
    fn equal_scores_keep_deterministic_first_best_move() {
        let mut first_position = Position::starting();
        let mut first_history = SearchHistory::from_position(&first_position);
        let first = alpha_beta_search(&mut first_position, &mut first_history, 2)
            .expect("first search succeeds");

        let mut second_position = Position::starting();
        let mut second_history = SearchHistory::from_position(&second_position);
        let second = alpha_beta_search(&mut second_position, &mut second_history, 2)
            .expect("second search succeeds");

        assert_eq!(first.score(), second.score());
        assert_eq!(first.best_move(), second.best_move());
        assert_eq!(first.nodes(), second.nodes());
    }

    #[test]
    fn mate_in_one_uses_ply_relative_terminal_scoring() {
        let mut position = position("7k/5Q2/6K1/8/8/8/8/8 w - - 0 1");
        let snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);

        let result =
            alpha_beta_search(&mut position, &mut history, 1).expect("search succeeds");

        assert_eq!(result.score(), Score::mate_in(1).expect("supported ply"));
        let best_move = result.best_move().expect("mate has a root move");
        assert!(position
            .legal_moves()
            .expect("legal generation succeeds")
            .iter()
            .any(|current| current == best_move));
        assert_eq!(position, snapshot);
    }

    #[test]
    fn terminal_and_repetition_draw_roots_resolve_without_a_move() {
        let mut mate = position("7k/6Q1/6K1/8/8/8/8/8 b - - 150 1");
        let mut mate_history = SearchHistory::from_position(&mate);
        let mate_result =
            alpha_beta_search(&mut mate, &mut mate_history, 3).expect("mate search succeeds");
        assert_eq!(
            mate_result.score(),
            Score::mated_in(0).expect("supported ply")
        );
        assert_eq!(mate_result.best_move(), None);
        assert_eq!(mate_result.nodes(), 1);

        let mut game = Game::starting();
        play_knight_cycle(&mut game);
        play_knight_cycle(&mut game);
        let mut repeated = game.position().clone();
        let repeated_snapshot = repeated.clone();
        let mut history = game.search_history();
        let history_snapshot = history.clone();
        let draw = alpha_beta_search(&mut repeated, &mut history, 3)
            .expect("repetition search succeeds");
        assert_eq!(history.repetition_count(&repeated), 3);
        assert_eq!(draw.score(), Score::ZERO);
        assert_eq!(draw.best_move(), None);
        assert_eq!(draw.nodes(), 1);
        assert_eq!(repeated, repeated_snapshot);
        assert_eq!(history, history_snapshot);
    }

    #[test]
    fn mismatched_history_and_excessive_depth_fail_without_mutation() {
        let mut root = Position::starting();
        let snapshot = root.clone();
        let other = position("7k/8/8/8/8/8/8/K7 w - - 0 1");
        let mut history = SearchHistory::from_position(&other);
        let history_snapshot = history.clone();

        assert!(matches!(
            alpha_beta_search(&mut root, &mut history, 1),
            Err(AlphaBetaSearchError::HistoryPositionMismatch { .. })
        ));
        assert_eq!(root, snapshot);
        assert_eq!(history, history_snapshot);

        let mut history = SearchHistory::from_position(&root);
        let history_snapshot = history.clone();
        assert_eq!(
            alpha_beta_search(&mut root, &mut history, MAX_MATE_PLY + 1),
            Err(AlphaBetaSearchError::DepthTooLarge {
                depth: MAX_MATE_PLY + 1,
                maximum: MAX_MATE_PLY,
            })
        );
        assert_eq!(root, snapshot);
        assert_eq!(history, history_snapshot);
    }
}
