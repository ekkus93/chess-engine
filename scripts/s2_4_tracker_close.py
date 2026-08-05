#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md"


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


text = TRACKER.read_text(encoding="utf-8")
if "## S2-4 implementation record" in text:
    raise SystemExit("S2-4 implementation record already exists")

record = """
## S2-4 implementation record

- Disposition: complete; the standalone allocation-free SEE primitive is accepted for later controlled ordering or pruning candidates, while production search remains unchanged and activation remains false.
- Starting `master` SHA: `f5a4217ca55a8b8d469b3e23e727f85706ba9aff`.
- Core implementation SHA: `cbffe1287f7a0c54eae63de71c18211fd75d9503`.
- Robustness/performance evidence implementation SHA: `995529687ce5fb3ab28ef37d30cecccfcbfcbaa8`.
- Exact validation SHA: `ffae5bf54555ae3f1224135010ef4ea71633056e`.
- SEE schema: `1`; policy identifier: `53454556414c3031`; semantic checksum: `0367223104886e8e`; maximum alternating recapture plies: `64`.
- Stable exchange-accounting values are pawn `100`, knight `320`, bishop `330`, rook `500`, queen `900`, and king `20000`; they are deliberately independent of tuned evaluation weights.
- Added a typed fail-loud `chess-core` SEE API for ordinary captures, en passant, quiet promotions, and capture promotions. Ordinary quiet moves, double pawn pushes, castling, contradictory occupancy/geometry/promotion state, illegal king exposure, capacity exhaustion, and arithmetic overflow cannot silently become neutral scores.
- The production algorithm uses fixed local bitboards and bounded recursion, removes the actual en-passant pawn before attack recomputation, reveals rook/queen and bishop/queen x-rays, excludes pinned attackers and illegal king recaptures, chooses least valuable legal attackers deterministically, evaluates all promotion identities, and never mutates the caller's position or allocates heap memory.
- The independent oracle is structurally different: it uses authoritative legal move generation plus make/unmake after every exchange, filters legal recaptures to the contested square, applies the same deterministic least-value/source ordering contract, permits a side to decline a losing continuation, and compares curated plus deterministic generated positions.
- Permanent regressions cover winning/equal/poisoned exchanges, multiple attackers and defenders, rook and bishop x-rays, pins, illegal king recaptures, en-passant occupancy, quiet promotions, all four capture-promotion identities, color symmetry, exact root restoration, malformed input, capacity bounds, and deterministic semantic identity.
- Focused SEE run `31017544295`: x86-64 job `92345450893`, artifact `8935144456`, digest `85eaaa82b3e0c71064d79c922ddc3beb7f1155f024b7781737965c2465dfd2fc`; ARM64 job `92345450837`, artifact `8935145060`, digest `ff3818f13144a60cf18beb07c2fd66e9f2891430f46ca5030b1eb0467c64ba7d`; audit, formatting, strict Clippy, focused core/oracle/fuzz/Miri tests, release builds, seven-sample distributions, zero allocations, and stable result/semantic checksums passed. Median `see.exchange` time was `115 ns` on x86-64 and `86 ns` on ARM64 for this run.
- Exact Rust CI run `31017544604`: x86-64 workspace-quality job `92345452117` and native ARM64 job `92345451984`; all inherited and S2-4 audits, locked checks, strict Clippy, all-target tests, release perft, rustdoc, debug/release builds, UCI smoke, and differential oracle passed.
- Exact performance run `31017544299`: x86-64 job `92345451159`, artifact `8935143722`; ARM64 job `92345451033`, artifact `8935142184`; existing seven-sample distributions, zero-allocation audits, semantic checksums, and reference budgets remained green and unchanged.
- Exact robustness run `31017545028`: fuzz job `92345454104`, Miri job `92345454070`, sanitizer/TSan job `92345454065`; the dedicated SEE corpus/campaign, strict fuzz checks, Miri SEE regression, ASan/LSan SEE suite, lifecycle sanitizers, and TSan cancellation gate passed.
- Exact Android/JNI run `31017544444`: API-35 instrumented JNI job `92346311916`, host JVM job `92346311727`, Android lint job `92346311811`, artifact `8935371724`; all passed.
- Exact tracker authority run `31017544324`, job `92345450787`; all inherited audits, S2-3 baseline audit, standalone S2-4 audit, and pre-closure progression checks passed.
- No strength match was required or used because S2-4 adds an inactive standalone primitive and does not change search decisions, evaluation weights, policy identity, UCI, safe Rust facade, C ABI, JNI, Android, package version, performance references, or production defaults.
- Integration defects were repaired at their source or validation boundary: temporary payload transcription, fuzz-workspace formatting order, workflow-token scope separation, and an audit witness for a stronger `const` API. No lint suppression, ignored failure, downgraded gate, silent fallback, implicit discovery, temporary payload, or write-capable permanent workflow remains in the validated tree.
"""

