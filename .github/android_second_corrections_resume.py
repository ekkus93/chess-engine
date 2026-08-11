#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / ".github/android_second_corrections_ralph.py"
IMPLEMENTATION_START = "df9155171e84b1be295bf0cd482582d10e5b3d6c"
RESUME_SCRIPT = ROOT / ".github/android_second_corrections_resume.py"
RESUME_WORKFLOW = ROOT / ".github/workflows/android-second-corrections-resume.yml"

wrapper = WRAPPER.read_text()
match = re.search(r'base64\.b64decode\("([A-Za-z0-9+/=]+)"\)', wrapper)
if match is None:
    raise RuntimeError("could not extract bounded Ralph payload")
source = gzip.decompress(base64.b64decode(match.group(1))).decode()

replace_section_block = '''def replace_section(path: Path, start: str, end: str, replacement: str) -> None:\n    text = path.read_text()\n    a = text.index(start)\n    b = text.index(end, a)\n    path.write_text(text[:a] + replacement.rstrip() + "\\n\\n---\\n\\n" + text[b:])\n\n\n'''
update_section_block = replace_section_block + '''def update_section(path: Path, start: str, end: str, updater) -> None:\n    text = path.read_text()\n    a = text.index(start)\n    b = text.index(end, a)\n    path.write_text(text[:a] + updater(text[a:b]) + text[b:])\n\n\n'''
if replace_section_block not in source:
    raise RuntimeError("could not locate section helper insertion point")
source = source.replace(replace_section_block, update_section_block, 1)

cleanup_block = '''    if RALPH_WORKFLOW.exists():\n        RALPH_WORKFLOW.unlink()\n'''
cleanup_replacement = cleanup_block + '''    for path in (ROOT / ".github/android_second_corrections_resume.py", ROOT / ".github/workflows/android-second-corrections-resume.yml"):\n        if path.exists():\n            path.unlink()\n'''
if cleanup_block not in source:
    raise RuntimeError("could not locate bounded-helper cleanup point")
source = source.replace(cleanup_block, cleanup_replacement, 1)

main_pattern = re.compile(
    r'''def main\(\) -> None:\n.*?\n\nif __name__ == "__main__":\n    main\(\)\n''',
    re.DOTALL,
)
main_replacement = f'''def main() -> None:\n    configure_git()\n    implementation_start = "{IMPLEMENTATION_START}"\n    sc002()\n    final_source_sha, probe_run, probe_job, probe_artifact = sc003()\n    closure_sha = sc004(implementation_start, final_source_sha, (probe_run, probe_job, probe_artifact))\n    print(f"SECOND_CORRECTIONS_CLOSURE_SHA={{closure_sha}}", flush=True)\n    print("Repository-resident closure is complete. Permanent exact-SHA CI remains external terminal gate.", flush=True)\n\n\nif __name__ == "__main__":\n    main()\n'''
source, count = main_pattern.subn(main_replacement, source, count=1)
if count != 1:
    raise RuntimeError("could not replace bounded Ralph entry point")

exec(compile(source, "android_second_corrections_resume.payload", "exec"))
