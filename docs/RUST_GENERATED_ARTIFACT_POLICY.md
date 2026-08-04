# Versioned fixtures and generated-artifact policy

Repository artifacts fall into three categories.

## Source-controlled contracts

These are reviewed as source because runtime behavior depends on them:

- Rust source and Cargo lockfiles;
- Android/Kotlin source and build configuration;
- schema examples such as `fixtures/self_play_config.example` and `fixtures/tuning_config.example`;
- authoritative fixtures such as `fixtures/perft.tsv`, `fixtures/differential_corpus.tsv`, and `fixtures/self_play_openings.tsv`;
- minimized fuzz regressions and their explanatory README files;
- accepted reference performance baselines under `benchmarks/task24/`;
- generated code only when its generator, schema/version, provenance, and regeneration command are documented and reviewed.

Changing one of these files is a semantic code change. Schema versions must change when backward-incompatible parsing or meaning changes.

## Transient generated output

These are never committed by default:

- Cargo, fuzz, Gradle, and Android build directories;
- local virtual environments;
- self-play datasets produced during experimentation;
- SPSA checkpoints, candidate reports, and candidate artifacts;
- current performance TSVs and Callgrind output;
- Android logcat performance captures;
- temporary staging files/directories.

The root `.gitignore` contains explicit rules for the standard output locations. A developer may use another path, but remains responsible for keeping generated output untracked.

## Deliberate evidence promotion

A generated artifact may be committed only when all of the following are true:

1. it is required as an authoritative fixture, minimized regression, or accepted reference baseline;
2. its format has an explicit schema/version or stable semantic contract;
3. the exact source commit, command/configuration, seed where applicable, and checksum/provenance are recorded;
4. a deterministic validator or replay exists;
5. the commit explains why the artifact belongs in source control.

Promotion never implies runtime activation. Weight, book, and tuning artifacts still require their explicit adapter and activation policies.

## Automated audit

```bash
bash scripts/dev.sh artifact-audit
```

`scripts/task_25_artifact_audit.py` rejects:

- tracked filenames containing characters that make GitHub artifacts or cross-platform checkouts unsafe;
- tracked files in known transient build/output locations;
- missing required versioned fixtures/policy documents;
- missing `.gitignore` rules for standard generated output.

This audit runs in permanent CI. The previous empty filename containing a literal `*` was removed because it violated this policy and prevented portable artifact export.
