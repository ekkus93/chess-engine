from pathlib import Path

path = Path("crates/chess-core/src/attacks.rs")
text = path.read_text()
old = (
    "const ORTHOGONAL_DIRECTIONS: [(i8, i8); 4] = [(-1, 0), (1, 0), (0, -1), (0, 1)];\n"
    "const DIAGONAL_DIRECTIONS: [(i8, i8); 4] = [(-1, -1), (-1, 1), (1, -1), (1, 1)];\n"
)
if text.count(old) != 1:
    raise SystemExit("expected exactly one obsolete sliding-direction constant block")
path.write_text(text.replace(old, "", 1))
