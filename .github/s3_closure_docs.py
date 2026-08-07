from pathlib import Path

path = Path('docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_SPEC_2026-08-07.md')
text = path.read_text()
replacements = [
    (
        '**Status:** Active planning authority; implementation not yet complete  ',
        '**Status:** Complete — program closed without promotion  ',
    ),
    (
        '**Companion TODO:** `docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_TODO_2026-08-07.md`  ',
        '**Companion TODO:** `docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_TODO_2026-08-07.md`  \n**Final report:** `docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_IMPLEMENTATION_REPORT.md`  ',
    ),
]
for old, new in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'expected one spec witness, found {count}: {old!r}')
    text = text.replace(old, new, 1)
path.write_text(text)
