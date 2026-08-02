use chess_core::{Color, Move, Position, SearchHistory};
use chess_search::{alpha_beta_search, Score};

const SHORTER_MATE_FEN: &str = "7k/5Q2/6K1/8/8/8/8/8 w - - 0 1";
const SHORTER_DEPTH: u16 = 5;
const SURVIVAL_DEPTH: u16 = 6;

fn parent_score(child: Score) -> Score {
    if !child.is_mate() {
        return -child;
    }

    let raw = if child.centipawns() > 0 {
        -child.centipawns() + 1
    } else {
        -child.centipawns() - 1
    };
    Score::from_raw(raw).expect("one-ply mate normalization stays in range")
}

fn root_scores(position: &mut Position, depth: u16) -> Vec<(Move, Score)> {
    assert!(depth > 0);
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
        scores.push((current, parent_score(child.score())));
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

fn kqk_fen(white_king: u8, white_queen: u8, black_king: u8) -> String {
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
            match board[usize::from(row * 8 + file)] {
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

    format!("{placement} b - - 0 1")
}

#[test]
fn mine_task_13_5_distance_fixtures() {
    let mut shorter = Position::from_fen(SHORTER_MATE_FEN).expect("fixture FEN is valid");
    let shorter_scores = root_scores(&mut shorter, SHORTER_DEPTH);
    let shorter_best = shorter_scores
        .iter()
        .map(|(_, score)| *score)
        .max()
        .expect("shorter-mate root has legal moves");
    let mut positive_mates: Vec<Score> = shorter_scores
        .iter()
        .map(|(_, score)| *score)
        .filter(|score| score.is_mate() && score.centipawns() > 0)
        .collect();
    positive_mates.sort();
    positive_mates.dedup();
    assert!(positive_mates.len() >= 2);

    let white_kings = [20_u8, 21, 22, 28, 29, 30, 19, 27];
    let preferred_queens = [12_u8, 13, 14, 15, 4, 5, 6, 11, 3, 10, 18, 17];
    let mut queen_squares = preferred_queens.to_vec();
    queen_squares.extend((0_u8..64).filter(|square| !preferred_queens.contains(square)));
    let black_king = 7_u8;
    let mut survival = None;

    'positions: for white_king in white_kings {
        for white_queen in &queen_squares {
            if *white_queen == white_king || *white_queen == black_king {
                continue;
            }

            let fen = kqk_fen(white_king, *white_queen, black_king);
            let Ok(mut position) = Position::from_fen(&fen) else {
                continue;
            };
            if position.is_in_check(Color::White) {
                continue;
            }

            let mut history = SearchHistory::from_position(&position);
            let Ok(result) = alpha_beta_search(&mut position, &mut history, SURVIVAL_DEPTH) else {
                continue;
            };
            if !result.score().is_mate() || result.score().centipawns() >= 0 {
                continue;
            }

            let scores = root_scores(&mut position, SURVIVAL_DEPTH);
            let mut distinct: Vec<Score> = scores.iter().map(|(_, score)| *score).collect();
            distinct.sort();
            distinct.dedup();
            let best = scores
                .iter()
                .map(|(_, score)| *score)
                .max()
                .expect("forced-loss root has legal moves");
            let best_count = scores.iter().filter(|(_, score)| *score == best).count();

            if distinct.len() >= 2
                && best_count == 1
                && scores
                    .iter()
                    .all(|(_, score)| score.is_mate() && score.centipawns() < 0)
            {
                survival = Some((fen, result, scores));
                break 'positions;
            }
        }
    }

    let (survival_fen, survival_result, survival_scores) = survival.unwrap_or_else(|| {
        panic!(
            "no bounded longer-survival fixture found; shorter children=[{}]",
            score_lines(&shorter_scores)
        )
    });
    let survival_best = survival_scores
        .iter()
        .max_by_key(|(_, score)| *score)
        .expect("survival root has legal moves");

    panic!(
        "MINED_SHORTER fen={SHORTER_MATE_FEN} depth={SHORTER_DEPTH} best_score={} children=[{}]\nMINED_SURVIVAL fen={} depth={SURVIVAL_DEPTH} root_score={} root_best={} oracle_best={} oracle_score={} children=[{}]",
        shorter_best.centipawns(),
        score_lines(&shorter_scores),
        survival_fen,
        survival_result.score().centipawns(),
        survival_result
            .best_move()
            .expect("survival search has a move")
            .to_uci(),
        survival_best.0.to_uci(),
        survival_best.1.centipawns(),
        score_lines(&survival_scores),
    );
}
