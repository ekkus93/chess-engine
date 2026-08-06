from pathlib import Path

SOURCE_SHA = "8638611e38c712009e7f98bd4881fb266034df13"
STAGING_RUN = "31085412059"
ARTIFACT_ID = "8961204541"
ARTIFACT_DIGEST = "sha256:1c7ed56774119f9d771453e045b03345d4aae31d840eec30a7c03b96a28d8a19"
TRACKER = Path("docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md")
POLICY_DOC = Path("docs/RUST_CHESS_ENGINE_V0_2_S2_9_NULL_MOVE_POLICY_2026-08-05.md")
FINAL_DOC = Path("docs/RUST_CHESS_ENGINE_V0_2_S2_9_NULL_MOVE_2026-08-06.md")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one occurrence, found {count}")
    return text.replace(old, new, 1)


FINAL_DOC.write_text(f"""# S2-9 Null-Move Pruning Validation and Disposition

**Status:** Complete — standalone activation rejected
**Date:** 2026-08-06
**Branch:** `master`
**Validated candidate source SHA:** `{SOURCE_SHA}`
**Staging validation run:** `{STAGING_RUN}`
**Evidence artifact:** `{ARTIFACT_ID}`
**Artifact digest:** `{ARTIFACT_DIGEST}`
**Disposition:** `rejected_strength`
**Activation:** `false`

## Scope

S2-9.4 validates the isolated conservative null-move candidate implemented in S2-9.3. It does not alter the authoritative v0.1 policy, expose an experimental option through UCI or adapters, combine null move with rejected candidates, or activate the candidate.

## Candidate identity and frozen policy

- baseline policy identifier/checksum: `5630315f504f4c31` / `0c0769ef9d034770`;
- candidate policy identifier/checksum: `5332394e4d503031` / `4364aad2ac2abc2a`;
- evaluation identity/checksum: `424153454c494e45` / `d2cca7ae10ec6e34`;
- minimum remaining depth: `4`;
- speculative child depth: `depth - 1 - 2`;
- verification depth: `depth - 1`;
- side-to-move minimum non-pawn/non-king pieces: `2`;
- total minimum non-pawn/non-king pieces: `4`;
- every speculative fail-high requires verification;
- root, check, shallow, low-material, nested-null, verification, and mate-sensitive contexts remain disabled.

The synthetic transition still leaves legal clocks and `SearchHistory` unchanged, suppresses TT score reuse/storage throughout speculative subtrees, and restores the exact legal position before errors or cancellation propagate.

## Correctness evidence

The versioned 14-case corpus covers:

- classical and mutual zugzwang-sensitive endings;
- root stalemate and a high-material position that becomes stalemate after a synthetic pass;
- threefold and fivefold repetition roots;
- halfmove-clock values `99`, `100`, `149`, and `150`;
- mate distance and longest-survival behavior;
- a sparse position that actually enters the speculative null path;
- repeated successful searches and bounded node-cancellation restoration.

Every case matched the baseline score and completed depth. All best moves were identical, every reported PV replayed legally, position/history restoration was exact, and incremental/full Zobrist parity held.

Deterministic aggregate:

- case count: `14`;
- differing best moves: `0`;
- null attempts: `11071`;
- disabled nodes: `11066`;
- speculative fail-highs: `0`;
- verification searches: `0`;
- confirmed cutoffs: `0`;
- aggregate checksum: `75da625a5ae9c6d7`;
- activated: `false`.

The sparse exercise produced `946` attempts and `941` disabled nodes, proving that five speculative null searches executed while retaining exact baseline semantics. The absence of fail-highs means no verification or cutoff occurred in this corpus; the permanent invariants still require fail-high and verification totals to match and cutoffs not to exceed verifications.

## Fixed-node development protocol

- pairs/games: `8` / `16` color-swapped games;
- resource limit: `2000` nodes per move;
- maximum plies: `48`;
- candidate W/D/L: `0/0/0`;
- unfinished: `16`;
- illegal moves/crashes/time forfeits/infrastructure failures: `0/0/0/0`;
- decision: `rejected_strength`;
- report checksum: `81a8a72c9242da64`;
- activated: `false`.

Two independent deterministic generations were byte-identical. Because every game reached the bounded maximum-ply limit, this protocol supplied no positive standalone strength evidence. It does not prove the candidate is weaker; it fails the project acceptance gate.

## Clock development protocol

- pairs/games: `8` / `16` color-swapped games;
- resource limit: `10` milliseconds per move;
- maximum plies: `48`;
- candidate W/D/L: `0/0/0`;
- unfinished: `16`;
- illegal moves/crashes/time forfeits/infrastructure failures: `0/0/0/0`;
- decision: `rejected_strength`;
- report checksum: `9054382ea9b188c5`;
- activated: `false`.

This independent protocol likewise supplied no positive strength evidence and therefore rejects standalone activation under the existing fail-closed development rules.

## Disposition

The explicit S2-9 disposition is **`rejected_strength`**. Correctness and restoration requirements passed, but neither independent development protocol produced evidence sufficient for activation. The null-move candidate remains isolated and inactive. Production UCI, safe Rust APIs, C ABI, JNI, Android, package version, evaluation weights, authoritative v0.1 policy, and defaults remain unchanged.

## Fail-closed findings during validation

Validation corrected fixture and harness assumptions rather than weakening gates:

- rustfmt-only layout differences were applied verbatim;
- the opening generator now uses a mutable legal-move scratch position;
- terminal iterative-deepening accounting correctly records one root node per completed depth;
- a halfmove-`99` position may still evaluate as a forced claimable draw after the next legal move;
- the restoration stress position was changed from an unnecessarily expensive middlegame to a sparse position that still executes speculative null searches;
- synthetic-pass stalemate is tested directly with exact undo.

No lint suppression, ignored result, silent fallback, downgraded gate, or production activation was introduced.
""", encoding="utf-8")

