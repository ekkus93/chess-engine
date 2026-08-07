#!/usr/bin/env python3
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


# Remove the rejected SEE+LMR combination policy and restore S2-8 LMR isolation.
policy_path = Path("crates/chess-search/src/search_policy.rs")
policy = policy_path.read_text()
policy = replace_once(
    policy,
    "/// Stable identifier for the frozen inactive S2-14 SEE-ordering plus LMR candidate.\n"
    "pub const S2_14_SEE_LMR_SEARCH_POLICY_ID: u64 = 0x5332_3134_534c_4d31;\n",
    "",
    "remove S2-14 combined policy identifier",
)
policy = replace_once(
    policy,
    "    /// Frozen inactive S2-14 combination: SEE capture ordering plus verified LMR.\n"
    "    pub const S2_14_SEE_LMR: Self = Self {\n"
    "        bits: ExperimentalSearchFeature::SeeCaptureOrdering.bit()\n"
    "            | ExperimentalSearchFeature::LateMoveReductions.bit(),\n"
    "    };\n",
    "",
    "remove S2-14 combined feature set",
)
start_marker = "    /// Frozen inactive S2-14 candidate: SEE capture ordering plus bounded verified LMR.\n"
end_marker = "    /// Inactive S2-9 candidate: baseline semantics plus conservative verified null move.\n"
start = policy.find(start_marker)
end = policy.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit("remove S2-14 combined SearchPolicy: markers missing")
policy = policy[:start] + policy[end:]
policy = replace_once(
    policy,
    "        if self.late_move_reductions_enabled() {\n"
    "            let enabled = self.parameters.experimental_features.bits();\n"
    "            if enabled != ExperimentalSearchFeatures::LATE_MOVE_REDUCTIONS.bits()\n"
    "                && enabled != ExperimentalSearchFeatures::S2_14_SEE_LMR.bits()\n"
    "            {\n"
    "                return Err(SearchPolicyValidationError::LateMoveReductionsMustBeIsolated);\n"
    "            }\n"
    "        }",
    "        if self.late_move_reductions_enabled()\n"
    "            && self.parameters.experimental_features.bits()\n"
    "                != ExperimentalSearchFeatures::LATE_MOVE_REDUCTIONS.bits()\n"
    "        {\n"
    "            return Err(SearchPolicyValidationError::LateMoveReductionsMustBeIsolated);\n"
    "        }",
    "restore LMR isolation",
)
policy = replace_once(
    policy,
    "    /// Returns the frozen inactive S2-14 SEE-ordering plus LMR candidate.\n"
    "    #[must_use]\n"
    "    pub fn s2_14_see_lmr_candidate() -> Self {\n"
    "        Self::new(S2_14_SEE_LMR_SEARCH_POLICY_ID, SearchPolicy::S2_14_SEE_LMR)\n"
    "    }\n\n",
    "",
    "remove S2-14 combined factory",
)
policy = replace_once(
    policy,
    "    /// LMR was combined outside the isolated S2-8 or frozen S2-14 SEE+LMR policies.\n"
    "    LateMoveReductionsMustBeIsolated,",
    "    /// LMR was combined with another unevaluated experimental feature.\n"
    "    LateMoveReductionsMustBeIsolated,",
    "restore LMR error documentation",
)
policy = replace_once(
    policy,
    "            Self::LateMoveReductionsMustBeIsolated => formatter.write_str(\n"
    "                \"late move reductions are valid only as isolated S2-8 or frozen S2-14 SEE+LMR policy\",\n"
    "            ),",
    "            Self::LateMoveReductionsMustBeIsolated => formatter.write_str(\n"
    "                \"late move reductions must be evaluated as an isolated policy candidate\",\n"
    "            ),",
    "restore LMR error display",
)
policy = replace_once(
    policy,
    "        NULL_MOVE_PRUNING_SEARCH_POLICY_ID, S2_14_SEE_LMR_SEARCH_POLICY_ID,\n"
    "        SEE_AND_DELTA_QUIESCENCE_PRUNING_SEARCH_POLICY_ID,",
    "        NULL_MOVE_PRUNING_SEARCH_POLICY_ID, SEE_AND_DELTA_QUIESCENCE_PRUNING_SEARCH_POLICY_ID,",
    "remove S2-14 test import",
)
test_start = policy.find(
    "    #[test]\n"
    "    fn s2_14_see_lmr_candidate_is_exact_distinct_and_inactive_by_default() {\n"
)
if test_start < 0:
    raise SystemExit("remove S2-14 combined policy test: start missing")
