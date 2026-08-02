use core::mem::size_of;

use crate::{Move, MoveKind, PieceKind, Position, Square};

use super::{MoveList, MAX_PSEUDO_LEGAL_MOVES};

fn square(value: &str) -> Square {
    value.parse().expect("test square is valid")
}

fn moves_from(position: &Position, source: &str) -> Vec<Move> {
    let source = square(source);
    position
        .pseudo_legal_moves()
        .expect("fixture does not exceed move-list capacity")
        .iter()
        .filter(|current| current.source() == source)
        .collect()
}

#[test]
fn starting_position_has_twenty_moves_in_deterministic_order() {
    let position = Position::starting();
    let moves = position
        .pseudo_legal_moves()
        .expect("starting position fits move list");
    let actual: Vec<_> = moves
        .iter()
        .map(|current| (current.to_uci(), current.kind()))
        .collect();
    let expected = [
        ("a2a3", MoveKind::Quiet),
        ("a2a4", MoveKind::DoublePawnPush),
        ("b2b3", MoveKind::Quiet),
        ("b2b4", MoveKind::DoublePawnPush),
        ("c2c3", MoveKind::Quiet),
        ("c2c4", MoveKind::DoublePawnPush),
        ("d2d3", MoveKind::Quiet),
        ("d2d4", MoveKind::DoublePawnPush),
        ("e2e3", MoveKind::Quiet),
        ("e2e4", MoveKind::DoublePawnPush),
        ("f2f3", MoveKind::Quiet),
        ("f2f4", MoveKind::DoublePawnPush),
        ("g2g3", MoveKind::Quiet),
        ("g2g4", MoveKind::DoublePawnPush),
        ("h2h3", MoveKind::Quiet),
        ("h2h4", MoveKind::DoublePawnPush),
        ("b1a3", MoveKind::Quiet),
        ("b1c3", MoveKind::Quiet),
        ("g1f3", MoveKind::Quiet),
        ("g1h3", MoveKind::Quiet),
    ];
    assert_eq!(moves.len(), 20);
    assert_eq!(
        actual,
        expected
            .into_iter()
            .map(|(uci, kind)| (uci.to_owned(), kind))
            .collect::<Vec<_>>()
    );
}

#[test]
fn quiet_and_capture_promotions_preserve_all_underpromotion_identities() {
    let position = Position::from_fen("1r5k/P7/8/8/8/8/8/7K w - - 0 1").expect("valid FEN");
    let moves = moves_from(&position, "a7");
    let actual: Vec<_> = moves
        .iter()
        .map(|current| (current.to_uci(), current.kind(), current.promotion()))
        .collect();
    let expected = [
        ("a7a8n", MoveKind::KnightPromotion, PieceKind::Knight),
        ("a7a8b", MoveKind::BishopPromotion, PieceKind::Bishop),
        ("a7a8r", MoveKind::RookPromotion, PieceKind::Rook),
        ("a7a8q", MoveKind::QueenPromotion, PieceKind::Queen),
        ("a7b8n", MoveKind::KnightPromotionCapture, PieceKind::Knight),
        ("a7b8b", MoveKind::BishopPromotionCapture, PieceKind::Bishop),
        ("a7b8r", MoveKind::RookPromotionCapture, PieceKind::Rook),
        ("a7b8q", MoveKind::QueenPromotionCapture, PieceKind::Queen),
    ];
    assert_eq!(moves.len(), 8);
    assert_eq!(
        actual,
        expected
            .into_iter()
            .map(|(uci, kind, promotion)| (uci.to_owned(), kind, Some(promotion)))
            .collect::<Vec<_>>()
    );
}

#[test]
fn edge_pawns_and_knights_do_not_wrap() {
    let position = Position::from_fen("7k/8/8/8/8/8/P7/N6K w - - 0 1").expect("valid FEN");
    let pawn: Vec<_> = moves_from(&position, "a2")
        .into_iter()
        .map(Move::to_uci)
        .collect();
    let knight: Vec<_> = moves_from(&position, "a1")
        .into_iter()
        .map(Move::to_uci)
        .collect();
    assert_eq!(pawn, ["a2a3", "a2a4"]);
    assert_eq!(knight, ["a1b3", "a1c2"]);
}

#[test]
fn sliding_generation_stops_at_own_and_enemy_blockers() {
    let position =
        Position::from_fen("7k/8/3r4/3P4/1p1Q1B2/3p4/8/7K w - - 0 1").expect("valid FEN");
    let moves = moves_from(&position, "d4");
    let destinations: Vec<_> = moves.iter().map(|current| current.destination()).collect();

    assert!(!destinations.contains(&square("d5")));
    assert!(!destinations.contains(&square("f4")));
    assert!(destinations.contains(&square("d3")));
    assert!(destinations.contains(&square("b4")));
    assert!(!destinations.contains(&square("d2")));
    assert!(!destinations.contains(&square("a4")));
    assert_eq!(
        moves
            .iter()
            .find(|current| current.destination() == square("d3"))
            .map(|current| current.kind()),
        Some(MoveKind::Capture)
    );
}

#[test]
fn en_passant_candidate_uses_target_geometry_without_legal_validation() {
    let position = Position::from_fen("7k/8/8/3pP3/8/8/8/7K w - d6 0 1").expect("valid FEN");
    let moves = moves_from(&position, "e5");
    assert!(moves.iter().any(|current| {
        current.destination() == square("d6") && current.kind() == MoveKind::EnPassant
    }));
}

#[test]
fn castling_candidates_require_rights_pieces_and_empty_paths_but_not_safety() {
    let open = Position::from_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1").expect("valid FEN");
    let castles: Vec<_> = open
        .pseudo_legal_moves()
        .expect("fixture fits")
        .iter()
        .filter(|current| matches!(current.kind(), MoveKind::KingCastle | MoveKind::QueenCastle))
        .map(|current| (current.to_uci(), current.kind()))
        .collect();
    assert_eq!(
        castles,
        [
            ("e1g1".to_owned(), MoveKind::KingCastle),
            ("e1c1".to_owned(), MoveKind::QueenCastle),
        ]
    );

    let attacked = Position::from_fen("5r1k/8/8/8/8/8/8/R3K2R w KQ - 0 1").expect("valid FEN");
    assert!(attacked
        .pseudo_legal_moves()
        .expect("fixture fits")
        .iter()
        .any(|current| current.kind() == MoveKind::KingCastle));

    let missing_rook = Position::from_fen("7k/8/8/8/8/8/8/R3K3 w KQ - 0 1").expect("valid FEN");
    assert!(!missing_rook
        .pseudo_legal_moves()
        .expect("fixture fits")
        .iter()
        .any(|current| current.kind() == MoveKind::KingCastle));
}

#[test]
fn move_list_is_fixed_capacity_stack_storage() {
    let list = MoveList::new();
    assert!(list.is_empty());
    assert_eq!(list.len(), 0);
    assert_eq!(list.get(0), None);
    assert_eq!(MAX_PSEUDO_LEGAL_MOVES, 256);
    assert!(size_of::<MoveList>() <= 2048);
}