policy = POLICY_DOC.read_text(encoding="utf-8")
policy = replace_once(
    policy,
    "**Status:** Implementation complete; validation pending",
    "**Status:** Complete — standalone activation rejected; candidate inactive",
    "policy status",
)
old_remaining = """## Remaining S2-9.4 work

S2-9.4 must independently validate zugzwang, stalemate, repetition, fifty/seventy-five-move boundaries, mate distance, longest survival, exact restoration/cancellation, and fixed-node plus clock development strength. It must then record `accept`, `reject`, or `defer`. The candidate remains inactive until that evidence exists.
"""
new_remaining = f"""## S2-9.4 final disposition

S2-9.4 completed on candidate source SHA `{SOURCE_SHA}` in staging run `{STAGING_RUN}`. The 14-case correctness matrix passed with exact score/depth parity, zero differing best moves, legal PV replay, and exact restoration. Fixed-node report checksum `81a8a72c9242da64` and clock report checksum `9054382ea9b188c5` both returned `rejected_strength`. Standalone activation is rejected and the candidate remains inactive. See `docs/RUST_CHESS_ENGINE_V0_2_S2_9_NULL_MOVE_2026-08-06.md`.
"""
policy = replace_once(policy, old_remaining, new_remaining, "policy remaining section")
POLICY_DOC.write_text(policy, encoding="utf-8")

