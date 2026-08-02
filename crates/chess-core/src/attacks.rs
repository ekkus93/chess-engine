use crate::{Bitboard, Color, PieceKind, Position, Square};

const BOARD_SQUARES: usize = 64;
const GEOMETRY_ENTRIES: usize = BOARD_SQUARES * BOARD_SQUARES;
const ORTHOGONAL_DIRECTIONS: [(i8, i8); 4] = [(-1, 0), (1, 0), (0, -1), (0, 1)];
const DIAGONAL_DIRECTIONS: [(i8, i8); 4] = [(-1, -1), (-1, 1), (1, -1), (1, 1)];
const ALL_DIRECTIONS: [(i8, i8); 8] = [
    (-1, 0),
    (1, 0),
    (0, -1),
    (0, 1),
    (-1, -1),
    (-1, 1),
    (1, -1),
    (1, 1),
];

const PAWN_ATTACKS: [[Bitboard; BOARD_SQUARES]; 2] = [
    build_pawn_attacks(Color::White),
    build_pawn_attacks(Color::Black),
];
const KNIGHT_ATTACKS: [Bitboard; BOARD_SQUARES] = build_knight_attacks();
const KING_ATTACKS: [Bitboard; BOARD_SQUARES] = build_king_attacks();
const RAY_TABLE: [Bitboard; GEOMETRY_ENTRIES] = build_ray_table();
const BETWEEN_TABLE: [Bitboard; GEOMETRY_ENTRIES] = build_between_table();
const LINE_TABLE: [Bitboard; GEOMETRY_ENTRIES] = build_line_table();

/// Returns diagonal pawn attack geometry from `square` for `color`.
///
/// Target occupancy is deliberately ignored. This is an attack primitive, not
/// a capture generator.
#[must_use]
pub const fn pawn_attacks(color: Color, square: Square) -> Bitboard {
    PAWN_ATTACKS[color.index()][square.index() as usize]
}

/// Returns all knight attack destinations from `square`.
#[must_use]
pub const fn knight_attacks(square: Square) -> Bitboard {
    KNIGHT_ATTACKS[square.index() as usize]
}

/// Returns all king attack destinations from `square`.
#[must_use]
pub const fn king_attacks(square: Square) -> Bitboard {
    KING_ATTACKS[square.index() as usize]
}

/// Returns rook attacks for arbitrary occupancy.
///
/// The first occupied square on each ray is included and terminates that ray.
#[must_use]
pub fn rook_attacks(square: Square, occupancy: Bitboard) -> Bitboard {
    sliding_attacks(square, occupancy, &ORTHOGONAL_DIRECTIONS)
}

/// Returns bishop attacks for arbitrary occupancy.
///
/// The first occupied square on each ray is included and terminates that ray.
#[must_use]
pub fn bishop_attacks(square: Square, occupancy: Bitboard) -> Bitboard {
    sliding_attacks(square, occupancy, &DIAGONAL_DIRECTIONS)
}

/// Returns queen attacks for arbitrary occupancy.
#[must_use]
pub fn queen_attacks(square: Square, occupancy: Bitboard) -> Bitboard {
    rook_attacks(square, occupancy) | bishop_attacks(square, occupancy)
}

/// Returns the directed ray from `from` toward `through`.
///
/// The source is excluded. If the squares are aligned, the result includes
/// `through` and continues to the board edge. Non-aligned or identical squares
/// return an empty bitboard.
#[must_use]
pub const fn ray(from: Square, through: Square) -> Bitboard {
    RAY_TABLE[geometry_index(from, through)]
}

/// Returns squares strictly between two aligned squares.
///
/// Endpoints are excluded. Non-aligned or identical squares return an empty
/// bitboard.
#[must_use]
pub const fn between(from: Square, to: Square) -> Bitboard {
    BETWEEN_TABLE[geometry_index(from, to)]
}

/// Returns the complete rank, file, or diagonal containing two aligned squares.
///
/// Both endpoints and every square to both board edges are included. Identical
/// endpoints return that one square; non-aligned squares return an empty board.
#[must_use]
pub const fn line(from: Square, to: Square) -> Bitboard {
    LINE_TABLE[geometry_index(from, to)]
}

impl Position {
    /// Returns pieces of `by_color` that geometrically attack `target`.
    #[must_use]
    pub fn attackers_to(&self, target: Square, by_color: Color) -> Bitboard {
        let pawns = pawn_attacks(by_color.opposite(), target)
            & self.piece_bitboard(by_color, PieceKind::Pawn);
        let knights = knight_attacks(target) & self.piece_bitboard(by_color, PieceKind::Knight);
        let kings = king_attacks(target) & self.piece_bitboard(by_color, PieceKind::King);
        let diagonal = bishop_attacks(target, self.all_occupancy())
            & (self.piece_bitboard(by_color, PieceKind::Bishop)
                | self.piece_bitboard(by_color, PieceKind::Queen));
        let orthogonal = rook_attacks(target, self.all_occupancy())
            & (self.piece_bitboard(by_color, PieceKind::Rook)
                | self.piece_bitboard(by_color, PieceKind::Queen));
        pawns | knights | kings | diagonal | orthogonal
    }

