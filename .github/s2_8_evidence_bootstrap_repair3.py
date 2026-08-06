from pathlib import Path

path = Path('.github/s2_8_evidence_bootstrap.py')
text = path.read_text(encoding='utf-8')
for name in [
    '.github/s2_8_evidence_bootstrap_repair.py',
    '.github/s2_8_evidence_bootstrap_repair2.py',
    '.github/s2_8_evidence_bootstrap_repair3.py',
]:
    old = f'Path("{name}").unlink()'
    new = f'Path("{name}").unlink(missing_ok=True)'
    text = text.replace(old, new)
path.write_text(text, encoding='utf-8')
Path(__file__).unlink()
