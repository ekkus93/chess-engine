#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

root = Path(sys.argv[1]).resolve()
path = root / "crates/chess-search/src/transposition/store.rs"
text = path.read_text()
old = '''        for slot in 0..TRANSPOSITION_CLUSTER_SIZE {
            table.generation = generations[slot];
            let key = colliding_key(&table, base_key, slot as u64);
            assert_eq!(table.store(entry(key, depths[slot])).slot_index(), slot);
        }
'''
new = '''        for (slot, (&depth, &generation)) in depths.iter().zip(&generations).enumerate() {
            table.generation = generation;
            let key = colliding_key(&table, base_key, slot as u64);
            assert_eq!(table.store(entry(key, depth)).slot_index(), slot);
        }
'''
if text.count(old) != 1:
    raise SystemExit("unexpected depth fixture loop")
text = text.replace(old, new, 1)
old = '''        for slot in 0..TRANSPOSITION_CLUSTER_SIZE {
            table.generation = generations[slot];
            let key = colliding_key(&table, base_key, slot as u64);
            table.store(entry(key, 7));
        }
'''
new = '''        for (slot, generation) in generations.into_iter().enumerate() {
            table.generation = generation;
            let key = colliding_key(&table, base_key, slot as u64);
            table.store(entry(key, 7));
        }
'''
if text.count(old) != 1:
    raise SystemExit("unexpected age fixture loop")
path.write_text(text.replace(old, new, 1))
subprocess.run(["cargo", "fmt", "--all"], cwd=root, check=True)
subprocess.run(["git", "diff", "--check"], cwd=root, check=True)
