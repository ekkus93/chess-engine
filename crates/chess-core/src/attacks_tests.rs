use crate::{Bitboard, Color, Piece, PieceKind, Position, Square};

use super::{
    between, bishop_attacks, king_attacks, knight_attacks, line, pawn_attacks, queen_attacks, ray,
    rook_attacks,
};

const ORTHOGONAL: [(i8, i8); 4] = [(-1, 0), (1, 0), (0, -1), (0, 1)];
const DIAGONAL: [(i8, i8); 4] = [(-1, -1), (-1, 1), (1, -1), (1, 1)];

fn square(value: &str) -> Square {
    value.parse().expect("test square is valid")
}

fn board(values: &[&str]) -> Bitboard {
    let mut result = Bitboard::EMPTY;
    for value in values {
        result.set(square(value));
    }
    result
}

#[test]
fn leaper_tables_match_coordinate_oracle_for_every_square() {
    let knight_offsets = [
        (-2, -1),
        (-2, 1),
        (-1, -2),
        (-1, 2),
        (1, -2),
        (1, 2),
        (2, -1),
        (2, 1),
    ];
    let king_offsets = [
        (-1, -1),
        (-1, 0),
        (-1, 1),
        (0, -1),
        (0, 1),
        (1, -1),
        (1, 0),
        (1, 1),
    ];

    for index in 0..Square::COUNT {
        let source = Square::new(index).expect("index is valid");
        assert_eq!(
            knight_attacks(source),
            oracle_offsets(source, &knight_offsets),
            "knight {source}"
        );
        assert_eq!(
            king_attacks(source),
            oracle_offsets(source, &king_offsets),
            "king {source}"
        );
        assert_eq!(
            pawn_attacks(Color::White, source),
            oracle_offsets(source, &[(-1, -1), (-1, 1)]),
            "white pawn {source}"
        );
        assert_eq!(
            pawn_attacks(Color::Black, source),
            oracle_offsets(source, &[(1, -1), (1, 1)]),
            "black pawn {source}"
        );
    }

    assert_eq!(knight_attacks(square("a8")).count(), 2);
    assert_eq!(king_attacks(square("a8")).count(), 3);
    assert_eq!(pawn_attacks(Color::White, square("a8")), Bitboard::EMPTY);
    assert_eq!(pawn_attacks(Color::Black, square("h1")), Bitboard::EMPTY);
}

#[test]
fn sliding_attacks_match_independent_oracle_for_representative_occupancies() {
    let occupancies = [
        Bitboard::EMPTY,
        Bitboard::FULL,
        Bitboard::from_bits(0x55aa_55aa_55aa_55aa),
        Bitboard::from_bits(0x8100_2400_0024_0081),
        board(&["a8", "h8", "d5", "e4", "a1", "h1"]),
    ];

    for index in 0..Square::COUNT {
        let source = Square::new(index).expect("index is valid");
        for occupancy in occupancies {
            let rook = oracle_slider(source, occupancy, &ORTHOGONAL);
            let bishop = oracle_slider(source, occupancy, &DIAGONAL);
            assert_eq!(rook_attacks(source, occupancy), rook, "rook {source}");
            assert_eq!(bishop_attacks(source, occupancy), bishop, "bishop {source}");
            assert_eq!(
                queen_attacks(source, occupancy),
                rook | bishop,
                "queen {source}"
            );
        }
    }
}

#[test]
fn sliding_attacks_include_first_blocker_and_stop_after_it() {
    let occupancy = board(&["d6", "d2", "b4", "f4", "b6", "f6", "b2", "f2"]);
    assert_eq!(
        rook_attacks(square("d4"), occupancy),
        board(&["d5", "d6", "d3", "d2", "c4", "b4", "e4", "f4"])
    );
    assert_eq!(
        bishop_attacks(square("d4"), occupancy),
        board(&["c5", "b6", "e5", "f6", "c3", "b2", "e3", "f2"])
    );
    assert!(rook_attacks(square("a8"), Bitboard::EMPTY).contains(square("h8")));
    assert!(bishop_attacks(square("a8"), Bitboard::EMPTY).contains(square("h1")));
}

