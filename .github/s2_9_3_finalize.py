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

    audit_path = ROOT / "scripts/task_s2_9_null_move_feasibility_audit.sh"
    audit = audit_path.read_text(encoding="utf-8")
    audit = replace_once(
        audit,
        "grep -Fq '| S2-9 | Optional null-move pruning decision/candidate | **In progress — search-null transition complete; pruning policy not started** |' \"$tracker\" || fail \"summary status is not advanced\"",
        "grep -Fq '| S2-9 | Optional null-move pruning decision/candidate | **In progress — conservative policy complete; validation/disposition not started** |' \"$tracker\" || fail \"summary status is not advanced through S2-9.3\"",
        "feasibility summary assertion",
    )
    audit = replace_once(
        audit,
        "grep -Fq 'Begin with **S2-9.3 only**:' \"$tracker\" || fail \"next action does not point to S2-9.2\"",
        "grep -Fq 'Begin with **S2-9.4 only**:' \"$tracker\" || fail \"next action does not point to S2-9.4\"",
        "feasibility next action",
    )
    audit = replace_once(
        audit,
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
    audit_path.write_text(audit, encoding="utf-8")

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
