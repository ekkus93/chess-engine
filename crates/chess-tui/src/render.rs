use std::time::Duration;

use chess_core::{Color, DrawReason, Move, Piece, PieceKind, Position, Square};
use chess_search::{Score, MATE_SCORE, MAX_EVALUATION};

use crate::{
    app::{GameConfig, GameOutcome, GameSession},
    worker::SearchMetrics,
};

pub const MIN_TERMINAL_WIDTH: u16 = 58;
pub const MIN_TERMINAL_HEIGHT: u16 = 32;
pub const WIDE_TERMINAL_WIDTH: u16 = 80;
pub const STACKED_MIN_TERMINAL_HEIGHT: u16 = 46;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum BoardOrientation {
    White,
    Black,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum LayoutDecision {
    TooSmall,
    Horizontal,
    Vertical,
}

#[must_use]
pub const fn layout_decision(width: u16, height: u16) -> LayoutDecision {
    if width >= WIDE_TERMINAL_WIDTH && height >= MIN_TERMINAL_HEIGHT {
        LayoutDecision::Horizontal
    } else if width >= MIN_TERMINAL_WIDTH && height >= STACKED_MIN_TERMINAL_HEIGHT {
        LayoutDecision::Vertical
    } else {
        LayoutDecision::TooSmall
    }
}

#[must_use]
pub const fn orientation_for_config(config: GameConfig) -> BoardOrientation {
    match config {
        GameConfig::HumanVsEngine {
            human_color: Color::Black,
            ..
        } => BoardOrientation::Black,
        GameConfig::HumanVsEngine {
            human_color: Color::White,
            ..
        }
        | GameConfig::SelfPlay { .. } => BoardOrientation::White,
    }
}

#[must_use]
pub fn board_lines(position: &Position, orientation: BoardOrientation) -> Vec<String> {
    let files = match orientation {
        BoardOrientation::White => "    a   b   c   d   e   f   g   h",
        BoardOrientation::Black => "    h   g   f   e   d   c   b   a",
    };
    let separator = "  +---+---+---+---+---+---+---+---+";
    let mut lines = Vec::with_capacity(19);
    lines.push(files.to_owned());
    lines.push(separator.to_owned());

    for display_row in 0_u8..8 {
        let row = match orientation {
            BoardOrientation::White => display_row,
            BoardOrientation::Black => 7 - display_row,
        };
        let rank = 8 - row;
        let mut line = format!("{rank} |");
        for display_file in 0_u8..8 {
            let file = match orientation {
                BoardOrientation::White => display_file,
                BoardOrientation::Black => 7 - display_file,
            };
            let symbol = Square::from_row_file(row, file)
                .and_then(|square| position.piece_at(square))
                .map_or(' ', piece_symbol);
            line.push(' ');
            line.push(symbol);
            line.push_str(" |");
        }
        lines.push(line);
        lines.push(separator.to_owned());
    }
    lines.push(files.to_owned());
    lines
}

#[must_use]
pub fn piece_symbol(piece: Piece) -> char {
    let symbol = match piece.kind {
        PieceKind::Pawn => 'P',
        PieceKind::Knight => 'N',
        PieceKind::Bishop => 'B',
        PieceKind::Rook => 'R',
        PieceKind::Queen => 'Q',
        PieceKind::King => 'K',
    };
    match piece.color {
        Color::White => symbol,
        Color::Black => symbol.to_ascii_lowercase(),
    }
}

#[must_use]
pub fn format_move_history(moves: &[Move]) -> String {
    let mut lines = Vec::with_capacity(moves.len().div_ceil(2));
    for (index, pair) in moves.chunks(2).enumerate() {
        let move_number = index + 1;
        let white = pair[0].to_uci();
        let black = pair
            .get(1)
            .map_or(String::new(), |current| current.to_uci());
        if black.is_empty() {
            lines.push(format!("{move_number:>3}. {white}"));
        } else {
            lines.push(format!("{move_number:>3}. {white:<6} {black}"));
        }
    }
    lines.join("\n")
}

#[must_use]
pub fn turn_status(session: &GameSession) -> String {
    if let Some(outcome) = session.outcome {
        return format_outcome(outcome);
    }
    let side = session.game.position().side_to_move();
    let side_name = color_name(side);
    let mut status = format!("{side_name} to move");
    if session.game.position().is_in_check(side) {
        status.push_str(" — CHECK");
    }
    let claims = session.game.draw_claims();
    if claims.threefold_repetition() && claims.fifty_move_rule() {
        status.push_str(" — draw claim available (threefold / fifty-move)");
    } else if claims.threefold_repetition() {
        status.push_str(" — draw claim available (threefold)");
    } else if claims.fifty_move_rule() {
        status.push_str(" — draw claim available (fifty-move)");
    }
    status
}

#[must_use]
pub fn format_outcome(outcome: GameOutcome) -> String {
    match outcome {
        GameOutcome::Checkmate { winner } => {
            format!("Checkmate — {} wins", color_name(winner))
        }
        GameOutcome::Stalemate => "Draw — stalemate".to_owned(),
        GameOutcome::Draw(reason) => format!("Draw — {}", draw_reason_name(reason)),
        GameOutcome::Resignation { winner } => {
            format!("Resignation — {} wins", color_name(winner))
        }
    }
}

#[must_use]
pub fn format_search_metrics(metrics: Option<&SearchMetrics>) -> String {
    let Some(metrics) = metrics else {
        return "depth  -\nscore  -\nnodes  -\nnps    -\ntime   -\nhash   -\npv     -".to_owned();
    };
    let depth = metrics
        .depth
        .map_or_else(|| "-".to_owned(), |value| value.to_string());
    let score = metrics.score.map_or_else(|| "-".to_owned(), format_score);
    let nodes = metrics
        .nodes
        .map_or_else(|| "-".to_owned(), |value| value.to_string());
    let nps = metrics
        .nps
        .map_or_else(|| "-".to_owned(), |value| value.to_string());
    let elapsed = metrics
        .elapsed
        .map_or_else(|| "-".to_owned(), format_duration);
    let hash = metrics
        .hash_full_per_mille
        .map_or_else(|| "-".to_owned(), |value| format!("{value}‰"));
    let pv = if metrics.principal_variation.is_empty() {
        "-".to_owned()
    } else {
        metrics
            .principal_variation
            .iter()
            .map(|current| current.to_uci())
            .collect::<Vec<_>>()
            .join(" ")
    };
    format!(
        "depth  {depth}\nscore  {score}\nnodes  {nodes}\nnps    {nps}\ntime   {elapsed}\nhash   {hash}\npv     {pv}"
    )
}

#[must_use]
pub fn format_score(score: Score) -> String {
    let value = score.centipawns();
    if !score.is_mate() {
        return format!("{:+.2}", f64::from(value) / 100.0);
    }
    if value > MAX_EVALUATION {
        format!("mate +{} ply", MATE_SCORE - value)
    } else {
        format!("mate -{} ply", MATE_SCORE + value)
    }
}

fn format_duration(duration: Duration) -> String {
    if duration.as_secs() > 0 {
        format!("{:.2}s", duration.as_secs_f64())
    } else {
        format!("{}ms", duration.as_millis())
    }
}

#[must_use]
pub const fn color_name(color: Color) -> &'static str {
    match color {
        Color::White => "White",
        Color::Black => "Black",
    }
}

