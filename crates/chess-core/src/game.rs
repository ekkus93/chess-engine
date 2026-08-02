use core::fmt;

use crate::{Color, LegalMoveError, Move, MoveList, PieceKind, Position, PositionUndo};

const THREEFOLD_REPETITION_COUNT: usize = 3;
const FIVEFOLD_REPETITION_COUNT: usize = 5;
const FIFTY_MOVE_HALFMOVES: u16 = 100;
const SEVENTY_FIVE_MOVE_HALFMOVES: u16 = 150;

/// Draw conditions that the side to move may currently claim.
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct DrawClaims {
    threefold_repetition: bool,
    fifty_move_rule: bool,
}

impl DrawClaims {
    /// Returns whether the current position has occurred at least three times.
    #[must_use]
    pub const fn threefold_repetition(self) -> bool {
        self.threefold_repetition
    }

    /// Returns whether at least fifty moves per side have elapsed without a
    /// pawn move or capture.
    #[must_use]
    pub const fn fifty_move_rule(self) -> bool {
        self.fifty_move_rule
    }

    /// Returns whether at least one draw claim is currently available.
    #[must_use]
    pub const fn any(self) -> bool {
        self.threefold_repetition || self.fifty_move_rule
    }
}

/// A repetition- or move-count-based draw reason.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum DrawReason {
    /// The current position has occurred at least three times.
    ThreefoldRepetition,
    /// The current position has occurred at least five times.
    FivefoldRepetition,
    /// One hundred halfmoves elapsed without a pawn move or capture.
    FiftyMoveRule,
    /// One hundred fifty halfmoves elapsed without a pawn move or capture.
    SeventyFiveMoveRule,
    /// No legal sequence from the current material can end in checkmate.
    DeadPosition,
}

/// Current rule-level state of a game.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum GameStatus {
    /// Play may continue and no draw is currently claimable.
    Ongoing,
    /// The side to move has no legal move and is in check.
    Checkmate { winner: Color },
    /// The side to move has no legal move and is not in check.
    Stalemate,
    /// The game is drawn without requiring a player claim.
    AutomaticDraw(DrawReason),
    /// Play may continue, but the side to move may claim this draw.
    ClaimableDraw(DrawReason),
}

impl GameStatus {
    /// Returns whether this status ends the game automatically.
    #[must_use]
    pub const fn is_terminal(self) -> bool {
        matches!(
            self,
            Self::Checkmate { .. } | Self::Stalemate | Self::AutomaticDraw(_)
        )
    }
}

/// A fail-loud game-state or history operation error.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum GameError {
    /// Position rule processing failed.
    Rules(LegalMoveError),
    /// A move was requested after the game had already ended automatically.
    GameOver { status: GameStatus },
    /// An undo token did not match the current played-move and hash history.
    HistoryStateMismatch { current: Move },
}

impl fmt::Display for GameError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Rules(error) => error.fmt(formatter),
            Self::GameOver { status } => write!(formatter, "game is already over: {status:?}"),
            Self::HistoryStateMismatch { current } => write!(
                formatter,
                "game undo token for {} does not match current history",
                current.to_uci()
            ),
        }
    }
}

impl std::error::Error for GameError {}

impl From<LegalMoveError> for GameError {
    fn from(value: LegalMoveError) -> Self {
        Self::Rules(value)
    }
}

/// Opaque state required to reverse one successfully played game move.
#[derive(Debug, Eq, PartialEq)]
pub struct GameUndo {
    position_undo: PositionUndo,
    previous_move_count: usize,
    previous_hash_count: usize,
    resulting_zobrist: u64,
}

impl GameUndo {
    /// Returns the move bound to this undo token.
    #[must_use]
    pub const fn move_made(&self) -> Move {
        self.position_undo.move_made()
    }
}

/// A history-owning chess game over one current [`Position`].
///
/// The position remains history-free. This type owns played moves and every
/// position key from the root through the current position. Mutable position
/// access is deliberately not exposed because it would desynchronize history.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Game {
    position: Position,
    moves: Vec<Move>,
    position_hashes: Vec<u64>,
}

