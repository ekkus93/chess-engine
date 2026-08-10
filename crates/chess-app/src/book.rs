use std::sync::OnceLock;

use chess_book::{BookSelector, IndexedBook, IndexedBookRecord};
use chess_core::{Color, Game, Move, Position, UciMove};

#[derive(Clone, Copy, Debug)]
struct OpeningLine {
    name: &'static str,
    side: Color,
    weight: u32,
    moves: &'static [&'static str],
}

static BUILT_IN_BOOK: OnceLock<Result<IndexedBook, String>> = OnceLock::new();

pub(crate) fn select_move(position: &Position) -> Result<Option<Move>, String> {
    let book = match BUILT_IN_BOOK.get_or_init(build_book) {
        Ok(book) => book,
        Err(message) => return Err(message.clone()),
    };
    let mut selector = BookSelector::deterministic_highest_weight();
    selector
        .select(book, position)
        .map(|candidate| candidate.map(|candidate| candidate.chess_move()))
        .map_err(|error| error.to_string())
}

fn build_book() -> Result<IndexedBook, String> {
    let mut records = Vec::new();
    for (line_index, line) in OPENING_LINES.iter().enumerate() {
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
                let metadata = u32::try_from(line_index).map_err(|_| {
                    "built-in opening book line index does not fit in metadata".to_owned()
                })?;
                let record = IndexedBookRecord::with_metadata(
                    game.position(),
                    parsed,
                    line.weight,
                    metadata,
                )
                .map_err(|error| {
                    format!(
                        "built-in opening book line {:?} could not index move {move_text:?}: {error}",
                        line.name
                    )
                })?;
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
    IndexedBook::from_records(records)
        .map_err(|error| format!("built-in opening book index is invalid: {error}"))
}

fn resolve_legal_move(game: &mut Game, parsed: UciMove) -> Result<Move, String> {
    let legal_moves = game
        .legal_moves()
        .map_err(|error| format!("legal move generation failed: {error}"))?;
    let mut matches = legal_moves
        .iter()
        .copied()
        .filter(|candidate| parsed.matches(*candidate));
    let Some(chess_move) = matches.next() else {
        return Err(format!("move {parsed} is not legal"));
    };
    if matches.next().is_some() {
        return Err(format!("move {parsed} resolved to multiple legal identities"));
    }
    Ok(chess_move)
}

fn upsert_record(records: &mut Vec<IndexedBookRecord>, record: IndexedBookRecord) {
    let existing = records.iter().position(|candidate| {
        candidate.position_key() == record.position_key()
            && candidate.uci_move() == record.uci_move()
    });
    match existing {
        Some(index) if record.weight() > records[index].weight() => records[index] = record,
        Some(_) => {}
        None => records.push(record),
    }
}

const OPENING_LINES: &[OpeningLine] = &[
    OpeningLine { name: "Italian Game", side: Color::White, weight: 85, moves: &["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"] },
    OpeningLine { name: "Ruy Lopez", side: Color::White, weight: 95, moves: &["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"] },
    OpeningLine { name: "Queen's Gambit", side: Color::White, weight: 90, moves: &["d2d4", "d7d5", "c2c4"] },
    OpeningLine { name: "London System", side: Color::White, weight: 65, moves: &["d2d4", "d7d5", "c2c4", "c7c6", "c1f4", "g8f6", "g1f3", "a7a6"] },
    OpeningLine { name: "Scotch Game", side: Color::White, weight: 75, moves: &["e2e4", "e7e5", "g1f3", "b8c6", "d2d4"] },
    OpeningLine { name: "King's Gambit", side: Color::White, weight: 70, moves: &["e2e4", "e7e5", "f2f4"] },
    OpeningLine { name: "Vienna Game", side: Color::White, weight: 55, moves: &["e2e4", "e7e5", "b1c3"] },
    OpeningLine { name: "English Opening", side: Color::White, weight: 60, moves: &["c2c4"] },
    OpeningLine { name: "Reti Opening", side: Color::White, weight: 50, moves: &["g1f3", "d7d5", "c2c4"] },
    OpeningLine { name: "Catalan Opening", side: Color::White, weight: 70, moves: &["d2d4", "d7d5", "c2c4", "e7e6", "g1f3", "g8f6", "g2g3"] },
    OpeningLine { name: "King's Gambit Accepted: King's Knight Gambit", side: Color::White, weight: 80, moves: &["e2e4", "e7e5", "f2f4", "e5f4", "g1f3"] },
    OpeningLine { name: "King's Gambit Accepted: Bishop's Gambit", side: Color::White, weight: 45, moves: &["e2e4", "e7e5", "f2f4", "e5f4", "f1c4"] },
    OpeningLine { name: "King's Gambit Accepted: Classical Defense", side: Color::White, weight: 60, moves: &["e2e4", "e7e5", "f2f4", "e5f4", "g1f3", "g8f6", "f1c4", "f8c5"] },
    OpeningLine { name: "King's Gambit Accepted: Fischer Defense", side: Color::White, weight: 50, moves: &["e2e4", "e7e5", "f2f4", "e5f4", "g1f3", "d7d5"] },
    OpeningLine { name: "King's Gambit Declined: Classical", side: Color::White, weight: 55, moves: &["e2e4", "e7e5", "f2f4", "f8c5", "g1f3"] },
    OpeningLine { name: "King's Gambit Declined: Falkbeer Countergambit", side: Color::White, weight: 40, moves: &["e2e4", "e7e5", "f2f4", "d7d5", "e4d5"] },
    OpeningLine { name: "Sicilian Defense", side: Color::Black, weight: 100, moves: &["e2e4", "c7c5"] },
    OpeningLine { name: "French Defense", side: Color::Black, weight: 85, moves: &["e2e4", "e7e6"] },
    OpeningLine { name: "Caro-Kann Defense", side: Color::Black, weight: 80, moves: &["e2e4", "c7c6"] },
    OpeningLine { name: "Open Game", side: Color::Black, weight: 75, moves: &["e2e4", "e7e5"] },
    OpeningLine { name: "Scandinavian Defense", side: Color::Black, weight: 50, moves: &["e2e4", "d7d5"] },
    OpeningLine { name: "Pirc Defense", side: Color::Black, weight: 55, moves: &["e2e4", "d7d6", "d2d4", "g8f6", "g1f3"] },
    OpeningLine { name: "Queen's Gambit Declined", side: Color::Black, weight: 95, moves: &["d2d4", "d7d5", "c2c4", "e7e6"] },
    OpeningLine { name: "Slav Defense", side: Color::Black, weight: 90, moves: &["d2d4", "d7d5", "c2c4", "c7c6"] },
    OpeningLine { name: "King's Indian Defense", side: Color::Black, weight: 85, moves: &["d2d4", "g8f6", "c2c4", "g7g6"] },
    OpeningLine { name: "Nimzo-Indian Defense", side: Color::Black, weight: 80, moves: &["d2d4", "g8f6", "c2c4", "e7e6", "b1c3", "f8b4"] },
];

#[cfg(test)]
mod tests {
    use chess_core::{Game, UciMove};

    use super::{resolve_legal_move, select_move};

    fn apply(game: &mut Game, move_text: &str) {
        let parsed = move_text.parse::<UciMove>().expect("test UCI move");
        let chess_move = resolve_legal_move(game, parsed).expect("test legal move");
        game.make_move(chess_move).expect("test move applies");
    }

    #[test]
    fn built_in_book_selects_highest_weight_white_opening() {
        let game = Game::starting();
        assert_eq!(select_move(game.position()).expect("book lookup").expect("book move").to_uci(), "e2e4");
    }

    #[test]
    fn built_in_book_selects_sicilian_after_e2e4() {
        let mut game = Game::starting();
        apply(&mut game, "e2e4");
        assert_eq!(select_move(game.position()).expect("book lookup").expect("book move").to_uci(), "c7c5");
    }

    #[test]
    fn built_in_book_continues_white_ruy_lopez_line() {
        let mut game = Game::starting();
        for move_text in ["e2e4", "e7e5"] { apply(&mut game, move_text); }
        assert_eq!(select_move(game.position()).expect("book lookup").expect("book move").to_uci(), "g1f3");
        apply(&mut game, "g1f3");
        apply(&mut game, "b8c6");
        assert_eq!(select_move(game.position()).expect("book lookup").expect("book move").to_uci(), "f1b5");
    }

    #[test]
    fn built_in_book_miss_is_normal_after_uncovered_sicilian_position() {
        let mut game = Game::starting();
        for move_text in ["e2e4", "c7c5"] { apply(&mut game, move_text); }
        assert_eq!(select_move(game.position()).expect("book lookup"), None);
    }
}
