
## TODO.md

```md
# TODO.md

This file is intentionally strict and explicit so that a weaker coding model can make progress without inventing chess rules.

Read `THE_PLAN.md` first. Follow this TODO in order. Do not skip phases. Do not add AI or GUI work until the rules engine is correct.

---

## Global rules for the model editing this repo

### Rule 1: never mutate the board from `main.py`
All moves must go through a single validated API.

### Rule 2: do not preserve broken behavior for compatibility
If an existing test encodes incorrect chess behavior, fix or replace the test.

### Rule 3: every completed task needs tests
When implementing a rule, add or update tests in the same change.

### Rule 4: use the coordinate convention from `THE_PLAN.md`
- `row 0 = rank 8`
- `row 7 = rank 1`
- `col 0 = file a`
- `col 7 = file h`
- `e2 = (6, 4)`
- white moves "up" the internal array (toward smaller rows)

### Rule 5: do not implement AI yet
Any AI code is blocked until all rules tasks are green.

---

## Phase 0 — Inspect and clean the foundation

### T0.3 Remove invalid direct-mutation flow from CLI
Current `main.py` directly moves pieces on the board and flips turns without validation. That is wrong.

- [x] Replace raw board mutation in `main.py` with a call to a single engine method.
- [x] The CLI cannot make a move without validation.
- [x] The CLI does not directly assign `board[to] = piece`.
- [x] The CLI does not directly flip the turn.

**Acceptance criteria**
- The CLI cannot make a move without validation.
- The CLI does not directly assign `board[to] = piece`.
- The CLI does not directly flip the turn.

---

## Phase 1 — Define clean core types and conventions

### T1.1 Define `Piece` representation
The current board stores strings like `"Pawn"`, which loses color information.

- [ ] Create an explicit piece representation.
- [ ] It must encode both color and kind.
- [ ] Prefer a dataclass and enums, but a compact validated representation is acceptable.

**Recommended shape**
```python
@dataclass(frozen=True)
class Piece:
    color: Color
    kind: PieceType