test_end_marker = "    #[test]\n    fn s2_9_null_move_candidate_is_distinct_valid_and_inactive_by_default() {"
test_end = policy.find(test_end_marker, test_start)
if test_end < 0:
    raise SystemExit("remove S2-14 combined policy test: end missing")
policy = policy[:test_start] + policy[test_end:]
if "S2_14_SEE_LMR" in policy or "s2_14_see_lmr" in policy:
    raise SystemExit("rejected SEE+LMR policy residue remains")
policy_path.write_text(policy)

# Rebind the production complete-variant harness to the existing audited PVS policy.
production_path = Path("crates/chess-tools/src/bin/s2_14_production.rs")
production = production_path.read_text()
production = replace_once(
    production,
    "    let candidate_policy = SearchPolicySet::s2_14_see_lmr_candidate();",
    "    let candidate_policy = SearchPolicySet::principal_variation_search_candidate();",
    "select PVS production policy",
)
old_boundary = """    if policy.policy.see_capture_ordering_enabled()
        || policy.policy.late_move_reductions_enabled()
        || !candidate_policy.policy.see_capture_ordering_enabled()
        || !candidate_policy.policy.late_move_reductions_enabled()
        || candidate_policy.policy.principal_variation_search_enabled()
        || candidate_policy.policy.null_move_pruning_enabled()
    {
        return Err(\"S2-14 candidate policy boundary is invalid\".into());
    }
"""
new_boundary = """    if policy.policy.principal_variation_search_enabled()
        || !candidate_policy.policy.principal_variation_search_enabled()
        || candidate_policy.policy.see_capture_ordering_enabled()
        || candidate_policy.policy.see_quiescence_pruning_enabled()
        || candidate_policy.policy.delta_pruning_enabled()
        || candidate_policy.policy.late_move_reductions_enabled()
        || candidate_policy.policy.null_move_pruning_enabled()
    {
        return Err(\"S2-14 PVS candidate policy boundary is invalid\".into());
    }
"""
production = replace_once(production, old_boundary, new_boundary, "freeze PVS policy boundary")
for old, new in [
    ("0x5332_3133_534d_4f4b", "0x5332_3134_534d_4f4b"),
    ("0x5332_3133_4445_5631", "0x5332_3134_4445_5631"),
    ("0x5332_3133_5052_4f44", "0x5332_3134_5052_4f44"),
]:
    production = replace_once(production, old, new, "correct S2-14 seed identity")
if "s2_14_see_lmr" in production or "S2_14_SEE_LMR" in production:
    raise SystemExit("production harness still references rejected SEE+LMR policy")
production_path.write_text(production)

# Remove the duplicate derived candidate harness; S2-14 now reuses the proven S2-7 PVS harness.
candidate_path = Path("crates/chess-tools/src/bin/s2_14_candidate.rs")
if not candidate_path.is_file():
    raise SystemExit("expected duplicate S2-14 candidate harness")
candidate_path.unlink()

