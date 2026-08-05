#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / "crates/chess-tools/src/bin/s2_5_see_ordering.rs"
AUDIT = ROOT / "scripts/task_s2_5_see_ordering_audit.sh"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement, found {count}: {old[:140]!r}")
    path.write_text(text.replace(old, new, 1))


replace_once(
    BINARY,
    "        &baseline_policy,\n"
    "        &candidate_policy,\n"
    "        &weights,\n"
    "        EngineVariantResourceProtocol::FixedNodes(FIXED_NODE_LIMIT),\n",
    "        (&baseline_policy, &candidate_policy),\n"
    "        &weights,\n"
    "        EngineVariantResourceProtocol::FixedNodes(FIXED_NODE_LIMIT),\n",
)
replace_once(
    BINARY,
    "        &baseline_policy,\n"
    "        &candidate_policy,\n"
    "        &weights,\n"
    "        EngineVariantResourceProtocol::ClockMilliseconds(CLOCK_MILLISECONDS),\n",
    "        (&baseline_policy, &candidate_policy),\n"
    "        &weights,\n"
    "        EngineVariantResourceProtocol::ClockMilliseconds(CLOCK_MILLISECONDS),\n",
)
replace_once(
    BINARY,
    "    baseline_policy: &'a SearchPolicySet,\n"
    "    candidate_policy: &'a SearchPolicySet,\n"
    "    weights: &'a EvaluationWeightSet,\n"
    "    protocol: EngineVariantResourceProtocol,\n"
    "    protocol_name: &str,\n"
    ") -> Result<chess_tools::engine_variant_validation::EngineVariantValidationReport, Box<dyn Error>> {\n"
    "    let baseline_identity = identity(\n",
    "    policies: (&'a SearchPolicySet, &'a SearchPolicySet),\n"
    "    weights: &'a EvaluationWeightSet,\n"
    "    protocol: EngineVariantResourceProtocol,\n"
    "    protocol_name: &str,\n"
    ") -> Result<chess_tools::engine_variant_validation::EngineVariantValidationReport, Box<dyn Error>> {\n"
    "    let (baseline_policy, candidate_policy) = policies;\n"
    "    let baseline_identity = identity(\n",
)
replace_once(
    AUDIT,
    "  \"$root/scripts/s2_5_evidence_apply.py\" \\\n"
    "  \"$root/.github/workflows/s2-5-apply-temp.yml\" \\\n",
    "  \"$root/scripts/s2_5_evidence_apply.py\" \\\n"
    "  \"$root/scripts/s2_5_evidence_refine.py\" \\\n"
    "  \"$root/.github/workflows/s2-5-apply-temp.yml\" \\\n",
)

for path in [BINARY, AUDIT]:
    text = path.read_text()
    if "#[allow(" in text or "#[expect(" in text:
        raise SystemExit(f"{path}: lint suppression detected")

print("S2-5 evidence helper arguments refined")
