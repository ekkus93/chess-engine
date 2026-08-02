# Rust Engine Review Fix Spec — 2026-08-02

**Status:** Implemented; exact-head validation pending  
**Branch:** `rust-engine`  
**Companion TODO:** `docs/RUST_ENGINE_REVIEW_FIX_TODO_2026-08-02.md`  
**Origin:** Comprehensive Rust code review after Task 12 completion  
**Primary tracker:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`

---

## 1. Purpose

This document specifies the fix pass required before beginning or completing Task 13, "Reference search and alpha-beta." The review found that Tasks 0 through 12 are broadly implemented correctly, but several issues should be resolved before search work depends on the current APIs and documentation.

The most important issue is architectural: the efficient generated-legal make/unmake path exists inside `chess-core`, but it is not available to the separate `chess-search` crate. If Task 13 is implemented on top of the current public `Position::make_move` API, search will either regenerate legality for every child move or be forced to duplicate/reach around core internals. This would violate the intended no-clone-per-child and no-avoidable-regeneration search architecture.

The remaining issues are smaller but still worth fixing now: literal `Game` API coverage, stable divide timing output, stale live TODO next-operation text, incomplete Task 25 status cleanup, and explicit documentation/tests for the FEN parser's analysis-position policy.

---

## 2. Scope

This fix pass covers exactly these areas:

1. Search-safe generated legal move application API.
2. Explicit `Game` reset / set-position semantics.
3. Stable elapsed-time output for `chess-tools divide`.
4. Live TODO footer correction from stale Task 9 operations to Task 13 operations.
5. Task 25 checklist cleanup to reflect actual CI, documentation, and command coverage.
6. Explicit FEN policy documentation and tests for illegal-but-parseable analysis states.
7. Exact validation evidence before the review-fix task is marked complete.

This pass must not implement Task 13 search itself. It prepares the codebase so Task 13 can be implemented cleanly.

---

## 3. Non-goals

- Do not implement reference minimax, alpha-beta, quiescence, transposition tables, iterative deepening, UCI search, FFI, JNI, self-play, or tuning.
- Do not rewrite the rules core broadly.
- Do not weaken CI, lint, rustdoc, perft, or differential validation gates.
- Do not add first-party `allow` or `expect` lint suppressions.
- Do not add unsafe code to `chess-core` or `chess-search`.
- Do not change Python reference code as part of this pass.
- Do not introduce clone-per-child as a production search fallback.
- Do not silently auto-load configuration, weights, opening books, or search settings.

---

## 4. Global engineering constraints

The following constraints remain binding:

- Work on `rust-engine` unless a follow-up branch is explicitly requested.
- Keep `chess-core` independent of search, UCI, FFI, JNI, filesystems, and UI.
- Keep `chess-search` dependent only on portable core/search-support crates.
- Keep adapters outward-facing.
- Keep normal rule/search operations deterministic and allocation-conscious.
- Keep errors fail-loud and non-mutating on public failure paths.
- Preserve exact make/unmake restoration of board state, counters, castling, en-passant, side to move, cached kings, redundant bitboards, and Zobrist state.
- Preserve the existing score convention: positive scores favor the side to move.
- Preserve CI's strict interpretation that any first-party rustfmt, compiler, Clippy, test, rustdoc, or build finding is a source bug.

---

## 5. Fix 1 — Search-safe generated legal move application

### 5.1 Problem

`Position::make_move(current: Move)` is public and safe, but it calls `Position::is_legal_move`, which regenerates the current legal move list before applying the move. The efficient generated-legal path, `make_generated_legal_move`, is currently crate-private inside `chess-core`.

That split is good for protecting arbitrary public callers, but it is not sufficient for Task 13. Search is implemented in `chess-search`, a separate crate. Search needs to iterate legal moves generated for the current node and apply each one without rechecking membership by regenerating the same list.

### 5.2 Required outcome

`chess-search` must be able to do this efficiently and safely:

1. Ask the current `Position` for the legal moves at a node.
2. Iterate those legal moves in deterministic order.
3. Apply one of those legal moves without regenerating the legal move list.
4. Search the child.
5. Unmake using the returned `PositionUndo`.
6. Prove the root/node position is restored exactly.

The API must prevent external callers from constructing fake "trusted legal" identities that bypass legality. If a stale token or wrong-position token is used, the method must fail before mutation.

### 5.3 Preferred design

Use an additive token-based API rather than exposing the raw crate-private generated-legal function directly.

Recommended shape:

```rust
pub struct LegalMoveToken { /* private fields */ }

