from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one replacement witness, found {count}: {old!r}")
    p.write_text(text.replace(old, new, 1))


# S3-1.2: PositionEditor is an internal mutation capability, not public API.
replace_once(
    "crates/chess-core/src/position/mod.rs",
    "pub use editor::PositionEditor;\n",
    "use editor::PositionEditor;\n",
)
replace_once(
    "crates/chess-core/src/lib.rs",
    "#[doc(hidden)]\npub use position::{PositionEditor, PositionMutationError};\n",
    "#[doc(hidden)]\npub use position::PositionMutationError;\n",
)
replace_once(
    "crates/chess-core/src/position/editor.rs",
    "/// Only `Position` can construct an editor, so adapters cannot mutate mailbox\n/// or bitboard state directly.\n",
    "/// Only `Position` can construct an editor, so adapters cannot mutate mailbox\n/// or bitboard state directly. The editor deliberately does **not** update the\n/// Zobrist key: reversible move/search-null callers own incremental hash updates\n/// around editor mutations and verify them against authoritative recomputation.\n",
)

editor = Path("crates/chess-core/src/position/editor.rs")
text = editor.read_text()
if "editor_mutation_is_hash_neutral_until_the_caller_updates_hash_state" not in text:
    text += r'''

#[cfg(test)]
mod tests {
    use crate::{Piece, PieceKind, Position, Square};

    #[test]
    fn editor_mutation_is_hash_neutral_until_the_caller_updates_hash_state() {
        let mut position = Position::starting();
        let original_hash = position.zobrist();
        let square: Square = "a2".parse().expect("fixture square parses");
        let pawn = Piece::new(crate::Color::White, PieceKind::Pawn);

        {
            let mut editor = position.editor();
            assert_eq!(editor.remove_piece(square), Ok(pawn));
        }
        assert_eq!(position.zobrist(), original_hash);

        {
            let mut editor = position.editor();
            editor.add_piece(square, pawn).expect("fixture restores");
        }
        assert_eq!(position.zobrist(), original_hash);
        assert_eq!(position.zobrist(), position.recomputed_zobrist());
        position.validate_invariants().expect("restored position is valid");
    }
}
'''
    editor.write_text(text)

replace_once(
    "docs/RUST_MAKE_UNMAKE.md",
    "- cached king squares.\n\nIt also updates:\n",
    "- cached king squares.\n\n`PositionEditor` is intentionally an internal board-representation capability. It does not update the Zobrist key itself and is not exported from `chess-core`; the reversible move and search-null paths own incremental hash transitions around editor mutations and verify the stored key against authoritative recomputation in debug/test coverage.\n\nIt also updates:\n",
)

# S3 spec precision: distinguish the runtime vector from the named optimizer vector.
replace_once(
    "docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_SPEC_2026-08-07.md",
    "`EvaluationWeights`. The current dense tunable vector has 816 signed scalar\nvalues. S3 should treat these weights as an existing tuning surface, not as an\nalready-validated strength improvement.\n",
    "`EvaluationWeights`. The canonical runtime weight vector has 816 signed scalar\nvalues. The named optimizer surface contains 810 tunable scalars; six fixed-zero\nstructural slots (king material plus pawn/king mobility, each in two phases) are\nexcluded from tuning. S3 should treat the 810 named parameters as the tuning\nsurface, not as an already-validated strength improvement.\n",
)

