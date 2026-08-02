use crate::{Color, LegalMoveError, Move, MoveKind, Piece, PieceKind, Position, Square};

fn square(value: &str) -> Square {
    value.parse().expect("test square is valid")
}

fn legal_move(position: &mut Position, uci: &str) -> Move {
    position
        .legal_moves()
        .expect("legal moves")
        .iter()
        .find(|current| current.to_uci() == uci)
        .unwrap_or_else(|| panic!("expected legal move {uci}"))
}

fn assert_round_trip(fen: &str, uci: &str, expected_kind: MoveKind) {
    let mut position = Position::from_fen(fen).expect("valid FEN");
    let snapshot = position.clone();
    let current = legal_move(&mut position, uci);
    assert_eq!(current.kind(), expected_kind);

    let undo = position.make_move(current).expect("checked move succeeds");
    assert_eq!(undo.move_made(), current);
    position
        .validate_invariants()
        .expect("post-move invariants");
    position.unmake_move(undo).expect("unmake succeeds");
    position
        .validate_invariants()
        .expect("restored invariants");
    assert_eq!(position, snapshot, "{uci} did not restore exactly");
}

#[test]
fn every_move_category_round_trips_exactly() {
    let start = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
    let fixtures = [
        (start, "g1f3", MoveKind::Quiet),
        (start, "e2e4", MoveKind::DoublePawnPush),
        ("7k/8/8/8/4p3/3P4/8/7K w - - 0 1", "d3e4", MoveKind::Capture),
        ("7k/8/8/3pP3/8/8/8/7K w - d6 0 1", "e5d6", MoveKind::EnPassant),
        ("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1", "e1g1", MoveKind::KingCastle),
        ("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1", "e1c1", MoveKind::QueenCastle),
        ("7k/P7/8/8/8/8/8/7K w - - 0 1", "a7a8n", MoveKind::KnightPromotion),
        ("7k/P7/8/8/8/8/8/7K w - - 0 1", "a7a8b", MoveKind::BishopPromotion),
        ("7k/P7/8/8/8/8/8/7K w - - 0 1", "a7a8r", MoveKind::RookPromotion),
        ("7k/P7/8/8/8/8/8/7K w - - 0 1", "a7a8q", MoveKind::QueenPromotion),
        (
            "1r5k/P7/8/8/8/8/8/7K w - - 0 1",
            "a7b8n",
            MoveKind::KnightPromotionCapture,
        ),
        (
            "1r5k/P7/8/8/8/8/8/7K w - - 0 1",
            "a7b8b",
            MoveKind::BishopPromotionCapture,
        ),
        (
            "1r5k/P7/8/8/8/8/8/7K w - - 0 1",
            "a7b8r",
            MoveKind::RookPromotionCapture,
        ),
        (
            "1r5k/P7/8/8/8/8/8/7K w - - 0 1",
            "a7b8q",
            MoveKind::QueenPromotionCapture,
        ),
        ("r3k3/8/8/8/8/8/8/R6K w q - 0 1", "a1a8", MoveKind::Capture),
    ];

    for (fen, uci, kind) in fixtures {
        assert_round_trip(fen, uci, kind);
    }
}

#[test]
fn checked_application_rejects_illegal_move_without_mutation() {
    let mut position = Position::starting();
    let snapshot = position.clone();
    let illegal = Move::new(square("e2"), square("e5"), MoveKind::Quiet);

    assert_eq!(
        position.make_move(illegal),
        Err(LegalMoveError::IllegalMove { current: illegal })
    );
    assert_eq!(position, snapshot);
    position.validate_invariants().expect("invariants preserved");
}

#[test]
fn move_application_updates_side_clocks_and_en_passant_exactly() {
    let mut white = Position::starting();
    let white_snapshot = white.clone();
    let double = legal_move(&mut white, "e2e4");
    let undo = white.make_move(double).expect("white double push");
    assert_eq!(white.side_to_move(), Color::Black);
    assert_eq!(white.en_passant(), Some(square("e3")));
    assert_eq!(white.halfmove_clock().get(), 0);
    assert_eq!(white.fullmove_number().get(), 1);
    white.unmake_move(undo).expect("unmake white move");
    assert_eq!(white, white_snapshot);

    let mut black = Position::from_fen("7k/8/8/8/8/8/8/K7 b - - 17 23").expect("valid FEN");
    let black_snapshot = black.clone();
    let quiet = legal_move(&mut black, "h8g8");
    let undo = black.make_move(quiet).expect("black quiet move");
    assert_eq!(black.side_to_move(), Color::White);
    assert_eq!(black.en_passant(), None);
    assert_eq!(black.halfmove_clock().get(), 18);
    assert_eq!(black.fullmove_number().get(), 24);
    black.unmake_move(undo).expect("unmake black move");
    assert_eq!(black, black_snapshot);
}

