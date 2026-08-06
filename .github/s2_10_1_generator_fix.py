from pathlib import Path

path = Path("crates/chess-search/src/alpha_beta.rs")
text = path.read_text(encoding="utf-8")
needle = "                null_move_pruning: false,\n                weights:"
replacement = "                null_move_pruning: false,\n                futility_pruning: false,\n                weights:"
count = text.count(needle)
if count != 3:
    raise SystemExit(f"expected three test context initializers, found {count}")
path.write_text(text.replace(needle, replacement), encoding="utf-8")
Path(__file__).unlink()
