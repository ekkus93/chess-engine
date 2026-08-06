from pathlib import Path

AUDIT = Path('.github/workflows/tracker-close.yml')

def one(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected one match, found {count}')
    return text.replace(old, new, 1)

audit = AUDIT.read_text()
audit = one(audit, 'name: Strength tracker authority through S2-10.3', 'name: Strength tracker authority through S2-11', 'audit job name')
audit = one(audit, '- name: Verify progression through S2-10.3', '- name: Verify progression through S2-11', 'audit step name')
audit = one(audit,
    "          grep -Fq '| S2-11 | Fresh profiling and measured hot-path decisions | **Not started** |' \"$tracker\"",
    "          grep -Fq '| S2-11 | Fresh profiling and measured hot-path decisions | **Complete — x86-64 sliding dispatch accepted; non-x86 baseline preserved** |' \"$tracker\"\n          grep -Fq '| S2-12 | Optional Syzygy tablebase decision/integration | **Not started** |' \"$tracker\"",
    'audit summary row')
audit = one(audit,
    "          grep -Fq '# Task S2-11: Fresh profiling and measured hot-path decisions — NOT STARTED' \"$tracker\"",
    "          grep -Fq '# Task S2-11: Fresh profiling and measured hot-path decisions — COMPLETE' \"$tracker\"\n          grep -Fq '# Task S2-12: Optional Syzygy tablebase decision/integration — NOT STARTED' \"$tracker\"",
    'audit heading')
insert = '''
          s2_11="$(sed -n '/^# Task S2-11:/,/^# Task S2-12:/p' "$tracker")"
          test "$(grep -Fc -- '- [x]' <<<"$s2_11")" -eq 24
          test "$(grep -Fc -- '- [ ]' <<<"$s2_11")" -eq 0
          report=docs/RUST_CHESS_ENGINE_V0_2_S2_11_PROFILING_2026-08-06.md
          profile=benchmarks/s2-11/profile-summary.tsv
          comparison=benchmarks/s2-11/final-dispatch-comparison.tsv
          manifest=benchmarks/s2-11/artifact-manifest.tsv
          attacks=crates/chess-core/src/attacks.rs
          attack_tests=crates/chess-core/src/attacks_tests.rs
          grep -Fq '**Status:** Complete' "$report"
          grep -Fq '**Accepted implementation SHA:** `392342c3122c54c47cf485d8bb36c8f5a8c5a762`' "$report"
          grep -Fq 'portable ray-table candidate' "$report"
          grep -Fq $'x86-64\tattacks.sliding_sweep\t0.550814' "$comparison"
          grep -Fq $'arm64\tsearch.tactical.nodes20000\t1.000471' "$comparison"
          grep -Fq $'baseline-callgrind\tx86-64\t31103010137\t92621028212\t8968350766' "$manifest"
          grep -Fq $'final-dispatch\tarm64\t31105092637\t92628044139\t8969177826' "$manifest"
          grep -Fq $'x86-64\tprofile-search\tsliding_attack_instruction_share\t16.64' "$profile"
          grep -Fq '#[cfg(target_arch = "x86_64")]' "$attacks"
          grep -Fq '#[cfg(not(target_arch = "x86_64"))]' "$attacks"
          grep -Fq 'sliding_attacks_ray' "$attacks"
          grep -Fq 'sliding_attacks_step' "$attacks"
          grep -Fq 'sliding_attacks_match_independent_oracle_for_every_relevant_occupancy' "$attack_tests"

'''
audit = one(audit, "          grep -q '^permissions:' .github/workflows/tracker-close.yml\n", insert + "          grep -q '^permissions:' .github/workflows/tracker-close.yml\n", 'audit insertion')
audit = one(audit,
    '            .github/workflows/s2-10-3-closure.yml; do',
    '''            .github/workflows/s2-10-3-closure.yml \\
            .github/workflows/s2-11-profiling.yml \\
            .github/s2_11_sliding_candidate.py \\
            .github/s2_11_sliding_candidate_fix.py \\
            .github/workflows/s2-11-sliding-candidate.yml \\
            .github/workflows/s2-11-sliding-validation.yml \\
            .github/s2_11_x86_dispatch_candidate.py \\
            .github/workflows/s2-11-x86-dispatch-candidate.yml \\
            .github/workflows/s2-11-final-dispatch-validation.yml \\
            .github/s2_11_close.py \\
            .github/workflows/s2-11-close.yml; do''',
    'temporary path audit')
AUDIT.write_text(audit)
