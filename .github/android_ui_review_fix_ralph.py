#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODO = ROOT / "docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md"
IMPLEMENTATION_START = "218158b15d1b500e940eb7a13077636b446869f5"


def run(command: str) -> None:
    print("+", command, flush=True)
    subprocess.run(["bash", "-lc", command], cwd=ROOT, text=True, check=True)


def replace(old: str, new: str, count: int = 1) -> None:
    text = TODO.read_text()
    if text.count(old) < count:
        raise RuntimeError(f"TODO replacement target missing: {old[:160]!r}")
    TODO.write_text(text.replace(old, new, count))


subprocess.run(["git", "config", "user.name", "Ralph Loop"], cwd=ROOT, check=True)
subprocess.run(["git", "config", "user.email", "actions@users.noreply.github.com"], cwd=ROOT, check=True)

# Full applicable AR-021 validation surface on the API-35 runner.
run("gradle -p android-harness :android-app:testDebugUnitTest --no-daemon --stacktrace --console=plain")
run("gradle -p android-harness :android-app:lintDebug --no-daemon --stacktrace --console=plain")
run("cargo test --locked -p chess-core")
run("cargo test --locked -p chess-jni")
run("gradle -p android-harness :android-app:connectedDebugAndroidTest --no-daemon --stacktrace --console=plain")
run("bash scripts/dev.sh fast")
run("bash scripts/task_post_port_review_fix_audit.sh")

# Ensure this pass did not introduce first-party lint suppressions.
run(
    "if git diff --unified=0 " + IMPLEMENTATION_START +
    "..HEAD -- '*.rs' '*.kt' '*.kts' | grep -E '^\\+.*(#\\[(allow|expect)\\(|@Suppress)' >/tmp/review-fix-suppressions.txt; "
    "then cat /tmp/review-fix-suppressions.txt; exit 1; fi"
)

run_id = os.environ.get("GITHUB_RUN_ID", "unknown")
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()

for line in [
    "- [ ] Android app JVM/unit tests pass, including every test added by AR-001 through AR-020.",
    "- [ ] Android lint passes.",
    "- [ ] `crates/chess-core` tests pass, including AR-017's additions.",
    "- [ ] `crates/chess-jni` tests pass, including AR-019's extended contract test.",
    "- [ ] Full Android instrumentation suite passes, including every test added by this pass.",
    "- [ ] `bash scripts/dev.sh fast` passes — mandatory whenever the environment can run it (QI-002); if genuinely unavailable, the equivalent permanent general CI on the exact final SHA is required instead, and the unrun local command is explicitly recorded as such, never silently treated as passed.",
]:
    replace(line, line.replace("- [ ]", "- [x]", 1))

replace(
    "Implementation start SHA:\nFinal source SHA:\n\nAndroid app unit/lint results:\nchess-core test results:\nchess-jni test results:\nAndroid instrumentation results:\nbash scripts/dev.sh fast result:\n",
    f"Implementation start SHA:          {IMPLEMENTATION_START}\n"
    "Final source SHA:                 pending temporary-runner cleanup\n\n"
    f"Android app unit/lint results:    pass — full-validation run {run_id} at {head}\n"
    f"chess-core test results:          pass — full-validation run {run_id} at {head}\n"
    f"chess-jni test results:           pass — full-validation run {run_id} at {head}\n"
    f"Android instrumentation results: pass — full-validation run {run_id} at {head}\n"
    f"bash scripts/dev.sh fast result:  pass — full-validation run {run_id} at {head}\n",
)

# Record the validation state in its own commit. Permanent exact-SHA CI and final
# closure remain open until temporary Ralph machinery is removed.
subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=True)
subprocess.run(["git", "add", str(TODO.relative_to(ROOT))], cwd=ROOT, check=True)
subprocess.run(["git", "commit", "-m", "docs(android): record review-fix full validation"], cwd=ROOT, check=True)
subprocess.run(["git", "push", "origin", "HEAD:master"], cwd=ROOT, check=True)
print("AR-021 full validation recorded", subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), flush=True)
