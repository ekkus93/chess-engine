use chess_book::{
    BookSelectionError, BookSelector, IndexedBook, IndexedBookError, IndexedBookQueryError,
    IndexedBookRecord,
};
use chess_core::{Position, UciMove};

const FORMAT_VERSION_OFFSET: usize = 8;

fn record(position: &Position, uci_move: &str, weight: u32) -> IndexedBookRecord {
    IndexedBookRecord::new(
        position,
        uci_move
            .parse::<UciMove>()
            .expect("test UCI syntax is valid"),
        weight,
    )
    .expect("test position key is valid")
}

fn book(records: Vec<IndexedBookRecord>) -> IndexedBook {
    IndexedBook::from_records(records).expect("test records are unique")
}

fn selected_uci(
    selector: &mut BookSelector,
    opening_book: &IndexedBook,
    position: &Position,
) -> String {
    selector
        .select(opening_book, position)
        .expect("book selection succeeds")
        .expect("test book has a position entry")
        .chess_move()
        .to_uci()
}

#[test]
fn invalid_move_is_rejected_from_indexed_book() {
    let position = Position::starting();
    let illegal_move = "e2e5"
        .parse::<UciMove>()
        .expect("test UCI syntax is valid");
    let opening_book = book(vec![
        IndexedBookRecord::new(&position, illegal_move, 100)
            .expect("syntax-valid record construction succeeds"),
    ]);
    let mut selector = BookSelector::deterministic_highest_weight();

    assert_eq!(
        selector.select(&opening_book, &position),
        Err(BookSelectionError::Book(
            IndexedBookQueryError::IllegalMove {
                uci_move: illegal_move,
            },
        )),
    );
}

#[test]
fn equal_weight_ties_use_ascending_uci_order() {
    let position = Position::starting();
    let opening_book = book(vec![
        record(&position, "e2e4", 50),
        record(&position, "d2d4", 50),
        record(&position, "g1f3", 25),
    ]);
    let mut selector = BookSelector::deterministic_highest_weight();

    assert_eq!(
        selected_uci(&mut selector, &opening_book, &position),
        "d2d4",
    );
}

#[test]
fn same_seed_reproduces_weighted_selection_sequence() {
    let position = Position::starting();
    let opening_book = book(vec![
        record(&position, "b1c3", 2),
        record(&position, "d2d4", 5),
        record(&position, "e2e4", 11),
        record(&position, "g1f3", 3),
    ]);
    let seed = 0x19_05_c0ff_ee12_3456;
    let mut first = BookSelector::weighted_random(seed);
    let mut second = BookSelector::weighted_random(seed);

    let first_sequence = (0..64)
        .map(|_| selected_uci(&mut first, &opening_book, &position))
        .collect::<Vec<_>>();
    let second_sequence = (0..64)
        .map(|_| selected_uci(&mut second, &opening_book, &position))
        .collect::<Vec<_>>();

    assert_eq!(first_sequence, second_sequence);
    assert_eq!(first.seed(), Some(seed));
    assert_eq!(second.seed(), Some(seed));
}

#[test]
fn corrupt_and_unsupported_data_are_typed_errors() {
    let position = Position::starting();
    let opening_book = book(vec![record(&position, "e2e4", 100)]);

    let mut unsupported = opening_book.to_bytes();
    unsupported[FORMAT_VERSION_OFFSET..FORMAT_VERSION_OFFSET + 2]
        .copy_from_slice(&2_u16.to_le_bytes());
    assert_eq!(
        IndexedBook::from_bytes(&unsupported),
        Err(IndexedBookError::UnsupportedFormatVersion { found: 2 }),
    );

    let mut corrupt = opening_book.to_bytes();
    *corrupt
        .last_mut()
        .expect("one-record book has a payload byte") ^= 0x80;
    assert!(matches!(
        IndexedBook::from_bytes(&corrupt),
        Err(IndexedBookError::PayloadChecksumMismatch { .. }),
    ));
}
