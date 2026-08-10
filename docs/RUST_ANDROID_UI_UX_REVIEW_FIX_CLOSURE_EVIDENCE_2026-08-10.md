# Rust Android UI/UX Review-Fix Closure Evidence — 2026-08-10

**Status:** Complete — bounded review-fix implementation and permanent exact-source-SHA validation passed
**Review baseline SHA:** `98e21939b0665f2f54ade7f87cdcaba3fe48025f`
**Implementation-start SHA:** `218158b15d1b500e940eb7a13077636b446869f5`
**Validated final source SHA:** `6d9a84d910a3e6438aef390aa733a4b62a71dfdd`
**Companion spec:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SPEC_2026-08-10.md`
**Companion TODO:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md`

## Closure disposition

The bounded Android UI/UX review-fix pass is complete. AR-001 through AR-020 were implemented and individually gated. AR-020's runtime rotation test executed successfully on API 35; the blocked/manual carve-out was not used. No first-party lint suppression was added and no existing green test was weakened or deleted to obtain closure.

The temporary Ralph validation run also passed before permanent closure: run `31409800032` completed successfully, including Android JVM/unit tests, Android lint, `chess-core`, `chess-jni`, all 39 Android instrumentation tests, `bash scripts/dev.sh fast`, and the TODO-authority audit after removal of the temporary source-modifying runner.

## Permanent exact-source-SHA CI

Both required permanent workflows validated the same exact source SHA `6d9a84d910a3e6438aef390aa733a4b62a71dfdd`.

### General / Rust CI

- Workflow: `CI`
- Run: `31417242747`
- Job: `93549046687` — `Rust workspace quality`
- Conclusion: `success`
- Validated SHA: `6d9a84d910a3e6438aef390aa733a4b62a71dfdd`

The job passed workspace/audit verification, formatting, strict Clippy, workspace tests, console PTY acceptance, release perft, documentation builds, debug/release builds, UCI smoke, and differential corpus/seeded playout validation.

### Android JNI CI

- Workflow: `Android JNI`
- Run: `31417240241`
- Job `93549039534` — `Android/Kotlin lint and unit tests` — `success`
- Job `93549039574` — `Android API 35 JNI and app smoke` — `success`
- Job `93549039612` — `Host JVM JNI contract` — `success`
- Overall conclusion: `success`
- Validated SHA: `6d9a84d910a3e6438aef390aa733a4b62a71dfdd`

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
