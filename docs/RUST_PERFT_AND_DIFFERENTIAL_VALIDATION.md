# Rust Perft and Differential Validation

This document defines the authoritative move-generation validation contract introduced by Task 11.

## Authoritative perft manifest

`fixtures/perft.tsv` is the single machine-readable source for the six standard positions and their exact depth-one through depth-five node counts. The suite covers the starting position, Kiwipete, en-passant and rook-ending geometry, castling and promotion stress, promotion with check evasion, and a tactical positional stress position.

`crates/chess-core/tests/authoritative_perft.rs` consumes the manifest directly. Every assertion also verifies exact position restoration and all internal invariants after traversal.

The execution tiers are:

- ordinary workspace tests: every position through depth three;
- required CI release gate: every position through depth four;
- scheduled or manually dispatched slow gate: every position through depth five.

The depth-five corpus totals 469,080,960 leaf nodes. It remains outside ordinary CI so routine changes receive fast feedback without weakening the complete gate.

## Deterministic validation tools

`chess-tools` exposes stable commands for diagnostics and automation:

```text
chess-tools legal [FEN]
chess-tools play UCI [FEN]
chess-tools perft DEPTH [FEN]
chess-tools divide DEPTH [FEN]
chess-tools suite MAX_DEPTH
chess-tools oracle
```

Legal moves and divide rows are sorted by canonical UCI text. Divide emits one tab-delimited move/count row followed by `total\t<N>` and `elapsed_nanos\t<N>`. The stable timing field measures divide calculation and total accumulation before output, while the move rows remain mechanically comparable.

`play` resolves an exact legal UCI identity and emits the canonical child FEN. `suite` validates the repository manifest through a requested depth from one command.

## Independent differential oracle

`requirements/oracle.txt` pins the external rules implementation to `chess==1.11.2`. `scripts/differential_oracle.py` refuses to run against any other version.

The Rust binary serves a persistent tab-delimited protocol with three operations:

- sorted legal UCI moves for a FEN;
- canonical child FEN after one legal UCI move;
- exact perft count at a requested depth.

A persistent process is used so corpus and random validation do not pay one process startup per position or move.

## Permanent differential corpus

`fixtures/differential_corpus.tsv` contains fifteen valid positions. It includes all six standard perft roots plus focused cases for:

- all four castling rights;
- castling while the king is checked;
- rook capture and castling-right changes;
- valid en passant;
- horizontal and diagonal en-passant pins;
- quiet and capture promotions;
- double check;
- absolute pins.

The harness validates every corpus FEN before starting Rust, then compares:

- the complete sorted legal-move set;
- the canonical child FEN for every legal root move;
- an independent recursive perft total;
- deterministic random legal playouts from the corpus roots.

CI uses twelve games of up to forty-eight plies with seed `0xC0FFEE`. The validated implementation covered fifteen corpus positions, 293 child FENs, 272,991 independently counted perft nodes, and 576 seeded plies without divergence.

## Fixture integrity and errata

Expected counts and FENs are inseparable fixture data. During Task 11, two specification rows paired standard expected counts with different legal boards. The Kiwipete and tactical positional FENs were corrected to the boards that produce the recorded standard counts. The manifest, differential corpus, and specification now agree.

A fixture mismatch must not be treated automatically as an engine defect. The exact FEN must first be evaluated by the pinned independent oracle. Conversely, an engine mismatch must be preserved as a focused corpus regression before the fix is accepted.

## Failure contract

Differential failures report the fixture or random-game index, ply, exact FEN, comparison category, expected value, and Rust value. The random seed is printed in successful and failing runs so every sequence is reproducible.

Invalid corpus entries are reported together before any Rust comparison. Illegal UCI requests and ambiguous move identities fail loudly. The oracle protocol returns explicit `ok` or `error` records and never silently substitutes a move or position.

## Validation evidence

Strict implementation validation:

- SHA: `1711fefe37b93163ec316ba9528742d6f87f8496`;
- CI run/job: `30733309460` / `91457298625`;
- rustfmt, Cargo check, Clippy with warnings denied, 89 executed Rust tests, release depth-four perft, rustdoc, debug build, and release build passed;
- differential totals: fifteen positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies.

Slow depth-five validation:

- validated SHA: `e5c44147c8f6097f1d60c8d6d73a051da4fc13a1`;
- run/job: `30733437572` / `91457637460`;
- result: all six fixtures passed, totaling 469,080,960 leaves in 39.77 seconds.

Task 12 may rely on this rule and move-generation layer while implementing evaluation and trace output.
