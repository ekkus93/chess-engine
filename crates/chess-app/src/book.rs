use std::sync::OnceLock;

use chess_core::{Color, Game, Move, Position, UciMove};

const SPLITMIX64_INCREMENT: u64 = 0x9e37_79b9_7f4a_7c15;
const SPLITMIX64_MULTIPLIER_ONE: u64 = 0xbf58_476d_1ce4_e5b9;
const SPLITMIX64_MULTIPLIER_TWO: u64 = 0x94d0_49bb_1331_11eb;

#[derive(Clone, Copy, Debug)]
struct OpeningLine {
    name: &'static str,
    side: Color,
    weight: u32,
    moves: &'static [&'static str],
}

#[derive(Clone, Debug, Eq, PartialEq)]
struct BookRecord {
    position_key: String,
    uci_move: UciMove,
    weight: u32,
}

static BUILT_IN_BOOK: OnceLock<Result<Vec<BookRecord>, String>> = OnceLock::new();

pub(crate) fn select_move(position: &Position) -> Result<Option<Move>, String> {
    let candidates = candidates_for_position(position)?;
    let Some((mut best_move, mut best_weight)) = candidates.first().copied() else {
        return Ok(None);
    };
    for (candidate, weight) in candidates.iter().copied().skip(1) {
        if weight > best_weight {
            best_move = candidate;
            best_weight = weight;
        }
    }
    Ok(Some(best_move))
}

pub(crate) fn select_weighted_move(position: &Position, seed: u64) -> Result<Option<Move>, String> {
    let candidates = candidates_for_position(position)?;
    if candidates.is_empty() {
        return Ok(None);
    }
    let total_weight = candidates.iter().try_fold(0_u64, |total, (_, weight)| {
        total
            .checked_add(u64::from(*weight))
            .ok_or_else(|| "built-in opening-book candidate weight total overflowed".to_owned())
    })?;
    if total_weight == 0 {
        return Err("weighted built-in opening-book selection has zero total weight".to_owned());
    }

    let mut rng_state = seed;
    let mut target = sample_below(&mut rng_state, total_weight);
    for (candidate, weight) in candidates {
        let weight = u64::from(weight);
        if target < weight {
            return Ok(Some(candidate));
        }
        target -= weight;
    }
    unreachable!("a sample below positive total weight selects one candidate");
}

fn candidates_for_position(position: &Position) -> Result<Vec<(Move, u32)>, String> {
    let book = match BUILT_IN_BOOK.get_or_init(build_book) {
        Ok(book) => book,
        Err(message) => return Err(message.clone()),
    };
    let key = position_key(position)?;
    let mut records = book
        .iter()
        .filter(|record| record.position_key == key)
        .collect::<Vec<_>>();
    records.sort_by_key(|record| record.uci_move);

    let mut game = Game::new(position.clone());
    records
        .into_iter()
        .map(|record| {
            resolve_legal_move(&mut game, record.uci_move)
                .map(|chess_move| (chess_move, record.weight))
                .map_err(|message| {
                    format!(
                        "built-in opening book selected invalid move {} for position {}: {message}",
                        record.uci_move,
                        position.to_fen()
                    )
                })
        })
        .collect()
}

fn sample_below(rng_state: &mut u64, upper_bound: u64) -> u64 {
    debug_assert!(upper_bound > 0);
    let rejection_threshold = upper_bound.wrapping_neg() % upper_bound;
    loop {
        let sample = next_random_u64(rng_state);
        if sample >= rejection_threshold {
            return sample % upper_bound;
        }
    }
}

fn next_random_u64(rng_state: &mut u64) -> u64 {
    *rng_state = rng_state.wrapping_add(SPLITMIX64_INCREMENT);
    let mut value = *rng_state;
    value = (value ^ (value >> 30)).wrapping_mul(SPLITMIX64_MULTIPLIER_ONE);
    value = (value ^ (value >> 27)).wrapping_mul(SPLITMIX64_MULTIPLIER_TWO);
    value ^ (value >> 31)
}

