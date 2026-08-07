from pathlib import Path

path = Path('.github/s3_phase2.py')
text = path.read_text()
old = 'end = text.index("fn loss_dataset_fingerprint(\\n", start)'
new = 'end = text.index("fn loss_dataset_fingerprint(", start)'
if text.count(old) != 1:
    raise SystemExit(f'expected one phase2 helper boundary witness, found {text.count(old)}')
path.write_text(text.replace(old, new, 1))
