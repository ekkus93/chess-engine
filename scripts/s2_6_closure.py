#!/usr/bin/env python3
from pathlib import Path

TRACKER = Path("docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md")
CONTRACT = Path("docs/RUST_CHESS_ENGINE_V0_2_S2_6_QUIESCENCE_2026-08-05.md")

tracker = TRACKER.read_text()
contract = CONTRACT.read_text()

record = r'''## S2-6 implementation record

- Disposition: complete; the isolated SEE-pruning candidate and the separately identified SEE-plus-delta candidate are both **rejected for activation**. Both remain typed, inactive controlled candidates; production search and all adapters continue to use the authoritative v0.1 policy.
- Starting `master` SHA: `4174c2bf69f4e30b49b669960c33ec506197d425`.
- Core implementation SHA: `e778864e470fb967d215c0dc08fb864222802619`.
- Permanent evidence implementation SHA: `3f59152650be324348008f5b7dfb248f33f6a7dd`.
- Exact validated candidate SHA: `199c893ecd50601491612b8b196f6e93169a32fa`.
- Baseline policy identifier/checksum: `5630315f504f4c31` / `0c0769ef9d034770`.
- SEE-pruning policy identifier/checksum: `5332365345455031` / `3638a5c288517f61`.
- SEE-plus-delta policy identifier/checksum: `53323644454c5031` / `9f2ec2d471425fb7`.
- Baseline contract remains exact: terminal and rule-draw resolution precede the tactical guard; stand-pat is allowed only outside check; checked nodes search every legal evasion; non-checked nodes search captures and every promotion; guard exhaustion in check remains typed `QuiescenceDepthLimitReachedInCheck`; cancellation and all error paths restore position, history, line length, and Zobrist identity.
- SEE pruning uses a strict `< -100 cp` threshold and excludes in-check nodes, promotions, en passant, checking moves, mate-score windows, and sole tactical responses. SEE/internal contradictions propagate as typed errors; there is no unpruned, MVV-LVA, neutral-score, or static-evaluation fallback.
- Delta pruning is a separate identity evaluated only after the SEE candidate received its disposition. It requires SEE pruning, uses a fixed `200 cp` margin plus typed captured-piece maximum gain, and initially excludes in-check nodes, promotions, checking moves, mate-score domains, and sole tactical responses. Attempts and prunes are counted independently.
- Frozen 13-case tactical parity passed for baseline, SEE, and delta identities. Seven explicitly bounded independent reference-quiescence comparisons passed. Aggregate checksum: `702e3076191d8a25`; total SEE prunes: `4197`; delta attempts/prunes: `9344/1566`; every report records `activated=false`.
- Fixed-node SEE comparison: 8 pairs / 16 games at 2,000 nodes; wins/losses `0/0`, unfinished `16`; no illegal moves, crashes, time forfeits, or infrastructure failures; `rejected_strength`; x86-64 report checksum `44edc6685584dc71`.
- Clock SEE comparison: 8 pairs / 16 games at 10 ms; wins/losses `0/0`, unfinished `16`; no illegal moves, crashes, time forfeits, or infrastructure failures; `rejected_strength`; checksum `c1dff6ae8f6ab694`.
- SEE was therefore rejected before delta interpretation. Delta fixed-node comparison: 8 pairs / 16 games, wins/losses `0/0`, unfinished `16`, `rejected_strength`, checksum `14ab1519be67e186`. Delta clock comparison: 8 pairs / 16 games, wins/losses `0/0`, unfinished `16`, `rejected_strength`, checksum `883ef0ea8c0eff10`. All failure categories remained zero.
- Seven-sample x86-64 distribution: baseline median `208614279 ns`; SEE `215341536 ns` (ratio `1.032247`); delta `226274520 ns` (ratio `1.084655`). Deterministic nodes remained `40000`; qnodes were `35620/35293/35047`; beta cutoffs `3265/3517/3745`; first-move cutoffs `2715/2928/3144`.
- Seven-sample ARM64 distribution: baseline median `173743305 ns`; SEE `178666293 ns` (ratio `1.028335`); delta `187212494 ns` (ratio `1.077523`). The same deterministic node, qnode, cutoff, SEE, and delta counts were reproduced.
- End-to-end allocation maxima are reported honestly: baseline `42` calls / `28400` bytes; SEE `44` / `28418` (`+2` / `+18`); delta `48` / `28484` (`+6` / `+84`). The separate designated recursive hot-path audit remained zero-allocation on x86-64 and ARM64.
- Permanent focused run `31049824797`: x86-64 job `92454143665`, artifact `8948044156`, digest `a263c00f7cf4aaf4ba0134832038f559290917d3cb091bcb3f0d04ad089f3b8f`; ARM64 job `92454143629`, artifact `8948004424`, digest `08b7cf67f4ad6b5185b22749448c4a35e973a320f0c5158ac5b540e95a6aadbc`; all focused correctness, duplicate deterministic evidence, strength, timing, allocation, and artifact gates passed.
- Exact Rust CI run `31049824721`: x86-64 workspace-quality job `92454153203` and native ARM64 job `92454153087`; all audits, locked checks, strict Clippy, all-target/all-feature tests, release perft, rustdoc, debug/release builds, UCI smoke, and differential oracle passed.
- Exact robustness run `31049825021`: fuzz job `92454158035`, Miri job `92454158042`, sanitizer/TSan job `92454158158`; all passed.
- Exact performance run `31049824916`: x86-64 job `92454205219` and ARM64 job `92454205258`; zero-allocation and reference-budget gates passed.
- Exact Android/JNI run `31049824819`: API-35 instrumented JNI job `92454146368`, host JVM job `92454146421`, Android lint job `92454146646`; all passed.
- Production UCI, safe Rust facade, C ABI, JNI, Android, package version, evaluation weights, authoritative v0.1 policy, and defaults remain unchanged. No first-party lint suppression, ignored failure, downgraded gate, silent fallback, implicit discovery, temporary helper, or write-capable permanent workflow remains in the validated candidate tree.

'''

