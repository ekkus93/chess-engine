from pathlib import Path

TRACKER = Path("docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md")
text = TRACKER.read_text()

record = """## S2-2 implementation record

- Disposition: complete; generalized complete-engine-variant validation infrastructure accepted for later candidate work; activation remains false.
- Implementation SHA: `7077c0b2b97b17f1d0dd6ef42fc59e830dcc8069`.
- Exact validation SHA: `ead3be20f7ba027d3c6ab9629ca0e094e6e9eb0f`.
- Complete-variant report schema: `1`; protocol identifier: `5641524956414c31`.
- The historical weight-only report remains schema `1`, identifier `43414e4456414c31`, format `chess-candidate-validation-v1`, and production minimum 200 pairs.
- Added complete identity binding for source SHA, engine version, policy, weights, book/tablebase state, TT size, build identity, and exact invocation.
- Added bounded smoke, paired development, and production tiers; production requires at least 200 independent opening pairs / 400 color-swapped games.
- Added equal-resource `fixed_nodes` and `clock_ms` protocols with recorded purpose, shared limits/configuration, and independent variant transposition tables.
- Added correctness pre-gates for authoritative perft, forced mate, longest survival, tactical/legal-PV behavior, and repeated-search equivalence; failed correctness or infrastructure prevents all match games.
- Added semantic opening deduplication, deterministic seeded scheduling, color-swapped pairs, pair-average statistics, sample standard error, and a one-sided 95% lower confidence bound using the existing z-value.
- Acceptance is fail-closed: the lower bound must strictly exceed `0.5 + minimum_score_margin`, unfinished games have a separate ceiling, ties/inconclusive evidence reject, and only production may emit `accepted_for_activation`.
- Wins, draws, losses, unfinished games, illegal moves, crashes, time forfeits, and infrastructure failures are separate; typed failures are never silently converted into chess results.
- Reports are canonical, checksummed, strictly parsed, atomically persisted through caller-selected same-directory paths, and always serialize `activated=false`.
- Permanent focused run `31002053527`, job `92293045464`: source audit, formatting, strict Clippy, complete-variant tests, and legacy weight-only compatibility passed.
- Exact Rust CI run `31002053507`: x86-64 job `92293040865` and native ARM64 job `92293040807`; all audits, locked checks, strict Clippy, all-target tests, release perft, rustdoc, builds, UCI smoke, and differential oracle passed.
- Exact performance run `31002053545`: x86-64 job `92293062822`, artifact `8928690363`; ARM64 job `92293062784`, artifact `8928694029`; zero-allocation and reference-budget gates passed.
- Exact robustness run `31002053571`: Miri job `92293065411`, sanitizer job `92293065540`, fuzz job `92293065551`; all passed.
- Exact Android/JNI run `31002053564`: API-35 instrumented JNI job `92293579404`, host JVM job `92293579417`, Android lint job `92293579446`; all substantive gates passed.
- No production strength match was required or used because S2-2 adds inactive validation infrastructure and does not change production search, evaluation, adapters, package version, or defaults.
- Integration failures were fixed at source or audit-workflow level. No lint suppression, ignored failure, downgraded gate, silent fallback, implicit configuration discovery, write-capable staging workflow, or temporary payload remains.

"""

status_marker = "## Status rules\n"
if status_marker not in text:
    raise SystemExit("status marker missing")
if "## S2-2 implementation record" not in text:
    text = text.replace(status_marker, record + status_marker, 1)

replacements = {
    "| S2-2 | Generalized strength-validation infrastructure | **Not started** |":
        "| S2-2 | Generalized strength-validation infrastructure | **Complete** |",
    "# Task S2-2: Generalized strength-validation infrastructure — NOT STARTED":
        "# Task S2-2: Generalized strength-validation infrastructure — COMPLETE",
    "**S2-2 gate:** Engine variants can be compared reproducibly without weakening the existing fail-closed candidate protocol.":
        "**S2-2 gate:** Complete. Complete engine variants can be compared reproducibly under fixed-node or clock protocols, fail closed before or during match play, preserve the existing weight-only protocol, and remain inactive.",
    "Begin with **S2-2 only**: generalized strength-validation infrastructure. Do not implement SEE, PVS, LMR, pruning, or tablebases until S2-2 and S2-3 establish generalized variant validation and baseline diagnostics.":
        "Begin with **S2-3 only**: baseline strength, diagnostics, and performance capture. Do not implement SEE, PVS, LMR, pruning, or tablebases until S2-3 establishes exact baseline diagnostics and evidence.",
}
for old, new in replacements.items():
    if old not in text:
        raise SystemExit(f"required tracker text missing: {old}")
    text = text.replace(old, new, 1)

start = text.index("# Task S2-2: Generalized strength-validation infrastructure — COMPLETE")
end = text.index("# Task S2-3: Baseline strength, diagnostics, and performance capture — NOT STARTED")
segment = text[start:end]
if "- [ ]" not in segment:
    raise SystemExit("S2-2 segment has no open checkboxes")
segment = segment.replace("- [ ]", "- [x]")
text = text[:start] + segment + text[end:]

TRACKER.write_text(text)
