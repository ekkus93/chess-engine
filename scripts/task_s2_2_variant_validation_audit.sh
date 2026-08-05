#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
module="$root/crates/chess-tools/src/engine_variant_validation.rs"
lib="$root/crates/chess-tools/src/lib.rs"
legacy="$root/crates/chess-tools/src/candidate_validation.rs"
workflow="$root/.github/workflows/s2-2-stage.yml"
doc="$root/docs/RUST_CHESS_ENGINE_VARIANT_VALIDATION.md"

require_file() {
  local path="$1"
  test -f "$path" || { echo "missing S2-2 asset: $path" >&2; exit 1; }
}

require_literal() {
  local literal="$1"
  local path="$2"
  grep -Fq "$literal" "$path" || {
    echo "missing S2-2 witness in ${path#$root/}: $literal" >&2
    exit 1
  }
}

for path in "$module" "$lib" "$legacy" "$workflow" "$doc"; do
  require_file "$path"
done

require_literal 'pub mod engine_variant_validation;' "$lib"
require_literal 'pub const ENGINE_VARIANT_VALIDATION_SCHEMA_VERSION: u16 = 1;' "$module"
require_literal 'pub const ENGINE_VARIANT_VALIDATION_IDENTIFIER: u64 = 0x5641_5249_5641_4c31;' "$module"
require_literal 'pub const MINIMUM_PRODUCTION_VARIANT_PAIRS: u32 = 200;' "$module"
require_literal 'pub enum EngineVariantValidationTier' "$module"
require_literal 'pub enum EngineVariantResourceProtocol' "$module"
require_literal 'FixedNodes(u64)' "$module"
require_literal 'ClockMilliseconds(u64)' "$module"
require_literal 'pub struct EngineVariantRuntime' "$module"
require_literal 'pub struct RecordedEngineVariantIdentity' "$module"
require_literal 'pub enum EngineVariantGameFailure' "$module"
for marker in 'IllegalMove {' 'Crash {' 'TimeForfeit {' 'Infrastructure {'; do
  require_literal "$marker" "$module"
done
require_literal 'pub struct EngineVariantCorrectnessSummary' "$module"
require_literal 'pub struct EngineVariantValidationReport' "$module"
require_literal 'AcceptedForActivation' "$module"
require_literal '"accepted_for_activation"' "$module"
require_literal 'pub const fn activated(&self) -> bool {' "$module"
require_literal 'games must not run after a failed correctness pre-gate' "$module"
require_literal 'variant-validation pair is not exactly color-balanced' "$module"
require_literal 'lower_confidence_bound' "$module"
require_literal 'pub fn run_engine_variant_validation' "$module"
require_literal 'pub fn write_engine_variant_validation_report_atomic' "$module"
require_literal 'pub fn deserialize(text: &str) -> Result<Self, ToolError>' "$module"
require_literal 'engine-variant validation reports must remain inactive' "$module"

# The historical weight-only schema and protocol remain unchanged and separately authoritative.
require_literal 'pub const CANDIDATE_VALIDATION_SCHEMA_VERSION: u16 = 1;' "$legacy"
require_literal 'pub const CANDIDATE_VALIDATION_IDENTIFIER: u64 = 0x4341_4e44_5641_4c31;' "$legacy"
require_literal 'pub const MINIMUM_VALIDATION_PAIRS: u32 = 200;' "$legacy"
require_literal 'const FORMAT_MARKER: &str = "chess-candidate-validation-v1";' "$legacy"

# Staging machinery must not survive, and the permanent workflow must be read-only.
for path in \
  "$root/scripts/s2_2_stage.py" \
  "$root/scripts/.s2_2_payload_0" \
  "$root/scripts/.s2_2_payload_1" \
  "$root/scripts/.s2_2_payload_2" \
  "$root/scripts/.s2_2_payload_3"; do
  test ! -e "$path" || { echo "temporary S2-2 staging asset remains: $path" >&2; exit 1; }
done

require_literal 'contents: read' "$workflow"
if grep -Eq 'contents: write|git push|git commit|s2_2_stage.py|\.s2_2_payload_' "$workflow"; then
  echo 'S2-2 workflow retains write or temporary staging behavior' >&2
  exit 1
fi

echo 'S2-2 complete engine-variant validation audit passed'
