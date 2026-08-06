from pathlib import Path

REPORT = Path('docs/RUST_CHESS_ENGINE_V0_2_S2_11_PROFILING_2026-08-06.md')
BENCH = Path('benchmarks/s2-11')

BENCH.mkdir(parents=True, exist_ok=True)
(BENCH / 'profile-summary.tsv').write_text('''architecture\tworkload\tmetric\tvalue\tunit\trun
x86-64\tprofile-perft\tsliding_attack_instruction_share\t24.54\tpercent_approx\t31103010137
x86-64\tprofile-search\tsliding_attack_instruction_share\t16.64\tpercent_approx\t31103010137
arm64\tprofile-perft\tsliding_attack_instruction_share\t12.09\tpercent_approx\t31103010137
arm64\tprofile-search\tsliding_attack_instruction_share\t8.38\tpercent_approx\t31103010137
x86-64\tprofile-search\tevaluation_instruction_share\t4.79\tpercent_approx\t31103010137
arm64\tprofile-search\tevaluation_instruction_share\t3.27\tpercent_approx\t31103010137
x86-64\tprofile-search\tmove_ordering_instruction_share\t14.50\tpercent_approx\t31103010137
arm64\tprofile-search\tmove_ordering_instruction_share\t13.00\tpercent_approx\t31103010137
x86-64\tprofile-search\tmake_unmake_instruction_share\t18.30\tpercent_approx\t31103010137
arm64\tprofile-search\tmake_unmake_instruction_share\t18.14\tpercent_approx\t31103010137
x86-64\tprofile-search\tmemcpy_instruction_share\t5.36\tpercent_approx\t31103010137
arm64\tprofile-search\tmemcpy_instruction_share\t7.07\tpercent_approx\t31103010137
''')
(BENCH / 'final-dispatch-comparison.tsv').write_text('''architecture\tbenchmark\tcandidate_ratio
x86-64\tattacks.sliding_sweep\t0.550814
x86-64\tmovegen.legal\t0.778231
x86-64\tperft.starting.depth4\t0.884574
x86-64\tperft.kiwipete.depth3\t0.788024
x86-64\tperft.endgame.depth4\t0.934694
x86-64\tsearch.starting.nodes20000\t0.938395
x86-64\tsearch.tactical.nodes20000\t0.951872
x86-64\tffi.legal_moves\t0.786974
x86-64\tffi.search_nodes\t0.942809
arm64\tattacks.sliding_sweep\t0.995237
arm64\tmovegen.legal\t0.993612
arm64\tperft.starting.depth4\t1.001534
arm64\tperft.kiwipete.depth3\t0.998643
arm64\tperft.endgame.depth4\t0.993703
arm64\tsearch.starting.nodes20000\t1.000896
arm64\tsearch.tactical.nodes20000\t1.000471
arm64\tffi.legal_moves\t0.990773
arm64\tffi.search_nodes\t0.998548
''')
(BENCH / 'artifact-manifest.tsv').write_text('''stage\tarchitecture\trun_id\tjob_id\tartifact_id\tdigest\tsource_sha
baseline-performance\tx86-64\t31100066672\t-\t8967077294\tsha256:3e71b7ec1887ed29a6676b0274602a06836c5db629fa2935fa6bd5c2cec4328e\tb20d34b3fc6210f0eff7a2124168e6d5e084f36a
baseline-performance\tarm64\t31100066672\t-\t8967076768\tsha256:414f77ae9e56785dbfe3a0819371f1505424560b0b8761e9d54f8a4cb65048db\tb20d34b3fc6210f0eff7a2124168e6d5e084f36a
baseline-callgrind\tx86-64\t31103010137\t92621028212\t8968350766\tsha256:bd941fdc742a09224ff0178347c4b7c0d0b8fc942ff80962f9897f660a4615bc\tb20d34b3fc6210f0eff7a2124168e6d5e084f36a
baseline-callgrind\tarm64\t31103010137\t92621028108\t8968365608\tsha256:fbc60f2b39078aaa1b4019a07b822efc5001f34138ded25572dbaf2a152dae0d\tb20d34b3fc6210f0eff7a2124168e6d5e084f36a
portable-candidate\tx86-64\t31104319109\t92625431797\t8968909641\tsha256:69357a47856dc04edf9968b678cd231cfbc6dc9f16b480ae9578a214f06f1dc4\t507a7536e9312b607c091fd873d29396c1b578d7
portable-candidate\tarm64\t31104319109\t92625431759\t8968925643\tsha256:fddddb7b77bdb23d0685417c69643e79f7447e0869c4d4e05410dc73a7e337de\t507a7536e9312b607c091fd873d29396c1b578d7
final-dispatch\tx86-64\t31105092637\t92628044216\t8969180920\tsha256:1cb53e029936cef3caedccdb1fd1f5d1b13ffe079481ade61039a9131746aa7b\t392342c3122c54c47cf485d8bb36c8f5a8c5a762
final-dispatch\tarm64\t31105092637\t92628044139\t8969177826\tsha256:6e4ba7a6d726bfe86968701f558976910e20fcd7316aaa216edfe185fb511a3c\t392342c3122c54c47cf485d8bb36c8f5a8c5a762
android-jni\tandroid-arm64\t31100066741\t-\t8967168646\tsha256:45656b54a2c2733ff66a819b63e0df374a4013354aaba002900859a500eb2741\tb20d34b3fc6210f0eff7a2124168e6d5e084f36a
''')

