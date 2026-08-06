from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one occurrence, found {count}")
    return text.replace(old, new, 1)


source = Path("crates/chess-tools/src/bin/s2_7_pvs.rs").read_text(encoding="utf-8")
for old, new in [
    ("principal_variation_search_candidate", "late_move_reductions_candidate"),
    ("principal_variation_search_enabled", "late_move_reductions_enabled"),
    ("pvs_zero_window_searches", "lmr_reductions"),
    ("pvs_researches", "lmr_verification_searches"),
    ("PVS", "LMR"),
    ("pvs", "lmr"),
    ("S2_7", "S2_8"),
    ("S2-7", "S2-8"),
    ("s2_7", "s2_8"),
    ("s2-7", "s2-8"),
    ("0x5332_37", "0x5332_38"),
]:
    source = source.replace(old, new)

source = replace_once(
    source,
    "    lmr_reductions: u64,\n    lmr_verification_searches: u64,\n",
    "    lmr_reductions: u64,\n    lmr_reduced_fail_highs: u64,\n    lmr_verification_searches: u64,\n",
    "aggregate fail-high field",
)
source = replace_once(
    source,
    "    let mut total_lmr_reductions = 0_u64;\n"
    "    let mut total_lmr_verification_searches = 0_u64;\n",
    "    let mut total_lmr_reductions = 0_u64;\n"
    "    let mut total_lmr_reduced_fail_highs = 0_u64;\n"
    "    let mut total_lmr_verification_searches = 0_u64;\n",
    "parity fail-high total",
)
source = replace_once(
    source,
    "        total_lmr_verification_searches = total_lmr_verification_searches\n"
    "            .checked_add(candidate_diagnostics.lmr_verification_searches())\n"
    "            .ok_or(\"LMR re-search total overflow\")?;\n",
    "        total_lmr_reduced_fail_highs = total_lmr_reduced_fail_highs\n"
    "            .checked_add(candidate_diagnostics.lmr_reduced_fail_highs())\n"
    "            .ok_or(\"LMR reduced fail-high total overflow\")?;\n"
    "        total_lmr_verification_searches = total_lmr_verification_searches\n"
    "            .checked_add(candidate_diagnostics.lmr_verification_searches())\n"
    "            .ok_or(\"LMR verification total overflow\")?;\n",
    "parity fail-high accumulation",
)
source = replace_once(
    source,
    "\tlmr_reductions={}\tlmr_verification_searches={}\tbaseline_diagnostics=",
    "\tlmr_reductions={}\tlmr_reduced_fail_highs={}\tlmr_verification_searches={}\tbaseline_diagnostics=",
    "parity row headings",
)
source = replace_once(
    source,
    "            candidate_diagnostics.lmr_reductions(),\n"
    "            candidate_diagnostics.lmr_verification_searches(),\n"
    "            baseline_diagnostics.semantic_checksum(),\n",
    "            candidate_diagnostics.lmr_reductions(),\n"
    "            candidate_diagnostics.lmr_reduced_fail_highs(),\n"
    "            candidate_diagnostics.lmr_verification_searches(),\n"
    "            baseline_diagnostics.semantic_checksum(),\n",
    "parity row fail-high value",
)
source = replace_once(
    source,
    "            candidate_diagnostics.lmr_reductions(),\n"
    "            candidate_diagnostics.lmr_verification_searches(),\n"
    "            candidate_diagnostics.semantic_checksum(),\n",
    "            candidate_diagnostics.lmr_reductions(),\n"
    "            candidate_diagnostics.lmr_reduced_fail_highs(),\n"
    "            candidate_diagnostics.lmr_verification_searches(),\n"
    "            candidate_diagnostics.semantic_checksum(),\n",
    "parity checksum fail-high value",
)
source = replace_once(
    source,
    "    if total_lmr_verification_searches > total_lmr_reductions {\n"
    "        return Err(\"LMR re-search total exceeds zero-window search total\".into());\n"
    "    }\n",
    "    if total_lmr_reduced_fail_highs != total_lmr_verification_searches {\n"
    "        return Err(\"LMR reduced fail-high and verification totals differ\".into());\n"
    "    }\n"
    "    if total_lmr_verification_searches > total_lmr_reductions {\n"
    "        return Err(\"LMR verification total exceeds reduction total\".into());\n"
    "    }\n",
    "parity verification invariant",
)
source = replace_once(
    source,
    "    writeln!(output, \"total_lmr_verification_searches\t{total_lmr_verification_searches}\")?;\n",
    "    writeln!(output, \"total_lmr_reduced_fail_highs\t{total_lmr_reduced_fail_highs}\")?;\n"
    "    writeln!(output, \"total_lmr_verification_searches\t{total_lmr_verification_searches}\")?;\n",
    "parity fail-high summary",
)
source = replace_once(
    source,
    "    if diagnostics.lmr_reductions() != 0 || diagnostics.lmr_verification_searches() != 0 {\n",
    "    if diagnostics.lmr_reductions() != 0\n"
    "        || diagnostics.lmr_reduced_fail_highs() != 0\n"
    "        || diagnostics.lmr_verification_searches() != 0\n"
    "    {\n",
    "baseline fail-high validation",
)
source = replace_once(
    source,
    "    if diagnostics.lmr_verification_searches() > diagnostics.lmr_reductions() {\n"
    "        return Err(format!(\"candidate case {identifier} has more re-searches than probes\").into());\n"
    "    }\n",
    "    if diagnostics.lmr_reduced_fail_highs() != diagnostics.lmr_verification_searches() {\n"
    "        return Err(format!(\"candidate case {identifier} has unverified reduced fail-highs\").into());\n"
    "    }\n"
    "    if diagnostics.lmr_verification_searches() > diagnostics.lmr_reductions() {\n"
    "        return Err(format!(\"candidate case {identifier} has more verifications than reductions\").into());\n"
    "    }\n",
    "candidate fail-high validation",
)
source = replace_once(
    source,
    "\tcandidate_lmr_reductions={}\tcandidate_lmr_verification_searches={}\tactivated=false",
    "\tcandidate_lmr_reductions={}\tcandidate_lmr_reduced_fail_highs={}\tcandidate_lmr_verification_searches={}\tactivated=false",
    "benchmark comparison headings",
)
source = replace_once(
    source,
    "        candidate.aggregate.lmr_reductions,\n"
    "        candidate.aggregate.lmr_verification_searches,\n",
    "        candidate.aggregate.lmr_reductions,\n"
    "        candidate.aggregate.lmr_reduced_fail_highs,\n"
    "        candidate.aggregate.lmr_verification_searches,\n",
    "benchmark comparison fail-high value",
)
source = replace_once(
    source,
    "    if baseline.aggregate.lmr_reductions != 0 || baseline.aggregate.lmr_verification_searches != 0 {\n",
    "    if baseline.aggregate.lmr_reductions != 0\n"
    "        || baseline.aggregate.lmr_reduced_fail_highs != 0\n"
    "        || baseline.aggregate.lmr_verification_searches != 0\n"
    "    {\n",
    "benchmark baseline fail-high check",
)
source = replace_once(
    source,
    "    if candidate.aggregate.lmr_reductions == 0\n"
    "        || candidate.aggregate.lmr_verification_searches > candidate.aggregate.lmr_reductions\n"
    "    {\n"
    "        return Err(\"candidate benchmark did not exercise valid LMR accounting\".into());\n"
    "    }\n",
    "    if candidate.aggregate.lmr_reductions == 0\n"
    "        || candidate.aggregate.lmr_reduced_fail_highs\n"
    "            != candidate.aggregate.lmr_verification_searches\n"
    "        || candidate.aggregate.lmr_verification_searches > candidate.aggregate.lmr_reductions\n"
    "    {\n"
    "        return Err(\"candidate benchmark did not exercise valid verified LMR accounting\".into());\n"
    "    }\n",
    "benchmark candidate fail-high check",
)
source = replace_once(
    source,
    "\tlmr_reductions={}\tlmr_verification_searches={}\tchecksum=",
    "\tlmr_reductions={}\tlmr_reduced_fail_highs={}\tlmr_verification_searches={}\tchecksum=",
    "benchmark sample headings",
)
source = replace_once(
    source,
    "            aggregate.lmr_reductions,\n"
    "            aggregate.lmr_verification_searches,\n"
    "            aggregate.checksum,\n",
    "            aggregate.lmr_reductions,\n"
    "            aggregate.lmr_reduced_fail_highs,\n"
    "            aggregate.lmr_verification_searches,\n"
    "            aggregate.checksum,\n",
    "benchmark sample fail-high value",
)
source = replace_once(
    source,
    "        (\n"
    "            &mut aggregate.lmr_verification_searches,\n"
    "            diagnostics.lmr_verification_searches(),\n"
    "        ),\n",
    "        (\n"
    "            &mut aggregate.lmr_reduced_fail_highs,\n"
    "            diagnostics.lmr_reduced_fail_highs(),\n"
    "        ),\n"
    "        (\n"
    "            &mut aggregate.lmr_verification_searches,\n"
    "            diagnostics.lmr_verification_searches(),\n"
    "        ),\n",
    "benchmark aggregate fail-high",
)
Path("crates/chess-tools/src/bin/s2_8_lmr.rs").write_text(source, encoding="utf-8")

