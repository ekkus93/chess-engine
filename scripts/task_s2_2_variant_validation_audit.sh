#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
module="$root/crates/chess-tools/src/engine_variant_validation.rs"
lib="$root/crates/chess-tools/src/lib.rs"
legacy="$root/crates/chess-tools/src/candidate_validation.rs"
workflow="$root/.github/workflows/s2-2-stage.yml"
doc="$root/docs/RUST_CHESS_ENGINE_VARIANT_VALIDATION.md"

for path in "$module" "$lib" "$legacy" "$workflow" "$doc"; do
  test -f "$path" || { echo "missing S2-2 asset: $path" >&2; exit 1; }
done

grep -Fq 'pub mod engine_variant_validation;' "$lib"
grep -Fq 'pub const ENGINE_VARIANT_VALIDATION_SCHEMA_VERSION: u16 = 1;' "$module"
grep -Fq 'pub const ENGINE_VARIANT_VALIDATION_IDENTIFIER: u64 = 0x5641_5249_5641_4c31;' "$module"
grep -Fq 'pub const MINIMUM_PRODUCTION_VARIANT_PAIRS: u32 = 200;' "$module"
grep -Fq 'pub enum EngineVariantValidationTier' "$module"
grep -Fq 'pub enum EngineVariantResourceProtocol' "$module"
grep -Fq 'FixedNodes(u64)' "$module"
grep -Fq 'ClockMilliseconds(u64)' "$module"
grep -Fq 'pub struct EngineVariantRuntime' "$module"
grep -Fq 'pub struct RecordedEngineVariantIdentity' "$module"
grep -Fq 'pub enum EngineVariantGameFailure' "$module"
for marker in 'IllegalMove {' 'Crash {' 'TimeForfeit {' 'Infrastructure {'; do
  grep -Fq "$marker" "$module"
done
grep -Fq 'pub struct EngineVariantCorrectnessSummary' "$module"
grep -Fq 'pub struct EngineVariantValidationReport' "$module"
grep -Fq 'AcceptedForActivation' "$module"
grep -Fq '"accepted_for_activation"' "$module"
grep -Fq 'pub const fn activated(&self) -> bool {' "$module"
grep -Fq 'false' "$module"
grep -Fq 'games must not run after a failed correctness pre-gate' "$module"
grep -Fq 'variant-validation pair is not exactly color-balanced' "$module"
grep -Fq 'lower_confidence_bound' "$module"
grep -Fq 'pub fn run_engine_variant_validation' "$module"
grep -Fq 'pub fn write_engine_variant_validation_report_atomic' "$module"
grep -Fq 'pub fn deserialize_engine_variant_validation_report' "$module"

# The historical weight-only schema and protocol remain unchanged and separately authoritative.
grep -Fq 'pub const CANDIDATE_VALIDATION_SCHEMA_VERSION: u16 = 1;' "$legacy"
grep -Fq 'pub const CANDIDATE_VALIDATION_IDENTIFIER: u64 = 0x4341_4e44_5641_4c31;' "$legacy"
grep -Fq 'pub const MINIMUM_VALIDATION_PAIRS: u32 = 200;' "$legacy"
grep -Fq 'const FORMAT_MARKER: &str = "chess-candidate-validation-v1";' "$legacy"

# Staging machinery must not survive, and the permanent workflow must be read-only.
for path in \
  "$root/scripts/s2_2_stage.py" \
  "$root/scripts/.s2_2_payload_0" \
  "$root/scripts/.s2_2_payload_1" \
  "$root/scripts/.s2_2_payload_2" \
  "$root/scripts/.s2_2_payload_3"; do
  test ! -e "$path" || { echo "temporary S2-2 staging asset remains: $path" >&2; exit 1; }
done

grep -Fq 'contents: read' "$workflow"
if grep -Eq 'contents: write|git push|git commit|s2_2_stage.py|\.s2_2_payload_' "$workflow"; then
  echo 'S2-2 workflow retains write or temporary staging behavior' >&2
  exit 1
fi

echo 'S2-2 complete engine-variant validation audit passed'
