from pathlib import Path


def replace_once(path: str, old: str, new: str, label: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one occurrence, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_in_unique_line(path: str, witness: str, old: str, new: str, label: str) -> None:
    target = Path(path)
    lines = target.read_text(encoding="utf-8").splitlines(keepends=True)
    matches = [index for index, line in enumerate(lines) if witness in line]
    if len(matches) != 1:
        raise SystemExit(f"{label}: expected one witness line, found {len(matches)}")
    index = matches[0]
    if lines[index].count(old) != 1:
        raise SystemExit(f"{label}: field is not unique on witness line")
    lines[index] = lines[index].replace(old, new, 1)
    target.write_text("".join(lines), encoding="utf-8")


source = "crates/chess-tools/src/bin/s2_8_lmr.rs"
replace_once(
    source,
    "    qnodes: u64,\n    beta_cutoffs: u64,\n",
    "    qnodes: u64,\n    selective_depth: u16,\n    beta_cutoffs: u64,\n",
    "aggregate selective-depth field",
)
replace_in_unique_line(
    source,
    "median_time_ratio=",
    "candidate_qnodes={}",
    "candidate_qnodes={}\\tbaseline_selective_depth={}\\tcandidate_selective_depth={}",
    "comparison selective-depth headings",
)
replace_once(
    source,
    "        baseline.aggregate.qnodes,\n        candidate.aggregate.qnodes,\n        baseline.aggregate.beta_cutoffs,\n",
    "        baseline.aggregate.qnodes,\n        candidate.aggregate.qnodes,\n        baseline.aggregate.selective_depth,\n        candidate.aggregate.selective_depth,\n        baseline.aggregate.beta_cutoffs,\n",
    "comparison selective-depth values",
)
replace_in_unique_line(
    source,
    "sample\\tpolicy=",
    "qnodes={}",
    "qnodes={}\\tselective_depth={}",
    "sample selective-depth heading",
)
replace_once(
    source,
    "            aggregate.qnodes,\n            aggregate.beta_cutoffs,\n",
    "            aggregate.qnodes,\n            aggregate.selective_depth,\n            aggregate.beta_cutoffs,\n",
    "sample selective-depth value",
)
replace_once(
    source,
    "    aggregate.checksum = aggregate\n",
    "    aggregate.selective_depth = aggregate.selective_depth.max(diagnostics.selective_depth());\n    aggregate.checksum = aggregate\n",
    "selective-depth aggregation",
)
replace_in_unique_line(
    source,
    "summary\\tpolicy=",
    "maximum_nanos={}",
    "maximum_nanos={}\\tselective_depth={}",
    "summary selective-depth heading",
)
replace_once(
    source,
    "        summary.maximum_nanos,\n        summary.maximum_allocations,\n",
    "        summary.maximum_nanos,\n        summary.aggregate.selective_depth,\n        summary.maximum_allocations,\n",
    "summary selective-depth value",
)

audit = "scripts/task_s2_8_lmr_audit.sh"
replace_once(
    audit,
    "grep -q 'lmr_reduced_fail_highs' \"$evidence\" || fail \"evidence omits reduced fail-highs\"\n",
    "grep -q 'lmr_reduced_fail_highs' \"$evidence\" || fail \"evidence omits reduced fail-highs\"\n"
    "grep -q 'selective_depth' \"$evidence\" || fail \"evidence omits selective depth\"\n",
    "selective-depth audit witness",
)

Path(".github/s2_8_selective_depth_patch.py").unlink()
Path(".github/workflows/s2-8-selective-depth-patch.yml").unlink()
