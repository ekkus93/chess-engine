# Rust Chess Engine S4 Closure Hardening Final Validation — 2026-08-07

**Status:** Complete exact closed-authority validation evidence
**Closed-authority candidate SHA:** `c8f31b07562111034b3eb6bd0fd81e04c7185133`
**Exact validated hardening closure SHA:** `040dbfa7d88df71380c9082d224f54b99e17c583`

## Permanent validation matrix

All required permanent workflows completed successfully on exact SHA `040dbfa7d88df71380c9082d224f54b99e17c583`:

- CI run `31214468559`: x86-64 workspace-quality job `92984632692` success; ARM64 workspace-build job `92984632651` success.
- Performance run `31214473918`: ARM64 job `92984650575` success; x86-64 job `92984650722` success.
- Robustness run `31214467831`: native sanitizers/leak job `92984630799`, fuzz/corpus job `92984630807`, and Miri job `92984630842` all success.
- Android/JNI run `31214467810`: Android/Kotlin lint job `92984646200`, host-JVM JNI job `92984646272`, and API-35 JNI smoke job `92984646321` all success.
- S4 Evaluation Tuning Calibration run `31214467814`, guardrails job `92984630452`: success.
- Post-CI bounded report-publication run `31215644023`, report job `92988408595`: success.

CI passed the complete authority/audit chain, no-lint-suppression rule, lockfile drift check, formatting, workspace check, strict Clippy, all-target/all-feature workspace tests, authoritative release perft, documentation build, debug/release builds, UCI smoke, and pinned differential-oracle corpus/seeded playouts.

## Retained artifacts

The workflows that intentionally publish retained evidence produced:

- x86-64 Performance artifact `9007948263`, digest `sha256:4aa8e1ed737a51728b2a4edd8e98fac671be89307979c2476e45d4ac39aaf63b`;
- ARM64 Performance artifact `9007944932`, digest `sha256:a32c74557f09348a4856cc0591c798d2b472d321d958ae84eef967d13a8598cf`;
- Android Performance artifact `9008040056`, digest `sha256:48224d6b5da1d299caa9403a573f8642f4ba2b21d88847d24946f9b737f3a38a`.

CI, Robustness, S4, and report-publication intentionally retained no workflow artifacts for this run.

## Final disposition

The closure-hardening program is complete. The code-review findings were corrected without reopening tuning or changing production chess behavior. Package/UCI remains `0.1.0`; v0.1 search policy and evaluator weights remain production authority; candidate `520db5dd58086a8a` remains inactive and `rejected_strength`; no ABI/JNI/Kotlin/Android behavior, opening default, tablebase state, or production selector changed.
