#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

fail() {
  echo "s4-evaluation-tuning-calibration-audit: $*" >&2
  exit 1
}

require_file() {
  test -f "$1" || fail "missing required file: $1"
}

require_literal() {
  grep -Fq "$1" "$2" || fail "missing witness in $2: $1"
}

spec=docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_SPEC_2026-08-07.md
tracker=docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_TODO_2026-08-07.md
baseline=docs/RUST_CHESS_ENGINE_S4_BASELINE_2026-08-07.md
legacy=docs/LEGACY_TODO_INDEX.md
s3_tracker=docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_TODO_2026-08-07.md
s3_report=docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_IMPLEMENTATION_REPORT.md

for path in "$spec" "$tracker" "$baseline" "$legacy" "$s3_tracker" "$s3_report"; do
  require_file "$path"
done

# Preserve all prior closure/correctness guarantees.
bash scripts/task_s3_evaluation_strength_audit.sh

# S4 is the only active program; S3 remains closed and historical.
require_literal 'Active S4 evaluation tuning calibration program' "$legacy"
require_literal '`docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_TODO_2026-08-07.md`' "$legacy"
require_literal '**Status:** Active — not yet implemented' "$tracker"
require_literal '**Status:** Active planning authority; implementation not yet complete' "$spec"
require_literal '**Status:** Complete — program closed without promotion' "$s3_tracker"
if grep -Fq '| Active S3 evaluation strength program |' "$legacy"; then
  fail 'closed S3 tracker is active again'
fi

# Baseline identity and explicit correction of the inherited S3 closure gate.
require_literal '**S4 planning baseline SHA:** `543dce22e51e71f821e37754a97ce0f33c3be122`' "$baseline"
require_literal '**S4 clean operational baseline SHA:** `b02623f20417c7f5769b6a16fc94566239e7979a`' "$baseline"
require_literal '**Unchanged production/code baseline SHA:** `677cd2a4d2a4a4f3c376f7bf47fae412171206fb`' "$baseline"
require_literal 'Package/UCI version: `0.1.0`.' "$baseline"
require_literal 'v0.1 search-policy identifier/checksum: `5630315f504f4c31` / `0c0769ef9d034770`.' "$baseline"
require_literal 'Baseline evaluation-weight identifier/checksum: `424153454c494e45` / `d2cca7ae10ec6e34`.' "$baseline"
require_literal 'Runtime evaluation weight-vector length: `816`; named tunable-parameter count: `810`.' "$baseline"
require_literal 'C ABI version: `1`.' "$baseline"
require_literal 'Rust JNI export source blob: `63a3e4e4b7dcbe12106b17a36ce15117daa46cf8`.' "$baseline"
require_literal 'Kotlin public wrapper blob: `67c58b41e86be4d00ffb07a7296f5034f10b198e`.' "$baseline"
require_literal 'S3 Evaluation Strength run `31186888170`, job `92893571662`: **failure**.' "$baseline"
require_literal 'A failed permanent gate is not reclassified as green' "$baseline"

# Release identities remain frozen.
require_literal 'version = "0.1.0"' Cargo.toml
require_literal 'pub const V0_1_SEARCH_POLICY_ID: u64 = 0x5630_315f_504f_4c31;' crates/chess-search/src/search_policy.rs
require_literal 'pub const BASELINE_WEIGHT_SET_ID: u64 = 0x4241_5345_4c49_4e45;' crates/chess-search/src/weights.rs
require_literal 'pub const WEIGHT_VALUE_COUNT: usize = 816;' crates/chess-search/src/weights.rs
require_literal 'pub const TUNABLE_PARAMETER_COUNT: usize = 810;' crates/chess-tune/src/lib.rs
require_literal 'pub const S3_CANDIDATE_SCHEMA_VERSION: u16 = 1;' crates/chess-tools/src/s3_candidate.rs
require_literal 'pub const S3_CANDIDATE_FORMAT_IDENTIFIER: u64 = 0x5333_4341_4e44_3031;' crates/chess-tools/src/s3_candidate.rs

# Temporary S4 staging controls must never become permanent evidence.
while IFS= read -r path; do
  case "$path" in
    .github/workflows/s4-evaluation-tuning-calibration.yml)
      ;;
    *)
      fail "temporary S4 control remains: $path"
      ;;
  esac
done < <(find .github -maxdepth 2 -type f \( -name 's4_*stage*.py' -o -name 's4-*-stage.yml' -o -name 's4_*fix*.py' \) -print | sort)

# Permanent S4 workflow must be read-only.
require_file .github/workflows/s4-evaluation-tuning-calibration.yml
if grep -Fq 'contents: write' .github/workflows/s4-evaluation-tuning-calibration.yml; then
  fail 'permanent S4 workflow is write-capable'
fi
require_literal 'contents: read' .github/workflows/s4-evaluation-tuning-calibration.yml

# Calibration work must not create a production Python/subprocess fallback.
if grep -R --line-number --include='*.rs' -E 'Command::new\("python(3)?"|Py_Initialize|pyo3' crates; then
  fail 'production Rust gained a Python/subprocess fallback'
fi

echo 'S4 evaluation-tuning calibration baseline audit passed'