impl LegalMoveToken {
    pub const fn move_made(&self) -> Move;
}

pub struct LegalMoveTokenList { /* fixed-capacity storage */ }

impl LegalMoveTokenList {
    pub const fn len(&self) -> usize;
    pub const fn is_empty(&self) -> bool;
    pub fn iter(&self) -> impl ExactSizeIterator<Item = LegalMoveToken> + '_;
}

impl Position {
    pub fn legal_move_tokens(&mut self) -> Result<LegalMoveTokenList, LegalMoveError>;
    pub fn make_legal_token(
        &mut self,
        token: LegalMoveToken,
    ) -> Result<PositionUndo, LegalMoveError>;
}
```

Exact names may differ, but the semantics must be equivalent.

`LegalMoveToken` should include enough origin data to reject stale or wrong-position use before mutation. At minimum, it should bind to:

- the exact packed move identity;
- the source position's canonical Zobrist key;
- the source side to move.

If practical, include additional cheap origin metadata such as fullmove number and halfmove clock. The Zobrist key is the core identity, but adding counters makes stale-token diagnostics more precise and avoids conflating repetition identity with full position state in this public safety boundary.

### 5.4 Safety requirements

- `LegalMoveToken` fields must be private.
- External crates must not be able to construct a token except by receiving it from the current position's legal-token generator.
- `make_legal_token` must reject a token whose origin does not match the current position before any mutation.
- `make_legal_token` must still validate that the encoded move matches the current board state before mutation.
- Debug builds and tests should assert that the resulting position matches authoritative recomputation expectations, including Zobrist.
- The existing safe public `make_move(Move)` should remain available for callers that only have a raw `Move`.
- The existing crate-private generated path may remain as the internal primitive, but it must not become an unsafe public bypass.

### 5.5 Performance requirements

- Token generation should reuse the legal move generation path; it should not create heap-heavy structures.
- The token list should be bounded with the same or equivalent capacity as the existing move list.
- Applying a valid token must not regenerate legal moves.
- Search tests in `chess-search` must prove that the API is usable from outside `chess-core`.

### 5.6 Tests

Add tests for:

- token list length and move identities match `legal_moves()` for representative positions;
- a legal token applies and unmakes exactly;
- stale token after any move is rejected before mutation;
- token from a different position is rejected before mutation;
- token from the same board layout but different side/counters is handled according to the documented origin policy;
- every accepted token in a curated corpus makes, validates invariants, unmakes, and restores exact equality;
- `chess-search` can call the public token API without depending on crate-private core internals.

---

## 6. Fix 2 — Explicit `Game` reset / set-position semantics

### 6.1 Problem

The detailed Task 10 definition requires reset, set-position, play, undo, and status operations. The current `Game` API supports construction, status, legal moves, play, undo, and detached search history. It does not expose explicit reset or set-position operations.

This may be functionally replaceable by constructing a new `Game`, but the TODO's literal API requirement should either be implemented or intentionally revised. Implementing it is preferred because UCI and future adapter code will need explicit `ucinewgame` and `position fen ...` style state replacement.

### 6.2 Required outcome

Add explicit game state replacement APIs with unambiguous history semantics.

Recommended shape:

```rust
impl Game {
    pub fn reset_to_starting(&mut self);
    pub fn set_position(&mut self, position: Position);
}
```

The exact names may differ, but the behavior must be clear and tested.

### 6.3 Semantics

`reset_to_starting`:

- replaces the current position with `Position::starting()`;
- clears played moves;
- resets `position_hashes` to exactly one root hash for the starting position;
- returns no error unless the chosen API has a broader fallible abstraction.

`set_position(position)`:

- replaces the current position with the provided validated `Position`;
- clears played moves;
- resets `position_hashes` to exactly one root hash for the new root;
- does not preserve previous repetition history;
- does not silently merge old history with the new root.

### 6.4 Tests

Add tests proving:

- reset after one or more moves returns to `Game::starting()` state;
- set-position after moves clears move history and hash history;
- status after set-position is computed from the new root;
- search history created after set-position starts from the new root only;
- stale `GameUndo` tokens from before reset/set-position are rejected or impossible to use successfully.

---

## 7. Fix 3 — Stable elapsed-time output for divide

### 7.1 Problem

The detailed Task 11 definition requires `divide` to print canonical UCI root moves, child counts, total, and elapsed time. The current `chess-tools divide` prints the rows and total but not elapsed time.

### 7.2 Required outcome

Add elapsed-time reporting to `chess-tools divide` while preserving stable machine-readable output.

Recommended format:

```text
<uci>\t<nodes>
...
total\t<nodes>
elapsed_nanos\t<nanos>
```

Use `elapsed_nanos` rather than human-readable duration text because it is deterministic in format and easy for scripts to parse. The value itself will naturally vary and should not be compared exactly in tests beyond being parseable and nonzero for nontrivial work.

### 7.3 Compatibility policy

- Keep existing move rows unchanged.
- Keep `total\t<nodes>` unchanged.
- Add elapsed output after total.
- Update tests to account for the additional line.
- Update documentation/examples that show divide output.

---

## 8. Fix 4 — Live TODO footer correction

### 8.1 Problem

The live TODO summary says Task 13 is active, but the bottom "Immediate next operations" section is stale and still describes Task 9 Zobrist work.

### 8.2 Required outcome

Replace the stale footer with Task 13 preparation and implementation operations.

Recommended replacement:

1. Complete the review-fix pass in `docs/RUST_ENGINE_REVIEW_FIX_TODO_2026-08-02.md`.
2. Add the search-safe legal-token make/unmake API required by Task 13.
3. Begin Task 13 reference search only after the review-fix validation gate passes.
4. Implement no-prune reference negamax/minimax first.
5. Implement alpha-beta only after reference search and terminal fixtures are stable.
6. Validate search immutability and exact root restoration before marking Task 13 complete.

---

## 9. Fix 5 — Task 25 checklist cleanup

### 9.1 Problem

Task 25 is correctly marked partial, but some subitems appear stale. Since Tasks 11 and 12 added perft tooling, differential tooling, evaluation docs, and weight tooling, Task 25 should distinguish what now exists from what remains incomplete.

### 9.2 Required outcome

Update Task 25 in the live TODO to reflect current truth:

Already present:

- Linux rustfmt/check/Clippy/tests/rustdoc/debug/release CI;
- Python validation preserved separately;
- exact-SHA status publisher / dispatcher if still present and verified;
- release depth-four perft in CI;
- scheduled/manual slow depth-five perft workflow;
- workspace architecture docs;
- core values/coordinates/moves docs;
- position/invariants docs;
- FEN/UCI docs;
- attack generation docs;
- pseudo/legal generation docs;
- make/unmake docs;
- Zobrist/hash docs;
- game/draw docs;
- perft/differential docs;
- baseline evaluator docs;
- perft/divide/legal/play/suite/oracle CLI tooling;
- eval/eval-bench/weight export/validate CLI tooling.

Still incomplete unless separately verified:

- AArch64 CI;
- Android compile CI;
- JNI CI;
- Miri;
- sanitizer;
- fuzzing;
- nightly/longer perft beyond current scheduled depth-five policy if required;
- scheduled strength testing;
- UCI executable commands;
- Android commands;
- self-play commands;
- tuning commands;
- versioned generated-artifact policy across all future artifacts;
- Task 25 final gate.

Do not mark Task 25 complete in this fix pass.

---

## 10. Fix 6 — FEN analysis-position policy documentation and tests

### 10.1 Problem

The current FEN parser is strict about syntax and core structural invariants, but it is not a full reachability/legal-position validator. This is normal for engine analysis tooling, but the policy should be explicit because the TODO uses the phrase "strict playable FEN."

Examples requiring explicit policy:

- adjacent kings;
- side not to move already attacking the side-to-move king in an impossible-history way;
- castling rights present when the home king or rook is missing;
- en-passant target with no legal en-passant capture;
- both sides in check;
- positions legal as analysis setups but unreachable from the standard initial position.

### 10.2 Required outcome

Document and test the parser policy. The project may choose either a stricter parser or an analysis-position parser, but the choice must be intentional.

Preferred policy for an engine core:

- Keep `Position::from_fen` as a strict syntax and structurally valid analysis-position parser.
- Reject malformed syntax, invalid counters, invalid en-passant target rank, pawns on promotion ranks, missing kings, multiple kings, and redundant-state invariant failures.
- Do not require proof of reachability from the standard initial position.
- Do not require castling rights to imply the current presence of the matching home king and rook; legal move generation already refuses castling without the actual pieces and empty path.
- Do not require the FEN en-passant target to be legally capturable; repetition Zobrist already canonicalizes non-capturable en-passant targets away.
- Decide explicitly whether adjacent kings and both-kings-in-check states are rejected or accepted as analysis positions. If accepted, ensure legal move generation and status code fail safely and do not panic. If rejected, implement validation and add error variants.

### 10.3 Documentation

Add or update a rules/notation document to include a section named "FEN validation policy". It must define:

- syntax validation;
- structural validation;
- analysis-state tolerance;
- what is rejected;
- what is intentionally accepted;
- consequences for Zobrist, legal move generation, and differential corpus use.

### 10.4 Tests

Add tests that lock in the policy for:

- castling rights without matching home rook;
- castling rights without matching home king;
- non-capturable en-passant target;
- adjacent kings;
- both kings in check;
- side-to-move already in check;
- side-not-to-move in check;
- malformed FEN still rejected without panic.

If a case is intentionally accepted, the test must prove downstream operations do not panic. If a case is rejected, the test must assert the exact structured error category.

---

## 11. Documentation and tracker requirements

This fix pass must update, at minimum:

- `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`;
- `docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md` if present and used as the live phase report;
- relevant domain docs for make/unmake/search boundary, game history, divide tooling, and FEN policy.

Do not claim Task 13 is started or complete merely because this fix pass prepares an API for Task 13.

---

## 12. Validation gate

Before marking this review-fix pass complete, run the strict existing gate on the exact final SHA:

```bash
cargo fmt --all -- --check
cargo check --locked --workspace --all-targets --all-features
cargo clippy --locked --workspace --all-targets --all-features -- -D warnings
cargo test --locked --workspace --all-features
RUSTDOCFLAGS="-D warnings" cargo doc --locked --workspace --all-features --no-deps
cargo build --locked --workspace --all-features
cargo build --locked --workspace --all-features --release
cargo test --locked -p chess-core --release authoritative_perft_depth_four -- --ignored --exact
python scripts/differential_oracle.py \
  --binary target/release/chess-tools \
  --corpus fixtures/differential_corpus.tsv \
  --games 12 \
  --plies 48 \
  --seed 0xC0FFEE
```

If CI is used as the authoritative execution environment, record:

- exact commit SHA;
- workflow run ID;
- job ID;
- test count;
- perft result;
- differential corpus summary;
- any accepted external warnings/notices.

---

## 13. Completion criteria

This fix pass is complete only when:

- `chess-search` has a safe efficient path to apply generated legal moves without public revalidation;
- stale/wrong-position legal tokens fail before mutation;
- `Game` reset/set-position semantics are explicit and tested, or the TODO is deliberately revised with a clear rationale;
- `chess-tools divide` emits stable elapsed-time output;
- the live TODO footer points to Task 13, not Task 9;
- Task 25 accurately reflects completed versus remaining CI/docs/command work;
- FEN policy is documented and covered by tests;
- strict validation passes on the exact final SHA;
- no temporary one-shot workflow or diagnostic artifact remains unless explicitly documented.
