# Rust Chess Engine Post-Port Review Fix Spec

**Status:** Draft for implementation
**Date:** 2026-08-04
**Branch:** `master`
**Scope owner:** post-port review cleanup after Task 27 full port-program signoff
**Primary TODO:** `docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_TODO_2026-08-04.md`
**Related authoritative tracker:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`
**Related final report:** `docs/RUST_CHESS_ENGINE_PORT_IMPLEMENTATION_REPORT.md`

## 1. Purpose

The Rust chess-engine port is already signed off through Task 27. This spec does
not reopen Task 27 and must not relitigate the full migration, rewrite the
engine architecture, or weaken any existing correctness gate.

This follow-up exists to address concrete review findings discovered after the
port signoff:

1. make legal move generation fail loudly if the internal pseudo-legal generator
   emits a move that contradicts current position state;
2. normalize stale Task 21 status wording in the live tracker;
3. make historical TODO files unmistakably non-authoritative so future agents do
   not confuse them with the Rust-port tracker;
4. clarify documentation language around strict FEN parsing versus safe analysis
   positions.

The expected output is a small, auditable cleanup/hardening patch with no silent
behavior changes outside the listed areas.

## 2. Current repository facts

The active branch is `master`. The current signed-off Rust port uses:

- live tracker: `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`;
- final port report: `docs/RUST_CHESS_ENGINE_PORT_IMPLEMENTATION_REPORT.md`;
- Task 26 audit: `scripts/task_26_v0_1_audit.sh`;
- Task 27 audit: `scripts/task_27_full_port_audit.sh`.

The final port report already states that Rust is authoritative and Python is
reference-only. That decision must remain unchanged.

Task 21 is complete as a tuning, rejection, and activation-boundary lifecycle:
no tuned candidate is active, the tested production candidate was rejected, and
baseline weights remain authoritative. Future tuned-weight promotion is a
separate strength change and is not part of this cleanup.

## 3. Non-goals

This work must not:

- change legal chess semantics except to convert impossible internal
  pseudo-legal output from silent skip to typed failure;
- change FEN acceptance policy unless an existing accepted position is proven
  unsafe;
- activate tuned weights;
- introduce NNUE, SEE, tablebases, multithreaded search, or strength tuning;
- modify public ABI/JNI layouts unless required by a discovered validation
  failure;
- delete Python source or history;
- delete legacy TODO files without explicit inventory and archive/deprecation
  rationale;
- lower any CI, audit, lint, perft, differential, Android, robustness, or
  performance gate.

## 4. Required changes

### 4.1 Fail-loud legal movegen hardening

`crates/chess-core/src/position/legal.rs` currently generates pseudo-legal moves,
then filters them through current-state checks and king-safety validation. The
code has a typed `LegalMoveError::InvalidGeneratedMove`, but internal state
contradictions discovered during filtering may be skipped with `continue`.

The implementation must change this so that a pseudo-legal move that contradicts
current position state returns a typed error instead of being silently ignored.

Required behavior:

- If a pseudo-legal move source square is empty, return
  `LegalMoveError::InvalidGeneratedMove { current }`.
- If the moving piece exists but has the wrong color for `side_to_move`, return
  `LegalMoveError::InvalidGeneratedMove { current }`.
- If `generated_move_matches_state(current, moving_piece)` is false, return
  `LegalMoveError::InvalidGeneratedMove { current }`.
- Ordinary legal filtering must continue to reject pseudo-legal but king-unsafe
  moves without treating them as internal contradictions.
- Castling transit/destination attack rejection remains normal legal filtering,
  not an internal generator error.
- En-passant discovered-check rejection remains normal legal filtering, not an
  internal generator error.
- Public illegal move attempts through `Position::make_move` must still return
  `LegalMoveError::IllegalMove { current }` when the caller proposes a move that
  is simply not legal in the current position.

The goal is to surface contradictions between pseudo-legal generation and board
state, not to classify ordinary chess-illegal candidates as engine faults.

### 4.2 Legal movegen regression coverage

Add focused tests proving that internal pseudo-legal contradictions are
fail-loud. Because public APIs cannot normally construct a contradictory
pseudo-legal move list, the tests may use the narrowest crate-private test hook
necessary, provided that:

- the hook is compiled only for tests;
- it does not alter production legal generation;
- it is not exported from the public crate API;
- it exercises the same validation branch used by `Position::legal_moves()`.

Preferred implementation shape:

- factor the per-candidate validation into a small private helper;
- unit-test the helper with curated impossible moves or intentionally edited
  positions;
- keep normal legal movegen tests unchanged except for any new fail-loud witness.

The tests must also prove that ordinary legal filtering still works for at least
one king-unsafe pseudo-legal candidate and one castling/en-passant special-rule
case already covered by existing tests.

### 4.3 Task 21 status normalization

The live TODO summary and Task 21 gate identify Task 21 as complete, but the
Task 21 section header may still read as in progress. Normalize that wording so
all Task 21 status surfaces agree.

Required behavior:

- The live tracker summary row remains complete.
- The detailed Task 21 heading must read complete.
- The Task 21 gate language must continue to say that baseline weights remain
  authoritative and future tuned-weight promotion is a separate strength change.
- Do not alter the rejected-candidate evidence.
- Do not claim that any tuned candidate was accepted or activated.

### 4.4 Legacy TODO archive/deprecation policy

The repository contains older TODO files that predate or sit outside the
Rust-port tracker. These can confuse future agents. This follow-up must make the
authoritative status clear without destroying useful historical context.

Required behavior:

- Inventory legacy TODO-like files under `docs/` that are not the authoritative
  Rust-port tracker, the Rust-port task definitions, or this follow-up.
- Choose one policy and apply it consistently:
  - move legacy TODOs under an archive directory; or
  - add a clear deprecation banner to each legacy TODO; or
  - create an index that marks them historical and leave filenames unchanged.
- The chosen policy must make
  `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md` and this follow-up TODO the
  only active TODO documents for the Rust-port line of work.
- Do not delete historical files unless the patch also proves they are generated,
  duplicated, or obsolete artifacts whose removal is safe.
- Update documentation or audit scripts if necessary so future validation does
  not mistake archived TODOs for active work.

Preferred policy: add a single index file plus minimal per-file banners only if
necessary. A mass move is acceptable only if it does not break links used by
existing reports.

### 4.5 FEN policy clarification

The FEN parser is strict about six-field syntax, square notation, counts,
promotion-rank pawns, duplicate castling tokens, en-passant rank consistency,
and structural invariants. It also intentionally accepts safe analysis
positions that may not be game-reachable.

Documentation must state this precisely.

Required behavior:

- Clarify that `Position::from_fen` parses strict structural FEN for playable
  analysis positions, not only game-reachable positions.
- Explain that structural acceptance does not imply the position could have
  arisen from a legal game.
- Preserve existing safe-analysis support unless a concrete bug is found.
- Ensure docs do not overclaim that castling rights, en-passant targets, or king
  configurations are fully game-history-reachable.
- Cross-reference the existing analysis-position tests where appropriate.

## 5. Implementation constraints

- Keep changes small and local.
- Prefer typed errors over panics or silent fallback.
- Do not add first-party lint suppressions.
- Do not weaken `warnings = deny` or strict Clippy policy.
- Do not introduce runtime Python use into production Rust crates.
- Preserve the existing public API unless a stronger fail-loud behavior is a
  compatible error-path change.
- Preserve deterministic ordering of legal moves, UCI output, self-play,
  tuning, and validation tools.
- Preserve all version/schema constants unless a separate migration is added and
  validated.

## 6. Required validation

At minimum, the implementation must pass:

```bash
cargo fmt --all -- --check
cargo check --workspace --locked --all-targets --all-features
cargo clippy --workspace --locked --all-targets --all-features -- -D warnings
cargo test --workspace --locked --all-targets --all-features
cargo test --workspace --locked --release authoritative_perft
python3 scripts/differential_oracle.py
bash scripts/task_26_v0_1_audit.sh
bash scripts/task_27_full_port_audit.sh
```

If any Android-facing code, public facade contract, ABI, JNI, generated-artifact
policy, or workflow file is touched, also require the permanent Android JNI gate.

If performance-sensitive movegen/search code is touched, also run the permanent
performance gate or provide exact evidence that the change is fail-loud-only and
should not affect hot-path successful legal positions.

## 7. Acceptance criteria

This follow-up is complete only when all of the following are true:

- legal movegen contradictions fail with `LegalMoveError::InvalidGeneratedMove`;
- ordinary illegal caller moves still fail as caller-level illegal moves;
- existing legal move counts and authoritative perft are unchanged;
- Task 21 status wording is consistent across the live tracker;
- historical TODO files are clearly archived, indexed, or deprecated;
- FEN documentation accurately distinguishes structural analysis FEN from
  game-reachable position legality;
- Task 26 and Task 27 audits still pass;
- the final TODO for this follow-up records exact commit SHA, commands, CI runs,
  and any deviations.

## 8. Expected final note

The final implementation note should explicitly say:

- this work did not reopen Task 27;
- no tuned weights were activated;
- no chess-rule semantics changed for valid legal positions;
- the only core behavior change is fail-loud handling for impossible internal
  pseudo-legal generator output;
- the authoritative Rust-port tracker remains
  `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`.