fn build_book() -> Result<Vec<BookRecord>, String> {
    let mut records = Vec::new();
    for line in OPENING_LINES {
        let mut game = Game::starting();
        for (ply_index, move_text) in line.moves.iter().enumerate() {
            let parsed = move_text.parse::<UciMove>().map_err(|error| {
                format!(
                    "built-in opening book line {:?} has invalid move {move_text:?} at ply {ply_index}: {error}",
                    line.name
                )
            })?;
            let chess_move = resolve_legal_move(&mut game, parsed).map_err(|message| {
                format!(
                    "built-in opening book line {:?} failed at move {move_text:?}, ply {ply_index}: {message}",
                    line.name
                )
            })?;
            if line.side == game.position().side_to_move() {
                let record = BookRecord {
                    position_key: position_key(game.position())?,
                    uci_move: parsed,
                    weight: line.weight,
                };
                upsert_record(&mut records, record);
            }
            game.make_move(chess_move).map_err(|error| {
                format!(
                    "built-in opening book line {:?} could not apply move {move_text:?}: {error}",
                    line.name
                )
            })?;
        }
    }
    Ok(records)
}

fn position_key(position: &Position) -> Result<String, String> {
    let fen = position.to_fen();
    let fields = fen.split_whitespace().take(4).collect::<Vec<_>>();
    if fields.len() != 4 {
        return Err(format!(
            "position FEN did not contain the four repetition-relevant fields: {fen}"
        ));
    }
    Ok(fields.join(" "))
}

fn resolve_legal_move(game: &mut Game, parsed: UciMove) -> Result<Move, String> {
    let legal_moves = game
        .legal_moves()
        .map_err(|error| format!("legal move generation failed: {error}"))?;
    let mut matches = legal_moves
        .iter()
        .filter(|candidate| parsed.matches(*candidate));
    let Some(chess_move) = matches.next() else {
        return Err(format!("move {parsed} is not legal"));
    };
    if matches.next().is_some() {
        return Err(format!(
            "move {parsed} resolved to multiple legal identities"
        ));
    }
    Ok(chess_move)
}

fn upsert_record(records: &mut Vec<BookRecord>, record: BookRecord) {
    let existing = records.iter().position(|candidate| {
        candidate.position_key == record.position_key && candidate.uci_move == record.uci_move
    });
    match existing {
        Some(index) if record.weight > records[index].weight => records[index] = record,
        Some(_) => {}
        None => records.push(record),
    }
}

