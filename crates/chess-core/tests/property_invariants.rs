use chess_core::{Color, Move, MoveKind, Position, Square};

const MAX_PLIES: usize = 48;
const ROOT_FENS: [&str; 6] = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
    "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",
    "4k3/P6p/8/8/8/8/p6P/4K3 w - - 0 1",
    "r2q1rk1/pp1nbppp/2p1pn2/3p4/3P4/2N1PN2/PPQ1BPPP/R3K2R w KQ - 4 10",
    "4r1k1/8/8/8/8/8/4R3/4K3 w - - 0 1",
];
const SEEDS: [u64; 4] = [
    0x23_01_0000_0000_0001,
    0x23_01_0000_0000_0002,
    0x23_01_0000_0000_0003,
    0x23_01_0000_0000_0004,
];

#[derive(Clone, Copy)]
struct DeterministicRng(u64);

impl DeterministicRng {
    fn next(&mut self) -> u64 {
        self.0 = self.0.wrapping_add(0x9e37_79b9_7f4a_7c15);
        let mut value = self.0;
        value = (value ^ (value >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
        value = (value ^ (value >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
        value ^ (value >> 31)
    }
}

fn assert_position_properties(position: &Position, context: &str) {
    position
        .validate_invariants()
        .unwrap_or_else(|error| panic!("{context}: invariant failure: {error}"));
    assert_eq!(
        position.zobrist(),
        position.recomputed_zobrist(),
        "{context}: incremental hash diverged from full recomputation"
    );

    let fen = position.to_fen();
    let reparsed = Position::from_fen(&fen)
        .unwrap_or_else(|error| panic!("{context}: canonical FEN did not parse: {fen}: {error}"));
    assert_eq!(
        reparsed, *position,
        "{context}: canonical FEN changed the logical position: {fen}"
    );
    assert_eq!(
        reparsed.to_fen(),
        fen,
        "{context}: parse/serialize/parse was not stable"
    );
}

#[test]
fn every_square_and_packed_move_round_trips_exhaustively() {
    for index in 0..Square::COUNT {
        let square = Square::new(index).expect("property index is a valid square");
        let text = square.to_string();
        let parsed: Square = text.parse().expect("formatted square parses");
        assert_eq!(parsed, square, "square index {index}");
        assert_eq!(square.index(), index, "square index {index}");
        assert_eq!(
            square.row() * 8 + square.file(),
            index,
            "square index {index}"
        );
        assert_eq!(
            Square::from_row_file(square.row(), square.file()),
            Some(square),
            "square index {index}"
        );
    }

    for source_index in 0..Square::COUNT {
        let source = Square::new(source_index).expect("source index is valid");
        for destination_index in 0..Square::COUNT {
            let destination = Square::new(destination_index).expect("destination index is valid");
            for kind in MoveKind::ALL {
                let current = Move::new(source, destination, kind);
                assert_eq!(current.source(), source);
                assert_eq!(current.destination(), destination);
                assert_eq!(current.kind(), kind);
                assert_eq!(current.promotion(), kind.promotion());
            }
        }
    }
}

#[test]
fn generated_legal_play_preserves_core_properties_and_restores_exactly() {
    for (root_index, root_fen) in ROOT_FENS.iter().enumerate() {
        for seed in SEEDS {
            let effective_seed = seed ^ u64::try_from(root_index).expect("small root index");
            let mut rng = DeterministicRng(effective_seed);
            let mut position = Position::from_fen(root_fen).expect("property root FEN is valid");
            let root = position.clone();
            let mut undos = Vec::new();

            for ply in 0..MAX_PLIES {
                let context = format!(
                    "root={root_index} seed={effective_seed:#018x} ply={ply} fen={}",
                    position.to_fen()
                );
                assert_position_properties(&position, &context);

                let before_generation = position.clone();
                let moves = position
                    .legal_moves()
                    .unwrap_or_else(|error| panic!("{context}: legal generation failed: {error}"));
                assert_eq!(
                    position, before_generation,
                    "{context}: legal generation mutated the position"
                );
                if moves.is_empty() {
                    break;
                }

                let move_index = usize::try_from(rng.next() % moves.len() as u64)
                    .expect("selected move index fits usize");
                let current = moves.get(move_index).expect("selected legal move exists");
                assert!(
                    position
                        .is_legal_move(current)
                        .unwrap_or_else(|error| panic!(
                            "{context}: legality check failed: {error}"
                        )),
                    "{context}: generated move {} was rejected",
                    current.to_uci()
                );
                assert_eq!(
                    position, before_generation,
                    "{context}: legality check mutated the position"
                );

                let moving_side = position.side_to_move();
                let immediate_undo = position.make_move(current).unwrap_or_else(|error| {
                    panic!(
                        "{context}: generated legal move {} was not accepted: {error}",
                        current.to_uci()
                    )
                });
                assert_eq!(immediate_undo.move_made(), current);
                assert!(
                    !position.is_in_check(moving_side),
                    "{context}: legal move {} left {moving_side:?} in check",
                    current.to_uci()
                );
                assert_position_properties(
                    &position,
                    &format!("{context} after {}", current.to_uci()),
                );

                position
                    .unmake_move(immediate_undo)
                    .unwrap_or_else(|error| panic!("{context}: immediate unmake failed: {error}"));
                assert_eq!(
                    position, before_generation,
                    "{context}: immediate make/unmake did not restore exactly"
                );
                assert_position_properties(&position, &format!("{context} restored"));

                let sequence_undo = position.make_move(current).unwrap_or_else(|error| {
                    panic!(
                        "{context}: replay of generated legal move {} failed: {error}",
                        current.to_uci()
                    )
                });
                undos.push(sequence_undo);
            }

            while let Some(undo) = undos.pop() {
                position.unmake_move(undo).unwrap_or_else(|error| {
                    panic!(
                        "root={root_index} seed={effective_seed:#018x}: sequence unmake failed: {error}"
                    )
                });
                assert_position_properties(
                    &position,
                    &format!("root={root_index} seed={effective_seed:#018x} reverse"),
                );
            }
            assert_eq!(
                position, root,
                "root={root_index} seed={effective_seed:#018x}: full sequence did not restore"
            );
            assert_eq!(position.side_to_move(), root.side_to_move());
            assert_eq!(
                position.is_in_check(Color::White),
                root.is_in_check(Color::White)
            );
            assert_eq!(
                position.is_in_check(Color::Black),
                root.is_in_check(Color::Black)
            );
        }
    }
}