#[must_use]
pub const fn draw_reason_name(reason: DrawReason) -> &'static str {
    match reason {
        DrawReason::ThreefoldRepetition => "threefold repetition",
        DrawReason::FivefoldRepetition => "fivefold repetition",
        DrawReason::FiftyMoveRule => "fifty-move rule",
        DrawReason::SeventyFiveMoveRule => "seventy-five-move rule",
        DrawReason::DeadPosition => "dead position",
    }
}

#[cfg(test)]
mod tests {
    use chess_core::{Color, Game, Position};
    use chess_search::Score;

    use super::{
        board_lines, format_move_history, format_score, layout_decision, BoardOrientation,
        LayoutDecision,
    };

    #[test]
    fn starting_board_orients_both_sides_and_uses_knight_n() {
        let position = Position::starting();
        let white = board_lines(&position, BoardOrientation::White);
        assert_eq!(
            white.first().expect("file row"),
            "    a   b   c   d   e   f   g   h"
        );
        assert!(white[2].contains("r | n | b | q | k | b | n | r"));
        assert!(white[16].contains("R | N | B | Q | K | B | N | R"));

        let black = board_lines(&position, BoardOrientation::Black);
        assert_eq!(
            black.first().expect("file row"),
            "    h   g   f   e   d   c   b   a"
        );
        assert!(black[2].starts_with("1 |"));
        assert!(black[16].starts_with("8 |"));
    }

    #[test]
    fn move_history_numbers_odd_and_even_plies() {
        let mut game = Game::starting();
        for notation in ["e2e4", "e7e5", "g1f3"] {
            let syntax = notation.parse::<chess_core::UciMove>().expect("syntax");
            let legal = game.legal_moves().expect("legal moves");
            let current = legal
                .iter()
                .find(|candidate| syntax.matches(*candidate))
                .expect("fixture move is legal");
            game.make_move(current).expect("fixture move applies");
        }
        assert_eq!(
            format_move_history(game.moves()),
            "  1. e2e4   e7e5\n  2. g1f3"
        );
    }

    #[test]
    fn mate_scores_are_distinct_from_centipawns() {
        assert_eq!(format_score(Score::from_evaluation(24)), "+0.24");
        assert!(format_score(Score::mate_in(3).expect("mate score")).starts_with("mate +"));
        assert!(format_score(Score::mated_in(2).expect("mate score")).starts_with("mate -"));
    }

    #[test]
    fn layout_requires_enough_height_for_the_complete_board() {
        assert_eq!(layout_decision(20, 8), LayoutDecision::TooSmall);
        assert_eq!(layout_decision(70, 24), LayoutDecision::TooSmall);
        assert_eq!(layout_decision(79, 45), LayoutDecision::TooSmall);
        assert_eq!(layout_decision(58, 46), LayoutDecision::Vertical);
        assert_eq!(layout_decision(80, 32), LayoutDecision::Horizontal);
        assert_eq!(layout_decision(120, 30), LayoutDecision::TooSmall);
    }

    #[test]
    fn black_orientation_is_selected_for_black_human() {
        let config = crate::app::GameConfig::HumanVsEngine {
            human_color: Color::Black,
            engine_depth: 3,
        };
        assert_eq!(
            super::orientation_for_config(config),
            BoardOrientation::Black
        );
    }
}

#[cfg(test)]
mod hardening_tests;
