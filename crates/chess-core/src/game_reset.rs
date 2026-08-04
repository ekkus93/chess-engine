use crate::{Game, Position};

impl Game {
    /// Replaces this game with the standard starting position and fresh history.
    pub fn reset_to_starting(&mut self) {
        *self = Self::starting();
    }

    /// Replaces this game root and discards all prior move and repetition history.
    ///
    /// `Position` is already validated, so replacement is infallible. The new
    /// hash history contains exactly the supplied root position.
    pub fn set_position(&mut self, position: Position) {
        *self = Self::new(position);
    }
}

#[cfg(test)]
mod tests {
    use crate::{Color, Game, GameError, GameStatus, Position, UciMove};

    fn play(game: &mut Game, text: &str) -> crate::GameUndo {
        let syntax = text.parse::<UciMove>().expect("test UCI syntax is valid");
        let current = game
            .legal_moves()
            .expect("legal generation succeeds")
            .iter()
            .find(|candidate| syntax.matches(*candidate))
            .expect("test move is legal");
        game.make_move(current).expect("test move is playable")
    }

    #[test]
    fn reset_to_starting_discards_position_and_history() {
        let mut game = Game::starting();
        let stale = play(&mut game, "e2e4");
        let _reply = play(&mut game, "e7e5");

        game.reset_to_starting();

        assert_eq!(game, Game::starting());
        assert_eq!(game.ply_count(), 0);
        assert_eq!(game.position_hashes(), &[Position::starting().zobrist()]);
        assert!(matches!(
            game.unmake_move(stale),
            Err(GameError::HistoryStateMismatch { .. })
        ));
    }

    #[test]
    fn set_position_establishes_one_new_root() {
        let mut game = Game::starting();
        let stale = play(&mut game, "g1f3");
        let mate = Position::from_fen("7k/6Q1/6K1/8/8/8/8/8 b - - 0 1").expect("mate FEN is valid");
        let expected_hash = mate.zobrist();

        game.set_position(mate);

        assert_eq!(game.ply_count(), 0);
        assert!(game.moves().is_empty());
        assert_eq!(game.position_hashes(), &[expected_hash]);
        assert_eq!(
            game.status(),
            Ok(GameStatus::Checkmate {
                winner: Color::White
            })
        );
        let history = game.search_history();
        assert_eq!(history.root_len(), 1);
        assert_eq!(history.line_len(), 0);
        assert_eq!(history.current_zobrist(), Some(expected_hash));
        assert!(matches!(
            game.unmake_move(stale),
            Err(GameError::HistoryStateMismatch { .. })
        ));
    }
}
