#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / "crates/chess-tools/src/bin/s2_5_see_ordering.rs"
AUDIT = ROOT / "scripts/task_s2_5_see_ordering_audit.sh"
DOC = ROOT / "docs/RUST_CHESS_ENGINE_V0_2_S2_5_SEE_ORDERING_2026-08-05.md"
WORKFLOW = ROOT / ".github/workflows/s2-5-see-ordering.yml"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement, found {count}: {old[:160]!r}")
    path.write_text(text.replace(old, new, 1))


replace_once(
    BINARY,
    "    println!(\n"
    "        \"comparison\\tmedian_time_ratio={ratio:.6}\\tbaseline_nodes={}\\tcandidate_nodes={}\\tbaseline_qnodes={}\\tcandidate_qnodes={}\\tbaseline_cutoffs={}\\tcandidate_cutoffs={}\\tbaseline_first_move_cutoffs={}\\tcandidate_first_move_cutoffs={}\\tcandidate_see_calls={}\\tcandidate_see_winning={}\\tcandidate_see_equal={}\\tcandidate_see_losing={}\\tactivated=false\",\n"
    "        baseline.aggregate.nodes,\n"
    "        candidate.aggregate.nodes,\n"
    "        baseline.aggregate.qnodes,\n"
    "        candidate.aggregate.qnodes,\n"
    "        baseline.aggregate.beta_cutoffs,\n"
    "        candidate.aggregate.beta_cutoffs,\n"
    "        baseline.aggregate.first_move_cutoffs,\n"
    "        candidate.aggregate.first_move_cutoffs,\n"
    "        candidate.aggregate.see_calls,\n"
    "        candidate.aggregate.see_winning,\n"
    "        candidate.aggregate.see_equal,\n"
    "        candidate.aggregate.see_losing,\n"
    "    );\n"
    "    if baseline.maximum_allocations != 0 || candidate.maximum_allocations != 0 {\n"
    "        return Err(\"S2-5 search benchmark observed heap allocation\".into());\n"
    "    }\n",
    "    let allocation_delta = i128::from(candidate.maximum_allocations)\n"
    "        - i128::from(baseline.maximum_allocations);\n"
    "    let allocated_byte_delta = i128::from(candidate.maximum_allocated_bytes)\n"
    "        - i128::from(baseline.maximum_allocated_bytes);\n"
    "    println!(\n"
    "        \"comparison\\tmedian_time_ratio={ratio:.6}\\tbaseline_nodes={}\\tcandidate_nodes={}\\tbaseline_qnodes={}\\tcandidate_qnodes={}\\tbaseline_cutoffs={}\\tcandidate_cutoffs={}\\tbaseline_first_move_cutoffs={}\\tcandidate_first_move_cutoffs={}\\tbaseline_maximum_allocations={}\\tcandidate_maximum_allocations={}\\tallocation_delta={}\\tbaseline_maximum_allocated_bytes={}\\tcandidate_maximum_allocated_bytes={}\\tallocated_byte_delta={}\\tcandidate_see_calls={}\\tcandidate_see_winning={}\\tcandidate_see_equal={}\\tcandidate_see_losing={}\\tactivated=false\",\n"
    "        baseline.aggregate.nodes,\n"
    "        candidate.aggregate.nodes,\n"
    "        baseline.aggregate.qnodes,\n"
    "        candidate.aggregate.qnodes,\n"
    "        baseline.aggregate.beta_cutoffs,\n"
    "        candidate.aggregate.beta_cutoffs,\n"
    "        baseline.aggregate.first_move_cutoffs,\n"
    "        candidate.aggregate.first_move_cutoffs,\n"
    "        baseline.maximum_allocations,\n"
    "        candidate.maximum_allocations,\n"
    "        allocation_delta,\n"
    "        baseline.maximum_allocated_bytes,\n"
    "        candidate.maximum_allocated_bytes,\n"
    "        allocated_byte_delta,\n"
    "        candidate.aggregate.see_calls,\n"
    "        candidate.aggregate.see_winning,\n"
    "        candidate.aggregate.see_equal,\n"
    "        candidate.aggregate.see_losing,\n"
    "    );\n",
)

replace_once(
    AUDIT,
    "require_literal 'S2-5 search benchmark observed heap allocation' \"$evidence\"\n",
    "require_literal 'baseline_maximum_allocations' \"$evidence\"\n"
    "require_literal 'candidate_maximum_allocations' \"$evidence\"\n"
    "require_literal 'allocation_delta' \"$evidence\"\n",
)
replace_once(
    AUDIT,
    "  \"$root/scripts/s2_5_evidence_refine.py\" \\\n"
    "  \"$root/.github/workflows/s2-5-apply-temp.yml\" \\\n",
    "  \"$root/scripts/s2_5_evidence_refine.py\" \\\n"
    "  \"$root/scripts/s2_5_evidence_allocation_refine.py\" \\\n"
    "  \"$root/.github/workflows/s2-5-apply-temp.yml\" \\\n",
)

replace_once(
    DOC,
    "- seven-sample timing, node, qnode, cutoff, first-move-cutoff, SEE-class, and allocation evidence;\n"
    "- a hard zero-allocation assertion for the measured search calls;\n"
    "- read-only evidence artifacts bound to the exact source SHA and build identity.\n",
    "- seven-sample timing, node, qnode, cutoff, first-move-cutoff, SEE-class, and end-to-end allocation evidence;\n"
    "- explicit baseline/candidate allocation counts and deltas without mislabeling the allocation-bearing iterative-deepening result path as zero-allocation;\n"
    "- the repository's existing hard zero-allocation audit for designated core hot paths;\n"
    "- read-only evidence artifacts bound to the exact source SHA and build identity.\n",
)

replace_once(
    WORKFLOW,
    "      - name: Capture seven-sample x86-64 distribution\n"
    "        run: target/release/s2_5_see_ordering benchmark 7 | tee s2-5-linux-x86-64.tsv\n",
    "      - name: Preserve the existing zero-allocation hot-path gate\n"
    "        run: cargo run --locked --release -p chess-tools --bin performance -- allocation-audit\n\n"
    "      - name: Capture seven-sample x86-64 end-to-end distribution\n"
    "        run: target/release/s2_5_see_ordering benchmark 7 | tee s2-5-linux-x86-64.tsv\n",
)
replace_once(
    WORKFLOW,
    "      - name: Capture seven-sample ARM64 distribution\n"
    "        run: target/release/s2_5_see_ordering benchmark 7 | tee s2-5-linux-arm64.tsv\n",
    "      - name: Preserve the existing ARM64 zero-allocation hot-path gate\n"
    "        run: cargo run --locked --release -p chess-tools --bin performance -- allocation-audit\n\n"
    "      - name: Capture seven-sample ARM64 end-to-end distribution\n"
    "        run: target/release/s2_5_see_ordering benchmark 7 | tee s2-5-linux-arm64.tsv\n",
)

for path in [BINARY, AUDIT, DOC, WORKFLOW]:
    text = path.read_text()
    if "#[allow(" in text or "#[expect(" in text:
        raise SystemExit(f"{path}: lint suppression detected")

print("S2-5 allocation evidence boundary corrected")