tracker = TRACKER.read_text(encoding="utf-8")
tracker = replace_once(
    tracker,
    "- Disposition: implementation complete; validation and strength disposition remain pending; activation remains false.",
    "- Disposition: implementation complete; S2-9.4 validation is recorded below; standalone activation is rejected and activation remains false.",
    "S2-9.3 disposition",
)
record = f"""## S2-9.4 validation record

- Disposition: complete; standalone null-move activation rejected as `rejected_strength`; candidate remains inactive.
- Validated candidate source SHA: `{SOURCE_SHA}`.
- Staging validation run: `{STAGING_RUN}`; evidence artifact `{ARTIFACT_ID}`; digest `{ARTIFACT_DIGEST}`.
- Final record: `docs/RUST_CHESS_ENGINE_V0_2_S2_9_NULL_MOVE_2026-08-06.md`.
- Candidate identity/checksum: `5332394e4d503031` / `4364aad2ac2abc2a`; baseline remains `5630315f504f4c31` / `0c0769ef9d034770`.
- The versioned 14-case corpus covers zugzwang, root and synthetic-pass stalemate, threefold/fivefold repetition, halfmove clocks `99/100/149/150`, mate distance, longest survival, active speculative-null execution, repeated restoration, and bounded node cancellation.
- Every exact case matched baseline score and completed depth; all 14 best moves matched; all PVs replayed legally; position/history/Zobrist restoration passed.
- Aggregate diagnostics: `11071` attempts, `11066` disabled nodes, `0` speculative fail-highs, `0` verifications, `0` cutoffs; checksum `75da625a5ae9c6d7`; activated `false`.
- Fixed-node development: 8 pairs / 16 games at 2,000 nodes and 48 maximum plies; all 16 unfinished, all failure categories zero, `rejected_strength`, checksum `81a8a72c9242da64`.
- Clock development: 8 pairs / 16 games at 10 ms and 48 maximum plies; all 16 unfinished, all failure categories zero, `rejected_strength`, checksum `9054382ea9b188c5`.
- The evidence does not establish that null move is weaker; it supplies no positive standalone strength basis and therefore fails the project acceptance gate in both independent protocols.
- Production UCI, safe Rust facade, C ABI, JNI, Android, package version, evaluation weights, authoritative v0.1 policy, and defaults remain unchanged.

"""
tracker = replace_once(tracker, "## Program guardrails\n", record + "## Program guardrails\n", "S2-9.4 record insertion")
tracker = replace_once(
    tracker,
    "| S2-9 | Optional null-move pruning decision/candidate | **In progress — conservative policy complete; validation/disposition not started** |",
    "| S2-9 | Optional null-move pruning decision/candidate | **Complete — standalone rejected; inactive** |",
    "summary row",
)
tracker = replace_once(
    tracker,
    "# Task S2-9: Optional null-move pruning decision/candidate — IN PROGRESS",
    "# Task S2-9: Optional null-move pruning decision/candidate — COMPLETE",
    "task heading",
)
old_s294 = """## S2-9.4 Validation if implemented

- [ ] Zugzwang corpus.
- [ ] Stalemate and repetition corpus.
- [ ] Fifty/seventy-five move boundaries.
- [ ] Mate-distance and longest-survival corpus.
- [ ] Exact restoration and cancellation.
- [ ] Development fixed-node and clock matches.
- [ ] Explicit disposition; default inactive.

**S2-9 gate:** Null move is either rejected/deferred with architectural evidence or implemented conservatively with dedicated correctness and strength evidence.
"""
new_s294 = """## S2-9.4 Validation if implemented

- [x] Zugzwang corpus.
- [x] Stalemate and repetition corpus.
- [x] Fifty/seventy-five move boundaries.
- [x] Mate-distance and longest-survival corpus.
- [x] Exact restoration and cancellation.
- [x] Development fixed-node and clock matches.
- [x] Explicit disposition; default inactive.

**S2-9 gate:** Complete. The conservative candidate passed the dedicated correctness/restoration matrix, both independent development protocols returned `rejected_strength`, standalone activation is rejected, and the candidate remains inactive.
"""
tracker = replace_once(tracker, old_s294, new_s294, "S2-9.4 checklist")
tracker = replace_once(
    tracker,
    "Begin with **S2-9.4 only**: validate the inactive conservative null-move candidate against zugzwang, stalemate, repetition, fifty/seventy-five-move, mate-distance, longest-survival, restoration, cancellation, fixed-node, and clock protocols. Do not activate the candidate, begin S2-10, or combine it with rejected candidates until S2-9.4 records an explicit evidence-backed disposition.",
    "Begin with **S2-10.1 only**: decide whether a separately versioned, shallow non-PV futility-pruning candidate is justified by the current profile and accepted baseline. Do not combine it with rejected PVS, LMR, SEE/delta, or null-move candidates, and do not activate or expose it through production adapters without its own correctness and strength disposition.",
    "initial next action",
)
TRACKER.write_text(tracker, encoding="utf-8")

feasibility = Path("scripts/task_s2_9_null_move_feasibility_audit.sh")
text = feasibility.read_text(encoding="utf-8")
text = replace_once(text, "| S2-9 | Optional null-move pruning decision/candidate | **In progress — conservative policy complete; validation/disposition not started** |", "| S2-9 | Optional null-move pruning decision/candidate | **Complete — standalone rejected; inactive** |", "feasibility summary")
text = replace_once(text, "# Task S2-9: Optional null-move pruning decision/candidate — IN PROGRESS", "# Task S2-9: Optional null-move pruning decision/candidate — COMPLETE", "feasibility heading")
text = replace_once(text, "Begin with **S2-9.4 only**:", "Begin with **S2-10.1 only**:", "feasibility next action")
text = replace_once(text, "[[ \"$(grep -Fc -- '- [ ]' <<<\"$s2_9_remaining\")\" -gt 0 ]] || fail \"later S2-9 implementation work was marked complete without evidence\"", "[[ \"$(grep -Fc -- '- [x]' <<<\"$s2_9_remaining\")\" -eq 19 ]] || fail \"later S2-9 work is not fully completed\"\n[[ \"$(grep -Fc -- '- [ ]' <<<\"$s2_9_remaining\")\" -eq 0 ]] || fail \"later S2-9 work still has incomplete requirements\"", "feasibility progression")
feasibility.write_text(text, encoding="utf-8")

