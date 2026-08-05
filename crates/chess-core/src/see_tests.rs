use crate::{Move, MoveKind, PieceKind, Position, UciMove};

use super::{
    exchange_gain, static_exchange_evaluation, static_exchange_piece_value,
    static_exchange_semantic_checksum, SeeBoard, StaticExchangeClass, StaticExchangeError,
    StaticExchangeMoveStateError, StaticExchangeValue, MAX_STATIC_EXCHANGE_PLIES,
    STATIC_EXCHANGE_POLICY_ID, STATIC_EXCHANGE_SCHEMA_VERSION,
};

fn resolve_legal_move(position: &mut Position, value: &str) -> Move {
    let parsed = value.parse::<UciMove>().expect("fixture UCI move parses");
    position
        .legal_moves()
        .expect("fixture legal moves generate")
        .iter()
        .find(|current| parsed.matches(*current))
        .unwrap_or_else(|| panic!("fixture move {value} is legal"))
}

fn evaluate_fixture(fen: &str, uci: &str) -> StaticExchangeValue {
    let mut position = Position::from_fen(fen).expect("fixture FEN parses");
    let current = resolve_legal_move(&mut position, uci);
    let root = position.clone();
    let value = static_exchange_evaluation(&position, current).expect("fixture SEE succeeds");
    assert_eq!(position, root, "SEE mutated the caller's position");
    assert_eq!(
        position.zobrist(),
        position.recomputed_zobrist(),
        "SEE changed the caller's incremental hash"
    );
    value
}

fn oracle_immediate_gain(position: &Position, current: Move) -> i32 {
    let moving = position
        .piece_at(current.source())
        .expect("oracle move source contains a piece");
    let captured = if current.kind() == MoveKind::EnPassant {
        static_exchange_piece_value(PieceKind::Pawn)
    } else if current.kind().is_capture() {
        static_exchange_piece_value(
            position
                .piece_at(current.destination())
                .expect("oracle capture target contains a piece")
                .kind,
        )
    } else {
        0
    };
    let resulting = current.promotion().unwrap_or(moving.kind);
    captured + static_exchange_piece_value(resulting) - static_exchange_piece_value(moving.kind)
}

fn oracle_response(position: &mut Position, target: crate::Square, ply: u8) -> i32 {
    assert!(
        ply < MAX_STATIC_EXCHANGE_PLIES,
        "legal exchange oracle exceeded fixed capacity"
    );
    let moves = position
        .legal_moves()
        .expect("oracle legal move generation succeeds");
    let mut least = None;
    for current in moves.iter() {
        if current.destination() != target || !current.kind().is_capture() {
            continue;
        }
        let attacker = position
            .piece_at(current.source())
            .expect("oracle legal capture has a source piece");
        let key = (
            static_exchange_piece_value(attacker.kind),
            current.source().index(),
        );
        least = Some(least.map_or(key, |previous: (i32, u8)| previous.min(key)));
    }
    let Some((_, selected_source)) = least else {
        return 0;
    };

    let mut best = None;
    for current in moves.iter() {
        if current.source().index() != selected_source
            || current.destination() != target
            || !current.kind().is_capture()
        {
            continue;
        }
        let immediate = oracle_immediate_gain(position, current);
        let undo = position
            .make_move(current)
            .expect("oracle legal recapture applies");
        let response = oracle_response(position, target, ply + 1);
        position
            .unmake_move(undo)
            .expect("oracle legal recapture restores");
        let current_gain = immediate - response;
        best = Some(best.map_or(current_gain, |previous: i32| previous.max(current_gain)));
    }
    best.unwrap_or_default().max(0)
}

fn oracle_static_exchange(position: &Position, current: Move) -> i32 {
    let mut working = position.clone();
    let root = working.clone();
    assert!(
        working
            .legal_moves()
            .expect("oracle root legal moves generate")
            .iter()
            .any(|candidate| candidate == current),
        "oracle root move {} must be legal",
        current.to_uci()
    );
    let immediate = oracle_immediate_gain(&working, current);
    let target = current.destination();
    let undo = working
        .make_move(current)
        .expect("oracle root move applies");
    let response = oracle_response(&mut working, target, 0);
    working
        .unmake_move(undo)
        .expect("oracle root move restores");
    assert_eq!(working, root, "oracle did not restore its root");
    immediate - response
}

fn compare_fixture_with_oracle(fen: &str, uci: &str) {
    let mut position = Position::from_fen(fen).expect("fixture FEN parses");
    let current = resolve_legal_move(&mut position, uci);
    let root = position.clone();
    let actual = static_exchange_evaluation(&position, current)
        .expect("production SEE succeeds")
        .centipawns();
    let expected = oracle_static_exchange(&position, current);
    assert_eq!(actual, expected, "{fen} {uci}");
    assert_eq!(position, root, "oracle comparison mutated fixture");
}