REPORT.write_text('''# Rust Chess Engine v0.2 S2-11 Profiling and Hot-Path Decisions

**Status:** Complete
**Date:** 2026-08-06
**Baseline source SHA:** `b20d34b3fc6210f0eff7a2124168e6d5e084f36a`
**Portable candidate SHA:** `507a7536e9312b607c091fd873d29396c1b578d7`
**Accepted implementation SHA:** `392342c3122c54c47cf485d8bb36c8f5a8c5a762`
**Final validation witness SHA:** `6f5472de19e2b784d1f965815bb5ee19d09efa43`
**Production integration:** active, behaviorally equivalent

## Decision summary

Fresh Callgrind and seven-sample timing evidence was captured on x86-64 and native ARM64. Direct legal generation is deferred pending dedicated legality-probe instrumentation. Incremental evaluation is deferred because evaluation consumed only about `4.79%` of x86-64 and `3.27%` of ARM64 search instructions. TT replacement/packing is rejected as not hot, custom allocation is rejected because measured hot paths remain zero-allocation, and move-list/layout work is deferred to an isolated future candidate.

Sliding attacks were the only justified implementation target. A portable ray-table candidate improved the microbenchmark on both architectures but regressed representative ARM64 legal-generation, perft, search, and FFI workloads by roughly `2%` to `6.4%`; it was rejected. The accepted candidate uses compile-time architecture dispatch: x86-64 uses precomputed rays and nearest-blocker bit scans, while non-x86 targets preserve the original step-walk. There is no runtime CPU detection, magic-bitboard dependency, PEXT dependency, or silent fallback.

## Correctness contract

The permanent exhaustive oracle test compares rook and bishop attacks for every source square and every relevant blocker subset against the independent step-walk oracle. Candidate and baseline retain identical attack sets, perft results, fixed-node search diagnostics, semantic checksums, and allocation counts. The exact validation workloads remained `4,085,603` perft nodes and `250,000` main nodes / `242,711` qnodes / depth `4` for search.

Because the accepted change is behaviorally equivalent, no chess-strength match was run. A game result would measure noise rather than a semantic engine variant.

## Performance disposition

The accepted dispatch produced the following matched median results:

- x86-64 sliding sweep ratio `0.550814` (`44.9%` faster);
- x86-64 representative search ratios `0.938395` and `0.951872` (`6.2%` and `4.8%` faster);
- x86-64 representative perft ratios from `0.788024` to `0.934694` (`21.2%` to `6.5%` faster);
- ARM64 representative ratios remained approximately parity, from `0.990773` to `1.001534`.

Raw identifiers and digests are preserved in `benchmarks/s2-11/artifact-manifest.tsv`; compact profile and matched-comparison summaries are preserved beside it. Existing performance references and budgets were not overwritten or automatically updated.

## Reconsideration gates

Direct legal generation requires isolated instrumentation proving which legality probes are avoidable, followed by exhaustive move-set equivalence, perft, differential, property, fuzz, and restoration evidence. Incremental evaluation requires a materially larger measured share and exact full-recomputation parity after every make/unmake path. Move-list/layout work requires an isolated candidate with allocation, cache/copy, correctness, and architecture-specific evidence. Magic, PEXT, TT packing, and custom allocator work remain prohibited without new profile evidence.
''')

