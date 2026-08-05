from pathlib import Path
import subprocess


def strip_trailing_whitespace(path: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    normalized = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
    file_path.write_text(normalized, encoding="utf-8")


strip_trailing_whitespace("docs/RUST_CHESS_ENGINE_V0_2_S2_7_PVS_2026-08-05.md")

# The workflow-scoped GITHUB_TOKEN cannot create or delete workflow files.
# Publish the already validated engine tree without workflow mutations; the
# GitHub connector installs the permanent gate and removes this bootstrap in
# separate explicit commits.
permanent_workflow = Path(".github/workflows/s2-7-pvs.yml")
if not permanent_workflow.is_file():
    raise SystemExit("generated permanent S2-7 workflow is missing")
permanent_workflow.unlink()

bootstrap_workflow = subprocess.check_output(
    ["git", "show", "HEAD:.github/workflows/s2-7-bootstrap.yml"],
    text=True,
)
Path(".github/workflows/s2-7-bootstrap.yml").write_text(
    bootstrap_workflow,
    encoding="utf-8",
)

Path(".github/s2_7_publication_repair.py").unlink()