    /// Returns whether `target` is attacked by at least one piece of `by_color`.
    #[must_use]
    pub fn is_square_attacked(&self, target: Square, by_color: Color) -> bool {
        !self.attackers_to(target, by_color).is_empty()
    }

    /// Returns enemy pieces currently checking `color`'s king.
    #[must_use]
    pub fn checkers_to_king(&self, color: Color) -> Bitboard {
        self.attackers_to(self.king_square(color), color.opposite())
    }

    /// Returns pieces of `color` absolutely pinned to that color's king.
    ///
    /// A piece is returned when it is the sole blocker between its king and an
    /// opposing rook, bishop, or queen on a compatible ray.
    #[must_use]
    pub fn pinned_pieces(&self, color: Color) -> Bitboard {
        let king = self.king_square(color);
        let mut pinned = Bitboard::EMPTY;

        for (row_step, file_step) in ALL_DIRECTIONS {
            let diagonal = row_step != 0 && file_step != 0;
            let mut row = king.row() as i8 + row_step;
            let mut file = king.file() as i8 + file_step;
            let mut candidate = None;

            while in_bounds(row, file) {
                let square = square_from_coordinates(row, file);
                if let Some(piece) = self.piece_at(square) {
                    if candidate.is_none() {
                        if piece.color == color {
                            candidate = Some(square);
                        } else {
                            break;
                        }
                    } else {
                        if piece.color != color && slider_matches_direction(piece.kind, diagonal) {
                            pinned.set(candidate.expect("candidate was checked"));
                        }
                        break;
                    }
                }
                row += row_step;
                file += file_step;
            }
        }

        pinned
    }
}

fn sliding_attacks(square: Square, occupancy: Bitboard, directions: &[(i8, i8)]) -> Bitboard {
    let mut attacks = Bitboard::EMPTY;
    for &(row_step, file_step) in directions {
        let mut row = square.row() as i8 + row_step;
        let mut file = square.file() as i8 + file_step;
        while in_bounds(row, file) {
            let target = square_from_coordinates(row, file);
            attacks.set(target);
            if occupancy.contains(target) {
                break;
            }
            row += row_step;
            file += file_step;
        }
    }
    attacks
}

const fn geometry_index(from: Square, to: Square) -> usize {
    from.index() as usize * BOARD_SQUARES + to.index() as usize
}

const fn build_pawn_attacks(color: Color) -> [Bitboard; BOARD_SQUARES] {
    let mut table = [Bitboard::EMPTY; BOARD_SQUARES];
    let mut index = 0_usize;
    while index < BOARD_SQUARES {
        let row = (index / 8) as i8;
        let file = (index % 8) as i8;
        let row_step = match color {
            Color::White => -1,
            Color::Black => 1,
        };
        let bits =
            coordinate_bit(row + row_step, file - 1) | coordinate_bit(row + row_step, file + 1);
        table[index] = Bitboard::from_bits(bits);
        index += 1;
    }
    table
}

const fn build_knight_attacks() -> [Bitboard; BOARD_SQUARES] {
    let mut table = [Bitboard::EMPTY; BOARD_SQUARES];
    let mut index = 0_usize;
    while index < BOARD_SQUARES {
        let row = (index / 8) as i8;
        let file = (index % 8) as i8;
        let bits = coordinate_bit(row - 2, file - 1)
            | coordinate_bit(row - 2, file + 1)
            | coordinate_bit(row - 1, file - 2)
            | coordinate_bit(row - 1, file + 2)
            | coordinate_bit(row + 1, file - 2)
            | coordinate_bit(row + 1, file + 2)
            | coordinate_bit(row + 2, file - 1)
            | coordinate_bit(row + 2, file + 1);
        table[index] = Bitboard::from_bits(bits);
        index += 1;
    }
    table
}

const fn build_king_attacks() -> [Bitboard; BOARD_SQUARES] {
    let mut table = [Bitboard::EMPTY; BOARD_SQUARES];
    let mut index = 0_usize;
    while index < BOARD_SQUARES {
        let row = (index / 8) as i8;
        let file = (index % 8) as i8;
        let bits = coordinate_bit(row - 1, file - 1)
            | coordinate_bit(row - 1, file)
            | coordinate_bit(row - 1, file + 1)
            | coordinate_bit(row, file - 1)
            | coordinate_bit(row, file + 1)
            | coordinate_bit(row + 1, file - 1)
            | coordinate_bit(row + 1, file)
            | coordinate_bit(row + 1, file + 1);
        table[index] = Bitboard::from_bits(bits);
        index += 1;
    }
    table
}

