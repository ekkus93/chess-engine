use chess_core::{Color, DrawReason, Game, Position, UciMove};

use super::serialize_game;
use crate::app::{AppState, GameConfig, GameOutcome};

fn apply_uci(game: &mut Game, uci: &str) {
    let syntax = uci.parse::<UciMove>().expect("fixture syntax");
    let current = game
        .legal_moves()
        .expect("legal moves")
        .iter()
        .find(|candidate| syntax.matches(*candidate))
        .expect("fixture move legal");
    game.make_move(current).expect("fixture move applies");
}

#[test]
fn human_black_serialization_without_timestamp_has_zero_moves() {
    let mut app = AppState::new();
    app.start_game(GameConfig::HumanVsEngine {
        human_color: Color::Black,
        engine_depth: 5,
    })
    .expect("game starts");
    let text = serialize_game(app.session.as_ref().expect("session"), None);
    assert_eq!(
        text,
        "Chess Engine Rust TUI save v1\nmode: human-vs-engine\nhuman-color: Black\nengine-depth: 5\nmoves: \nresult: ongoing\n"
    );
    assert!(!text.contains("date:"));
    assert!(!text.contains("PGN"));
}

#[test]
fn self_play_serialization_preserves_distinct_depths() {
    let mut app = AppState::new();
    app.start_game(GameConfig::SelfPlay {
        white_depth: 2,
        black_depth: 7,
    })
    .expect("self-play starts");
    let text = serialize_game(app.session.as_ref().expect("session"), Some("fixed-time"));
    assert!(text.contains("date: fixed-time"));
    assert!(text.contains("mode: self-play"));
    assert!(text.contains("white-depth: 2"));
    assert!(text.contains("black-depth: 7"));
}

#[test]
fn serialization_preserves_multiple_moves_in_exact_order() {
    let mut app = AppState::new();
    app.start_game(GameConfig::HumanVsEngine {
        human_color: Color::White,
        engine_depth: 3,
    })
    .expect("game starts");
    let game = &mut app.session.as_mut().expect("session").game;
    for uci in ["e2e4", "e7e5", "g1f3", "b8c6"] {
        apply_uci(game, uci);
    }
    let text = serialize_game(app.session.as_ref().expect("session"), None);
    assert!(text.contains("moves: e2e4 e7e5 g1f3 b8c6\n"));
}

#[test]
fn serialization_preserves_explicit_promotion_identity() {
    let mut app = AppState::new();
    app.start_game(GameConfig::HumanVsEngine {
        human_color: Color::White,
        engine_depth: 1,
    })
    .expect("game starts");
    app.session.as_mut().expect("session").game =
        Game::new(Position::from_fen("7k/4P3/8/8/8/8/8/7K w - - 0 1").expect("promotion fixture"));
    app.submit_human_move("e7e8q").expect("promotion applies");
    let text = serialize_game(app.session.as_ref().expect("session"), None);
    assert!(text.contains("moves: e7e8q\n"));
}

#[test]
fn serialization_covers_every_result_disposition() {
    let cases = [
        (
            GameOutcome::Checkmate {
                winner: Color::White,
            },
            "result: Checkmate — White wins",
        ),
        (GameOutcome::Stalemate, "result: Draw — stalemate"),
        (
            GameOutcome::Draw(DrawReason::DeadPosition),
            "result: Draw — dead position",
        ),
        (
            GameOutcome::Resignation {
                winner: Color::Black,
            },
            "result: Resignation — Black wins",
        ),
    ];

    for (outcome, expected) in cases {
        let mut app = AppState::new();
        app.start_game(GameConfig::HumanVsEngine {
            human_color: Color::White,
            engine_depth: 1,
        })
        .expect("game starts");
        app.session.as_mut().expect("session").outcome = Some(outcome);
        let text = serialize_game(app.session.as_ref().expect("session"), None);
        assert!(text.contains(expected), "missing {expected:?} in {text:?}");
        assert!(!text.contains("PGN"));
    }
}