#[test]
fn geometry_tables_match_independent_oracle_for_every_square_pair() {
    for from_index in 0..Square::COUNT {
        let from = Square::new(from_index).expect("index is valid");
        for to_index in 0..Square::COUNT {
            let to = Square::new(to_index).expect("index is valid");
            assert_eq!(ray(from, to), oracle_ray(from, to), "ray {from} {to}");
            assert_eq!(
                between(from, to),
                oracle_between(from, to),
                "between {from} {to}"
            );
            assert_eq!(line(from, to), oracle_line(from, to), "line {from} {to}");
            assert_eq!(between(from, to), between(to, from));
            assert_eq!(line(from, to), line(to, from));
        }
    }
}

#[test]
fn position_attack_queries_match_independent_fixture_oracle() {
    let fixtures = [
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "r3k2r/ppp2ppp/2n5/3pp3/3PP3/2N5/PPP2PPP/R3K2R b KQkq e3 17 42",
        "4r1k1/8/8/8/8/5n2/4R3/4K3 w - - 0 1",
        "4k3/8/8/3pP3/8/8/8/4K3 w - - 0 1",
    ];

    for fen in fixtures {
        let position = Position::from_fen(fen).expect("fixture FEN is valid");
        for index in 0..Square::COUNT {
            let target = Square::new(index).expect("index is valid");
            for color in [Color::White, Color::Black] {
                let expected = oracle_attackers_to(&position, target, color);
                assert_eq!(
                    position.attackers_to(target, color),
                    expected,
                    "{fen}: {color} attackers to {target}"
                );
                assert_eq!(
                    position.is_square_attacked(target, color),
                    !expected.is_empty()
                );
            }
        }
    }
}

#[test]
fn checker_and_absolute_pin_queries_are_exact() {
    let double_check = Position::from_fen("4r1k1/8/8/8/8/5n2/8/4K3 w - - 0 1").expect("valid FEN");
    assert_eq!(
        double_check.checkers_to_king(Color::White),
        board(&["e8", "f3"])
    );
    assert_eq!(double_check.checkers_to_king(Color::Black), Bitboard::EMPTY);

    let pinned = Position::from_fen("4r1k1/8/8/8/8/8/4R3/4K3 w - - 0 1").expect("valid FEN");
    assert_eq!(pinned.pinned_pieces(Color::White), board(&["e2"]));
    assert_eq!(pinned.pinned_pieces(Color::Black), Bitboard::EMPTY);

    let two_blockers =
        Position::from_fen("4r1k1/8/8/8/8/4B3/4R3/4K3 w - - 0 1").expect("valid FEN");
    assert_eq!(two_blockers.pinned_pieces(Color::White), Bitboard::EMPTY);
}

#[test]
fn pawn_attack_geometry_is_independent_of_target_occupancy() {
    let source = square("e5");
    let expected = board(&["d6", "f6"]);
    assert_eq!(pawn_attacks(Color::White, source), expected);

    for occupancy in [Bitboard::EMPTY, expected, Bitboard::FULL] {
        assert_eq!(
            pawn_attacks(Color::White, source) & occupancy,
            expected & occupancy
        );
    }
}

fn oracle_offsets(source: Square, offsets: &[(i8, i8)]) -> Bitboard {
    let mut attacks = Bitboard::EMPTY;
    for &(row_delta, file_delta) in offsets {
        let row = source.row() as i8 + row_delta;
        let file = source.file() as i8 + file_delta;
        if let Some(target) = checked_square(row, file) {
            attacks.set(target);
        }
    }
    attacks
}

fn oracle_slider(source: Square, occupancy: Bitboard, directions: &[(i8, i8)]) -> Bitboard {
    let mut attacks = Bitboard::EMPTY;
    for &(row_delta, file_delta) in directions {
        let mut row = source.row() as i8 + row_delta;
        let mut file = source.file() as i8 + file_delta;
        while let Some(target) = checked_square(row, file) {
            attacks.set(target);
            if occupancy.contains(target) {
                break;
            }
            row += row_delta;
            file += file_delta;
        }
    }
    attacks
}

fn oracle_ray(from: Square, to: Square) -> Bitboard {
    let Some((row_step, file_step)) = oracle_direction(from, to) else {
        return Bitboard::EMPTY;
    };
    let mut result = Bitboard::EMPTY;
    let mut row = from.row() as i8 + row_step;
    let mut file = from.file() as i8 + file_step;
    while let Some(current) = checked_square(row, file) {
        result.set(current);
        row += row_step;
        file += file_step;
    }
    result
}