transition = Path("scripts/task_s2_9_search_null_transition_audit.sh")
text = transition.read_text(encoding="utf-8")
text = replace_once(text, "| S2-9 | Optional null-move pruning decision/candidate | **In progress — conservative policy complete; validation/disposition not started** |", "| S2-9 | Optional null-move pruning decision/candidate | **Complete — standalone rejected; inactive** |", "transition summary")
text = replace_once(text, "Begin with **S2-9.4 only**:", "Begin with **S2-10.1 only**:", "transition next action")
transition.write_text(text, encoding="utf-8")

policy_audit = Path("scripts/task_s2_9_null_move_policy_audit.sh")
text = policy_audit.read_text(encoding="utf-8")
text = replace_once(text, "grep -Fq 'Begin with **S2-9.4 only**:' \"$tracker\"", "grep -Fq 'Begin with **S2-10.1 only**:' \"$tracker\"", "policy next action")
policy_audit.write_text(text, encoding="utf-8")

validation_audit = Path("scripts/task_s2_9_null_move_validation_audit.sh")
validation_audit.write_text(f"""#!/usr/bin/env bash
set -euo pipefail

fail() {{
  echo "S2-9.4 null-move validation audit failed: $*" >&2
  exit 1
}}

tracker=docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md
record=docs/RUST_CHESS_ENGINE_V0_2_S2_9_NULL_MOVE_2026-08-06.md
policy_record=docs/RUST_CHESS_ENGINE_V0_2_S2_9_NULL_MOVE_POLICY_2026-08-05.md
corpus=fixtures/s2_9_null_move_validation_v1.tsv
tests=crates/chess-search/tests/s2_9_null_move_validation.rs
harness=crates/chess-tools/src/bin/s2_9_null_move.rs
policy=crates/chess-search/src/search_policy.rs
search=crates/chess-search/src/alpha_beta.rs
workflow=.github/workflows/s2-9-null-policy.yml

for path in "$tracker" "$record" "$policy_record" "$corpus" "$tests" "$harness" "$policy" "$search" "$workflow"; do
  [[ -f "$path" ]] || fail "missing $path"
done

[[ "$(head -n 1 "$corpus")" == $'S2_9_NULL_MOVE_VALIDATION\t1' ]] || fail "corpus header changed"
rows="$(grep -Ev '^(#|$)' "$corpus" | tail -n +2 | wc -l | tr -d ' ')"
[[ "$rows" -eq 14 ]] || fail "expected 14 corpus rows, found $rows"
for category in zugzwang stalemate repetition fifty-move seventy-five-move mate-distance longest-survival midgame; do
  grep -Fq $'\t'"$category"$'\t' "$corpus" || fail "missing corpus category $category"
done

grep -Fq 'make_search_null()' "$tests" || fail "synthetic-pass stalemate transition is missing"
grep -Fq 'unmake_search_null(undo)' "$tests" || fail "synthetic-pass restoration is missing"
grep -Fq 'repetition_root' "$tests" || fail "repetition regression is missing"
grep -Fq '99_u16' "$tests" && fail "unexpected generated halfmove loop shape"
grep -Fq '[100_u16, 149_u16, 150_u16]' "$tests" || fail "rule-boundary roots are missing"
grep -Fq 'mate_distance_and_longest_survival_match_baseline' "$tests" || fail "mate corpus is missing"
grep -Fq 'repeated_success_and_bounded_cancellation_restore_exactly' "$tests" || fail "restoration/cancellation regression is missing"
grep -Fq 'null_move_speculative_fail_highs()' "$tests" || fail "verification invariant is missing"

grep -Fq 'const FIXED_NODE_PAIRS: u32 = 8;' "$harness" || fail "fixed-node pair count changed"
grep -Fq 'const FIXED_NODE_LIMIT: u64 = 2_000;' "$harness" || fail "fixed-node limit changed"
grep -Fq 'const CLOCK_PAIRS: u32 = 8;' "$harness" || fail "clock pair count changed"
grep -Fq 'const CLOCK_MILLISECONDS: u64 = 10;' "$harness" || fail "clock limit changed"
grep -Fq 'const MAXIMUM_MATCH_PLIES: u32 = 48;' "$harness" || fail "maximum match plies changed"
grep -Fq 'diff' .github/workflows/s2-9-null-policy.yml || fail "deterministic reproducibility gate is missing"

grep -Fq '**Validated candidate source SHA:** `{SOURCE_SHA}`' "$record" || fail "validated source SHA is missing"
grep -Fq '**Staging validation run:** `{STAGING_RUN}`' "$record" || fail "staging run is missing"
grep -Fq '**Evidence artifact:** `{ARTIFACT_ID}`' "$record" || fail "artifact ID is missing"
grep -Fq '**Artifact digest:** `{ARTIFACT_DIGEST}`' "$record" || fail "artifact digest is missing"
grep -Fq '**Disposition:** `rejected_strength`' "$record" || fail "final disposition is missing"
grep -Fq '**Activation:** `false`' "$record" || fail "inactive disposition is missing"
grep -Fq 'aggregate checksum: `75da625a5ae9c6d7`' "$record" || fail "parity checksum is missing"
grep -Fq 'report checksum: `81a8a72c9242da64`' "$record" || fail "fixed-node checksum is missing"
grep -Fq 'report checksum: `9054382ea9b188c5`' "$record" || fail "clock checksum is missing"
grep -Fq '**Status:** Complete — standalone activation rejected; candidate inactive' "$policy_record" || fail "policy record was not closed"

grep -Fq '| S2-9 | Optional null-move pruning decision/candidate | **Complete — standalone rejected; inactive** |' "$tracker" || fail "summary is not complete"
grep -Fq '# Task S2-9: Optional null-move pruning decision/candidate — COMPLETE' "$tracker" || fail "task heading is not complete"
grep -Fq '## S2-9.4 validation record' "$tracker" || fail "validation record is missing"
grep -Fq 'Begin with **S2-10.1 only**:' "$tracker" || fail "next action is not S2-10.1"
s2_9="$(sed -n '/# Task S2-9:/,/# Task S2-10:/p' "$tracker")"
[[ "$(grep -Fc -- '- [x]' <<<"$s2_9")" -eq 23 ]] || fail "S2-9 does not have exactly 23 completed requirements"
[[ "$(grep -Fc -- '- [ ]' <<<"$s2_9")" -eq 0 ]] || fail "S2-9 still has incomplete requirements"
s2_10="$(sed -n '/# Task S2-10:/,/# Task S2-11:/p' "$tracker")"
[[ "$(grep -Fc -- '- [x]' <<<"$s2_10")" -eq 0 ]] || fail "S2-10 was started prematurely"
[[ "$(grep -Fc -- '- [ ]' <<<"$s2_10")" -gt 0 ]] || fail "S2-10 has no remaining work"

grep -Fq '&SearchPolicy::V0_1' "$search" || fail "default production search is not V0_1"
grep -Fq 'pub fn null_move_pruning_candidate' "$policy" || fail "isolated candidate identity is missing"
if grep -R -n -E 'make_search_null|NULL_MOVE_PRUNING' crates/chess-uci crates/chess-api crates/chess-ffi crates/chess-jni 2>/dev/null; then
  fail "null move leaked into a production adapter"
fi

for path in .github/s2_9_4_finalize.py .github/workflows/s2-9-4-stage.yml .github/workflows/s2-9-4-finalize.yml; do
  [[ ! -e "$path" ]] || fail "temporary helper remains: $path"
done

grep -q '^permissions:' "$workflow" || fail "permanent workflow permissions are missing"
grep -q '^  contents: read$' "$workflow" || fail "permanent workflow is not read-only"
if grep -q 'contents: write' "$workflow"; then
  fail "permanent workflow can write repository contents"
fi

echo "S2-9.4 null-move validation audit passed"
""", encoding="utf-8")

Path(__file__).unlink()