# S3-1.3: process-level stale-result and repeated-stop coverage.
uci = Path("crates/chess-uci/tests/uci_process.rs")
text = uci.read_text()
if "position_replacement_discards_active_search_without_stale_bestmove" not in text:
    text += r'''

#[test]
fn position_replacement_discards_active_search_without_stale_bestmove() {
    let mut process = UciProcess::spawn();
    process.send("position startpos");
    process.send("go infinite");
    let before_replace = process.read_until(OUTPUT_TIMEOUT, |line| line.starts_with("info depth "));
    assert!(before_replace.iter().all(|line| !line.starts_with("bestmove ")));

    process.send("position startpos moves e2e4");
    process.send("isready");
    let replacement = process.read_until(OUTPUT_TIMEOUT, |line| line == "readyok");
    assert!(
        replacement.iter().all(|line| !line.starts_with("bestmove ")),
        "position replacement leaked stale bestmove: {replacement:?}"
    );

    process.send("go depth 1");
    let fresh = process.read_through_bestmove();
    assert_legal_bestmove(game_after_moves(&["e2e4"]), bestmove_line(&fresh));
    process.quit_cleanly();
}

#[test]
fn ucinewgame_discards_active_search_without_stale_bestmove() {
    let mut process = UciProcess::spawn();
    process.send("position startpos moves e2e4");
    process.send("go infinite");
    let before_new_game = process.read_until(OUTPUT_TIMEOUT, |line| line.starts_with("info depth "));
    assert!(before_new_game.iter().all(|line| !line.starts_with("bestmove ")));

    process.send("ucinewgame");
    process.send("isready");
    let reset = process.read_until(OUTPUT_TIMEOUT, |line| line == "readyok");
    assert!(
        reset.iter().all(|line| !line.starts_with("bestmove ")),
        "ucinewgame leaked stale bestmove: {reset:?}"
    );

    process.send("go depth 1");
    let fresh = process.read_through_bestmove();
    assert_legal_bestmove(Game::starting(), bestmove_line(&fresh));
    process.quit_cleanly();
}

#[test]
fn repeated_stop_and_restart_cycles_emit_exactly_one_bestmove_per_search() {
    let mut process = UciProcess::spawn();
    process.send("position startpos");

    for cycle in 0..3 {
        process.send("go infinite");
        let before_stop = process.read_until(OUTPUT_TIMEOUT, |line| line.starts_with("info depth "));
        assert!(before_stop.iter().all(|line| !line.starts_with("bestmove ")));
        process.send("stop");
        let after_stop = process.read_through_bestmove();
        assert_legal_bestmove(Game::starting(), bestmove_line(&after_stop));
        let bestmove_count = before_stop
            .iter()
            .chain(after_stop.iter())
            .filter(|line| line.starts_with("bestmove "))
            .count();
        assert_eq!(bestmove_count, 1, "cycle {cycle} emitted an unexpected final-move count");

        process.send("isready");
        let readiness = process.read_until(OUTPUT_TIMEOUT, |line| line == "readyok");
        assert!(
            readiness.iter().all(|line| !line.starts_with("bestmove ")),
            "cycle {cycle} leaked an extra bestmove after stop: {readiness:?}"
        );
    }

    process.quit_cleanly();
}
'''
    uci.write_text(text)

# Make the inherited authority audit S3-status-agnostic while still requiring the program.
replace_once(
    "scripts/task_post_port_review_fix_audit.sh",
    "grep -Fq '# Task S3-0: Authority registration and v0.1 baseline freeze — NOT STARTED' \"$s3_todo\"\ngrep -Fq '# Task S3-12: Final report and closure — NOT STARTED' \"$s3_todo\"\n",
    "grep -Fq '# Task S3-0: Authority registration and v0.1 baseline freeze' \"$s3_todo\"\ngrep -Fq '# Task S3-12: Final report and closure' \"$s3_todo\"\n",
)

