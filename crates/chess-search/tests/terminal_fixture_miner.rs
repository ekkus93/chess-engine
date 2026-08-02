use chess_core::{Move, Position, SearchHistory};
use chess_search::{alpha_beta_search, Score};

const SHORTER_MATE_FEN: &str = "7k/5Q2/6K1/8/8/8/8/8 w - - 0 1";
const SEARCH_DEPTH: u16 = 5;

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

#[test]
fn mine_task_13_5_distance_fixtures() {
    let mut shorter = Position::from_fen(SHORTER_MATE_FEN).expect("fixture FEN is valid");
    let shorter_scores = root_scores(&mut shorter, SEARCH_DEPTH);
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
    assert!(
        positive_mates.len() >= 2,
        "shorter fixture must contain distinct winning mate distances: {}",
        score_lines(&shorter_scores)
    );

    let mut survival = None;
    for (candidate, score) in &shorter_scores {
        if !score.is_mate() || score.centipawns() <= 0 || *score == shorter_best {
            continue;
        }

        let mut child = shorter.clone();
        let token = child
            .legal_move_tokens()
            .expect("shorter root tokens generate")
            .iter()
            .find(|token| token.move_made() == *candidate)
            .expect("candidate token is present");
        let _undo = child
            .make_legal_token(token)
            .expect("slower mating move applies");
        let child_scores = root_scores(&mut child, SEARCH_DEPTH - 1);
        let mut distinct: Vec<Score> = child_scores.iter().map(|(_, value)| *value).collect();
        distinct.sort();
        distinct.dedup();

        if distinct.len() >= 2
            && child_scores
                .iter()
                .all(|(_, value)| value.is_mate() && value.centipawns() < 0)
        {
            survival = Some((child.to_fen(), *candidate, *score, child_scores));
            break;
        }
    }

    let (survival_fen, slower_move, slower_score, survival_scores) =
        survival.unwrap_or_else(|| {
            panic!(
                "no longer-survival child found; shorter children=[{}]",
                score_lines(&shorter_scores)
            )
        });
    let survival_best = survival_scores
        .iter()
        .max_by_key(|(_, score)| *score)
        .expect("survival root has legal moves");

    panic!(
        "MINED_SHORTER fen={SHORTER_MATE_FEN} depth={SEARCH_DEPTH} best_score={} children=[{}]\nMINED_SURVIVAL via={} via_score={} fen={} depth={} best={} best_score={} children=[{}]",
        shorter_best.centipawns(),
        score_lines(&shorter_scores),
        slower_move.to_uci(),
        slower_score.centipawns(),
        survival_fen,
        SEARCH_DEPTH - 1,
        survival_best.0.to_uci(),
        survival_best.1.centipawns(),
        score_lines(&survival_scores),
    );
}