impl Game {
    /// Creates a game rooted at `position` with no known prior moves.
    #[must_use]
    pub fn new(position: Position) -> Self {
        let position_hashes = vec![position.zobrist()];
        Self {
            position,
            moves: Vec::new(),
            position_hashes,
        }
    }

    /// Creates a game in the standard starting position.
    #[must_use]
    pub fn starting() -> Self {
        Self::new(Position::starting())
    }

    /// Returns the current position without permitting history-breaking edits.
    #[must_use]
    pub const fn position(&self) -> &Position {
        &self.position
    }

    /// Returns played moves in chronological order.
    #[must_use]
    pub fn moves(&self) -> &[Move] {
        &self.moves
    }

    /// Returns position hashes from the root position through the current one.
    #[must_use]
    pub fn position_hashes(&self) -> &[u64] {
        &self.position_hashes
    }

    /// Returns the number of played halfmoves.
    #[must_use]
    pub fn ply_count(&self) -> usize {
        self.moves.len()
    }

    /// Generates all legal moves without changing game history.
    pub fn legal_moves(&mut self) -> Result<MoveList, GameError> {
        self.position.legal_moves().map_err(GameError::from)
    }

    /// Returns the number of current-position occurrences in known reversible
    /// history, including the current position.
    #[must_use]
    pub fn repetition_count(&self) -> usize {
        repetition_count(&self.position_hashes, &self.position)
    }

    /// Returns every draw claim currently available to the side to move.
    #[must_use]
    pub fn draw_claims(&self) -> DrawClaims {
        DrawClaims {
            threefold_repetition: self.repetition_count() >= THREEFOLD_REPETITION_COUNT,
            fifty_move_rule: self.position.halfmove_clock().get() >= FIFTY_MOVE_HALFMOVES,
        }
    }

    /// Returns the current rule-level game status.
    ///
    /// Checkmate and stalemate are resolved before move-count draws. This makes
    /// checkmate authoritative when the final move also reaches the automatic
    /// seventy-five-move threshold. If both claimable rules apply, threefold
    /// repetition is the reported status and [`Game::draw_claims`] exposes both.
    pub fn status(&mut self) -> Result<GameStatus, GameError> {
        let legal_moves = self.position.legal_moves()?;
        if legal_moves.is_empty() {
            let side = self.position.side_to_move();
            if self.position.is_in_check(side) {
                return Ok(GameStatus::Checkmate {
                    winner: side.opposite(),
                });
            }
            return Ok(GameStatus::Stalemate);
        }

        if self.position.is_dead_position() {
            return Ok(GameStatus::AutomaticDraw(DrawReason::DeadPosition));
        }
        if self.repetition_count() >= FIVEFOLD_REPETITION_COUNT {
            return Ok(GameStatus::AutomaticDraw(DrawReason::FivefoldRepetition));
        }
        if self.position.halfmove_clock().get() >= SEVENTY_FIVE_MOVE_HALFMOVES {
            return Ok(GameStatus::AutomaticDraw(DrawReason::SeventyFiveMoveRule));
        }

        let claims = self.draw_claims();
        if claims.threefold_repetition() {
            return Ok(GameStatus::ClaimableDraw(DrawReason::ThreefoldRepetition));
        }
        if claims.fifty_move_rule() {
            return Ok(GameStatus::ClaimableDraw(DrawReason::FiftyMoveRule));
        }
        Ok(GameStatus::Ongoing)
    }

    /// Plays one exact legal move and appends its move and repetition identity.
    ///
    /// Automatic terminal states reject further moves. Claimable draws do not
    /// stop play until an external game controller accepts a claim.
    pub fn make_move(&mut self, current: Move) -> Result<GameUndo, GameError> {
        let status = self.status()?;
        if status.is_terminal() {
            return Err(GameError::GameOver { status });
        }

        let previous_move_count = self.moves.len();
        let previous_hash_count = self.position_hashes.len();
        let position_undo = self.position.make_move(current)?;
        let resulting_zobrist = self.position.zobrist();
        self.moves.push(current);
        self.position_hashes.push(resulting_zobrist);
        debug_assert_eq!(self.position_hashes.len(), self.moves.len() + 1);
        debug_assert_eq!(self.position_hashes.last(), Some(&self.position.zobrist()));

        Ok(GameUndo {
            position_undo,
            previous_move_count,
            previous_hash_count,
            resulting_zobrist,
        })
    }