#[test]
fn stable_values_identity_and_classification_are_exact() {
    assert_eq!(STATIC_EXCHANGE_SCHEMA_VERSION, 1);
    assert_eq!(STATIC_EXCHANGE_POLICY_ID, 0x5345_4556_414c_3031);
    assert_eq!(
        PieceKind::ALL.map(static_exchange_piece_value),
        [100, 320, 330, 500, 900, 20_000]
    );
    assert_eq!(static_exchange_semantic_checksum(), 0x0367_2231_0488_6e8e);
    assert_eq!(
        StaticExchangeValue::from_centipawns(-1).class(),
        StaticExchangeClass::Losing
    );
    assert_eq!(
        StaticExchangeValue::from_centipawns(0).class(),
        StaticExchangeClass::Equal
    );
    assert_eq!(
        StaticExchangeValue::from_centipawns(1).class(),
        StaticExchangeClass::Winning
    );
}

#[test]
fn exact_basic_and_defended_capture_values_are_stable() {
    assert_eq!(
        evaluate_fixture("4k3/8/8/3p4/4P3/8/8/4K3 w - - 0 1", "e4d5").centipawns(),
        100
    );
    assert_eq!(
        evaluate_fixture("4k3/8/2p5/3p4/4P3/8/8/4K3 w - - 0 1", "e4d5").centipawns(),
        0
    );
    assert_eq!(
        evaluate_fixture("3r2k1/8/8/3p4/3Q4/8/8/4K3 w - - 0 1", "d4d5").centipawns(),
        -800
    );
}

#[test]
fn pinned_and_illegal_king_recaptures_are_excluded() {
    assert_eq!(
        evaluate_fixture("4k3/4n3/8/3p4/2P5/8/8/4R1K1 w - - 0 1", "c4d5").centipawns(),
        100
    );
    assert_eq!(
        evaluate_fixture("8/8/4k3/3p4/2P5/8/6B1/6K1 w - - 0 1", "c4d5").centipawns(),
        100
    );
}

#[test]
fn en_passant_removes_the_real_pawn_before_xray_recalculation() {
    assert_eq!(
        evaluate_fixture("3r2k1/8/8/3pP3/8/8/8/6K1 w - d6 0 1", "e5d6").centipawns(),
        0
    );
}

#[test]
fn quiet_and_capture_promotions_include_the_material_delta() {
    assert_eq!(
        evaluate_fixture("7k/P7/8/8/8/8/8/7K w - - 0 1", "a7a8q").centipawns(),
        800
    );
    let fen = "1r5k/P7/8/8/8/8/8/7K w - - 0 1";
    for (uci, expected) in [
        ("a7b8n", 720),
        ("a7b8b", 730),
        ("a7b8r", 900),
        ("a7b8q", 1_300),
    ] {
        assert_eq!(evaluate_fixture(fen, uci).centipawns(), expected, "{uci}");
    }
}

#[test]
fn color_symmetric_captures_have_identical_values() {
    let white = evaluate_fixture("4k3/8/8/3p4/4P3/8/8/4K3 w - - 0 1", "e4d5");
    let black = evaluate_fixture("4k3/8/8/8/3p4/4P3/8/4K3 b - - 0 1", "d4e3");
    assert_eq!(white, black);
}

#[test]
fn rook_and_bishop_xray_sequences_match_the_independent_legal_oracle() {
    compare_fixture_with_oracle("6k1/8/4p3/3p4/2B5/8/8/3R2K1 w - - 0 1", "c4d5");
    compare_fixture_with_oracle("6k1/2p5/3p4/5N2/8/6B1/8/6K1 w - - 0 1", "f5d6");
    compare_fixture_with_oracle("3r2k1/8/2p5/3p4/4PN2/8/8/3R2K1 w - - 0 1", "e4d5");
}

