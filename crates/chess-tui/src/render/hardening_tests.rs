use std::time::Duration;

use chess_core::{Color, DrawReason, Game, Piece, PieceKind, Position, UciMove};
use chess_search::Score;

use super::{
    board_lines, draw_reason_name, format_duration, format_move_history, format_outcome,
    format_score, format_search_metrics, layout_decision, orientation_for_config, piece_symbol,
    turn_status, BoardOrientation, LayoutDecision, MIN_TERMINAL_HEIGHT, MIN_TERMINAL_WIDTH,
    STACKED_MIN_TERMINAL_HEIGHT, WIDE_TERMINAL_WIDTH,
};
use crate::{
    app::{GameConfig, GameOutcome, GameSession},
    worker::{SearchMetrics, SearchTicket},
};

fn apply_uci(game: &mut Game, uci: &str) -> chess_core::Move {
    let syntax = uci.parse::<UciMove>().expect("fixture syntax");
    let current = game
        .legal_moves()
        .expect("legal moves")
        .iter()
        .find(|candidate| syntax.matches(*candidate))
        .expect("fixture move legal");
    game.make_move(current).expect("fixture move applies");
    current
}

fn session(game: Game) -> GameSession {
    GameSession {
        game,
        config: GameConfig::HumanVsEngine {
            human_color: Color::White,
            engine_depth: 3,
        },
        generation: 1,
        active_search: None::<SearchTicket>,
        thinking: false,
        auto_play: false,
        outcome: None,
        status_message: None,
        engine_info: None,
    }
}

#[test]
fn every_piece_kind_has_unambiguous_white_and_black_symbols() {
    let expected = [
        (PieceKind::Pawn, 'P', 'p'),
        (PieceKind::Knight, 'N', 'n'),
        (PieceKind::Bishop, 'B', 'b'),
        (PieceKind::Rook, 'R', 'r'),
        (PieceKind::Queen, 'Q', 'q'),
        (PieceKind::King, 'K', 'k'),
    ];
    for (kind, white, black) in expected {
        assert_eq!(piece_symbol(Piece::new(Color::White, kind)), white);
        assert_eq!(piece_symbol(Piece::new(Color::Black, kind)), black);
    }
}

#[test]
fn orientation_contract_covers_both_human_sides_and_self_play() {
    assert_eq!(
        orientation_for_config(GameConfig::HumanVsEngine {
            human_color: Color::White,
            engine_depth: 3,
        }),
        BoardOrientation::White
    );
    assert_eq!(
        orientation_for_config(GameConfig::HumanVsEngine {
            human_color: Color::Black,
            engine_depth: 3,
        }),
        BoardOrientation::Black
    );
    assert_eq!(
        orientation_for_config(GameConfig::SelfPlay {
            white_depth: 2,
            black_depth: 4,
        }),
        BoardOrientation::White
    );
    assert_eq!(
        board_lines(&Position::starting(), BoardOrientation::White).len(),
        19
    );
    assert_eq!(
        board_lines(&Position::starting(), BoardOrientation::Black).len(),
        19
    );
}

#[test]
fn move_history_covers_empty_one_two_and_multiple_plies() {
    let mut game = Game::starting();
    assert_eq!(format_move_history(game.moves()), "");
    apply_uci(&mut game, "e2e4");
    assert_eq!(format_move_history(game.moves()), "  1. e2e4");
    apply_uci(&mut game, "e7e5");
    assert_eq!(format_move_history(game.moves()), "  1. e2e4   e7e5");
    apply_uci(&mut game, "g1f3");
    assert!(format_move_history(game.moves()).ends_with("  2. g1f3"));
    apply_uci(&mut game, "b8c6");
    assert!(format_move_history(game.moves()).ends_with("  2. g1f3   b8c6"));
}

#[test]
fn fully_populated_search_metrics_render_real_values_and_ordered_pv() {
    let mut game = Game::starting();
    let e2e4 = apply_uci(&mut game, "e2e4");
    let e7e5 = apply_uci(&mut game, "e7e5");
    let metrics = SearchMetrics {
        depth: Some(7),
        score: Some(Score::from_evaluation(-125)),
        nodes: Some(12_345),
        nps: Some(67_890),
        elapsed: Some(Duration::from_millis(1_500)),
        principal_variation: vec![e2e4, e7e5],
        hash_full_per_mille: Some(321),
    };
    let text = format_search_metrics(Some(&metrics));
    for expected in [
        "depth  7",
        "score  -1.25",
        "nodes  12345",
        "nps    67890",
        "time   1.50s",
        "hash   321‰",
        "pv     e2e4 e7e5",
    ] {
        assert!(text.contains(expected), "missing {expected:?} in {text:?}");
    }

    let empty_pv = SearchMetrics {
        depth: Some(1),
        score: Some(Score::from_evaluation(0)),
        nodes: Some(0),
        nps: Some(0),
        elapsed: Some(Duration::from_millis(25)),
        principal_variation: Vec::new(),
        hash_full_per_mille: Some(0),
    };
    let text = format_search_metrics(Some(&empty_pv));
    assert!(text.contains("score  +0.00"));
    assert!(text.contains("time   25ms"));
    assert!(text.contains("pv     -"));
}

