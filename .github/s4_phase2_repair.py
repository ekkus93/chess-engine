from pathlib import Path

path = Path('crates/chess-tune/src/trace.rs')
text = path.read_text()
old = '''        let corrupted = text.replacen("positive", "positive", 0).replace(
            "initial_weight_checksum=0000000000000016",
            "initial_weight_checksum=0000000000000017",
        );'''
new = '''        let corrupted = text.replace(
            "initial_weight_checksum=0000000000000016",
            "initial_weight_checksum=0000000000000017",
        );'''
if text.count(old) != 1:
    raise SystemExit('trace corruption-test anchor missing')
path.write_text(text.replace(old, new, 1))
