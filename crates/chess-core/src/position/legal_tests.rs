use crate::{Move, MoveKind, PieceKind, Position, Square};

use super::LegalMoveError;

fn square(value: &str) -> Square {
    value.parse().expect("test square is valid")
}

fn legal_uci(position: &mut Position) -> Result<Vec<String>, LegalMoveError> {
    Ok(position.legal_moves()?.iter().map(Move::to_uci).collect())
}

#[test]
fn starting_position_perft_and_divide_are_exact_and_restore_state() {
    let mut position = Position::starting();
    let snapshot = position.clone();
    assert_eq!(position.legal_moves().expect("legal moves").len(), 20);
    assert_eq!(position, snapshot);

    for (depth, expected) in [(1, 20), (2, 400), (3, 8_902), (4, 197_281)] {
        assert_eq!(position.perft(depth).expect("perft succeeds"), expected);
        assert_eq!(position, snapshot, "depth {depth} restored position");
        position.validate_invariants().expect("restored invariants");
    }

    let divide = position.divide(2).expect("divide succeeds");
    assert_eq!(divide.len(), 20);
    assert!(divide.iter().all(|(_, nodes)| *nodes == 20));
    assert_eq!(divide.iter().map(|(_, nodes)| nodes).sum::<u64>(), 400);
    assert_eq!(position, snapshot);
}

#[test]
fn single_check_allows_capture_block_and_king_evasions() {
    let mut capture = Position::from_fen("6k1/8/8/8/8/5n2/6P1/4K3 w - - 0 1").expect("valid FEN");
    assert!(capture
        .legal_moves()
        .expect("legal moves")
        .iter()
        .any(|current| current.to_uci() == "g2f3" && current.kind() == MoveKind::Capture));

    let mut block = Position::from_fen("4r1k1/8/8/8/8/8/8/2B1K3 w - - 0 1").expect("valid FEN");
    let moves = block.legal_moves().expect("legal moves");
    assert!(moves.iter().any(|current| current.to_uci() == "c1e3"));
    assert!(moves.iter().any(|current| current.source() == square("e1")));
}

#[test]
fn double_check_allows_only_king_moves() {
    let mut position = Position::from_fen("4r1k1/8/8/8/1b6/8/8/4K3 w - - 0 1").expect("valid FEN");
    let moves = position.legal_moves().expect("legal moves");
    assert!(!moves.is_empty());
    assert!(moves.iter().all(|current| current.source() == square("e1")));
}

#[test]
fn absolute_pins_restrict_moves_to_the_pin_line() {
    let mut position = Position::from_fen("4r1k1/8/8/8/8/8/4R3/4K3 w - - 0 1").expect("valid FEN");
    let pinned_moves: Vec<_> = position
        .legal_moves()
        .expect("legal moves")
        .iter()
        .filter(|current| current.source() == square("e2"))
        .collect();
    assert!(!pinned_moves.is_empty());
    assert!(pinned_moves
        .iter()
        .all(|current| current.destination().file() == square("e1").file()));
    assert!(!pinned_moves
        .iter()
        .any(|current| current.destination() == square("d2")));
}

#[test]
fn king_moves_into_attack_and_king_captures_are_rejected() {
    let mut checked = Position::from_fen("4r1k1/8/8/8/8/8/8/4K3 w - - 0 1").expect("valid FEN");
    assert!(!checked
        .legal_moves()
        .expect("legal moves")
        .iter()
        .any(|current| current.destination() == square("e2")));

    let mut adjacent = Position::from_fen("8/8/8/8/8/8/4k3/4K3 w - - 0 1").expect("valid FEN");
    assert!(!adjacent
        .legal_moves()
        .expect("legal moves")
        .iter()
        .any(|current| current.destination() == square("e2")));
}

#[test]
fn all_four_castles_are_legal_when_every_condition_is_satisfied() {
    let mut white = Position::from_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1").expect("valid FEN");
    let white_moves = legal_uci(&mut white).expect("legal moves");
    assert!(white_moves.contains(&"e1g1".to_owned()));
    assert!(white_moves.contains(&"e1c1".to_owned()));

    let mut black = Position::from_fen("r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1").expect("valid FEN");
    let black_moves = legal_uci(&mut black).expect("legal moves");
    assert!(black_moves.contains(&"e8g8".to_owned()));
    assert!(black_moves.contains(&"e8c8".to_owned()));
}

