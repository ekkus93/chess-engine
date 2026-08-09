use std::time::Duration;

use chess_core::{Color, DrawReason, Move, Piece, PieceKind, Position, Square};
use chess_search::{Score, MATE_SCORE, MAX_EVALUATION};

use crate::{controller::{GameConfig, GameOutcome, GameSession}, worker::SearchMetrics};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum BoardOrientation {
    White,
    Black,
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
        let black = pair.get(1).map_or(String::new(), |current| current.to_uci());
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
    let mut status = format!("{} to move", color_name(side));
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
        GameOutcome::Checkmate { winner } => format!("Checkmate — {} wins", color_name(winner)),
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
    let depth = metrics.depth.map_or_else(|| "-".to_owned(), |value| value.to_string());
    let score = metrics.score.map_or_else(|| "-".to_owned(), format_score);
    let nodes = metrics.nodes.map_or_else(|| "-".to_owned(), |value| value.to_string());
    let nps = metrics.nps.map_or_else(|| "-".to_owned(), |value| value.to_string());
    let elapsed = metrics.elapsed.map_or_else(|| "-".to_owned(), format_duration);
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

#[must_use]
pub fn format_duration(duration: Duration) -> String {
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
    use std::time::Duration;

    use chess_core::{Color, Game, Piece, PieceKind, Position, UciMove};
    use chess_search::Score;

    use super::{
        board_lines, format_duration, format_move_history, format_score, format_search_metrics,
        orientation_for_config, piece_symbol, turn_status, BoardOrientation,
    };
    use crate::{controller::{GameConfig, GameController}, worker::SearchMetrics};

    fn apply_uci(game: &mut Game, uci: &str) {
        let syntax = uci.parse::<UciMove>().expect("fixture syntax");
        let current = game
            .legal_moves()
            .expect("legal moves")
            .iter()
            .find(|candidate| syntax.matches(*candidate))
            .expect("fixture legal");
        game.make_move(current).expect("move applies");
    }

    #[test]
    fn board_orientation_and_symbols_are_stable() {
        let white = board_lines(&Position::starting(), BoardOrientation::White);
        assert_eq!(white[0], "    a   b   c   d   e   f   g   h");
        assert!(white[2].contains("r | n | b | q | k | b | n | r"));
        assert!(white[16].contains("R | N | B | Q | K | B | N | R"));
        let black = board_lines(&Position::starting(), BoardOrientation::Black);
        assert_eq!(black[0], "    h   g   f   e   d   c   b   a");
        assert!(black[2].starts_with("1 |"));
        assert_eq!(piece_symbol(Piece::new(Color::White, PieceKind::Knight)), 'N');
        assert_eq!(piece_symbol(Piece::new(Color::Black, PieceKind::Knight)), 'n');
        assert_eq!(
            orientation_for_config(GameConfig::HumanVsEngine {
                human_color: Color::Black,
                engine_depth: 3,
            }),
            BoardOrientation::Black
        );
    }

    #[test]
    fn move_history_numbers_odd_and_even_plies() {
        let mut game = Game::starting();
        for uci in ["e2e4", "e7e5", "g1f3"] {
            apply_uci(&mut game, uci);
        }
        assert_eq!(format_move_history(game.moves()), "  1. e2e4   e7e5\n  2. g1f3");
    }

    #[test]
    fn metrics_do_not_fabricate_missing_values() {
        assert_eq!(
            format_search_metrics(None),
            "depth  -\nscore  -\nnodes  -\nnps    -\ntime   -\nhash   -\npv     -"
        );
        let metrics = SearchMetrics {
            depth: Some(4),
            score: Some(Score::from_evaluation(24)),
            elapsed: Some(Duration::from_millis(25)),
            ..SearchMetrics::default()
        };
        let text = format_search_metrics(Some(&metrics));
        assert!(text.contains("depth  4"));
        assert!(text.contains("score  +0.24"));
        assert!(text.contains("nodes  -"));
    }

    #[test]
    fn score_and_duration_formatting_cover_mate_and_centipawns() {
        assert_eq!(format_score(Score::from_evaluation(-75)), "-0.75");
        assert!(format_score(Score::mate_in(1).expect("mate score")).starts_with("mate +"));
        assert!(format_score(Score::mated_in(1).expect("mate score")).starts_with("mate -"));
        assert_eq!(format_duration(Duration::from_millis(999)), "999ms");
        assert_eq!(format_duration(Duration::from_secs(1)), "1.00s");
    }

    #[test]
    fn turn_status_reports_check_and_draw_claims() {
        let mut controller = GameController::new();
        controller
            .start_game(GameConfig::HumanVsEngine {
                human_color: Color::White,
                engine_depth: 1,
            })
            .expect("game starts");
        controller.session.as_mut().expect("session").game = Game::new(
            Position::from_fen("7k/8/8/8/8/8/7R/K7 b - - 0 1").expect("check fixture"),
        );
        assert!(turn_status(controller.session.as_ref().expect("session")).contains("CHECK"));
    }
}