# Generated evidence outputs must never enter source control.
gitignore = Path(".gitignore").read_text(encoding="utf-8")
addition = """
# Generated S2-8 evidence outputs
/s2-8-deterministic-*/
/s2-8-clock/
/s2-8-bootstrap-benchmark.tsv
/s2-8-linux-*.tsv
"""
if "# Generated S2-8 evidence outputs" not in gitignore:
    Path(".gitignore").write_text(gitignore.rstrip() + "\n" + addition, encoding="utf-8")

# Extend the permanent audit to require the evidence harness and read-only workflow.
audit_path = Path("scripts/task_s2_8_lmr_audit.sh")
audit = audit_path.read_text(encoding="utf-8")
audit = replace_once(
    audit,
    "tests=\"crates/chess-search/tests/s2_8_lmr.rs\"\n",
    "tests=\"crates/chess-search/tests/s2_8_lmr.rs\"\n"
    "evidence=\"crates/chess-tools/src/bin/s2_8_lmr.rs\"\n"
    "workflow=\".github/workflows/s2-8-lmr.yml\"\n",
    "audit evidence paths",
)
audit = replace_once(
    audit,
    "for path in \"$policy\" \"$search\" \"$diagnostics\" \"$ordering\" \"$lib\" \"$tests\"; do\n",
    "for path in \"$policy\" \"$search\" \"$diagnostics\" \"$ordering\" \"$lib\" \"$tests\" \"$evidence\" \"$workflow\"; do\n",
    "audit evidence existence",
)
audit += """
grep -q 'late_move_reductions_candidate' "$evidence" || fail "evidence harness does not select LMR"
grep -q 'lmr_reduced_fail_highs' "$evidence" || fail "evidence omits reduced fail-highs"
grep -q 'activated\\tfalse' "$evidence" || fail "evidence omits inactive disposition"
grep -q '^permissions:' "$workflow" || fail "workflow permissions are missing"
grep -q '^  contents: read$' "$workflow" || fail "permanent workflow is not read-only"
if grep -q 'contents: write' "$workflow"; then
  fail "permanent workflow can write repository contents"
fi
"""
audit_path.write_text(audit, encoding="utf-8")

Path(".github/s2_8_evidence_bootstrap.py").unlink()
Path(".github/workflows/s2-8-evidence-bootstrap.yml").unlink()
