from pathlib import Path


path = Path("crates/chess-search/src/iterative_deepening.rs")
text = path.read_text()
for old, new in (
    ("        alpha: window.alpha(),", "        alpha: policy.window.alpha(),"),
    ("        beta: window.beta(),", "        beta: policy.window.beta(),"),
):
    if text.count(old) != 1:
        raise SystemExit(f"unexpected aspiration diagnostic field: {old!r}")
    text = text.replace(old, new, 1)
path.write_text(text)