#[test]
fn capture_token_records_exact_piece_and_square() {
    let mut position =
        Position::from_fen("7k/8/8/8/4p3/3P4/8/7K w - - 9 12").expect("valid FEN");
    let current = legal_move(&mut position, "d3e4");
    let undo = position.make_move(current).expect("capture succeeds");

    assert_eq!(undo.move_made(), current);
    assert_eq!(
        undo.captured(),
        Some((square("e4"), Piece::new(Color::Black, PieceKind::Pawn)))
    );
    assert_eq!(position.halfmove_clock().get(), 0);
    position.unmake_move(undo).expect("capture unmake succeeds");
}

#[test]
fn mismatched_undo_is_rejected_before_mutation() {
    let mut position = Position::starting();
    let white_move = legal_move(&mut position, "e2e4");
    let white_undo = position.make_move(white_move).expect("white move");
    let black_move = legal_move(&mut position, "e7e5");
    let black_undo = position.make_move(black_move).expect("black move");
    let snapshot = position.clone();

    assert_eq!(
        position.unmake_move(white_undo),
        Err(LegalMoveError::UndoStateMismatch {
            current: white_move,
        })
    );
    assert_eq!(position, snapshot);
    position.validate_invariants().expect("invariants preserved");

    position
        .unmake_move(black_undo)
        .expect("top undo still succeeds");
}

#[test]
fn counter_overflow_failures_do_not_mutate() {
    let mut halfmove =
        Position::from_fen("7k/8/8/8/8/8/8/K7 w - - 65535 1").expect("valid FEN");
    let halfmove_snapshot = halfmove.clone();
    let quiet = Move::new(square("a1"), square("b1"), MoveKind::Quiet);
    assert_eq!(
        halfmove.make_move(quiet),
        Err(LegalMoveError::HalfmoveClockOverflow)
    );
    assert_eq!(halfmove, halfmove_snapshot);

    let mut fullmove =
        Position::from_fen("7k/8/8/8/8/8/8/K7 b - - 0 65535").expect("valid FEN");
    let fullmove_snapshot = fullmove.clone();
    let quiet = Move::new(square("h8"), square("g8"), MoveKind::Quiet);
    assert_eq!(
        fullmove.make_move(quiet),
        Err(LegalMoveError::FullmoveNumberOverflow)
    );
    assert_eq!(fullmove, fullmove_snapshot);
}

#[test]
fn every_legal_move_in_curated_positions_restores_exactly() {
    let fixtures = [
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 4 17",
        "7k/8/8/3pP3/8/8/8/7K w - d6 8 31",
        "1r5k/P7/8/8/8/8/8/7K w - - 12 44",
        "4r1k1/8/8/8/8/8/4R3/4K3 w - - 3 9",
    ];

    for fen in fixtures {
        let mut position = Position::from_fen(fen).expect("valid FEN");
        let baseline = position.clone();
        let moves: Vec<_> = position
            .legal_moves()
            .expect("legal moves")
            .iter()
            .collect();
        for current in moves {
            let snapshot = position.clone();
            let undo = position
                .make_generated_legal_move(current)
                .expect("generated move succeeds");
            position.validate_invariants().expect("post-move invariants");
            position
                .unmake_generated_legal_move(undo)
                .expect("generated unmake succeeds");
            assert_eq!(position, snapshot, "{} from {fen}", current.to_uci());
        }
        assert_eq!(position, baseline);
    }
}

#[derive(Clone, Copy)]
struct DeterministicRng(u64);

impl DeterministicRng {
    fn next(&mut self) -> u64 {
        self.0 = self
            .0
            .wrapping_mul(6_364_136_223_846_793_005)
            .wrapping_add(1_442_695_040_888_963_407);
        self.0
    }
}

#[test]
fn deterministic_random_legal_sequences_restore_exactly() {
    for seed in [1, 2, 3, 5, 8, 13, 21, 34] {
        let mut position = Position::starting();
        let baseline = position.clone();
        let mut rng = DeterministicRng(seed);
        let mut history = Vec::new();

        for _ in 0..128 {
            let moves = position.legal_moves().expect("legal moves");
            if moves.is_empty() {
                break;
            }
            let index = (rng.next() % moves.len() as u64) as usize;
            let current = moves
                .iter()
                .nth(index)
                .expect("selected move index is in range");
            let undo = position
                .make_generated_legal_move(current)
                .expect("generated move succeeds");
            position.validate_invariants().expect("playout invariants");
            history.push(undo);
        }

        assert!(!history.is_empty());
        while let Some(undo) = history.pop() {
            position
                .unmake_generated_legal_move(undo)
                .expect("reverse playout succeeds");
            position.validate_invariants().expect("reverse invariants");
        }
        assert_eq!(position, baseline, "seed {seed} did not restore");
    }
}