baseline = Path("docs/RUST_CHESS_ENGINE_S3_BASELINE_2026-08-07.md")
if not baseline.exists():
    baseline.write_text(r'''# Rust Chess Engine S3 Baseline — 2026-08-07

**Status:** Frozen S3 planning baseline; v0.1 remains authoritative  
**S3 planning/authority SHA:** `90a015c2cf8b8d45edcd07d705fb6ca58fe336f7`  
**Unchanged production/code baseline SHA:** `677cd2a4d2a4a4f3c376f7bf47fae412171206fb`  
**S3 specification:** `docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_SPEC_2026-08-07.md`  
**S3 tracker:** `docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_TODO_2026-08-07.md`

## Authority and release state

- Package/UCI version: `0.1.0`.
- S2 remains closed without promotion; S2-15 was skipped and no S2 candidate is release authority.
- Search-policy schema: `1`.
- v0.1 search-policy identifier/checksum: `5630315f504f4c31` / `0c0769ef9d034770`.
- Evaluation-weight schema: `1`.
- Baseline evaluation-weight identifier/checksum: `424153454c494e45` / `d2cca7ae10ec6e34`.
- Runtime weight-vector length: `816`; named tunable-parameter count: `810`.
- C ABI version: `1`.
- Opening book is disabled by default; UCI accepts book data only through the explicit `--book <path>` adapter argument and `OwnBook` defaults to false.
- Tablebases/Syzygy are disabled and absent from the production adapter surface.
- No public UCI, safe-Rust facade, C ABI, JNI/Kotlin, or Android API exposes experimental S2 `SearchPolicy` selection.

## Canonical v0.1 policy text

```text
chess-search-policy-v1
schema=1
identifier=5630315f504f4c31
checksum=0c0769ef9d034770
alpha_beta=full_window_fail_soft
transposition=clustered_full_key
move_ordering=v0_1_mvv_lva_killers_history
quiescence=captures_promotions_and_evasions
aspiration_windows=true
aspiration_half_width_centipawns=50
maximum_quiescence_ply=64
maximum_check_extensions_per_line=1
experimental_features=0000000000000000
```

## JNI/Kotlin public-surface identity at the planning baseline

- Rust JNI export source blob: `63a3e4e4b7dcbe12106b17a36ce15117daa46cf8` (`crates/chess-jni/src/lib.rs`).
- Kotlin public wrapper blob: `67c58b41e86be4d00ffb07a7296f5034f10b198e` (`crates/chess-jni/kotlin/src/main/kotlin/com/ekkus93/chessengine/ChessEngine.kt`).
- The public JNI/Kotlin method set remains the v0.1 surface; no experimental search-policy selector is present.

## Exact planning-baseline validation evidence

The S3 planning commit changes documentation and TODO-authority audit state only; it does not change engine/search/adapter semantics relative to the validated production code baseline.

- Performance run `31179459890`: success.
  - Linux ARM64 job `92868991862`: success.
  - Linux x86-64 job `92868991953`: success.
- Robustness run `31179459861`: success.
  - Native sanitizers/leak job `92868992382`: success.
  - Miri core subset job `92868992584`: success.
  - Fuzz/corpus job `92868992629`: success.
- Android/JNI run `31179459876`: success.
  - Android/Kotlin lint job `92868991789`: success.
  - Android API 35 JNI smoke job `92868991806`: success.
  - Host JVM JNI contract job `92868991817`: success.
- Report-master validation run `31179755209`: success.
- CI run `31179459907`: exact planning-baseline run; ARM64 job `92868992078` succeeded. The x86-64 workspace-quality job `92868991929` was still running when this baseline record was first staged and must be recorded as successful before S3-0 is marked complete.

## Non-promotion rule

This document is evidence capture only. It authorizes no weight, search-policy, version, opening, tablebase, ABI, JNI, Android, or production-default change. Candidate work begins only after the S3 tracker records its own validated implementation evidence.
''')