    /// Reverses one played move and restores its exact history state.
    ///
    /// Tokens must be consumed in last-in, first-out order. A mismatched token
    /// is rejected before either the position or history is changed.
    pub fn unmake_move(&mut self, undo: GameUndo) -> Result<(), GameError> {
        let current = undo.move_made();
        if self.moves.len() != undo.previous_move_count + 1
            || self.position_hashes.len() != undo.previous_hash_count + 1
            || self.moves.last().copied() != Some(current)
            || self.position_hashes.last().copied() != Some(undo.resulting_zobrist)
            || self.position.zobrist() != undo.resulting_zobrist
        {
            return Err(GameError::HistoryStateMismatch { current });
        }

        self.position.unmake_move(undo.position_undo)?;
        let removed_move = self.moves.pop();
        let removed_hash = self.position_hashes.pop();
        debug_assert_eq!(removed_move, Some(current));
        debug_assert_eq!(removed_hash, Some(undo.resulting_zobrist));
        debug_assert_eq!(self.position_hashes.len(), self.moves.len() + 1);
        debug_assert_eq!(self.position_hashes.last(), Some(&self.position.zobrist()));
        Ok(())
    }

    /// Creates a detached history stack for one search rooted at this game.
    ///
    /// Search pushes and pops line positions on the returned value. The game's
    /// move and repetition histories cannot be changed through that copy.
    #[must_use]
    pub fn search_history(&self) -> SearchHistory {
        SearchHistory {
            hashes: self.position_hashes.clone(),
            root_len: self.position_hashes.len(),
        }
    }
}

impl Default for Game {
    fn default() -> Self {
        Self::starting()
    }
}

impl From<Position> for Game {
    fn from(value: Position) -> Self {
        Self::new(value)
    }
}

/// A fail-loud search-line history restoration error.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SearchHistoryError {
    /// A pop token was not the most recently pushed search-line position.
    UndoStateMismatch,
}

impl fmt::Display for SearchHistoryError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::UndoStateMismatch => {
                formatter.write_str("search-history undo token does not match the current line")
            }
        }
    }
}

impl std::error::Error for SearchHistoryError {}

/// Opaque state required to reverse one search-history push.
#[derive(Debug, Eq, PartialEq)]
pub struct SearchHistoryUndo {
    previous_len: usize,
    pushed_zobrist: u64,
}

/// A detached root-game plus reversible search-line repetition history.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SearchHistory {
    hashes: Vec<u64>,
    root_len: usize,
}

impl SearchHistory {
    /// Creates a search history rooted at one position with no prior game data.
    #[must_use]
    pub fn from_position(position: &Position) -> Self {
        Self {
            hashes: vec![position.zobrist()],
            root_len: 1,
        }
    }

    /// Returns the root game-history length retained by this search.
    #[must_use]
    pub const fn root_len(&self) -> usize {
        self.root_len
    }

    /// Returns the number of currently pushed search-line positions.
    #[must_use]
    pub fn line_len(&self) -> usize {
        self.hashes.len() - self.root_len
    }

    /// Returns the total number of root and line position identities.
    #[must_use]
    pub fn len(&self) -> usize {
        self.hashes.len()
    }

    /// Returns whether the history contains no position identities.
    #[must_use]
    pub fn is_empty(&self) -> bool {
        self.hashes.is_empty()
    }

    /// Returns the latest recorded position identity.
    #[must_use]
    pub fn current_zobrist(&self) -> Option<u64> {
        self.hashes.last().copied()
    }

    /// Returns the current-position occurrence count within reversible history.
    #[must_use]
    pub fn repetition_count(&self, position: &Position) -> usize {
        repetition_count(&self.hashes, position)
    }

