#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLOSE = ROOT / ".github/android_second_corrections_close.py"
RESUME_SCRIPT = ".github/android_second_corrections_close_resume.py"
RESUME_WORKFLOW = ".github/workflows/android-second-corrections-close-resume.yml"

source = CLOSE.read_text()
needle = '    run("bash", "scripts/dev.sh", "fast")\n'
pos = source.index(needle)
# The first dev.sh-fast invocation runs before the source-mutating temporary workflow
# deletes itself, so the permanent workflow-policy audit correctly rejects it. Keep the
# second invocation, which runs against the actual candidate closure tree after cleanup.
source = source[:pos] + source[pos + len(needle):]

namespace: dict[str, object] = {"__name__": "android_second_corrections_close_payload"}
exec(compile(source, "android_second_corrections_close.payload", "exec"), namespace)

original_close_authority = namespace["close_authority"]
audit_path = ROOT / "scripts/task_post_port_review_fix_audit.sh"


def close_authority_with_resume_hygiene() -> None:
    original_close_authority()  # type: ignore[operator]
    audit = audit_path.read_text()
    anchor = '    ".github/workflows/android-second-corrections-close.yml" \\\n'
    addition = anchor + (
        '    ".github/android_second_corrections_close_resume.py" \\\n'
        '    ".github/workflows/android-second-corrections-close-resume.yml" \\\n'
    )
    if audit.count(anchor) != 1:
        raise RuntimeError("closure audit helper anchor not found exactly once")
    audit_path.write_text(audit.replace(anchor, addition, 1))


namespace["close_authority"] = close_authority_with_resume_hygiene
temporaries = namespace["TEMPORARIES"]
assert isinstance(temporaries, list)
temporaries.extend([RESUME_SCRIPT, RESUME_WORKFLOW])
namespace["finalize"]()  # type: ignore[operator]
