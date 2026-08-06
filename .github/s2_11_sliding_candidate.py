from pathlib import Path
import subprocess

ATTACKS = Path("crates/chess-core/src/attacks.rs")
TESTS = Path("crates/chess-core/src/attacks_tests.rs")


def blob_sha(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one source match, found {count}")
    return text.replace(old, new, 1)


if blob_sha(ATTACKS) != "644ec43d80f85c296a7d0137b0130929f04cb205":
    raise SystemExit("attacks.rs no longer matches the profiled S2-10 source blob")
if blob_sha(TESTS) != "e0d624796e8d61acf91b2cbc8c9f86741f4c4d29":
    raise SystemExit("attacks_tests.rs no longer matches the profiled S2-10 source blob")

attacks = ATTACKS.read_text()
attacks = replace_once(
    attacks,
    "const ALL_DIRECTIONS: [(i8, i8); 8] = [\n"
    "    (-1, 0),\n"
    "    (1, 0),\n"
    "    (0, -1),\n"
    "    (0, 1),\n"
    "    (-1, -1),\n"
    "    (-1, 1),\n"
    "    (1, -1),\n"
    "    (1, 1),\n"
    "];\n",
    "const ALL_DIRECTIONS: [(i8, i8); 8] = [\n"
    "    (-1, 0),\n"
    "    (1, 0),\n"
    "    (0, -1),\n"
    "    (0, 1),\n"
    "    (-1, -1),\n"
    "    (-1, 1),\n"
    "    (1, -1),\n"
    "    (1, 1),\n"
    "];\n"
    "const ORTHOGONAL_DIRECTION_INDICES: [usize; 4] = [0, 1, 2, 3];\n"
    "const DIAGONAL_DIRECTION_INDICES: [usize; 4] = [4, 5, 6, 7];\n"
    "const DIRECTION_DECREASES_INDEX: [bool; 8] =\n"
    "    [true, false, true, false, true, true, false, false];\n",
    "direction metadata",
)
attacks = replace_once(
    attacks,
    "static RAY_TABLE: [Bitboard; GEOMETRY_ENTRIES] = build_ray_table();\n",
    "static SLIDING_RAYS: [[Bitboard; BOARD_SQUARES]; 8] = build_sliding_rays();\n"
    "static RAY_TABLE: [Bitboard; GEOMETRY_ENTRIES] = build_ray_table();\n",
    "sliding ray table",
)
attacks = replace_once(
    attacks,
    "    sliding_attacks(square, occupancy, &ORTHOGONAL_DIRECTIONS)\n",
    "    sliding_attacks(square, occupancy, &ORTHOGONAL_DIRECTION_INDICES)\n",
    "rook dispatch",
)
attacks = replace_once(
    attacks,
    "    sliding_attacks(square, occupancy, &DIAGONAL_DIRECTIONS)\n",
    "    sliding_attacks(square, occupancy, &DIAGONAL_DIRECTION_INDICES)\n",
    "bishop dispatch",
)
attacks = replace_once(
    attacks,
    "fn sliding_attacks(square: Square, occupancy: Bitboard, directions: &[(i8, i8)]) -> Bitboard {\n"
    "    let mut attacks = Bitboard::EMPTY;\n"
    "    for &(row_step, file_step) in directions {\n"
    "        let mut row = square.row() as i8 + row_step;\n"
    "        let mut file = square.file() as i8 + file_step;\n"
    "        while in_bounds(row, file) {\n"
    "            let target = square_from_coordinates(row, file);\n"
    "            attacks.set(target);\n"
    "            if occupancy.contains(target) {\n"
    "                break;\n"
    "            }\n"
    "            row += row_step;\n"
    "            file += file_step;\n"
    "        }\n"
    "    }\n"
    "    attacks\n"
    "}\n\n",
    "fn sliding_attacks(\n"
    "    square: Square,\n"
    "    occupancy: Bitboard,\n"
    "    direction_indices: &[usize; 4],\n"
    ") -> Bitboard {\n"
    "    let square_index = usize::from(square.index());\n"
    "    let occupancy = occupancy.bits();\n"
    "    let mut attacks = 0_u64;\n\n"
    "    for &direction_index in direction_indices {\n"
    "        let ray = SLIDING_RAYS[direction_index][square_index].bits();\n"
    "        let blockers = ray & occupancy;\n"
    "        if blockers == 0 {\n"
    "            attacks |= ray;\n"
    "            continue;\n"
    "        }\n\n"
    "        let blocker_index = if DIRECTION_DECREASES_INDEX[direction_index] {\n"
    "            63_usize - blockers.leading_zeros() as usize\n"
    "        } else {\n"
    "            blockers.trailing_zeros() as usize\n"
    "        };\n"
    "        let beyond_blocker = SLIDING_RAYS[direction_index][blocker_index].bits();\n"
    "        attacks |= ray ^ beyond_blocker;\n"
    "    }\n\n"
    "    Bitboard::from_bits(attacks)\n"
    "}\n\n"
    "const fn build_sliding_rays() -> [[Bitboard; BOARD_SQUARES]; 8] {\n"
    "    let mut rays = [[Bitboard::EMPTY; BOARD_SQUARES]; 8];\n"
    "    let mut direction_index = 0_usize;\n"
    "    while direction_index < ALL_DIRECTIONS.len() {\n"
    "        let (row_step, file_step) = ALL_DIRECTIONS[direction_index];\n"
    "        let mut square_index = 0_usize;\n"
    "        while square_index < BOARD_SQUARES {\n"
    "            let mut row = (square_index / 8) as i8 + row_step;\n"
    "            let mut file = (square_index % 8) as i8 + file_step;\n"
    "            let mut bits = 0_u64;\n"
    "            while in_bounds(row, file) {\n"
    "                bits |= coordinate_bit(row, file);\n"
    "                row += row_step;\n"
    "                file += file_step;\n"
    "            }\n"
    "            rays[direction_index][square_index] = Bitboard::from_bits(bits);\n"
    "            square_index += 1;\n"
    "        }\n"
    "        direction_index += 1;\n"
    "    }\n"
    "    rays\n"
    "}\n\n",
    "portable ray-table implementation",
)
ATTACKS.write_text(attacks)

tests = TESTS.read_text()
tests = replace_once(
    tests,
    "#[test]\n"
    "fn sliding_attacks_include_first_blocker_and_stop_after_it() {\n",
    "#[test]\n"
    "fn sliding_attacks_match_independent_oracle_for_every_relevant_occupancy() {\n"
    "    for index in 0..Square::COUNT {\n"
    "        let source = Square::new(index).expect(\"index is valid\");\n"
    "        assert_slider_subsets(source, &ORTHOGONAL, rook_attacks);\n"
    "        assert_slider_subsets(source, &DIAGONAL, bishop_attacks);\n"
    "    }\n"
    "}\n\n"
    "#[test]\n"
    "fn sliding_attacks_include_first_blocker_and_stop_after_it() {\n",
    "exhaustive blocker-subset regression",
)
tests = replace_once(
    tests,
    "fn oracle_slider(source: Square, occupancy: Bitboard, directions: &[(i8, i8)]) -> Bitboard {\n",
    "fn assert_slider_subsets(\n"
    "    source: Square,\n"
    "    directions: &[(i8, i8)],\n"
    "    actual: fn(Square, Bitboard) -> Bitboard,\n"
    ") {\n"
    "    let relevant = oracle_slider(source, Bitboard::EMPTY, directions).bits();\n"
    "    let mut subset = relevant;\n"
    "    loop {\n"
    "        let occupancy = Bitboard::from_bits(subset);\n"
    "        assert_eq!(\n"
    "            actual(source, occupancy),\n"
    "            oracle_slider(source, occupancy, directions),\n"
    "            \"slider {source}, occupancy {subset:#018x}\"\n"
    "        );\n"
    "        if subset == 0 {\n"
    "            break;\n"
    "        }\n"
    "        subset = subset.wrapping_sub(1) & relevant;\n"
    "    }\n"
    "}\n\n"
    "fn oracle_slider(source: Square, occupancy: Bitboard, directions: &[(i8, i8)]) -> Bitboard {\n",
    "subset helper",
)
TESTS.write_text(tests)