    /// Pushes one post-move search position.
    pub fn push_position(&mut self, position: &Position) -> SearchHistoryUndo {
        let undo = SearchHistoryUndo {
            previous_len: self.hashes.len(),
            pushed_zobrist: position.zobrist(),
        };
        self.hashes.push(position.zobrist());
        undo
    }

    /// Pops one search-line position using its exact LIFO token.
    pub fn pop_position(&mut self, undo: SearchHistoryUndo) -> Result<(), SearchHistoryError> {
        if self.hashes.len() != undo.previous_len + 1
            || self.hashes.len() <= self.root_len
            || self.hashes.last().copied() != Some(undo.pushed_zobrist)
        {
            return Err(SearchHistoryError::UndoStateMismatch);
        }
        let removed = self.hashes.pop();
        debug_assert_eq!(removed, Some(undo.pushed_zobrist));
        Ok(())
    }
}

impl Position {
    /// Returns whether `color`'s king is currently attacked.
    #[must_use]
    pub fn is_in_check(&self, color: Color) -> bool {
        !self.checkers_to_king(color).is_empty()
    }

    /// Conservatively recognizes positions in which checkmate is unreachable.
    ///
    /// This proves only these material classes dead:
    ///
    /// - king against king;
    /// - king and one bishop against king;
    /// - king and one knight against king;
    /// - bishops only, with every bishop confined to the same square color.
    ///
    /// Pawns, rooks, queens, any position containing a knight plus another
    /// minor piece, and bishops spanning both square colors are deliberately
    /// reported as not dead. That includes two-knight and bishop-versus-knight
    /// positions where cooperative mate remains legally reachable.
    #[must_use]
    pub fn is_dead_position(&self) -> bool {
        let pawns = self.piece_bitboard(Color::White, PieceKind::Pawn)
            | self.piece_bitboard(Color::Black, PieceKind::Pawn);
        let rooks = self.piece_bitboard(Color::White, PieceKind::Rook)
            | self.piece_bitboard(Color::Black, PieceKind::Rook);
        let queens = self.piece_bitboard(Color::White, PieceKind::Queen)
            | self.piece_bitboard(Color::Black, PieceKind::Queen);
        if !(pawns | rooks | queens).is_empty() {
            return false;
        }

        let bishops = self.piece_bitboard(Color::White, PieceKind::Bishop)
            | self.piece_bitboard(Color::Black, PieceKind::Bishop);
        let knights = self.piece_bitboard(Color::White, PieceKind::Knight)
            | self.piece_bitboard(Color::Black, PieceKind::Knight);
        if bishops.count() + knights.count() <= 1 {
            return true;
        }
        if !knights.is_empty() {
            return false;
        }

        let mut square_color = None;
        for square in bishops {
            let current = (square.row() + square.file()) & 1;
            match square_color {
                Some(expected) if expected != current => return false,
                Some(_) => {}
                None => square_color = Some(current),
            }
        }
        true
    }
}

fn repetition_count(hashes: &[u64], position: &Position) -> usize {
    if hashes.last().copied() != Some(position.zobrist()) {
        return 0;
    }
    let reversible_positions = usize::from(position.halfmove_clock().get()).saturating_add(1);
    let start = hashes.len().saturating_sub(reversible_positions);
    hashes[start..]
        .iter()
        .filter(|&&hash| hash == position.zobrist())
        .count()
}

#[cfg(test)]
mod tests {
    use crate::{Color, DrawReason, Game, GameError, GameStatus, Position, UciMove};

    fn position(fen: &str) -> Position {
        fen.parse().expect("test FEN is valid")
    }

    fn resolve(game: &mut Game, text: &str) -> crate::Move {
        let syntax = text.parse::<UciMove>().expect("test UCI syntax is valid");
        game.legal_moves()
            .expect("legal generation succeeds")
            .iter()
            .find(|candidate| syntax.matches(*candidate))
            .expect("test move is legal")
    }

    fn resolve_position(position: &mut Position, text: &str) -> crate::Move {
        let syntax = text.parse::<UciMove>().expect("test UCI syntax is valid");
        position
            .legal_moves()
            .expect("legal generation succeeds")
            .iter()
            .find(|candidate| syntax.matches(*candidate))
            .expect("test move is legal")
    }

