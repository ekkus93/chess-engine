#!/usr/bin/env python3
"""Fail-closed audit for tracked generated artifacts and portable filenames."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

UNSAFE_FILENAME_CHARACTERS = frozenset('*?:"<>|\r\n')
GENERATED_PREFIXES = (
    "target/",
    "fuzz/target/",
    "tmp/",
    ".venv-oracle/",
    "tuning-output/",
    "self-play-output/",
    "android-harness/.gradle/",
)
GENERATED_PARTS = ("/build/", "/target/")
GENERATED_BASENAMES = {
    "task24-android-performance.txt",
    "performance-linux-x86-64.tsv",
    "performance-linux-arm64.tsv",
}
REQUIRED_VERSIONED_FILES = (
    "fixtures/perft.tsv",
    "fixtures/differential_corpus.tsv",
    "fixtures/self_play_config.example",
    "fixtures/self_play_openings.tsv",
    "fixtures/tuning_config.example",
    "docs/RUST_GENERATED_ARTIFACT_POLICY.md",
)
REQUIRED_IGNORE_LINES = (
    ".venv-oracle/",
    "tuning-output/",
    "self-play-output/",
    "callgrind.*",
    "performance-*.tsv",
    "task24-android-performance.txt",
)


def unsafe_filename(path: str) -> bool:
    return any(character in path for character in UNSAFE_FILENAME_CHARACTERS)


def transient_generated_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if normalized.startswith("benchmarks/task24/"):
        return False
    basename = normalized.rsplit("/", 1)[-1]
    return (
        normalized.startswith(GENERATED_PREFIXES)
        or any(part in normalized for part in GENERATED_PARTS)
        or basename in GENERATED_BASENAMES
        or basename.startswith("callgrind.")
        or (basename.startswith("performance-") and basename.endswith(".tsv"))
    )


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        stdout=subprocess.PIPE,
    )
    return [item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def audit(root: Path) -> list[str]:
    errors: list[str] = []
    files = tracked_files()
    for path in files:
        if unsafe_filename(path):
            errors.append(f"tracked filename is not portable: {path!r}")
        if transient_generated_path(path):
            errors.append(f"transient generated artifact is tracked: {path!r}")
    for relative in REQUIRED_VERSIONED_FILES:
        if not (root / relative).is_file():
            errors.append(f"required versioned artifact is missing: {relative}")
    ignore_text = (root / ".gitignore").read_text(encoding="utf-8")
    ignore_lines = {line.strip() for line in ignore_text.splitlines()}
    for line in REQUIRED_IGNORE_LINES:
        if line not in ignore_lines:
            errors.append(f".gitignore is missing generated-artifact rule: {line}")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = audit(root)
    if errors:
        for error in errors:
            print(f"artifact-audit: {error}", file=sys.stderr)
        return 1
    print("artifact-audit: portable filenames and generated-artifact policy passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
