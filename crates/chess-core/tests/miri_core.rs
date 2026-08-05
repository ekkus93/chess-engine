use chess_core::{static_exchange_evaluation, Position, UciMove};

const STARTING_FEN: &str = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

#[test]
fn miri_fen_and_uci_round_trips_use_only_defined_core_operations() {
    let position = Position::from_fen(STARTING_FEN).expect("starting FEN is valid");
    position
        .validate_invariants()
        .expect("starting position invariants hold");
    assert_eq!(position.to_fen(), STARTING_FEN);

    let parsed = "e2e4".parse::<UciMove>().expect("UCI move parses");
    assert_eq!(parsed.to_string(), "e2e4");
}

#[test]
fn miri_bounded_make_unmake_restores_position_and_hash() {
    let mut position = Position::starting();
    let root = position.clone();
    let selectors = [0_usize, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144];
    let mut undos = Vec::new();

    for selector in selectors {
        let moves = position.legal_moves().expect("legal generation succeeds");
        if moves.is_empty() {
            break;
        }
        let current = moves
            .get(selector % moves.len())
            .expect("selected move exists");
        let undo = position.make_move(current).expect("generated move applies");
        position
            .validate_invariants()
            .expect("post-move invariants hold");
        assert_eq!(position.zobrist(), position.recomputed_zobrist());
        undos.push(undo);
    }

    while let Some(undo) = undos.pop() {
        position.unmake_move(undo).expect("unmake succeeds");
        position
            .validate_invariants()
            .expect("restored invariants hold");
        assert_eq!(position.zobrist(), position.recomputed_zobrist());
    }
    assert_eq!(position, root);
}

#[test]
fn miri_static_exchange_is_deterministic_non_mutating_and_bounded() {
    let mut position = Position::from_fen("3r2k1/8/8/3pP3/8/8/8/6K1 w - d6 0 1")
        .expect("SEE fixture FEN is valid");
    let requested = "e5d6".parse::<UciMove>().expect("SEE UCI parses");
    let current = position
        .legal_moves()
        .expect("SEE fixture legal generation succeeds")
        .iter()
        .find(|current| requested.matches(*current))
        .expect("SEE fixture move is legal");
    let root = position.clone();
    let first = static_exchange_evaluation(&position, current).expect("SEE succeeds");
    let second = static_exchange_evaluation(&position, current).expect("repeated SEE succeeds");
    assert_eq!(first, second);
    assert_eq!(first.centipawns(), 0);
    assert_eq!(position, root);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
}
