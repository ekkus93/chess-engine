#!/usr/bin/env python3
from pathlib import Path

tracker = Path("docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md")
text = tracker.read_text()

record = """## S2-3 implementation record

- Disposition: complete; the authoritative v0.1 search, tactical, performance, and identical-policy strength baselines are frozen for later isolated candidate comparisons; activation remains false.
- Deterministic diagnostics implementation SHA: `db05a9243afbfae95971b7715ea70f48757d5144`.
- Tactical corpus and strength-control harness implementation SHA: `58015782deb0573810a61140446bde37d9cd9a3e`.
- Exact validation SHA: `9a56a27552b5032860802db8fe5d82d65ac93d2d`.
- Authoritative v0.1 policy identifier/checksum: `5630315f504f4c31` / `0c0769ef9d034770`.
- Authoritative baseline weight identifier/checksum: `424153454c494e45` / `d2cca7ae10ec6e34`.
- Added fixed-size allocation-free search diagnostics for main nodes, qnodes, selective depth, beta cutoffs, first-move cutoffs, quiescence cutoffs, and stand-pat cutoffs while preserving existing TT and check-extension diagnostics.
- Reserved stable zero counters for PVS, SEE, quiescence SEE/delta pruning, LMR, null move, frontier futility/razoring, and late-move pruning. Exact-result aggregation fails with a typed counter-specific overflow; request-wide observation saturates the affected counter and sets an explicit overflow bit.
- Permanent tests prove node/count consistency, reserved-counter inactivity, deterministic checksums, exact repeated-search equivalence, legal PVs, and root position/history restoration. No per-node heap storage or tracing was added.
- Frozen tactical corpus schema `1` contains 13 required categories. Corpus checksum: `f9632e70214cd44a`; aggregate tactical result checksum: `6ab1d87d467d0a2b`; every row passed and records `activated=false`.
- Deterministically generated 200-opening control suite checksum: `1cf5dfa5ebbe0bc5`.
- Identical-policy smoke control: 1 pair / 2 games; mean `0.5`, sample standard error `0.0`, lower bound `0.5`, `rejected_strength`, `activated=false`; report checksum `68902aa6b915986e`.
- Identical-policy development control: 8 pairs / 16 games; mean `0.5`, sample standard error `0.0`, lower bound `0.5`, `rejected_strength`, `activated=false`; report checksum `4cdf0d802b6295e8`.
- Identical-policy production control: 200 pairs / 400 games; mean `0.5`, sample standard error `0.0`, lower bound `0.5`, `rejected_strength`, `activated=false`; report checksum `4df2e4004f4d960a`.
- Permanent focused run `31009413307`, job `92317414834`, artifact `8931829296` (`s2-3-baseline-9a56a27552b5032860802db8fe5d82d65ac93d2d`, artifact digest `6ef8a47a30387fc5038451317cd12cdb6cfeb0c43c2e17603c03357c42aacc2b`): audit, formatting, strict Clippy, focused tests, release build, two byte-identical full evidence generations, production control, and artifact preservation passed.
- Exact Rust CI run `31009414734`: x86-64 workspace-quality job `92317486379` and native ARM64 job `92317486396`; locked checks, strict Clippy, all-target tests, release perft, rustdoc, debug/release builds, UCI smoke, and differential oracle passed.
- Exact performance run `31009412488`: x86-64 job `92317412062`, artifact `8931750887`; ARM64 job `92317411999`, artifact `8931753848`; seven-sample distributions, zero-allocation audits, and unchanged reference-budget comparisons passed.
- Exact robustness run `31009413508`: fuzz job `92317415090`, Miri job `92317415217`, sanitizer/TSan job `92317415237`; all passed.
- Exact Android/JNI run `31009412535`: API-35 instrumented JNI job `92317424809`, host JVM job `92317424817`, Android lint job `92317424840`; all passed.
- Existing Task 24 performance rows, semantic checksums, x86-64/ARM64 reference files, UCI behavior, safe Rust facade, C ABI, JNI, Android, package version, search policy, evaluation weights, and production defaults remain unchanged.
- Integration defects were fixed at their source: exact staging witnesses, Clippy-clean tests, a mistakenly terminal proposed zugzwang fixture, canonical `key=value` report parsing, and one audit path overreach. No lint suppression, ignored failure, downgraded gate, silent fallback, implicit discovery, temporary payload, or write-capable permanent workflow remains.

"""

marker = "## Status rules\n"
if text.count(marker) != 1:
    raise SystemExit("expected one status-rules marker")
if "## S2-3 implementation record" in text:
    raise SystemExit("S2-3 implementation record already exists")
text = text.replace(marker, record + marker, 1)

old_summary = "| S2-3 | Baseline strength, diagnostics, and performance capture | **Not started** |"
new_summary = "| S2-3 | Baseline strength, diagnostics, and performance capture | **Complete** |"
if text.count(old_summary) != 1:
    raise SystemExit("expected one S2-3 summary row")
text = text.replace(old_summary, new_summary, 1)

start_marker = "# Task S2-3: Baseline strength, diagnostics, and performance capture — NOT STARTED"
end_marker = "\n---\n\n# Task S2-4: Correct allocation-free Static Exchange Evaluation — NOT STARTED"
start = text.find(start_marker)
end = text.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit("could not isolate S2-3 section")
section = text[start:end]
section = section.replace(
    start_marker,
    "# Task S2-3: Baseline strength, diagnostics, and performance capture — COMPLETE",
    1,
)
section = section.replace("- [ ]", "- [x]")
old_gate = "**S2-3 gate:** The authoritative v0.1 policy has exact search, performance, tactical, and strength baseline evidence."
new_gate = "**S2-3 gate:** Complete. The authoritative v0.1 policy has exact deterministic search diagnostics, a frozen tactical corpus, seven-sample x86-64 and ARM64 performance evidence, and symmetric smoke/development/200-pair production controls while remaining inactive."
if section.count(old_gate) != 1:
    raise SystemExit("expected one S2-3 gate")
section = section.replace(old_gate, new_gate, 1)
text = text[:start] + section + text[end:]

old_next = "Begin with **S2-3 only**: baseline strength, diagnostics, and performance capture. Do not implement SEE, PVS, LMR, pruning, or tablebases until S2-3 establishes exact baseline diagnostics and evidence."
new_next = "Begin with **S2-4 only**: correct allocation-free Static Exchange Evaluation. Do not integrate SEE into move ordering or pruning, and do not implement PVS, LMR, null move, frontier pruning, or tablebases until the standalone S2-4 SEE contract, independent oracle, robustness, and allocation gates are complete."
if text.count(old_next) != 1:
    raise SystemExit("expected one initial-next-action witness")
text = text.replace(old_next, new_next, 1)

tracker.write_text(text)