#[test]
fn score_and_duration_formatting_cover_sign_and_time_boundaries() {
    assert_eq!(format_score(Score::from_evaluation(250)), "+2.50");
    assert_eq!(format_score(Score::from_evaluation(0)), "+0.00");
    assert_eq!(format_score(Score::from_evaluation(-75)), "-0.75");
    assert!(format_score(Score::mate_in(1).expect("mate score")).starts_with("mate +"));
    assert!(format_score(Score::mated_in(1).expect("mate score")).starts_with("mate -"));
    assert_eq!(format_duration(Duration::from_millis(999)), "999ms");
    assert_eq!(format_duration(Duration::from_secs(1)), "1.00s");
}

#[test]
fn layout_decision_boundary_matrix_is_explicit() {
    assert_eq!(
        layout_decision(WIDE_TERMINAL_WIDTH - 1, MIN_TERMINAL_HEIGHT),
        LayoutDecision::TooSmall
    );
    assert_eq!(
        layout_decision(WIDE_TERMINAL_WIDTH, MIN_TERMINAL_HEIGHT - 1),
        LayoutDecision::TooSmall
    );
    assert_eq!(
        layout_decision(WIDE_TERMINAL_WIDTH, MIN_TERMINAL_HEIGHT),
        LayoutDecision::Horizontal
    );
    assert_eq!(
        layout_decision(WIDE_TERMINAL_WIDTH + 1, MIN_TERMINAL_HEIGHT),
        LayoutDecision::Horizontal
    );
    assert_eq!(
        layout_decision(MIN_TERMINAL_WIDTH - 1, STACKED_MIN_TERMINAL_HEIGHT),
        LayoutDecision::TooSmall
    );
    assert_eq!(
        layout_decision(MIN_TERMINAL_WIDTH, STACKED_MIN_TERMINAL_HEIGHT - 1),
        LayoutDecision::TooSmall
    );
    assert_eq!(
        layout_decision(MIN_TERMINAL_WIDTH, STACKED_MIN_TERMINAL_HEIGHT),
        LayoutDecision::Vertical
    );
    assert_eq!(layout_decision(200, 100), LayoutDecision::Horizontal);
}

#[test]
fn outcome_and_draw_reason_formatting_cover_every_variant() {
    assert_eq!(
        format_outcome(GameOutcome::Checkmate {
            winner: Color::White,
        }),
        "Checkmate — White wins"
    );
    assert_eq!(format_outcome(GameOutcome::Stalemate), "Draw — stalemate");
    assert_eq!(
        format_outcome(GameOutcome::Resignation {
            winner: Color::Black,
        }),
        "Resignation — Black wins"
    );
    assert_eq!(
        format_outcome(GameOutcome::Draw(DrawReason::DeadPosition)),
        "Draw — dead position"
    );

    let expected = [
        (DrawReason::ThreefoldRepetition, "threefold repetition"),
        (DrawReason::FivefoldRepetition, "fivefold repetition"),
        (DrawReason::FiftyMoveRule, "fifty-move rule"),
        (DrawReason::SeventyFiveMoveRule, "seventy-five-move rule"),
        (DrawReason::DeadPosition, "dead position"),
    ];
    for (reason, name) in expected {
        assert_eq!(draw_reason_name(reason), name);
    }
}

#[test]
fn turn_status_reports_check_and_claimable_draws_without_terminalizing_them() {
    let check =
        Game::new(Position::from_fen("7k/8/8/8/8/8/7R/K7 b - - 0 1").expect("check fixture"));
    let check_status = turn_status(&session(check));
    assert!(check_status.contains("Black to move"));
    assert!(check_status.contains("CHECK"));

    let fifty =
        Game::new(Position::from_fen("7k/8/8/8/8/8/R7/K7 w - - 100 51").expect("fifty fixture"));
    let fifty_status = turn_status(&session(fifty));
    assert!(fifty_status.contains("draw claim available (fifty-move)"));

    let mut threefold = Game::starting();
    for uci in [
        "g1f3", "g8f6", "f3g1", "f6g8", "g1f3", "g8f6", "f3g1", "f6g8",
    ] {
        apply_uci(&mut threefold, uci);
    }
    let repetition_status = turn_status(&session(threefold));
    assert!(repetition_status.contains("draw claim available (threefold)"));

    let mut both = Game::new(
        Position::from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 92 1")
            .expect("combined claim fixture"),
    );
    for uci in [
        "g1f3", "g8f6", "f3g1", "f6g8", "g1f3", "g8f6", "f3g1", "f6g8",
    ] {
        apply_uci(&mut both, uci);
    }
    let both_status = turn_status(&session(both));
    assert!(both_status.contains("draw claim available (threefold / fifty-move)"));
}
