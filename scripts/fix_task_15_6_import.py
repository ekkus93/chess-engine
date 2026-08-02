from pathlib import Path
import sys

path = Path(sys.argv[1]) / "crates/chess-search/src/transposition/diagnostics.rs"
text = path.read_text()
old = "use super::{TranspositionEntry, TranspositionTable, TRANSPOSITION_CLUSTER_SIZE};\n"
new = "use super::{TranspositionTable, TRANSPOSITION_CLUSTER_SIZE};\n"
if old not in text:
    raise SystemExit("expected diagnostics import not found")
path.write_text(text.replace(old, new, 1))
