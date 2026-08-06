import re
from pathlib import Path

path = Path("crates/chess-search/src/alpha_beta.rs")
text = path.read_text(encoding="utf-8")
pattern = re.compile(
    r"(?m)^(?P<indent>\s*)null_move_pruning: (?P<value>[^,\n]+),\n(?P=indent)weights:"
)
text, count = pattern.subn(
    lambda match: (
        f"{match.group('indent')}null_move_pruning: {match.group('value')},\n"
        f"{match.group('indent')}futility_pruning: false,\n"
        f"{match.group('indent')}weights:"
    ),
    text,
)
if count != 3:
    raise SystemExit(f"expected three test context initializers, found {count}")
path.write_text(text, encoding="utf-8")
Path(__file__).unlink()
