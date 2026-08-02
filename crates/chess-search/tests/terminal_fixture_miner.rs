use chess_core::{Color, Move, Position, SearchHistory};
use chess_search::{alpha_beta_search, Score};

fn kqk_fen(white_king: u8, white_queen: u8, black_king: u8, side: Color) -> String {
    let mut board = [None; 64];
    board[usize::from(white_king)] = Some('K');
    board[usize::from(white_queen)] = Some('Q');
    board[usize::from(black_king)] = Some('k');

    let mut placement = String::new();
    for row in 0..8_u8 {
        if row != 0 {
            placement.push('/');
        }
        let mut empty = 0_u8;
        for file in 0..8_u8 {
            let index = usize::from(row * 8 + file);
            match board[index] {
                Some(piece) => {
                    if empty != 0 {
                        placement.push(char::from(b'0' + empty));
                        empty = 0;
                    }
                    placement.push(piece);
                }
                None => empty += 1,
            }
        }
        if empty != 0 {
            placement.push(char::from(b'0' + empty));
        }
    }

    let side_text = match side {
        Color::White => "w",
        Color::Black => "b",
    };
    format!("{placement} {side_text} - - 0 1")
}

fn kings_are_separated(white_king: u8, black_king: u8) -> bool {
    let white_row = white_king / 8;
    let white_file = white_king % 8;
    let black_row = black_king / 8;
    let black_file = black_king % 8;
    white_row.abs_diff(black_row) > 1 || white_file.abs_diff(black_file) > 1
}

fn root_scores(position: &mut Position, depth: u16) -> Vec<(Move, Score)> {
    let snapshot = position.clone();
    let mut history = SearchHistory::from_position(position);
    let history_snapshot = history.clone();
    let tokens = position
        .legal_move_tokens()
        .expect("candidate legal tokens generate");
    let mut scores = Vec::with_capacity(tokens.len());

    for token in tokens.iter() {
        let current = token.move_made();
        let position_undo = position
            .make_legal_token(token)
            .expect("candidate token applies");
        let history_undo = history.push_position(position);
        let child = alpha_beta_search(position, &mut history, depth - 1)
            .expect("candidate child search succeeds");
        history
            .pop_position(history_undo)
            .expect("candidate history restores");
        position
            .unmake_move(position_undo)
            .expect("candidate position restores");
        scores.push((current, -child.score()));
    }

    assert_eq!(*position, snapshot);
    assert_eq!(history, history_snapshot);
    scores
}

fn score_lines(scores: &[(Move, Score)]) -> String {
    let mut lines: Vec<String> = scores
        .iter()
        .map(|(current, score)| format!("{}={}", current.to_uci(), score.centipawns()))
        .collect();
    lines.sort();
    lines.join(",")
}

#[test]
fn mine_task_13_5_distance_fixtures() {
    let white_kings = [13_u8, 14, 20, 21, 22, 29, 30];
    let black_kings = [0_u8, 7];
    let mut shorter = None;
    let mut survival = None;

    'outer: for black_king in black_kings {
        for white_king in white_kings {
            if !kings_are_separated(white_king, black_king) {
                continue;
            }
            for white_queen in 0..64_u8 {
                if white_queen == white_king || white_queen == black_king {
                    continue;
                }

                for side in [Color::White, Color::Black] {
                    let fen = kqk_fen(white_king, white_queen, black_king, side);
                    let Ok(mut position) = fen.parse::<Position>() else {
                        continue;
                    };
                    if position.enforce_invariants().is_err()
                        || position.is_in_check(side.opposite())
                    {
                        continue;
                    }

                    let depth = if side == Color::White { 5 } else { 6 };
                    let mut history = SearchHistory::from_position(&position);
                    let Ok(result) = alpha_beta_search(&mut position, &mut history, depth) else {
                        continue;
                    };
                    if !result.score().is_mate() {
                        continue;
                    }

                    let scores = root_scores(&mut position, depth);
                    let mut mate_scores: Vec<Score> = scores
                        .iter()
                        .map(|(_, score)| *score)
                        .filter(|score| {
                            score.is_mate()
                                && match side {
                                    Color::White => score.centipawns() > 0,
                                    Color::Black => score.centipawns() < 0,
                                }
                        })
                        .collect();
                    mate_scores.sort();
                    mate_scores.dedup();

                    if side == Color::White && mate_scores.len() >= 2 && shorter.is_none() {
                        shorter = Some((fen.clone(), depth, result, scores.clone()));
                    }
                    if side == Color::Black
                        && result.score().centipawns() < 0
                        && mate_scores.len() >= 2
                        && scores.iter().all(|(_, score)| score.is_mate() && score.centipawns() < 0)
                        && survival.is_none()
                    {
                        survival = Some((fen.clone(), depth, result, scores.clone()));
                    }
                    if shorter.is_some() && survival.is_some() {
                        break 'outer;
                    }
                }
            }
        }
    }

    let (shorter_fen, shorter_depth, shorter_result, shorter_scores) =
        shorter.expect("must find a shorter-mate fixture");
    let (survival_fen, survival_depth, survival_result, survival_scores) =
        survival.expect("must find a longer-survival fixture");

    panic!(
        "MINED_SHORTER fen={shorter_fen} depth={shorter_depth} score={} best={} children=[{}]\nMINED_SURVIVAL fen={survival_fen} depth={survival_depth} score={} best={} children=[{}]",
        shorter_result.score().centipawns(),
        shorter_result
            .best_move()
            .expect("shorter fixture has move")
            .to_uci(),
        score_lines(&shorter_scores),
        survival_result.score().centipawns(),
        survival_result
            .best_move()
            .expect("survival fixture has move")
            .to_uci(),
        score_lines(&survival_scores),
    );
}