    fn play(game: &mut Game, text: &str) -> crate::GameUndo {
        let current = resolve(game, text);
        game.make_move(current).expect("test move is playable")
    }

    fn play_knight_cycle(game: &mut Game) {
        let _white_out = play(game, "g1f3");
        let _black_out = play(game, "g8f6");
        let _white_back = play(game, "f3g1");
        let _black_back = play(game, "f6g8");
    }

    #[test]
    fn game_tracks_moves_hashes_and_exact_undo() {
        let mut game = Game::starting();
        let snapshot = game.clone();
        let current = resolve(&mut game, "e2e4");
        let undo = game.make_move(current).expect("e2e4 is playable");

        assert_eq!(game.moves(), &[current]);
        assert_eq!(game.position_hashes().len(), 2);
        assert_eq!(
            game.position_hashes().last(),
            Some(&game.position().zobrist())
        );
        assert_eq!(game.ply_count(), 1);

        game.unmake_move(undo).expect("matching undo succeeds");
        assert_eq!(game, snapshot);
    }

    #[test]
    fn game_undo_is_lifo_and_mismatch_is_non_mutating() {
        let mut game = Game::starting();
        let first = play(&mut game, "g1f3");
        let second = play(&mut game, "g8f6");
        let first_move = first.move_made();
        let snapshot = game.clone();

        assert_eq!(
            game.unmake_move(first),
            Err(GameError::HistoryStateMismatch {
                current: first_move
            })
        );
        assert_eq!(game, snapshot);
        game.unmake_move(second)
            .expect("most recent token remains valid");
    }

    #[test]
    fn mate_and_stalemate_are_distinguished() {
        let mut mate = Game::new(position("7k/6Q1/6K1/8/8/8/8/8 b - - 0 1"));
        assert_eq!(
            mate.status(),
            Ok(GameStatus::Checkmate {
                winner: Color::White
            })
        );

        let mut stalemate = Game::new(position("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"));
        assert_eq!(stalemate.status(), Ok(GameStatus::Stalemate));
    }

    #[test]
    fn repetition_transitions_from_claimable_to_automatic() {
        let mut game = Game::starting();
        play_knight_cycle(&mut game);
        assert_eq!(game.repetition_count(), 2);
        assert_eq!(game.status(), Ok(GameStatus::Ongoing));

        play_knight_cycle(&mut game);
        assert_eq!(game.repetition_count(), 3);
        assert!(game.draw_claims().threefold_repetition());
        assert_eq!(
            game.status(),
            Ok(GameStatus::ClaimableDraw(DrawReason::ThreefoldRepetition))
        );

        play_knight_cycle(&mut game);
        play_knight_cycle(&mut game);
        assert_eq!(game.repetition_count(), 5);
        assert_eq!(
            game.status(),
            Ok(GameStatus::AutomaticDraw(DrawReason::FivefoldRepetition))
        );
    }

    #[test]
    fn move_count_draws_use_exact_halfmove_thresholds() {
        let mut claimable = Game::new(position("8/8/8/8/8/8/R3K3/7k w - - 100 1"));
        assert!(claimable.draw_claims().fifty_move_rule());
        assert_eq!(
            claimable.status(),
            Ok(GameStatus::ClaimableDraw(DrawReason::FiftyMoveRule))
        );

        let mut automatic = Game::new(position("8/8/8/8/8/8/R3K3/7k w - - 150 1"));
        assert_eq!(
            automatic.status(),
            Ok(GameStatus::AutomaticDraw(DrawReason::SeventyFiveMoveRule))
        );
    }

    #[test]
    fn checkmate_precedes_the_seventy_five_move_rule() {
        let mut game = Game::new(position("7k/6Q1/6K1/8/8/8/8/8 b - - 150 1"));
        assert_eq!(
            game.status(),
            Ok(GameStatus::Checkmate {
                winner: Color::White
            })
        );
    }