fn oracle_between(from: Square, to: Square) -> Bitboard {
    let Some((row_step, file_step)) = oracle_direction(from, to) else {
        return Bitboard::EMPTY;
    };
    let mut result = Bitboard::EMPTY;
    let mut row = from.row() as i8 + row_step;
    let mut file = from.file() as i8 + file_step;
    while let Some(current) = checked_square(row, file) {
        if current == to {
            return result;
        }
        result.set(current);
        row += row_step;
        file += file_step;
    }
    Bitboard::EMPTY
}

fn oracle_line(from: Square, to: Square) -> Bitboard {
    if from == to {
        return Bitboard::from(from);
    }
    let Some((row_step, file_step)) = oracle_direction(from, to) else {
        return Bitboard::EMPTY;
    };
    let mut row = from.row() as i8;
    let mut file = from.file() as i8;
    while checked_square(row - row_step, file - file_step).is_some() {
        row -= row_step;
        file -= file_step;
    }
    let mut result = Bitboard::EMPTY;
    while let Some(current) = checked_square(row, file) {
        result.set(current);
        row += row_step;
        file += file_step;
    }
    result
}

fn oracle_direction(from: Square, to: Square) -> Option<(i8, i8)> {
    if from == to {
        return None;
    }
    let row_delta = to.row() as i8 - from.row() as i8;
    let file_delta = to.file() as i8 - from.file() as i8;
    let aligned = row_delta == 0 || file_delta == 0 || row_delta.abs() == file_delta.abs();
    if !aligned {
        return None;
    }
    Some((row_delta.signum(), file_delta.signum()))
}

fn oracle_attackers_to(position: &Position, target: Square, color: Color) -> Bitboard {
    let mut result = Bitboard::EMPTY;
    for index in 0..Square::COUNT {
        let source = Square::new(index).expect("index is valid");
        let Some(piece) = position.piece_at(source) else {
            continue;
        };
        if piece.color == color && oracle_piece_attacks(position, source, target, piece) {
            result.set(source);
        }
    }
    result
}

fn oracle_piece_attacks(position: &Position, source: Square, target: Square, piece: Piece) -> bool {
    let row_delta = target.row() as i8 - source.row() as i8;
    let file_delta = target.file() as i8 - source.file() as i8;
    match piece.kind {
        PieceKind::Pawn => {
            let forward = match piece.color {
                Color::White => -1,
                Color::Black => 1,
            };
            row_delta == forward && file_delta.abs() == 1
        }
        PieceKind::Knight => {
            (row_delta.abs() == 2 && file_delta.abs() == 1)
                || (row_delta.abs() == 1 && file_delta.abs() == 2)
        }
        PieceKind::King => row_delta.abs() <= 1 && file_delta.abs() <= 1,
        PieceKind::Bishop => {
            row_delta.abs() == file_delta.abs()
                && clear_path(
                    position,
                    source,
                    target,
                    row_delta.signum(),
                    file_delta.signum(),
                )
        }
        PieceKind::Rook => {
            (row_delta == 0 || file_delta == 0)
                && clear_path(
                    position,
                    source,
                    target,
                    row_delta.signum(),
                    file_delta.signum(),
                )
        }
        PieceKind::Queen => {
            (row_delta == 0 || file_delta == 0 || row_delta.abs() == file_delta.abs())
                && clear_path(
                    position,
                    source,
                    target,
                    row_delta.signum(),
                    file_delta.signum(),
                )
        }
    }
}

fn clear_path(
    position: &Position,
    source: Square,
    target: Square,
    row_step: i8,
    file_step: i8,
) -> bool {
    if row_step == 0 && file_step == 0 {
        return false;
    }
    let mut row = source.row() as i8 + row_step;
    let mut file = source.file() as i8 + file_step;
    while let Some(current) = checked_square(row, file) {
        if current == target {
            return true;
        }
        if position.piece_at(current).is_some() {
            return false;
        }
        row += row_step;
        file += file_step;
    }
    false
}

fn checked_square(row: i8, file: i8) -> Option<Square> {
    let row = u8::try_from(row).ok()?;
    let file = u8::try_from(file).ok()?;
    Square::from_row_file(row, file)
}
