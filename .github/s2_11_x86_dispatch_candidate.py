from pathlib import Path
import subprocess

ATTACKS = Path("crates/chess-core/src/attacks.rs")


def blob_sha(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one source match, found {count}")
    return text.replace(old, new, 1)


if blob_sha(ATTACKS) != "ce046fb753b3b5aee9240f86d48f89d4067c06d8":
    raise SystemExit("attacks.rs no longer matches the measured portable candidate")

text = ATTACKS.read_text()
text = replace_once(
    text,
    "const ORTHOGONAL_DIRECTION_INDICES: [usize; 4] = [0, 1, 2, 3];\n"
    "const DIAGONAL_DIRECTION_INDICES: [usize; 4] = [4, 5, 6, 7];\n"
    "const DIRECTION_DECREASES_INDEX: [bool; 8] = [true, false, true, false, true, true, false, false];\n",
    "#[cfg(not(target_arch = \"x86_64\"))]\n"
    "const ORTHOGONAL_DIRECTIONS: [(i8, i8); 4] = [(-1, 0), (1, 0), (0, -1), (0, 1)];\n"
    "#[cfg(not(target_arch = \"x86_64\"))]\n"
    "const DIAGONAL_DIRECTIONS: [(i8, i8); 4] = [(-1, -1), (-1, 1), (1, -1), (1, 1)];\n"
    "#[cfg(target_arch = \"x86_64\")]\n"
    "const ORTHOGONAL_DIRECTION_INDICES: [usize; 4] = [0, 1, 2, 3];\n"
    "#[cfg(target_arch = \"x86_64\")]\n"
    "const DIAGONAL_DIRECTION_INDICES: [usize; 4] = [4, 5, 6, 7];\n"
    "#[cfg(target_arch = \"x86_64\")]\n"
    "const DIRECTION_DECREASES_INDEX: [bool; 8] =\n"
    "    [true, false, true, false, true, true, false, false];\n",
    "architecture-specific direction metadata",
)
text = replace_once(
    text,
    "static SLIDING_RAYS: [[Bitboard; BOARD_SQUARES]; 8] = build_sliding_rays();\n",
    "#[cfg(target_arch = \"x86_64\")]\n"
    "static SLIDING_RAYS: [[Bitboard; BOARD_SQUARES]; 8] = build_sliding_rays();\n",
    "x86 ray table",
)
text = replace_once(
    text,
    "pub fn rook_attacks(square: Square, occupancy: Bitboard) -> Bitboard {\n"
    "    sliding_attacks(square, occupancy, &ORTHOGONAL_DIRECTION_INDICES)\n"
    "}\n",
    "pub fn rook_attacks(square: Square, occupancy: Bitboard) -> Bitboard {\n"
    "    #[cfg(target_arch = \"x86_64\")]\n"
    "    {\n"
    "        sliding_attacks_ray(square, occupancy, &ORTHOGONAL_DIRECTION_INDICES)\n"
    "    }\n"
    "    #[cfg(not(target_arch = \"x86_64\"))]\n"
    "    {\n"
    "        sliding_attacks_step(square, occupancy, &ORTHOGONAL_DIRECTIONS)\n"
    "    }\n"
    "}\n",
    "rook architecture dispatch",
)
text = replace_once(
    text,
    "pub fn bishop_attacks(square: Square, occupancy: Bitboard) -> Bitboard {\n"
    "    sliding_attacks(square, occupancy, &DIAGONAL_DIRECTION_INDICES)\n"
    "}\n",
    "pub fn bishop_attacks(square: Square, occupancy: Bitboard) -> Bitboard {\n"
    "    #[cfg(target_arch = \"x86_64\")]\n"
    "    {\n"
    "        sliding_attacks_ray(square, occupancy, &DIAGONAL_DIRECTION_INDICES)\n"
    "    }\n"
    "    #[cfg(not(target_arch = \"x86_64\"))]\n"
    "    {\n"
    "        sliding_attacks_step(square, occupancy, &DIAGONAL_DIRECTIONS)\n"
    "    }\n"
    "}\n",
    "bishop architecture dispatch",
)
text = replace_once(
    text,
    "fn sliding_attacks(\n",
    "#[cfg(target_arch = \"x86_64\")]\nfn sliding_attacks_ray(\n",
    "x86 ray function",
)
text = replace_once(
    text,
    "const fn build_sliding_rays() -> [[Bitboard; BOARD_SQUARES]; 8] {\n",
    "#[cfg(not(target_arch = \"x86_64\"))]\n"
    "fn sliding_attacks_step(\n"
    "    square: Square,\n"
    "    occupancy: Bitboard,\n"
    "    directions: &[(i8, i8); 4],\n"
    ") -> Bitboard {\n"
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
    "}\n\n"
    "#[cfg(target_arch = \"x86_64\")]\n"
    "const fn build_sliding_rays() -> [[Bitboard; BOARD_SQUARES]; 8] {\n",
    "non-x86 step implementation and x86 ray builder",
)
ATTACKS.write_text(text)
