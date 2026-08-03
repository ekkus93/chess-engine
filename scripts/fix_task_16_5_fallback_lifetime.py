#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
path = root / "crates/chess-search/src/iterative_deepening.rs"
text = path.read_text(encoding="utf-8")
old = '''    Ok(tokens.iter().next().map_or(
        SearchCancellationFallback::NoLegalMove,
        |token| SearchCancellationFallback::FirstLegalMove(token.move_made()),
    ))
'''
new = '''    let fallback = tokens.iter().next().map_or(
        SearchCancellationFallback::NoLegalMove,
        |token| SearchCancellationFallback::FirstLegalMove(token.move_made()),
    );
    Ok(fallback)
'''
if text.count(old) != 1:
    raise RuntimeError(f"expected one fallback expression, found {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Task 16.5 fallback lifetime fixed")