const OPENING_LINES: &[OpeningLine] = &[
    OpeningLine {
        name: "Italian Game",
        side: Color::White,
        weight: 85,
        moves: &["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"],
    },
    OpeningLine {
        name: "Ruy Lopez",
        side: Color::White,
        weight: 95,
        moves: &["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"],
    },
    OpeningLine {
        name: "Queen's Gambit",
        side: Color::White,
        weight: 90,
        moves: &["d2d4", "d7d5", "c2c4"],
    },
    OpeningLine {
        name: "London System",
        side: Color::White,
        weight: 65,
        moves: &[
            "d2d4", "d7d5", "c2c4", "c7c6", "c1f4", "g8f6", "g1f3", "a7a6",
        ],
    },
    OpeningLine {
        name: "Scotch Game",
        side: Color::White,
        weight: 75,
        moves: &["e2e4", "e7e5", "g1f3", "b8c6", "d2d4"],
    },
    OpeningLine {
        name: "King's Gambit",
        side: Color::White,
        weight: 70,
        moves: &["e2e4", "e7e5", "f2f4"],
    },
    OpeningLine {
        name: "Vienna Game",
        side: Color::White,
        weight: 55,
        moves: &["e2e4", "e7e5", "b1c3"],
    },
    OpeningLine {
        name: "English Opening",
        side: Color::White,
        weight: 60,
        moves: &["c2c4"],
    },
    OpeningLine {
        name: "Reti Opening",
        side: Color::White,
        weight: 50,
        moves: &["g1f3", "d7d5", "c2c4"],
    },
    OpeningLine {
        name: "Catalan Opening",
        side: Color::White,
        weight: 70,
        moves: &["d2d4", "d7d5", "c2c4", "e7e6", "g1f3", "g8f6", "g2g3"],
    },
    OpeningLine {
        name: "King's Gambit Accepted: King's Knight Gambit",
        side: Color::White,
        weight: 80,
        moves: &["e2e4", "e7e5", "f2f4", "e5f4", "g1f3"],
    },
    OpeningLine {
        name: "King's Gambit Accepted: Bishop's Gambit",
        side: Color::White,
        weight: 45,
        moves: &["e2e4", "e7e5", "f2f4", "e5f4", "f1c4"],
    },
    OpeningLine {
        name: "King's Gambit Accepted: Classical Defense",
        side: Color::White,
        weight: 60,
        moves: &[
            "e2e4", "e7e5", "f2f4", "e5f4", "g1f3", "g8f6", "f1c4", "f8c5",
        ],
    },
    OpeningLine {
        name: "King's Gambit Accepted: Fischer Defense",
        side: Color::White,
        weight: 50,
        moves: &["e2e4", "e7e5", "f2f4", "e5f4", "g1f3", "d7d5"],
    },
    OpeningLine {
        name: "King's Gambit Declined: Classical",
        side: Color::White,
        weight: 55,
        moves: &["e2e4", "e7e5", "f2f4", "f8c5", "g1f3"],
    },
    OpeningLine {
        name: "King's Gambit Declined: Falkbeer Countergambit",
        side: Color::White,
        weight: 40,
        moves: &["e2e4", "e7e5", "f2f4", "d7d5", "e4d5"],
    },
    OpeningLine {
        name: "Sicilian Defense: Najdorf",
        side: Color::Black,
        weight: 100,
        moves: &[
            "e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6",
            "b1c3", "a7a6",
        ],
    },
    OpeningLine {
        name: "Sicilian Defense: Alapin",
        side: Color::Black,
        weight: 90,
        moves: &[
            "e2e4", "c7c5", "c2c3", "d7d5", "e4d5", "d8d5", "d2d4", "g8f6",
        ],
    },
    OpeningLine {
        name: "Sicilian Defense: Closed",
        side: Color::Black,
        weight: 85,
        moves: &[
            "e2e4", "c7c5", "b1c3", "b8c6", "g2g3", "g7g6", "f1g2", "f8g7",
        ],
    },
    OpeningLine {
        name: "Sicilian Defense: Smith-Morra",
        side: Color::Black,
        weight: 80,
        moves: &[
            "e2e4", "c7c5", "d2d4", "c5d4", "c2c3", "d4c3", "b1c3", "b8c6",
        ],
    },
    OpeningLine {
        name: "French Defense",
        side: Color::Black,
        weight: 85,
        moves: &[
            "e2e4", "e7e6", "d2d4", "d7d5", "b1c3", "g8f6", "e4e5", "f6d7",
            "f2f4", "c7c5",
        ],
    },
    OpeningLine {
        name: "Caro-Kann Defense",
        side: Color::Black,
        weight: 80,
        moves: &[
            "e2e4", "c7c6", "d2d4", "d7d5", "b1c3", "d5e4", "c3e4", "c8f5",
            "e4g3", "f5g6",
        ],
    },
    OpeningLine {
        name: "Open Game",
        side: Color::Black,
        weight: 75,
        moves: &[
            "e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5", "d2d3", "g8f6",
        ],
    },
    OpeningLine {
        name: "Scandinavian Defense",
        side: Color::Black,
        weight: 50,
        moves: &[
            "e2e4", "d7d5", "e4d5", "d8d5", "b1c3", "d5d8", "d2d4", "g8f6",
        ],
    },
    OpeningLine {
        name: "Pirc Defense",
        side: Color::Black,
        weight: 55,
        moves: &[
            "e2e4", "d7d6", "d2d4", "g8f6", "b1c3", "g7g6", "g1f3", "f8g7",
        ],
    },
    OpeningLine {
        name: "Queen's Gambit Declined",
        side: Color::Black,
        weight: 95,
        moves: &[
            "d2d4", "d7d5", "c2c4", "e7e6", "b1c3", "g8f6", "c1g5", "f8e7",
            "e2e3", "e8g8",
        ],
    },
    OpeningLine {
        name: "Slav Defense",
        side: Color::Black,
        weight: 90,
        moves: &[
            "d2d4", "d7d5", "c2c4", "c7c6", "g1f3", "g8f6", "b1c3", "d5c4",
            "a2a4", "c8f5",
        ],
    },
    OpeningLine {
        name: "King's Indian Defense",
        side: Color::Black,
        weight: 85,
        moves: &[
            "d2d4", "g8f6", "c2c4", "g7g6", "b1c3", "f8g7", "e2e4", "d7d6",
            "g1f3", "e8g8",
        ],
    },
    OpeningLine {
        name: "Nimzo-Indian Defense",
        side: Color::Black,
        weight: 80,
        moves: &[
            "d2d4", "g8f6", "c2c4", "e7e6", "b1c3", "f8b4", "e2e3", "e8g8",
            "f1d3", "d7d5",
        ],
    },
];

