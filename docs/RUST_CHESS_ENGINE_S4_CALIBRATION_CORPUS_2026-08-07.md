# Rust Chess Engine S4 Calibration Corpus Evidence — 2026-08-07

**Status:** Complete corpus evidence  
**Date:** 2026-08-07  
**Source SHA:** `eb517a5641f19ecb8631aaec0234adbdfc3bf3c9`  
**Workflow run:** `31199370707`  
**Workflow job:** `92935372960`  
**Artifact ID:** `9002250000`  
**Artifact ZIP SHA-256:** `e83623d4323784b1ede8d44cc0b2d699d529aa8e96de3c447ae3de7414c97165`

## Purpose

S4-7 replaces the S3 32-game depth-1 pilot corpus with stronger deterministic fixed-node calibration corpora. The goal is not to claim playing strength; it is to provide a reproducible, provenance-bound loss dataset with more positions and occurrences before bounded optimizer calibration.

Both corpora use:

- maximum plies: `256`;
- independent White/Black TT budget: `1 MiB` each;
- check extension: disabled;
- claimable draw policy: accept;
- opening positions: excluded from tuning rows;
- split: `70/20/10` train/validation/test;
- opening source: `fixtures/self_play_openings.tsv`;
- no clock or implicit/default resource selection;
- `activated=false`.

## Medium corpus

Frozen configuration SHA-256: `e87920bfbacddc9f49072cd0d357be82f89e8b09d9c9d1e42bd75454827765c6`

- games: `64`;
- seed: `1395929911`;
- White/Black resource: `512 nodes/move`;
- dataset checksum: `dec450317a756c1b`;
- manifest checksum: `2fd0a46d7ec2e975`;
- positions / eligible rows: `1,311`;
- training occurrences: `4,197`;
- validation occurrences: `2,105`;
- excluded rows: `0`;
- admission: `true`.

The workflow generated the medium corpus twice at the identical canonical path `/tmp/s4-medium`, recursively diffed the complete directories, compared generation logs byte-for-byte, and compared validation logs byte-for-byte. All equality gates passed.

## Stronger corpus

Frozen configuration SHA-256: `11102da8d9581089429884e29a1a942c6d504e300813e9229e3270036361def1`

- games: `96`;
- seed: `1395929912`;
- White/Black resource: `1,024 nodes/move`;
- dataset checksum: `85c0e5949cb329e3`;
- manifest checksum: `979df002ced7fda5`;
- positions / eligible rows: `1,530`;
- training occurrences: `8,202`;
- validation occurrences: `2,465`;
- excluded rows: `0`;
- admission: `true`.

The workflow generated the stronger corpus twice at the identical canonical path `/tmp/s4-stronger`, recursively diffed the complete directories, compared generation logs byte-for-byte, and compared validation logs byte-for-byte. All equality gates passed.

## Scale comparison

| Metric | Medium | Stronger |
|---|---:|---:|
| Games | 64 | 96 |
| Unique/eligible positions | 1,311 | 1,530 |
| Training occurrences | 4,197 | 8,202 |
| Validation occurrences | 2,105 | 2,465 |
| Excluded rows | 0 | 0 |

The stronger corpus has both more games and more unique positions than the medium corpus, and materially more training/validation occurrence weight. It is therefore the frozen S4-8/S4-9 calibration dataset unless a later fail-closed gate proves it unusable.

## Artifact policy

The generated datasets are workflow artifacts only. They are not committed to Git. Reproduction is defined by the exact source SHA, explicit configuration, canonical output path, dataset/manifest checksums, and the read-only workflow.

No evaluator candidate, public API, engine default, package version, search policy, opening behavior, or activation state changed during corpus generation.
