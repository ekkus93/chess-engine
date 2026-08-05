from pathlib import Path


def strip_trailing_whitespace(path: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    normalized = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
    file_path.write_text(normalized, encoding="utf-8")


strip_trailing_whitespace("docs/RUST_CHESS_ENGINE_V0_2_S2_7_PVS_2026-08-05.md")

workflow_path = Path(".github/workflows/s2-7-pvs.yml")
workflow = workflow_path.read_text(encoding="utf-8")
focused_line = "          cargo test --locked -p chess-search --test s2_7_pvs\n"
if workflow.count(focused_line) != 2:
    raise SystemExit("expected two duplicate focused-test commands in permanent workflow")
workflow = workflow.replace(focused_line, "")
workflow = workflow.replace(
    "      - name: Run focused and complete search tests\n",
    "      - name: Run complete search tests\n",
)
workflow_path.write_text(workflow, encoding="utf-8")

Path(".github/s2_7_publication_repair.py").unlink()
