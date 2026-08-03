from pathlib import Path

IMPLEMENTATION_SHA = "82b5100f501fe4e4a845d5fb3bdbb1c8fe7d34ef"
VALIDATED_PR_HEAD = "4bb4e30f457b9b84e09485cf51629ab0b3c6d37d"
RUST_RUN = "30859905206"
RUST_JOB = "91839380997"
ANDROID_RUN = "30859905203"
HOST_JOB = "91839428990"
EMULATOR_JOB = "91839429013"


def require_once(path: Path, value: str) -> None:
    count = path.read_text().count(value)
    if count != 1:
        raise SystemExit(f"{path}: expected one occurrence of {value!r}, found {count}")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one occurrence of {old!r}, found {count}")
    path.write_text(text.replace(old, new, 1))


def main() -> None:
    definitions = Path("docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md")
    for item in (
        "deterministic highest weight;",
        "weighted random;",
        "explicit local RNG seed;",
        "legal-move validation before return.",
    ):
        replace_once(definitions, f"- [ ] {item}", f"- [x] {item}")
    for deferred in (
        "- [ ] UCI option to enable/disable book.",
        "- [ ] Safe API configuration.",
        "- [ ] Android asset-supplied book example.",
        "- [ ] Normal operation when no book exists.",
    ):
        require_once(definitions, deferred)

    summary = Path("docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md")
    replace_once(
        summary,
        "| 19 | **In progress** — opening-book abstraction and versioned indexed format complete. |",
        "| 19 | **In progress** — opening-book abstraction, versioned indexed format, and selection policies complete. |",
    )
    replace_once(
        summary,
        "- Task 19.2 versioned indexed opening-book format is complete. Task 19.3 selection policies are next.",
        "- Task 19.3 opening-book selection policies are complete. Task 19.4 adapter integration is next.",
    )
    replace_once(summary, "- [ ] 19.3 Policies.", "- [x] 19.3 Policies.")
    require_once(summary, "- [ ] 19.4 Integration.")
    require_once(summary, "- [ ] 19.5 Tests.")
    require_once(summary, "- [ ] Task 19 gate.")

    ralph = Path("docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md")
    replace_once(
        ralph,
        "**Current phase:** Task 19.2 versioned indexed format complete; Task 19.3 selection policies are next",
        "**Current phase:** Task 19.3 opening-book selection policies complete; Task 19.4 adapter integration is next",
    )
    row_19_2 = "| 19.2 | `781e876563e8b21bb50e6fa83af6afe92b260910` | Rust `30855596855` / `91825754603`; Android `30855596897` / `91825818389`, `91825818440` | version-1 project-specific fixed-record indexed format, canonical four-field FEN keys, little-endian schema, header/payload CRC-32, strict structural corruption rejection, seven focused tests; 317 Rust tests and Android regressions green |"
    row_19_3 = f"| 19.3 | `{IMPLEMENTATION_SHA}` | Rust `{RUST_RUN}` / `{RUST_JOB}`; Android `{ANDROID_RUN}` / `{HOST_JOB}`, `{EMULATOR_JOB}` | exact indexed UCI-to-legal-move resolution, generic candidate revalidation, deterministic highest-weight policy with canonical tie ordering, explicit local-seed SplitMix64 weighted policy, six focused tests; 323 Rust tests and Android regressions green |"
    replace_once(ralph, row_19_2, f"{row_19_2}\n{row_19_3}")

    contract = Path("docs/RUST_OPENING_BOOK_SELECTION.md")
    text = contract.read_text()
    if "## Completion evidence" in text:
        raise SystemExit(f"{contract}: completion evidence already exists")
    evidence = f"""

## Completion evidence

- Exact merged implementation SHA: `{IMPLEMENTATION_SHA}`.
- Exact PR head validated before rebase merge: `{VALIDATED_PR_HEAD}`; the production policy blob is unchanged at the merged SHA.
- Permanent Rust validation: run `{RUST_RUN}`, job `{RUST_JOB}`.
- Permanent Android regression validation: run `{ANDROID_RUN}`, host JVM job `{HOST_JOB}`, API-35 emulator job `{EMULATOR_JOB}`.
- Six focused Task 19.3 policy and legality tests passed; `chess-book` executed 17 tests and the complete workspace executed 323 non-documentation Rust tests with zero failures.
- Committed lockfile verification, workspace metadata, rustfmt, all-target/all-feature compilation, strict Clippy with warnings denied, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and the independent differential oracle passed.
- Differential validation covered 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- The unchanged Android gate rebuilt and verified both JNI ABIs, passed host JVM tests, rebuilt the AAR/test APK, and passed the API-35 emulator lifecycle.
- Task 19.3 is complete. Tasks 19.4–19.5 and the overall Task 19 gate remain open.
"""
    contract.write_text(text.rstrip() + evidence)


if __name__ == "__main__":
    main()