#[test]
fn castling_rejects_check_transit_destination_and_lost_rights() {
    let fixtures = [
        ("4r2k/8/8/8/8/8/8/R3K2R w KQ - 0 1", "e1g1"),
        ("5r1k/8/8/8/8/8/8/R3K2R w KQ - 0 1", "e1g1"),
        ("6rk/8/8/8/8/8/8/R3K2R w KQ - 0 1", "e1g1"),
        ("7k/8/8/8/8/8/8/R2rK2R w KQ - 0 1", "e1g1"),
        ("7k/8/8/8/8/8/8/R3K2R w - - 0 1", "e1g1"),
    ];
    for (fen, forbidden) in fixtures {
        let mut position = Position::from_fen(fen).expect("valid FEN");
        assert!(
            !legal_uci(&mut position)
                .expect("legal moves")
                .contains(&forbidden.to_owned()),
            "{fen} generated {forbidden}"
        );
    }
}

#[test]
fn en_passant_requires_captured_pawn_and_preserves_king_safety() {
    let mut valid = Position::from_fen("7k/8/8/3pP3/8/8/8/7K w - d6 0 1").expect("valid FEN");
    assert!(legal_uci(&mut valid)
        .expect("legal moves")
        .contains(&"e5d6".to_owned()));

    let mut missing = Position::from_fen("7k/8/8/4P3/8/8/8/7K w - d6 0 1").expect("valid FEN");
    assert!(!legal_uci(&mut missing)
        .expect("legal moves")
        .contains(&"e5d6".to_owned()));

    let mut horizontal = Position::from_fen("7k/8/8/r4pPK/8/8/8/8 w - f6 0 1").expect("valid FEN");
    assert!(!legal_uci(&mut horizontal)
        .expect("legal moves")
        .contains(&"g5f6".to_owned()));

    let mut diagonal = Position::from_fen("7b/8/8/3pP3/8/8/1K6/7k w - d6 0 1").expect("valid FEN");
    assert!(!legal_uci(&mut diagonal)
        .expect("legal moves")
        .contains(&"e5d6".to_owned()));
}

#[test]
fn en_passant_target_expires_and_double_push_creates_one() {
    let mut position = Position::from_fen("7k/8/8/3pP3/8/8/8/7K w - d6 0 1").expect("valid FEN");
    let snapshot = position.clone();
    let quiet = Move::new(square("h1"), square("g1"), MoveKind::Quiet);
    let undo = position
        .make_generated_move(quiet)
        .expect("generated quiet move");
    assert_eq!(position.en_passant(), None);
    position
        .unmake_generated_move(quiet, undo)
        .expect("unmake quiet move");
    assert_eq!(position, snapshot);

    let mut start = Position::starting();
    let double = Move::new(square("e2"), square("e4"), MoveKind::DoublePawnPush);
    let undo = start
        .make_generated_move(double)
        .expect("generated double push");
    assert_eq!(start.en_passant(), Some(square("e3")));
    start
        .unmake_generated_move(double, undo)
        .expect("unmake double push");
    assert_eq!(start, Position::starting());
}

#[test]
fn promotions_remain_explicit_and_invalid_flags_are_rejected() {
    let mut position = Position::from_fen("1r5k/P7/8/8/8/8/8/7K w - - 0 1").expect("valid FEN");
    let promotions: Vec<_> = position
        .legal_moves()
        .expect("legal moves")
        .iter()
        .filter(|current| current.source() == square("a7"))
        .collect();
    assert_eq!(promotions.len(), 8);
    assert!(promotions
        .iter()
        .all(|current| current.promotion().is_some()));
    for kind in [
        PieceKind::Knight,
        PieceKind::Bishop,
        PieceKind::Rook,
        PieceKind::Queen,
    ] {
        assert_eq!(
            promotions
                .iter()
                .filter(|current| current.promotion() == Some(kind))
                .count(),
            2
        );
    }

    let invalid_non_pawn = Move::new(square("h1"), square("h2"), MoveKind::QueenPromotion);
    assert!(!position
        .is_legal_move(invalid_non_pawn)
        .expect("legal query succeeds"));

    let mut start = Position::starting();
    let invalid_rank = Move::new(square("a2"), square("a3"), MoveKind::QueenPromotion);
    assert!(!start
        .is_legal_move(invalid_rank)
        .expect("legal query succeeds"));
}