#[test]
fn malformed_exchange_inputs_fail_loudly_without_mutation() {
    let position =
        Position::from_fen("4k3/8/8/3p4/4P3/8/8/4K3 w - - 0 1").expect("fixture FEN parses");
    let root = position.clone();

    let quiet = Move::new(
        "e4".parse().expect("square"),
        "e5".parse().expect("square"),
        MoveKind::Quiet,
    );
    assert_eq!(
        static_exchange_evaluation(&position, quiet),
        Err(StaticExchangeError::NonExchangeMove { current: quiet })
    );

    let empty_source = Move::new(
        "a2".parse().expect("square"),
        "d5".parse().expect("square"),
        MoveKind::Capture,
    );
    assert_eq!(
        static_exchange_evaluation(&position, empty_source),
        Err(StaticExchangeMoveStateError::MissingSourcePiece {
            source: "a2".parse().expect("square")
        }
        .into())
    );

    let wrong_side_position =
        Position::from_fen("4k3/8/8/3p4/4P3/8/8/4K3 b - - 0 1").expect("fixture FEN parses");
    let wrong_side = Move::new(
        "e4".parse().expect("square"),
        "d5".parse().expect("square"),
        MoveKind::Capture,
    );
    assert!(matches!(
        static_exchange_evaluation(&wrong_side_position, wrong_side),
        Err(StaticExchangeError::MoveStateContradiction(
            StaticExchangeMoveStateError::WrongSideToMove { .. }
        ))
    ));

    let empty_target = Move::new(
        "e4".parse().expect("square"),
        "f5".parse().expect("square"),
        MoveKind::Capture,
    );
    assert!(matches!(
        static_exchange_evaluation(&position, empty_target),
        Err(StaticExchangeError::MoveStateContradiction(
            StaticExchangeMoveStateError::InvalidTargetState { .. }
        ))
    ));

    let invalid_geometry = Move::new(
        "e4".parse().expect("square"),
        "d5".parse().expect("square"),
        MoveKind::QueenPromotionCapture,
    );
    assert!(matches!(
        static_exchange_evaluation(&position, invalid_geometry),
        Err(StaticExchangeError::MoveStateContradiction(
            StaticExchangeMoveStateError::InvalidGeometry { .. }
        ))
    ));

    let pinned_position = Position::from_fen("4r1k1/8/8/8/3p4/4B3/8/4K3 w - - 0 1")
        .expect("pinned fixture FEN parses");
    let pinned_capture = Move::new(
        "e3".parse().expect("square"),
        "d4".parse().expect("square"),
        MoveKind::Capture,
    );
    assert_eq!(
        static_exchange_evaluation(&pinned_position, pinned_capture),
        Err(StaticExchangeMoveStateError::IllegalKingExposure {
            current: pinned_capture
        }
        .into())
    );

    assert_eq!(position, root);
}

#[test]
fn bounded_capacity_failure_is_explicit() {
    let position =
        Position::from_fen("4k3/8/2p5/3p4/4P3/8/8/4K3 w - - 0 1").expect("fixture FEN parses");
    let board = SeeBoard::from_position(&position);
    assert_eq!(
        exchange_gain(
            &board,
            "d5".parse().expect("square"),
            crate::Color::White,
            PieceKind::Pawn,
            MAX_STATIC_EXCHANGE_PLIES,
        ),
        Err(StaticExchangeError::ExchangeCapacityExceeded)
    );
}

#[test]
fn curated_and_deterministic_generated_positions_match_legal_oracle() {
    for (fen, uci) in [
        ("4k3/8/2p5/3p4/4P3/8/8/4K3 w - - 0 1", "e4d5"),
        ("3r2k1/8/8/3pP3/8/8/8/6K1 w - d6 0 1", "e5d6"),
        ("1r5k/P7/8/8/8/8/8/7K w - - 0 1", "a7b8q"),
        ("4k3/4n3/8/3p4/2P5/8/8/4R1K1 w - - 0 1", "c4d5"),
    ] {
        compare_fixture_with_oracle(fen, uci);
    }

    let mut comparisons = 0_usize;
    for seed in [1_u64, 0x9e37_79b9, 0x00c0_ffee, 0xdead_beef] {
        let mut selector = seed;
        let mut position = Position::starting();
        for _ in 0..72 {
            let moves = position
                .legal_moves()
                .expect("generated-position legal moves succeed");
            if moves.is_empty() {
                break;
            }
            let root = position.clone();
            for current in moves.iter() {
                if !current.kind().is_capture() && current.promotion().is_none() {
                    continue;
                }
                let actual = static_exchange_evaluation(&position, current)
                    .expect("legal exchange event is valid SEE input")
                    .centipawns();
                let expected = oracle_static_exchange(&position, current);
                assert_eq!(
                    actual,
                    expected,
                    "generated FEN {} move {}",
                    position.to_fen(),
                    current.to_uci()
                );
                assert_eq!(position, root, "generated SEE mutated the position");
                comparisons += 1;
            }

            selector = selector
                .wrapping_mul(6_364_136_223_846_793_005)
                .wrapping_add(1_442_695_040_888_963_407);
            let current = moves
                .get((selector as usize) % moves.len())
                .expect("generated selector is bounded");
            position
                .make_move(current)
                .expect("generated legal move applies");
        }
    }
    assert!(
        comparisons >= 32,
        "deterministic corpus produced only {comparisons} exchange comparisons"
    );
}