const fn build_ray_table() -> [Bitboard; GEOMETRY_ENTRIES] {
    let mut table = [Bitboard::EMPTY; GEOMETRY_ENTRIES];
    let mut from = 0_u8;
    while from < Square::COUNT {
        let mut to = 0_u8;
        while to < Square::COUNT {
            table[from as usize * BOARD_SQUARES + to as usize] =
                Bitboard::from_bits(ray_bits(from, to));
            to += 1;
        }
        from += 1;
    }
    table
}

const fn build_between_table() -> [Bitboard; GEOMETRY_ENTRIES] {
    let mut table = [Bitboard::EMPTY; GEOMETRY_ENTRIES];
    let mut from = 0_u8;
    while from < Square::COUNT {
        let mut to = 0_u8;
        while to < Square::COUNT {
            table[from as usize * BOARD_SQUARES + to as usize] =
                Bitboard::from_bits(between_bits(from, to));
            to += 1;
        }
        from += 1;
    }
    table
}

const fn build_line_table() -> [Bitboard; GEOMETRY_ENTRIES] {
    let mut table = [Bitboard::EMPTY; GEOMETRY_ENTRIES];
    let mut from = 0_u8;
    while from < Square::COUNT {
        let mut to = 0_u8;
        while to < Square::COUNT {
            table[from as usize * BOARD_SQUARES + to as usize] =
                Bitboard::from_bits(line_bits(from, to));
            to += 1;
        }
        from += 1;
    }
    table
}

const fn ray_bits(from: u8, to: u8) -> u64 {
    let (row_step, file_step) = aligned_step(from, to);
    if row_step == 0 && file_step == 0 {
        return 0;
    }
    let mut row = (from / 8) as i8 + row_step;
    let mut file = (from % 8) as i8 + file_step;
    let mut bits = 0_u64;
    while in_bounds(row, file) {
        bits |= coordinate_bit(row, file);
        row += row_step;
        file += file_step;
    }
    bits
}

const fn between_bits(from: u8, to: u8) -> u64 {
    let (row_step, file_step) = aligned_step(from, to);
    if row_step == 0 && file_step == 0 {
        return 0;
    }
    let mut row = (from / 8) as i8 + row_step;
    let mut file = (from % 8) as i8 + file_step;
    let target_row = (to / 8) as i8;
    let target_file = (to % 8) as i8;
    let mut bits = 0_u64;
    while in_bounds(row, file) {
        if row == target_row && file == target_file {
            return bits;
        }
        bits |= coordinate_bit(row, file);
        row += row_step;
        file += file_step;
    }
    0
}

const fn line_bits(from: u8, to: u8) -> u64 {
    if from == to {
        return 1_u64 << from;
    }
    let (row_step, file_step) = aligned_step(from, to);
    if row_step == 0 && file_step == 0 {
        return 0;
    }

    let mut row = (from / 8) as i8;
    let mut file = (from % 8) as i8;
    while in_bounds(row - row_step, file - file_step) {
        row -= row_step;
        file -= file_step;
    }

    let mut bits = 0_u64;
    while in_bounds(row, file) {
        bits |= coordinate_bit(row, file);
        row += row_step;
        file += file_step;
    }
    bits
}

const fn aligned_step(from: u8, to: u8) -> (i8, i8) {
    let from_row = (from / 8) as i8;
    let from_file = (from % 8) as i8;
    let row_delta = (to / 8) as i8 - from_row;
    let file_delta = (to % 8) as i8 - from_file;
    if row_delta == 0 && file_delta != 0 {
        return (0, sign(file_delta));
    }
    if file_delta == 0 && row_delta != 0 {
        return (sign(row_delta), 0);
    }
    if absolute(row_delta) == absolute(file_delta) && row_delta != 0 {
        return (sign(row_delta), sign(file_delta));
    }
    (0, 0)
}

const fn sign(value: i8) -> i8 {
    if value < 0 {
        -1
    } else {
        1
    }
}

const fn absolute(value: i8) -> i8 {
    if value < 0 {
        -value
    } else {
        value
    }
}

const fn coordinate_bit(row: i8, file: i8) -> u64 {
    if in_bounds(row, file) {
        1_u64 << (row as u8 * 8 + file as u8)
    } else {
        0
    }
}

const fn in_bounds(row: i8, file: i8) -> bool {
    row >= 0 && row < 8 && file >= 0 && file < 8
}

fn square_from_coordinates(row: i8, file: i8) -> Square {
    Square::from_row_file(row as u8, file as u8).expect("coordinates were bounds checked")
}

const fn slider_matches_direction(kind: PieceKind, diagonal: bool) -> bool {
    if diagonal {
        matches!(kind, PieceKind::Bishop | PieceKind::Queen)
    } else {
        matches!(kind, PieceKind::Rook | PieceKind::Queen)
    }
}

#[cfg(test)]
#[path = "attacks_tests.rs"]
mod tests;
