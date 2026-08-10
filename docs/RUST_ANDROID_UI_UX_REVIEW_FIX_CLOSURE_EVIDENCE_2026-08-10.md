# Rust Android UI/UX Review-Fix Closure Evidence — 2026-08-10

**Status:** Complete — bounded review-fix implementation and permanent exact-source-SHA validation passed
**Review baseline SHA:** `98e21939b0665f2f54ade7f87cdcaba3fe48025f`
**Implementation-start SHA:** `218158b15d1b500e940eb7a13077636b446869f5`
**Validated final source SHA:** `6d9a84d910a3e6438aef390aa733a4b62a71dfdd`
**Authoritative closure-tree SHA:** `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84`
**Companion spec:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SPEC_2026-08-10.md`
**Companion TODO:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md`

## Closure disposition

The bounded Android UI/UX review-fix pass is complete. AR-001 through AR-020 were implemented and individually gated. AR-020's runtime rotation test executed successfully on API 35; the blocked/manual carve-out was not used. No first-party lint suppression was added and no existing green test was weakened or deleted to obtain closure.

The temporary Ralph validation run also passed before permanent closure: run `31409800032` completed successfully, including Android JVM/unit tests, Android lint, `chess-core`, `chess-jni`, all 39 Android instrumentation tests, `bash scripts/dev.sh fast`, and the TODO-authority audit after removal of the temporary source-modifying runner.

## Permanent exact-source-SHA CI — corrected by closure-corrections CC-005

The original source-tree validation and the later authoritative closure-tree validation are distinct historical facts. The original source SHA remains useful supporting evidence, but the exact authoritative closure tree was `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84` and has its own permanent green runs.

### Authoritative final closure tree

- SHA: `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84`
- General/Rust workflow `CI`: run `31419183264`
  - job `93555556721` — `Rust workspace quality` — `success`
  - job `93555556826` — `Linux ARM64 workspace build` — `success`
- Android workflow `Android JNI`: run `31419183273`
  - job `93555602583` — `Host JVM JNI contract` — `success`
  - job `93555602709` — `Android/Kotlin lint and unit tests` — `success`
  - job `93555602727` — `Android API 35 JNI and app smoke` — `success`

Both historical runs were independently re-queried during CC-005 via `gh run view`; each reported `status=completed`, `conclusion=success`, and `headSha=e9ab0fc623c22bd372ba9c8c2609dfcf74609f84`.

### Earlier source-tree supporting evidence

The earlier permanent runs remain valid evidence for source SHA `6d9a84d910a3e6438aef390aa733a4b62a71dfdd`:

- General/Rust run `31417242747`, job `93549046687` — `success`.
- Android run `31417240241`, jobs `93549039534`, `93549039574`, `93549039612` — `success`.

They are not presented as the authoritative exact-final-SHA citation.

### Product/test-surface equivalence between the two historical SHAs

This claim is supported by git comparison, not inferred from CI success:

```text
$ git diff --exit-code 6d9a84d910a3e6438aef390aa733a4b62a71dfdd..e9ab0fc623c22bd372ba9c8c2609dfcf74609f84 -- android-harness crates
(exit 0; empty output)
```

The unrestricted changed-file list was:

```text
docs/LEGACY_TODO_INDEX.md
docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md
docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md
scripts/task_post_port_review_fix_audit.sh
```

Therefore Android/Rust product and test surfaces were unchanged between the earlier source-validation SHA and the later closure-tree SHA, while the listed documentation/authority files changed as part of closure bookkeeping.

## Review-fix validation summary

- Newest-move history highlighting is implemented and tested.
- Board/piece/coordinate colors are centralized into semantic theme tokens.
- Player-visible setup copy no longer exposes internal JNI/native architecture terminology.
- API-35 system-bar appearance has runtime coverage.
- Board sizing and shrink-before-clip behavior are documented.
- Move-history auto-scroll no longer relies on the former effect-ordering race.
- Active-game operations fail closed as silent no-ops while setup, busy, or cleanup-required state forbids them.
- Layout assertions share a dp-normalized bounded-tolerance helper.
- Black orientation, tab switching, promotion/error dialogs, engine metrics, setup title, and busy/game-over geometry all have permanent coverage.
- Automated contrast validation covers text/control tokens, composite piece silhouettes, and legal-target markers over required board treatments.
- SAN capture edge cases and Kotlin snapshot-parser rejection paths are covered.
- Rust/Kotlin high-level snapshot protocol parity is pinned by a static contract test.
- Runtime rotation was exercised through UIAutomator and preserved a played `e2-e4` position while the Activity remained portrait.

## Closure-commit exact-SHA policy

This evidence commit changes authoritative documentation after the source SHA above was validated. Therefore the earlier source-SHA runs are not treated as validating the later documentation commit. After this closure tree is committed, a tree-identical validation-trigger commit is created through the connected GitHub API so the permanent Android and general/Rust workflows validate the exact authoritative closure tree without another documentation mutation. No later documentation edit may claim coverage from an earlier SHA.
