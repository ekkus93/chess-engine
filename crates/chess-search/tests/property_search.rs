use chess_core::{Move, Position, SearchHistory, Square};
use chess_search::{evaluate, iterative_deepening_search};

const PROPERTY_CASES: usize = 24;
const SEARCH_DEPTH: u16 = 2;
const ROOT_FENS: [&str; 4] = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
    "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",
    "r2q1rk1/pp1nbppp/2p1pn2/3p4/3P4/2N1PN2/PPQ1BPPP/R3K2R w KQ - 4 10",
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

fn generated_position(case: usize) -> Position {
    let root_index = case % ROOT_FENS.len();
    let mut position = Position::from_fen(ROOT_FENS[root_index]).expect("property root is valid");
    let case_number = u64::try_from(case).expect("small property case");
    let mut rng = DeterministicRng(0x23_01_5ea2_0000_0000 ^ case_number);
    let requested_plies = 4 + case % 20;

    for _ in 0..requested_plies {
        let moves = position.legal_moves().expect("legal moves generate");
        if moves.is_empty() {
            break;
        }
        let index = usize::try_from(rng.next() % moves.len() as u64)
            .expect("selected move index fits usize");
        let current = moves.get(index).expect("selected legal move exists");
        position
            .make_move(current)
            .expect("generated legal move applies");
    }

    position
}

fn mirrored_castling(value: &str) -> String {
    if value == "-" {
        return "-".to_owned();
    }

    let mut mirrored = String::new();
    if value.contains('k') {
        mirrored.push('K');
    }
    if value.contains('q') {
        mirrored.push('Q');
    }
    if value.contains('K') {
        mirrored.push('k');
    }
    if value.contains('Q') {
        mirrored.push('q');
    }
    if mirrored.is_empty() {
        "-".to_owned()
    } else {
        mirrored
    }
}

fn mirror_and_swap(position: &Position) -> Position {
    let fen = position.to_fen();
    let fields: Vec<_> = fen.split_ascii_whitespace().collect();
    assert_eq!(fields.len(), 6, "canonical FEN has six fields: {fen}");

    let board = fields[0]
        .split('/')
        .rev()
        .map(|rank| {
            rank.chars()
                .map(|character| {
                    if character.is_ascii_lowercase() {
                        character.to_ascii_uppercase()
                    } else if character.is_ascii_uppercase() {
                        character.to_ascii_lowercase()
                    } else {
                        character
                    }
                })
                .collect::<String>()
        })
        .collect::<Vec<_>>()
        .join("/");
    let side = match fields[1] {
        "w" => "b",
        "b" => "w",
        _ => panic!("canonical FEN has a valid side: {fen}"),
    };
    let castling = mirrored_castling(fields[2]);
    let en_passant = if fields[3] == "-" {
        "-".to_owned()
    } else {
        let square: Square = fields[3].parse().expect("canonical en-passant square parses");
        Square::from_row_file(7 - square.row(), square.file())
            .expect("mirrored en-passant square is valid")
            .to_string()
    };
    let mirrored = format!(
        "{board} {side} {castling} {en_passant} {} {}",
        fields[4], fields[5]
    );
    Position::from_fen(&mirrored)
        .unwrap_or_else(|error| panic!("mirrored property FEN did not parse: {mirrored}: {error}"))
}

fn assert_legal_pv(root: &Position, moves: &[Move], context: &str) {
    let mut cursor = root.clone();
    let mut undos = Vec::new();

    for (ply, current) in moves.iter().copied().enumerate() {
        let moving_side = cursor.side_to_move();
        let tokens = cursor
            .legal_move_tokens()
            .unwrap_or_else(|error| panic!("{context}: PV ply {ply} generation failed: {error}"));
        let token = tokens
            .iter()
            .find(|token| token.move_made() == current)
            .unwrap_or_else(|| {
                panic!(
                    "{context}: PV ply {ply} move {} is not legal in {}",
                    current.to_uci(),
                    cursor.to_fen()
                )
            });
        let undo = cursor.make_legal_token(token).unwrap_or_else(|error| {
            panic!(
                "{context}: PV ply {ply} move {} failed to apply: {error}",
                current.to_uci()
            )
        });
        assert!(
            !cursor.is_in_check(moving_side),
            "{context}: PV ply {ply} move {} leaves its king in check",
            current.to_uci()
        );
        cursor.validate_invariants().unwrap_or_else(|error| {
            panic!("{context}: PV ply {ply} invariant failure: {error}")
        });
        assert_eq!(
            cursor.zobrist(),
            cursor.recomputed_zobrist(),
            "{context}: PV ply {ply} hash mismatch"
        );
        undos.push(undo);
    }

    while let Some(undo) = undos.pop() {
        cursor
            .unmake_move(undo)
            .unwrap_or_else(|error| panic!("{context}: PV unmake failed: {error}"));
    }
    assert_eq!(cursor, *root, "{context}: PV make/unmake did not restore root");
}

#[test]
fn generated_positions_preserve_exact_evaluator_mirror_symmetry() {
    for case in 0..PROPERTY_CASES {
        let position = generated_position(case);
        let mirrored = mirror_and_swap(&position);
        assert_eq!(
            evaluate(&position),
            evaluate(&mirrored),
            "case={case} original={} mirrored={}",
            position.to_fen(),
            mirrored.to_fen()
        );
    }
}

#[test]
fn every_generated_search_principal_variation_is_a_legal_reversible_sequence() {
    for case in 0..PROPERTY_CASES {
        let root = generated_position(case);
        let mut position = root.clone();
        let position_snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);
        let history_snapshot = history.clone();
        let result = iterative_deepening_search(&mut position, &mut history, SEARCH_DEPTH)
            .unwrap_or_else(|error| {
                panic!("case={case} root={}: search failed: {error}", root.to_fen())
            });
        let final_iteration = result
            .final_iteration()
            .expect("positive depth always completes an iteration");
        let pv = final_iteration.principal_variation();
        assert!(
            pv.len() <= usize::from(SEARCH_DEPTH),
            "case={case}: PV exceeds completed depth"
        );
        assert_eq!(pv.moves().first().copied(), final_iteration.best_move());
        assert_legal_pv(
            &root,
            pv.moves(),
            &format!("case={case} root={}", root.to_fen()),
        );
        assert_eq!(position, position_snapshot, "case={case}: search mutated root");
        assert_eq!(history, history_snapshot, "case={case}: search mutated history");
        assert_eq!(position.zobrist(), position.recomputed_zobrist());
    }
}