#[cfg(test)]
mod tests {
    use chess_core::{Game, UciMove};

    use super::{resolve_legal_move, select_move, select_weighted_move};

    fn apply(game: &mut Game, move_text: &str) {
        let parsed = move_text.parse::<UciMove>().expect("test UCI move");
        let chess_move = resolve_legal_move(game, parsed).expect("test legal move");
        game.make_move(chess_move).expect("test move applies");
    }

    #[test]
    fn built_in_book_selects_highest_weight_white_opening() {
        let game = Game::starting();
        assert_eq!(
            select_move(game.position())
                .expect("book lookup")
                .expect("book move")
                .to_uci(),
            "e2e4"
        );
    }

    #[test]
    fn built_in_book_selects_sicilian_after_e2e4() {
        let mut game = Game::starting();
        apply(&mut game, "e2e4");
        assert_eq!(
            select_move(game.position())
                .expect("book lookup")
                .expect("book move")
                .to_uci(),
            "c7c5"
        );
    }

    #[test]
    fn weighted_book_selection_varies_black_defense_by_seed() {
        let mut game = Game::starting();
        apply(&mut game, "e2e4");

        assert_eq!(
            select_weighted_move(game.position(), 0)
                .expect("weighted book lookup")
                .expect("weighted book move")
                .to_uci(),
            "c7c6"
        );
        assert_eq!(
            select_weighted_move(game.position(), 13)
                .expect("weighted book lookup")
                .expect("weighted book move")
                .to_uci(),
            "c7c5"
        );
        assert_eq!(
            select_weighted_move(game.position(), 0)
                .expect("repeat weighted book lookup")
                .expect("repeat weighted book move")
                .to_uci(),
            "c7c6",
            "an explicit seed must remain reproducible"
        );
    }

    #[test]
    fn built_in_book_continues_sicilian_najdorf_for_black() {
        let mut game = Game::starting();
        for (white_move, black_move) in [
            ("e2e4", "c7c5"),
            ("g1f3", "d7d6"),
            ("d2d4", "c5d4"),
            ("f3d4", "g8f6"),
            ("b1c3", "a7a6"),
        ] {
            apply(&mut game, white_move);
            assert_eq!(
                select_move(game.position())
                    .expect("book lookup")
                    .expect("book move")
                    .to_uci(),
                black_move
            );
            apply(&mut game, black_move);
        }
    }

    #[test]
    fn built_in_book_covers_common_sicilian_second_moves() {
        for (white_second, black_reply) in [
            ("c2c3", "d7d5"),
            ("b1c3", "b8c6"),
            ("d2d4", "c5d4"),
        ] {
            let mut game = Game::starting();
            for move_text in ["e2e4", "c7c5", white_second] {
                apply(&mut game, move_text);
            }
            assert_eq!(
                select_move(game.position())
                    .expect("book lookup")
                    .expect("book move")
                    .to_uci(),
                black_reply
            );
        }
    }

    #[test]
    fn built_in_book_continues_white_ruy_lopez_line() {
        let mut game = Game::starting();
        for move_text in ["e2e4", "e7e5"] {
            apply(&mut game, move_text);
        }
        assert_eq!(
            select_move(game.position())
                .expect("book lookup")
                .expect("book move")
                .to_uci(),
            "g1f3"
        );
        apply(&mut game, "g1f3");
        apply(&mut game, "b8c6");
        assert_eq!(
            select_move(game.position())
                .expect("book lookup")
                .expect("book move")
                .to_uci(),
            "f1b5"
        );
    }

    #[test]
    fn built_in_book_miss_is_normal_after_uncovered_sicilian_position() {
        let mut game = Game::starting();
        for move_text in ["e2e4", "c7c5"] {
            apply(&mut game, move_text);
        }
        assert_eq!(select_move(game.position()).expect("book lookup"), None);
    }
}
