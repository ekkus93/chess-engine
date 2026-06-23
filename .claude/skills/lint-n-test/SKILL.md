---
description: Run ruff, mypy, pylint, and the full pytest suite. Use only when the user explicitly invokes this skill.
allowed-tools:
  - Bash(uv run python -m ruff *)
  - Bash(uv run python -m mypy *)
  - Bash(uv run python -m pylint *)
  - Bash(uv run python -m pytest *)
---

# Lint and Test

Run all linters and the full test suite in sequence. Report results clearly.

## Steps

Run these commands in order:

```bash
uv run python -m ruff check chess_game tests
uv run python -m mypy chess_game
uv run python -m pylint chess_game --score=y
uv run python -m pytest tests/ -q
```

Stop at the first failure and report the error. If all pass, confirm each check passed and the final test count.
