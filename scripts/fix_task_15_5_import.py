#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

root = Path(sys.argv[1]).resolve()
path = root / "crates/chess-search/src/transposition/store.rs"
text = path.read_text()
old = "use super::{\n    TranspositionCluster, TranspositionEntry, TranspositionTable, TRANSPOSITION_CLUSTER_SIZE,\n};\n"
new = "use super::{TranspositionCluster, TranspositionEntry, TranspositionTable};\n"
if text.count(old) != 1:
    raise SystemExit("unexpected production import shape")
text = text.replace(old, new, 1)
old = "    use super::{TranspositionStoreAction, TRANSPOSITION_CLUSTER_SIZE};\n    use crate::{\n        Score, TranspositionBound, TranspositionEntry, TranspositionScore, TranspositionTable,\n    };\n"
new = "    use super::TranspositionStoreAction;\n    use crate::{\n        Score, TranspositionBound, TranspositionEntry, TranspositionScore, TranspositionTable,\n        TRANSPOSITION_CLUSTER_SIZE,\n    };\n"
if text.count(old) != 1:
    raise SystemExit("unexpected test import shape")
path.write_text(text.replace(old, new, 1))
subprocess.run(["cargo", "fmt", "--all"], cwd=root, check=True)
subprocess.run(["git", "diff", "--check"], cwd=root, check=True)
