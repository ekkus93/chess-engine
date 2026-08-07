from pathlib import Path

path = Path('crates/chess-tools/src/lib.rs')
text = path.read_text()
old = 'pub mod s3;\n'
new = 'pub mod s3;\npub mod s3_candidate;\n'
if text.count(old) != 1:
    raise SystemExit(f'expected one S3 module witness, found {text.count(old)}')
path.write_text(text.replace(old, new, 1))