status_marker = "\n## Status rules"
if text.count(status_marker) != 1:
    raise SystemExit("status-rules insertion witness changed")
text = text.replace(status_marker, record + status_marker, 1)

summary_old = "| S2-4 | Correct allocation-free Static Exchange Evaluation | **Not started** |"
summary_new = "| S2-4 | Correct allocation-free Static Exchange Evaluation | **Complete** |"
if text.count(summary_old) != 1:
    raise SystemExit("S2-4 summary witness changed")
text = text.replace(summary_old, summary_new, 1)

start_marker = "# Task S2-4: Correct allocation-free Static Exchange Evaluation — NOT STARTED"
end_marker = "# Task S2-5: SEE capture-ordering candidate — NOT STARTED"
start = text.find(start_marker)
end = text.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit("S2-4 task boundaries changed")
section = text[start:end]
section = section.replace(
    start_marker,
    "# Task S2-4: Correct allocation-free Static Exchange Evaluation — COMPLETE",
    1,
)
section = section.replace("- [ ]", "- [x]")
gate_old = "**S2-4 gate:** SEE matches an independent legal capture oracle, is deterministic, fail-loud, non-mutating, and allocation-free."
gate_new = "**S2-4 gate:** Complete. SEE matches an independent legal capture oracle, is deterministic, fail-loud, non-mutating, allocation-free, and remains inactive outside controlled tooling."
if section.count(gate_old) != 1:
    raise SystemExit("S2-4 gate witness changed")
section = section.replace(gate_old, gate_new, 1)
if "- [ ]" in section:
    raise SystemExit("unchecked S2-4 item remains")
text = text[:start] + section + text[end:]

next_old = "Begin with **S2-4 only**: correct allocation-free Static Exchange Evaluation. Do not integrate SEE into move ordering or pruning, and do not implement PVS, LMR, null move, frontier pruning, or tablebases until the standalone S2-4 SEE contract, independent oracle, robustness, and allocation gates are complete."
next_new = "Begin with **S2-5 only**: the inactive SEE capture-ordering candidate. Do not add SEE pruning, quiescence redesign, PVS, LMR, null move, frontier pruning, or tablebases until S2-5 has isolated policy identity, exact correctness parity, diagnostics, performance evidence, and an explicit disposition."
if text.count(next_old) != 1:
    raise SystemExit("initial-next-action witness changed")
text = text.replace(next_old, next_new, 1)

TRACKER.write_text(text, encoding="utf-8")
Path(__file__).unlink()
run("git", "config", "user.name", "Phillip Chin")
run("git", "config", "user.email", "ekkus93@gmail.com")
run("git", "add", str(TRACKER.relative_to(ROOT)), "scripts/s2_4_tracker_close.py")
run("git", "commit", "-m", "docs: close S2-4 standalone SEE gate")
run("git", "push", "origin", "HEAD:master")