anchor = "## Program guardrails\n"
if tracker.count(anchor) != 1:
    raise SystemExit("expected one program-guardrails anchor")
if "## S2-6 implementation record" in tracker:
    raise SystemExit("S2-6 implementation record already exists")
tracker = tracker.replace(anchor, record + anchor, 1)

replacements = {
    "| S2-6 | Quiescence redesign candidates | **Not started** |":
        "| S2-6 | Quiescence redesign candidates | **Complete — SEE and delta rejected; inactive** |",
    "# Task S2-6: Quiescence redesign candidates — NOT STARTED":
        "# Task S2-6: Quiescence redesign candidates — COMPLETE",
    "**S2-6 gate:** Each quiescence semantic change has an isolated identity, targeted correctness evidence, and explicit acceptance/rejection/defer decision.":
        "**S2-6 gate:** Complete. Both semantic candidates have isolated identities and exact correctness evidence. SEE pruning was evaluated first and rejected; SEE-plus-delta was then evaluated independently and rejected. Both remain inactive, and production defaults are unchanged.",
    "Begin with **S2-4 only**": "Begin with **S2-7 only**",
}
for old, new in replacements.items():
    if tracker.count(old) != 1:
        raise SystemExit(f"expected one tracker witness: {old}")
    tracker = tracker.replace(old, new, 1)

start = tracker.index("# Task S2-6: Quiescence redesign candidates — COMPLETE")
end = tracker.index("# Task S2-7: Principal Variation Search candidate — NOT STARTED")
section = tracker[start:end]
if section.count("- [ ]") != 21:
    raise SystemExit(f"expected 21 unchecked S2-6 tasks, found {section.count('- [ ]')}")
section = section.replace("- [ ]", "- [x]")
tracker = tracker[:start] + section + tracker[end:]

s2_7_end = tracker.index("# Task S2-8:", end)
s2_7 = tracker[end:s2_7_end]
if "- [x]" in s2_7 or "- [ ]" not in s2_7:
    raise SystemExit("S2-7 state changed or has no open tasks")

status_old = "**Status:** In progress; baseline contract frozen and isolated candidates inactive"
status_new = "**Status:** Complete; both isolated candidates rejected for activation and remain inactive"
if contract.count(status_old) != 1:
    raise SystemExit("expected one S2-6 contract status")
contract = contract.replace(status_old, status_new, 1)

final_section = r'''

## Final evidence and disposition

The exact validated candidate tree is `199c893ecd50601491612b8b196f6e93169a32fa`. Permanent workflow run `31049824797` passed on x86-64 and native ARM64 and preserved exact-head artifacts. The frozen 13-case tactical corpus and seven bounded independent-reference cases passed with aggregate checksum `702e3076191d8a25`. The corpus observed `4197` SEE prunes and `9344/1566` delta attempts/prunes while preserving scores, completed depths, legal PVs, and root state.

SEE pruning was evaluated first. Its fixed-node and clock development reports both returned `rejected_strength`, with every one of the 16 games in each protocol reaching the explicit maximum-ply boundary and no illegal moves, crashes, time forfeits, or infrastructure failures. Its seven-sample median runtime was 3.22% slower than baseline on x86-64 and 2.83% slower on ARM64. It is rejected for activation.

Only after that disposition was fixed was the SEE-plus-delta identity interpreted. Its independent fixed-node and clock reports also returned `rejected_strength` with all failure categories zero. Its median runtime was 8.47% slower on x86-64 and 7.75% slower on ARM64. It is separately rejected for activation.

Both implementations remain explicit controlled identities for future experiments, but neither is reachable from production adapters or defaults. All exact-head CI, robustness, performance, ARM64, host-JNI, Android lint, and API-35 instrumented JNI gates passed. `activated=false` remains authoritative.
'''
if "## Final evidence and disposition" in contract:
    raise SystemExit("final S2-6 evidence already exists")
contract = contract.rstrip() + final_section + "\n"

TRACKER.write_text(tracker)
CONTRACT.write_text(contract)
print("S2-6 tracker and contract closure applied")