s3_audit = Path("scripts/task_s3_evaluation_strength_audit.sh")
if not s3_audit.exists():
    s3_audit.write_text(r'''#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

fail() {
  echo "s3-evaluation-strength-audit: $*" >&2
  exit 1
}

require_file() {
  test -f "$1" || fail "missing required file: $1"
}

require_literal() {
  grep -Fq "$1" "$2" || fail "missing witness in $2: $1"
}

spec=docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_SPEC_2026-08-07.md
tracker=docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_TODO_2026-08-07.md
baseline=docs/RUST_CHESS_ENGINE_S3_BASELINE_2026-08-07.md
legacy=docs/LEGACY_TODO_INDEX.md
editor=crates/chess-core/src/position/editor.rs
position_mod=crates/chess-core/src/position/mod.rs
core_lib=crates/chess-core/src/lib.rs
uci_tests=crates/chess-uci/tests/uci_process.rs

for path in "$spec" "$tracker" "$baseline" "$legacy" "$editor" "$position_mod" "$core_lib" "$uci_tests"; do
  require_file "$path"
done

# Preserve all v0.1/S2 closure boundaries, including the existing adapter escape audit.
bash scripts/task_v0_2_strength_audit.sh

require_literal 'Active S3 evaluation strength program' "$legacy"
require_literal '`docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_TODO_2026-08-07.md`' "$legacy"
require_literal '**S3 planning/authority SHA:** `90a015c2cf8b8d45edcd07d705fb6ca58fe336f7`' "$baseline"
require_literal '**Unchanged production/code baseline SHA:** `677cd2a4d2a4a4f3c376f7bf47fae412171206fb`' "$baseline"
require_literal 'Package/UCI version: `0.1.0`' "$baseline"
require_literal 'Runtime weight-vector length: `816`; named tunable-parameter count: `810`.' "$baseline"
require_literal 'experimental_features=0000000000000000' "$baseline"
require_literal 'Tablebases/Syzygy are disabled' "$baseline"

# PositionEditor must be private to chess-core and must explicitly remain hash-neutral.
if grep -Eq '^[[:space:]]*pub[[:space:]]+use[[:space:]].*PositionEditor' "$position_mod" "$core_lib"; then
  fail 'PositionEditor is publicly re-exported'
fi
require_literal 'use editor::PositionEditor;' "$position_mod"
require_literal 'does **not** update the' "$editor"
require_literal 'editor_mutation_is_hash_neutral_until_the_caller_updates_hash_state' "$editor"
require_literal 'PositionEditor` is intentionally an internal board-representation capability' docs/RUST_MAKE_UNMAKE.md

# No experimental SearchPolicy selector may escape through a production adapter.
for path in crates/chess-uci/src crates/chess-ffi/src crates/chess-jni/src crates/chess-jni/kotlin/src/main android-harness; do
  if grep -R --line-number --include='*.rs' --include='*.kt' 'SearchPolicy' "$path"; then
    fail "experimental SearchPolicy escaped through $path"
  fi
done
for token in PrincipalVariationSearch LateMoveReductions NullMovePruning FutilityPruning Razoring LateMovePruning SeeCaptureOrdering SeeQuiescencePruning DeltaPruning Syzygy Tablebase; do
  for path in crates/chess-uci/src crates/chess-ffi/src crates/chess-jni/src crates/chess-jni/kotlin/src/main android-harness; do
    if grep -R --line-number --include='*.rs' --include='*.kt' "$token" "$path"; then
      fail "experimental capability $token escaped through $path"
    fi
  done
done

# Process-level stale-result behavior is permanently named and testable.
require_literal 'fn position_replacement_discards_active_search_without_stale_bestmove()' "$uci_tests"
require_literal 'fn ucinewgame_discards_active_search_without_stale_bestmove()' "$uci_tests"
require_literal 'fn repeated_stop_and_restart_cycles_emit_exactly_one_bestmove_per_search()' "$uci_tests"
require_literal 'fn quit_interrupts_active_search_without_stale_bestmove()' "$uci_tests"
require_literal 'fn stop_interrupts_infinite_search_and_session_remains_ready()' "$uci_tests"

# S3 candidate exploration must not drift production release identity.
require_literal 'version = "0.1.0"' Cargo.toml
require_literal 'pub const V0_1_SEARCH_POLICY_ID: u64 = 0x5630_315f_504f_4c31;' crates/chess-search/src/search_policy.rs
require_literal 'pub const BASELINE_WEIGHT_SET_ID: u64 = 0x4241_5345_4c49_4e45;' crates/chess-search/src/weights.rs
require_literal 'pub const WEIGHT_VALUE_COUNT: usize = 816;' crates/chess-search/src/weights.rs
require_literal 'pub const TUNABLE_PARAMETER_COUNT: usize = 810;' crates/chess-tune/src/lib.rs

# No S3 staging helper is allowed to become a production fallback.
if grep -R --line-number --include='*.rs' -E 'Command::new\("python(3)?"|Py_Initialize|pyo3' crates; then
  fail 'production Rust gained a Python/subprocess fallback'
fi

echo 'S3 evaluation-strength guardrail audit passed'
''')
    s3_audit.chmod(0o755)
