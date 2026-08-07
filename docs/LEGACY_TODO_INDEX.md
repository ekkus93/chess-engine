# TODO Authority and Legacy Index

This file prevents historical planning documents from being mistaken for current implementation instructions.

## Active and authority documents

| Classification | Path | Authority |
|---|---|---|
| Completed Rust-port tracker | `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md` | Authoritative completion record for the Rust-port program. |
| Completed Rust-port task definitions | `docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md` | Detailed definitions and evidence for the completed Rust-port program. |
| Authority index, not an implementation TODO | `docs/LEGACY_TODO_INDEX.md` | Classifies active, completed-authority, and historical TODO-named documents. |

There is currently **no active implementation TODO**. A future program becomes active only when it is explicitly added to this authority table and to the permanent TODO-authority audit.

## Exhaustive classification rule

Apart from this authority index, every other Markdown file directly under `docs/` whose filename contains `TODO` and is not one of the two completed Rust-port authority documents above is a historical or legacy reference. Those files preserve implementation history, but they are not active instructions and must not override the completed Rust-port authority records or any future TODO explicitly registered in the authority table.

Inventory captured on 2026-08-05, reclassified at S2-16 closure on 2026-08-07, activated for S3 on 2026-08-07, and reclassified again at S3 closure on 2026-08-07: **73 TODO-named files total; 2 authority documents; 1 authority index; 70 historical.**

## Historical TODO inventory

- `docs/7FAILING_TESTS_TODO.md`
- `docs/AI_UNIT_TEST_COVERAGE_TODO.md`
- `docs/BIG_FIX1_TODO.md`
- `docs/BLACK_IMPROVEMENTS1_TODO.md`
- `docs/BLACK_IMPROVEMENTS2_TODO.md`
- `docs/BLACK_IMPROVEMENTS3_TODO.md`
- `docs/BOARD_FIX1_TODO.md`
- `docs/CHESS_ENGINE_AI_CLEANUP_TODO.md`
- `docs/CHESS_ENGINE_AI_SEARCH_FIX_TODO.md`
- `docs/CHESS_ENGINE_AI_TEST_RUNTIME_FIX_TODO.md`
- `docs/CHESS_ENGINE_AI_TEST_RUNTIME_REPO_HYGIENE_TODO.md`
- `docs/CHESS_ENGINE_AI_TT_REPAIR_TODO.md`
- `docs/CHESS_ENGINE_FIX8_FAST_SUITE_RUNTIME_TODO.md`
- `docs/CHESS_ENGINE_OPENING_BOOK_FINAL_FIX_TODO.md`
- `docs/CHESS_ENGINE_OPENING_BOOK_FIX_TODO.md`
- `docs/CHESS_ENGINE_OPENING_BOOK_TODO.md`
- `docs/CHESS_ENGINE_PLAN_FIX_TODO.md`
- `docs/CHESS_ENGINE_PROMOTION_CLEANUP_TODO.md`
- `docs/CHESS_ENGINE_REPAIR_FIX2_TODO.md`
- `docs/CHESS_ENGINE_REPAIR_FIX3_TODO.md`
- `docs/CHESS_ENGINE_REPAIR_FIX4_TODO.md`
- `docs/CHESS_ENGINE_REPAIR_TODO.md`
- `docs/CHESS_ENGINE_SLOW_STRENGTH_FIX10_TODO.md`
- `docs/CHESS_ENGINE_SLOW_STRENGTH_FIX9_TODO.md`
- `docs/CHESS_ENGINE_TEXEL_FAIL_LOUD_TODO.md`
- `docs/CHESS_ENGINE_TEXEL_FIX2_TODO.md`
- `docs/CHESS_ENGINE_TEXEL_FIX3_TODO.md`
- `docs/CHESS_ENGINE_TEXEL_FIX4_TODO.md`
- `docs/CHESS_ENGINE_TEXEL_FIX5_TODO.md`
- `docs/CHESS_ENGINE_TEXEL_FIX6_TODO.md`
- `docs/CHESS_ENGINE_TEXEL_FIX7_TODO.md`
- `docs/CHESS_ENGINE_TEXEL_FIX_TODO.md`
- `docs/EDGE_CASES_TODO.md`
- `docs/ENDGAME1_TODO.md`
- `docs/ENDGAME2_TODO.md`
- `docs/ENDGAME_FIX1_TODO.md`
- `docs/ENDGAME_FIX2_TODO.md`
- `docs/INT_TEST1_TODO.md`
- `docs/LINT_FIX1_TODO.md`
- `docs/LINT_FIX2_TODO.md`
- `docs/LINT_FIX3_TODO.md`
- `docs/MIDDLEGAME_FIX1_TODO.md`
- `docs/REFACTOR_BOARD_TODO.md`
- `docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_TODO_2026-08-04.md`
- `docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_TODO_2026-08-07.md`
- `docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md`
- `docs/RUST_ENGINE_REVIEW_FIX_TODO_2026-08-02.md`
- `docs/STOCKFISH1_TODO.md`
- `docs/STRATEGY10_TODO.md`
- `docs/STRATEGY11_TODO.md`
- `docs/STRATEGY12_TODO.md`
- `docs/STRATEGY13_TODO.md`
- `docs/STRATEGY14_TODO.md`
- `docs/STRATEGY15_TODO.md`
- `docs/STRATEGY1_TODO.md`
- `docs/STRATEGY2_TODO.md`
- `docs/STRATEGY3_TODO.md`
- `docs/STRATEGY4_TODO.md`
- `docs/STRATEGY5_TODO.md`
- `docs/STRATEGY6_TODO.md`
- `docs/STRATEGY7_TODO.md`
- `docs/STRATEGY8_TODO.md`
- `docs/STRATEGY9_TODO.md`
- `docs/TEXEL1_TODO.md`
- `docs/TODO.md`
- `docs/UCI1_TODO.md`
- `docs/UNIT_TEST1_TODO.md`
- `docs/WHITE_IMPROVEMENTS1_TODO.md`
- `docs/WHITE_IMPROVEMENTS2_TODO.md`
- `docs/WHITE_IMPROVEMENTS3_TODO.md`

## Maintenance rule

When a new active TODO is intentionally introduced, add it to the authority table and update the permanent TODO-authority audit. When an active program closes, move its TODO into the historical inventory and update the counts. Otherwise, a newly added `docs/*TODO*.md` file is historical by default and must be listed above.