# Rewrite the S2-14 candidate audit around the exact existing PVS identity.
audit_path = Path("scripts/task_s2_14_candidate_audit.sh")
audit_path.write_text("""#!/usr/bin/env bash
set -euo pipefail

policy='crates/chess-search/src/search_policy.rs'
pvs='crates/chess-tools/src/bin/s2_7_pvs.rs'
production='crates/chess-tools/src/bin/s2_14_production.rs'
rejection='docs/RUST_CHESS_ENGINE_V0_2_S2_14_SEE_LMR_PREFLIGHT_REJECTION_2026-08-06.md'

test -f \"$pvs\"
test -f \"$production\"
test -f \"$rejection\"
test ! -e crates/chess-tools/src/bin/s2_14_candidate.rs

grep -Fq 'pub const PRINCIPAL_VARIATION_SEARCH_POLICY_ID: u64 = 0x5332_3750_5653_3031;' \"$policy\"
grep -Fq 'pub fn principal_variation_search_candidate()' \"$policy\"
grep -Fq 'candidate_policy = SearchPolicySet::principal_variation_search_candidate()' \"$production\"
grep -Fq 'pair_count: 1_000' \"$production\"
grep -Fq 'const OPENING_COUNT: usize = 1_200' \"$production\"
grep -Fq 'opening_provenance\\tfirst_party_deterministic_generator_v1' \"$production\"
grep -Fq 'opening_license\\tMIT' \"$production\"
grep -Fq '0x5332_3134_534d_4f4b' \"$production\"
grep -Fq '0x5332_3134_4445_5631' \"$production\"
grep -Fq '0x5332_3134_5052_4f44' \"$production\"
grep -Fq '**Disposition:** `rejected_performance_preflight`' \"$rejection\"

if grep -R -E 'S2_14_SEE_LMR|s2_14_see_lmr' crates scripts/task_s2_14_candidate_audit.sh; then
  echo 'rejected SEE+LMR candidate remains in active source' >&2
  exit 1
fi

python3 - <<'PY2'
from pathlib import Path
text = Path('crates/chess-tools/src/bin/s2_14_production.rs').read_text()
start = text.index('let candidate_policy = SearchPolicySet::principal_variation_search_candidate();')
end = text.index('let openings = control_openings()?;', start)
block = text[start:end]
required = (
    '!candidate_policy.policy.principal_variation_search_enabled()',
    'candidate_policy.policy.see_capture_ordering_enabled()',
    'candidate_policy.policy.see_quiescence_pruning_enabled()',
    'candidate_policy.policy.delta_pruning_enabled()',
    'candidate_policy.policy.late_move_reductions_enabled()',
    'candidate_policy.policy.null_move_pruning_enabled()',
)
for witness in required:
    if witness not in block:
        raise SystemExit(f'missing PVS freeze witness: {witness}')
PY2

! grep -R -E 'principal_variation_search_candidate|PRINCIPAL_VARIATION_SEARCH_POLICY_ID' \
  crates/chess-uci crates/chess-ffi crates/chess-jni android-harness 2>/dev/null

echo 'S2-14 PVS candidate audit passed'
""")

