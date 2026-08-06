#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE_SHA = "029c16ed216a0fc84d6772c10ea8678ad202c6cf"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one occurrence, found {count}")
    return text.replace(old, new, 1)


def main() -> None:
    env = os.environ.copy()
    env["CORE_SHA"] = CORE_SHA
    subprocess.run(
        [sys.executable, ".github/s2_9_3_policy.py", "phase2"],
        cwd=ROOT,
        env=env,
        check=True,
    )

    feasibility_path = ROOT / "scripts/task_s2_9_null_move_feasibility_audit.sh"
    feasibility = feasibility_path.read_text(encoding="utf-8")
    feasibility = replace_once(
        feasibility,
        "grep -Fq '| S2-9 | Optional null-move pruning decision/candidate | **In progress — search-null transition complete; pruning policy not started** |' \"$tracker\" || fail \"summary status is not advanced\"",
        "grep -Fq '| S2-9 | Optional null-move pruning decision/candidate | **In progress — conservative policy complete; validation/disposition not started** |' \"$tracker\" || fail \"summary status is not advanced through S2-9.3\"",
        "feasibility summary assertion",
    )
    feasibility = replace_once(
        feasibility,
        "grep -Fq 'Begin with **S2-9.3 only**:' \"$tracker\" || fail \"next action does not point to S2-9.2\"",
        "grep -Fq 'Begin with **S2-9.4 only**:' \"$tracker\" || fail \"next action does not point to S2-9.4\"",
        "feasibility next action",
    )
    feasibility = replace_once(
        feasibility,
        """if grep -R --line-number -E 'make_search_null|unmake_search_null|null_move_pruning_enabled' \\
  crates/chess-search/src; then
  fail "null pruning integration landed before S2-9.3"
fi
""",
        """grep -Fq 'position.make_search_null()' "$search" || fail "S2-9.3 search-null integration is missing"
grep -Fq 'position.unmake_search_null(undo)' "$search" || fail "S2-9.3 search-null restoration is missing"
grep -Fq 'null_move_pruning_enabled' "$search" || fail "S2-9.3 policy gate is missing"
""",
        "feasibility implementation boundary",
    )
    feasibility_path.write_text(feasibility, encoding="utf-8")

    transition_path = ROOT / "scripts/task_s2_9_search_null_transition_audit.sh"
    transition = transition_path.read_text(encoding="utf-8")
    transition = replace_once(
        transition,
        """unexpected="$(grep -R --line-number -E 'make_search_null|unmake_search_null' crates \\
  | grep -v '^crates/chess-core/src/position/search_null.rs:' || true)"
[[ -z "$unexpected" ]] || fail "search-null transition escaped its core module: $unexpected"

if grep -R --line-number -E 'make_search_null|unmake_search_null|null_move_pruning_enabled' \\
  crates/chess-search/src crates/chess-uci crates/chess-ffi crates/chess-jni 2>/dev/null; then
  fail "search pruning or adapter integration landed during S2-9.2"
fi
""",
        """unexpected="$(grep -R --line-number -E 'make_search_null|unmake_search_null' crates \\
  | grep -v '^crates/chess-core/src/position/search_null.rs:' \\
  | grep -v '^crates/chess-search/src/alpha_beta.rs:' || true)"
[[ -z "$unexpected" ]] || fail "search-null transition escaped approved core/search modules: $unexpected"
grep -Fq 'position.make_search_null()' crates/chess-search/src/alpha_beta.rs \\
  || fail "S2-9.3 search integration is missing make_search_null"
grep -Fq 'position.unmake_search_null(undo)' crates/chess-search/src/alpha_beta.rs \\
  || fail "S2-9.3 search integration is missing unmake_search_null"
if grep -R --line-number -E 'make_search_null|unmake_search_null|null_move_pruning_enabled' \\
  crates/chess-uci crates/chess-ffi crates/chess-jni 2>/dev/null; then
  fail "search-null transition leaked into a production adapter"
fi
""",
        "transition integration boundary",
    )
    transition = replace_once(
        transition,
        """grep -Fq '| S2-9 | Optional null-move pruning decision/candidate | **In progress — search-null transition complete; pruning policy not started** |' "$tracker" \\
  || fail "tracker summary was not advanced"
""",
        """grep -Fq '| S2-9 | Optional null-move pruning decision/candidate | **In progress — conservative policy complete; validation/disposition not started** |' "$tracker" \\
  || fail "tracker summary was not advanced through S2-9.3"
""",
        "transition tracker summary",
    )
    transition = replace_once(
        transition,
        "grep -Fq 'Begin with **S2-9.3 only**:' \"$tracker\" || fail \"next action does not point to S2-9.3\"",
        "grep -Fq 'Begin with **S2-9.4 only**:' \"$tracker\" || fail \"next action does not point to S2-9.4\"",
        "transition next action",
    )
    transition = replace_once(
        transition,
        """s2_9_3="$(sed -n '/## S2-9.3 Conservative policy if implemented/,/## S2-9.4 Validation if implemented/p' "$tracker")"
[[ "$(grep -Fc -- '- [ ]' <<<"$s2_9_3")" -gt 0 ]] || fail "S2-9.3 was advanced without policy evidence"
""",
        """s2_9_3="$(sed -n '/## S2-9.3 Conservative policy if implemented/,/## S2-9.4 Validation if implemented/p' "$tracker")"
[[ "$(grep -Fc -- '- [x]' <<<"$s2_9_3")" -eq 7 ]] || fail "S2-9.3 does not have exactly seven completed requirements"
[[ "$(grep -Fc -- '- [ ]' <<<"$s2_9_3")" -eq 0 ]] || fail "S2-9.3 still has incomplete requirements"
""",
        "transition S2-9.3 progression",
    )
    transition_path.write_text(transition, encoding="utf-8")

    policy_audit_path = ROOT / "scripts/task_s2_9_null_move_policy_audit.sh"
    policy_audit = policy_audit_path.read_text(encoding="utf-8")
    policy_audit = replace_once(
        policy_audit,
        "test ! -e .github/workflows/s2-9-3-stage.yml\n",
        "test ! -e .github/workflows/s2-9-3-stage.yml\ntest ! -e .github/s2_9_3_finalize.py\n",
        "finalizer cleanup audit",
    )
    policy_audit_path.write_text(policy_audit, encoding="utf-8")

    Path(__file__).unlink()


if __name__ == "__main__":
    main()