    #[test]
    fn conservative_dead_position_detection_has_no_broad_minor_shortcuts() {
        for fen in [
            "7k/8/8/8/8/8/8/K7 w - - 0 1",
            "7k/8/8/8/8/8/8/KB6 w - - 0 1",
            "7k/8/8/8/8/8/8/KN6 w - - 0 1",
            "7k/8/8/6b1/8/8/8/K1B5 w - - 0 1",
        ] {
            assert!(position(fen).is_dead_position(), "expected dead: {fen}");
        }

        for fen in [
            "7k/8/8/8/6b1/8/8/K1B5 w - - 0 1",
            "7k/8/8/8/8/8/NN6/K7 w - - 0 1",
            "7k/8/8/8/8/8/BN6/K7 w - - 0 1",
            "7k/8/8/8/8/P7/8/K7 w - - 0 1",
        ] {
            assert!(!position(fen).is_dead_position(), "expected live: {fen}");
        }
    }

    #[test]
    fn automatic_dead_position_rejects_further_game_moves() {
        let mut game = Game::new(position("7k/8/8/8/8/8/8/K7 w - - 0 1"));
        assert_eq!(
            game.status(),
            Ok(GameStatus::AutomaticDraw(DrawReason::DeadPosition))
        );
        let current = resolve(&mut game, "a1a2");
        assert_eq!(
            game.make_move(current),
            Err(GameError::GameOver {
                status: GameStatus::AutomaticDraw(DrawReason::DeadPosition)
            })
        );
    }

    #[test]
    fn illegal_game_move_does_not_change_position_or_history() {
        let mut game = Game::starting();
        let snapshot = game.clone();
        let illegal = crate::Move::new(
            "e2".parse().expect("test square is valid"),
            "e5".parse().expect("test square is valid"),
            crate::MoveKind::Quiet,
        );

        assert!(matches!(game.make_move(illegal), Err(GameError::Rules(_))));
        assert_eq!(game, snapshot);
    }

    #[test]
    fn repetition_count_respects_the_irreversible_halfmove_boundary() {
        let current = position("8/8/8/8/8/8/R3K3/7k w - - 2 1");
        let hash = current.zobrist();
        let history = crate::SearchHistory {
            hashes: vec![hash, hash, hash ^ 1, hash],
            root_len: 4,
        };

        assert_eq!(history.repetition_count(&current), 2);
    }

    #[test]
    fn search_history_is_detached_and_reversible() {
        let mut game = Game::starting();
        play_knight_cycle(&mut game);
        let game_snapshot = game.clone();
        let mut search_position = game.position().clone();
        let mut history = game.search_history();

        assert_eq!(history.root_len(), game.position_hashes().len());
        assert_eq!(history.line_len(), 0);
        assert_eq!(history.repetition_count(&search_position), 2);

        let current = resolve_position(&mut search_position, "g1f3");
        let position_undo = search_position
            .make_move(current)
            .expect("search move is legal");
        let history_undo = history.push_position(&search_position);
        assert_eq!(history.line_len(), 1);
        assert_eq!(history.repetition_count(&search_position), 2);

        history
            .pop_position(history_undo)
            .expect("matching history pop succeeds");
        search_position
            .unmake_move(position_undo)
            .expect("matching position undo succeeds");
        assert_eq!(game, game_snapshot);
        assert_eq!(history.current_zobrist(), Some(game.position().zobrist()));
    }

    #[test]
    fn search_history_mismatched_pop_is_non_mutating() {
        let game = Game::starting();
        let mut search_position = game.position().clone();
        let mut history = game.search_history();

        let first_move = resolve_position(&mut search_position, "g1f3");
        let _first_position_undo = search_position
            .make_move(first_move)
            .expect("first search move is legal");
        let first_history_undo = history.push_position(&search_position);

        let second_move = resolve_position(&mut search_position, "g8f6");
        let _second_position_undo = search_position
            .make_move(second_move)
            .expect("second search move is legal");
        let _second_history_undo = history.push_position(&search_position);
        let snapshot = history.clone();

        assert_eq!(
            history.pop_position(first_history_undo),
            Err(crate::SearchHistoryError::UndoStateMismatch)
        );
        assert_eq!(history, snapshot);
    }
}