# Rewrite the preflight to reuse the already-audited PVS evidence tool.
workflow_path = Path(".github/workflows/s2-14-candidate-preflight.yml")
workflow_path.write_text("""name: S2-14 production candidate preflight

on:
  push:
    branches:
      - master
    paths:
      - '.github/workflows/s2-14-candidate-preflight.yml'
      - 'crates/chess-search/src/search_policy.rs'
      - 'crates/chess-tools/src/bin/s2_7_pvs.rs'
      - 'crates/chess-tools/src/bin/s2_14_production.rs'
      - 'scripts/task_s2_14_candidate_audit.sh'
  pull_request:
    branches:
      - master
    paths:
      - '.github/workflows/s2-14-candidate-preflight.yml'
      - 'crates/chess-search/src/search_policy.rs'
      - 'crates/chess-tools/src/bin/s2_7_pvs.rs'
      - 'crates/chess-tools/src/bin/s2_14_production.rs'
      - 'scripts/task_s2_14_candidate_audit.sh'

permissions:
  contents: read

env:
  # Frozen before PVS is selected for S2-14 production validation.
  # A median slowdown above 5% on either native architecture is materially bad.
  S2_14_MAX_MEDIAN_TIME_RATIO: '1.05'

concurrency:
  group: s2-14-preflight-${{ github.workflow }}-${{ github.ref }}-${{ github.sha }}
  cancel-in-progress: false

jobs:
  linux-x86-64:
    name: Linux x86-64 PVS correctness and performance
    runs-on: ubuntu-24.04
    timeout-minutes: 120
    steps:
      - uses: actions/checkout@v4
      - name: Install stable Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy
      - name: Cache Cargo data
        uses: Swatinem/rust-cache@v2
        with:
          shared-key: rust-engine-s2-14-pvs-preflight-x86-64
      - name: Audit frozen candidate boundary
        run: bash scripts/task_s2_14_candidate_audit.sh
      - name: Check formatting and strict Clippy
        run: |
          cargo fmt --all -- --check
          cargo clippy --locked -p chess-search -p chess-tools --all-targets --all-features -- -D warnings
      - name: Run PVS and production evidence tests
        run: |
          cargo test --locked -p chess-search --all-targets --all-features
          cargo test --locked -p chess-tools --bin s2_7_pvs
          cargo test --locked -p chess-tools --bin s2_14_production
      - name: Build release evidence tools
        run: |
          cargo build --locked --release -p chess-tools --bin s2_7_pvs
          cargo build --locked --release -p chess-tools --bin s2_14_production
      - name: Record exact build identity
        shell: bash
        run: |
          set -euo pipefail
          build_identity=\"$(rustc -Vv | paste -sd '|' - | tr ' ' '_')\"
          echo \"S2_7_SOURCE_SHA=${GITHUB_SHA}\" >> \"$GITHUB_ENV\"
          echo \"S2_7_BUILD_IDENTITY=${build_identity}\" >> \"$GITHUB_ENV\"
          echo \"S2_14_SOURCE_SHA=${GITHUB_SHA}\" >> \"$GITHUB_ENV\"
          echo \"S2_14_BUILD_IDENTITY=${build_identity}\" >> \"$GITHUB_ENV\"
          echo \"S2_14_EXACT_INVOCATION=s2-14-pvs-preflight-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}-x86-64\" >> \"$GITHUB_ENV\"
      - name: Generate byte-identical PVS evidence twice
        run: |
          target/release/s2_7_pvs deterministic s2-14-pvs-deterministic-a
          target/release/s2_7_pvs deterministic s2-14-pvs-deterministic-b
          diff -ru s2-14-pvs-deterministic-a s2-14-pvs-deterministic-b
      - name: Freeze suite and run bounded complete-variant smoke
        run: target/release/s2_14_production s2-14-freeze smoke fixed_nodes
      - name: Verify normalized production-suite SHA-256 and uniqueness
        shell: bash
        run: |
          set -euo pipefail
          openings=s2-14-freeze/s2-14-control-openings.tsv
          sha256sum \"$openings\" | tee s2-14-opening-sha256.txt
          count=\"$(tail -n +2 \"$openings\" | wc -l)\"
          unique=\"$(tail -n +2 \"$openings\" | sort -u | wc -l)\"
          test \"$count\" -ge 1000
          test \"$unique\" -eq \"$count\"
      - name: Preserve zero-allocation hot-path gate
        run: cargo run --locked --release -p chess-tools --bin performance -- allocation-audit
      - name: Capture seven-sample x86-64 PVS distribution
        run: target/release/s2_7_pvs benchmark 7 | tee s2-14-linux-x86-64.tsv
      - name: Enforce predeclared x86-64 performance gate
        shell: bash
        run: |
          set -euo pipefail
          ratio=\"$(awk -F'median_time_ratio=' '/^comparison/{split($2,a,\"\\t\"); print a[1]}' s2-14-linux-x86-64.tsv)\"
          test -n \"$ratio\"
          python3 -c 'import sys; r=float(sys.argv[1]); limit=float(sys.argv[2]); print(f\"median_time_ratio={r:.6f} limit={limit:.6f}\"); raise SystemExit(0 if r <= limit else 1)' \"$ratio\" \"$S2_14_MAX_MEDIAN_TIME_RATIO\"
      - name: Preserve x86-64 S2-14 preflight evidence
        uses: actions/upload-artifact@v4
        with:
          name: s2-14-pvs-preflight-linux-x86-64-${{ github.sha }}
          path: |
            s2-14-pvs-deterministic-a
            s2-14-freeze
            s2-14-opening-sha256.txt
            s2-14-linux-x86-64.tsv
          if-no-files-found: error
          retention-days: 30

  linux-arm64:
    name: Linux ARM64 PVS correctness and performance
    runs-on: ubuntu-24.04-arm
    timeout-minutes: 120
    steps:
      - uses: actions/checkout@v4
      - name: Install stable Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy
      - name: Cache Cargo data
        uses: Swatinem/rust-cache@v2
        with:
          shared-key: rust-engine-s2-14-pvs-preflight-arm64
      - name: Audit, lint, and test on native ARM64
        run: |
          bash scripts/task_s2_14_candidate_audit.sh
          cargo fmt --all -- --check
          cargo clippy --locked -p chess-search -p chess-tools --all-targets --all-features -- -D warnings
          cargo test --locked -p chess-search --all-targets --all-features
          cargo test --locked -p chess-tools --bin s2_7_pvs
          cargo test --locked -p chess-tools --bin s2_14_production
      - name: Build release evidence tools
        run: |
          cargo build --locked --release -p chess-tools --bin s2_7_pvs
          cargo build --locked --release -p chess-tools --bin s2_14_production
      - name: Record exact build identity
        shell: bash
        run: |
          set -euo pipefail
          build_identity=\"$(rustc -Vv | paste -sd '|' - | tr ' ' '_')\"
          echo \"S2_7_SOURCE_SHA=${GITHUB_SHA}\" >> \"$GITHUB_ENV\"
          echo \"S2_7_BUILD_IDENTITY=${build_identity}\" >> \"$GITHUB_ENV\"
          echo \"S2_14_SOURCE_SHA=${GITHUB_SHA}\" >> \"$GITHUB_ENV\"
          echo \"S2_14_BUILD_IDENTITY=${build_identity}\" >> \"$GITHUB_ENV\"
          echo \"S2_14_EXACT_INVOCATION=s2-14-pvs-preflight-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}-arm64\" >> \"$GITHUB_ENV\"
      - name: Generate native ARM64 PVS deterministic evidence
        run: target/release/s2_7_pvs deterministic s2-14-pvs-deterministic-arm64
      - name: Freeze native ARM64 identity and suite
        run: target/release/s2_14_production s2-14-freeze-arm64 smoke fixed_nodes
      - name: Preserve ARM64 zero-allocation hot-path gate
        run: cargo run --locked --release -p chess-tools --bin performance -- allocation-audit
      - name: Capture seven-sample ARM64 PVS distribution
        run: target/release/s2_7_pvs benchmark 7 | tee s2-14-linux-arm64.tsv
      - name: Enforce predeclared ARM64 performance gate
        shell: bash
        run: |
          set -euo pipefail
          ratio=\"$(awk -F'median_time_ratio=' '/^comparison/{split($2,a,\"\\t\"); print a[1]}' s2-14-linux-arm64.tsv)\"
          test -n \"$ratio\"
          python3 -c 'import sys; r=float(sys.argv[1]); limit=float(sys.argv[2]); print(f\"median_time_ratio={r:.6f} limit={limit:.6f}\"); raise SystemExit(0 if r <= limit else 1)' \"$ratio\" \"$S2_14_MAX_MEDIAN_TIME_RATIO\"
      - name: Preserve ARM64 S2-14 preflight evidence
        uses: actions/upload-artifact@v4
        with:
          name: s2-14-pvs-preflight-linux-arm64-${{ github.sha }}
          path: |
            s2-14-pvs-deterministic-arm64
            s2-14-freeze-arm64
            s2-14-linux-arm64.tsv
          if-no-files-found: error
          retention-days: 30
""")
