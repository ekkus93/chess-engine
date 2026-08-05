from pathlib import Path

path = Path("docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md")
text = path.read_text()

text = text.replace(
    "| S2-1 | Versioned search-policy and engine-variant identity | **Not started** |",
    "| S2-1 | Versioned search-policy and engine-variant identity | **Complete** |",
    1,
)
text = text.replace(
    "# Task S2-1: Versioned search-policy and engine-variant identity — NOT STARTED",
    "# Task S2-1: Versioned search-policy and engine-variant identity — COMPLETE",
    1,
)

start = text.index("# Task S2-1:")
end = text.index("\n---\n\n# Task S2-2:", start)
section = text[start:end]
section = section.replace("- [ ]", "- [x]")
section = section.replace(
    "**S2-1 gate:** A stable explicit engine/search identity exists without changing production behavior.",
    "**S2-1 gate:** Complete. A stable explicit engine/search identity exists, malformed and unsupported policy input fails closed, explicit v0.1 search is deterministic-equivalent to the existing default, and production adapters/defaults remain unchanged.",
    1,
)
text = text[:start] + section + text[end:]

marker = "## Status rules\n"
record = """## S2-1 implementation record

- Disposition: complete; identity infrastructure accepted for subsequent controlled validation work; activation remains false.
- Implementation SHA: `7e4e1aacb0160b96683646a29058ddd783043a6e`.
- Exact validation SHA: `d645aa625800238fba8d0be0cb7066ee56884120`.
- Search-policy schema: `1`.
- Authoritative v0.1 policy identifier: `5630315f504f4c31`.
- Authoritative v0.1 policy checksum: `0c0769ef9d034770`.
- Evaluation-weight identity remains baseline schema `1`, identifier `424153454c494e45`, checksum `d2cca7ae10ec6e34`.
- Added typed fail-closed search policy, canonical policy text I/O, controlled explicit-policy iterative search, complete engine-variant identity, permanent tests, documentation, audit, and focused CI workflow.
- Existing convenience search entry points continue to use the exact v0.1 policy and `EvaluationWeights::DEFAULT`.
- UCI, safe Rust facade, C ABI, JNI, Android, package version, and production defaults expose no experimental policy input and remain unchanged.
- Assigned future feature bits are identity-visible but validation rejects enabling SEE, PVS, LMR, null move, futility, razoring, delta pruning, and late-move pruning before their implementation tasks.
- Different policy or evaluator identities require separate caller-owned transposition tables.
- Permanent focused identity run `30995963744`, job `92272978556`: audit, formatting, strict Clippy, explicit v0.1 parity, policy schema, canonical text, variant identity, and CLI round-trip passed.
- Exact Rust CI run `30995963711`: x86-64 job `92273019216` and native ARM64 job `92273019344`; all audits, locked checks, strict Clippy, all-target tests, release perft, rustdoc, builds, UCI smoke, and differential oracle passed.
- Exact performance run `30995963716`: x86-64 job `92272978703`, artifact `8926152440`; ARM64 job `92272978813`, artifact `8926154375`; zero-allocation and reference-budget gates passed.
- Exact robustness run `30995963722`: fuzz job `92272978711`, sanitizer job `92272978801`, Miri job `92272978866`; all passed.
- Exact Android/JNI run `30995963800`: host JVM job `92272988350`, Android lint job `92272988457`, API-35 instrumented JNI job `92272988476`; all passed.
- No strength match was required or used because S2-1 changes identity/control infrastructure and preserves exact v0.1 production search behavior.
- Discovered integration defects were fixed at source or workflow level; no lint suppression, ignored failure, downgraded gate, silent fallback, implicit discovery, or temporary helper remains in the validated implementation tree.

"""
if record not in text:
    text = text.replace(marker, record + marker, 1)

text = text.replace(
    "Begin with **S2-1 only**: versioned search-policy and engine-variant identity. Do not implement SEE, PVS, LMR, pruning, or tablebases until S2-1, S2-2, and S2-3 establish explicit identity, generalized validation, and baseline diagnostics.",
    "Begin with **S2-2 only**: generalized strength-validation infrastructure. Do not implement SEE, PVS, LMR, pruning, or tablebases until S2-2 and S2-3 establish generalized variant validation and baseline diagnostics.",
    1,
)

path.write_text(text)
