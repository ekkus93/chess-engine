# TODO Authority and Legacy Index

This file prevents historical planning documents from being mistaken for current implementation instructions.

## Active and authority documents

| Classification | Path | Authority |
|---|---|---|
| Completed Rust-port tracker | `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md` | Authoritative completion record for the Rust-port program. |
| Completed Rust-port task definitions | `docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md` | Detailed definitions and evidence for the completed Rust-port program. |
| Archived Android UI/UX redesign planning tracker | `docs/RUST_ANDROID_UI_UX_REDESIGN_TODO_2026-08-10.md` | Preserved original implementation checklist. Its historical header/unchecked manual-local items are superseded for shipped-state authority by `docs/RUST_ANDROID_UI_UX_REDESIGN_CLOSURE_EVIDENCE_2026-08-10.md`. |
| Android UI/UX redesign closure evidence | `docs/RUST_ANDROID_UI_UX_REDESIGN_CLOSURE_EVIDENCE_2026-08-10.md` | Authoritative shipped-state, exact-SHA CI, visual-evidence, anti-fallback, and manual-follow-up record for the completed Android redesign. |
| Authority index, not an implementation TODO | `docs/LEGACY_TODO_INDEX.md` | Classifies active, completed-authority, and historical TODO-named documents. |

There is currently **no active implementation TODO** registered by this index. The Android redesign tracker is retained as planning history and must be interpreted through its closure-evidence document rather than by treating its historical `proposed / not started` header or unchecked manual/local-only items as current product state. The Rust console implementation TODO is retained as historical implementation/planning evidence now that the console product and shared application layer are already present. The Rust TUI implementation record remains important regression history (its automated implementation/PTY validation is complete while a short manual real-terminal smoke list remains open), but it is no longer the active code-implementation authority. Closed TUI hardening and S2, S3, S4 strength/tuning, S4 closure-hardening, and prior frontend TODOs are historical and cannot override the completed Rust-port authority records or a future TODO explicitly registered as active.

## Exhaustive classification rule

Apart from this authority index, every other Markdown file directly under `docs/` whose filename contains `TODO`, is not one of the two completed Rust-port authority documents above, and is not explicitly registered as active in the authority table is historical/planning evidence unless a separate closure authority is listed above. Those files preserve implementation history, but they are not active instructions and must not override completed authority records, closure evidence, or a future TODO explicitly registered in the authority table.

Inventory captured on 2026-08-05, reclassified at S2-16 closure on 2026-08-07, activated for S3 on 2026-08-07, reclassified again at S3 closure on 2026-08-07, activated for S4 on 2026-08-07, reclassified at S4 closure on 2026-08-07, updated for the Rust TUI program on 2026-08-07, updated for Rust TUI test/coverage hardening on 2026-08-08, updated for the Rust TUI post-milestone review-fix pass on 2026-08-09, activated for the Rust console/application-sharing program on 2026-08-09, activated for the Android UI/UX redesign on 2026-08-10, reclassified at automated Android UI/UX redesign closure on 2026-08-10, and updated for the Android UI/UX post-closure review-fix pass on 2026-08-10: **81 TODO-named files total; 2 completed Rust-port authority documents; 0 active implementation TODOs; 1 Android closure-evidence authority; 1 authority index; 78 historical/planning TODO records including the archived Android tracker.**

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
- `docs/RUST_ANDROID_UI_UX_REDESIGN_TODO_2026-08-10.md`
- `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md`
- `docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_TODO_2026-08-04.md`
- `docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_TODO_2026-08-07.md`
- `docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_TODO_2026-08-07.md`
- `docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_TODO_2026-08-07.md`
- `docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md`
- `docs/RUST_CONSOLE_TODO.md`
- `docs/RUST_ENGINE_REVIEW_FIX_TODO_2026-08-02.md`
- `docs/RUST_TUI_REVIEW_FIX_TODO_2026-08-09.md`
- `docs/RUST_TUI_TEST_COVERAGE_HARDENING_TODO.md`
- `docs/RUST_TUI_TODO.md`
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

When a new active TODO is intentionally introduced, add it to the authority table and update the permanent TODO-authority audit. When an active program closes, reclassify its tracker as historical/planning evidence and register its closure authority if one exists. Otherwise, a newly added `docs/*TODO*.md` file is historical by default and must be listed above.
