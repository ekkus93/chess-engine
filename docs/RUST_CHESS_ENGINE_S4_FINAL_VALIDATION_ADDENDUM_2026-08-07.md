# Rust Chess Engine S4 Final Validation Addendum — 2026-08-07

**Status:** Complete evidence correction
**Final closed S4 SHA:** `bc406d78d673cc3258e8b522bcec25c4838f5e32`
**Pre-closure implementation SHA:** `b66b256a5b81621ba5310a749b7b93e650cc6067`

## Purpose

This addendum closes the S4-12.3 repository-evidence gap. The original S4 implementation report recorded the fully green pre-closure implementation matrix but did not persist the completed permanent matrix for the final closed SHA. The final closed SHA was validated successfully; the exact run/job evidence is recorded here without changing the S4 tuning or strength disposition.

## Final exact-SHA permanent matrix

- CI run `31208874474`: x86-64 workspace-quality job `92966583551` success; ARM64 workspace-build job `92966583700` success.
- Performance run `31208875019`: x86-64 job `92966584891` success; ARM64 job `92966585078` success.
- Robustness run `31208875521`: sanitizer/leak job `92966586631`, Miri job `92966586666`, and fuzz/corpus job `92966586684` all success.
- Android/JNI run `31208874646`: host JVM JNI job `92966594534`, API-35 JNI smoke job `92966594629`, and Android/Kotlin lint job `92966594742` all success.
- S4 Evaluation Tuning Calibration run `31208874643`, guardrails job `92966583439`: success.
- Final bounded report-publication run `31209467578`, report job `92968530668`: success.

## Final exact-SHA artifacts

The final CI, Robustness, S4, and report-publication workflows did not publish retained workflow artifacts. The final Performance and Android workflows did:

- x86-64 performance artifact `9005860229`, digest `sha256:237302e15ac2113777423f275a8aa0e1377425f5fd45fdbfd1df877aadce9614`;
- ARM64 performance artifact `9005851414`, digest `sha256:a3a3381b9383f506523efbb489e652c968f5c35d70d26a1e554785f7a6fc40d3`;
- Android performance artifact `9005947857`, digest `sha256:afc6106218a8056922c6e17c5db9b967e43aa9abe55115cf42087e2f0b720667`.

## Disposition preserved

The S4 method remains accepted only for future controlled evaluator experimentation. Candidate value checksum `520db5dd58086a8a` remains inactive and rejected by both development-strength protocols. No evaluator/search-policy activation, package/UCI version change, ABI/JNI/Kotlin/Android behavior change, opening-default change, or tablebase change occurred.
