from pathlib import Path
import subprocess

tracked = subprocess.check_output(
    ["git", "ls-files", "-z", "--", "s2-7-*"],
).split(b"\0")
paths = [item.decode("utf-8") for item in tracked if item]
if not paths:
    raise SystemExit("no tracked root-level S2-7 evidence outputs found")

subprocess.run(["git", "rm", "-r", "--", *paths], check=True)

ignore_path = Path(".gitignore")
lines = ignore_path.read_text(encoding="utf-8").splitlines()
rules = [
    "# Generated S2-7 evidence outputs",
    "/s2-7-deterministic-*/",
    "/s2-7-clock/",
    "/s2-7-bootstrap-benchmark.tsv",
    "/s2-7-linux-*.tsv",
]
if lines and lines[-1] != "":
    lines.append("")
for rule in rules:
    if rule not in lines:
        lines.append(rule)
ignore_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

Path(".github/s2_7_generated_output_cleanup.py").unlink()
