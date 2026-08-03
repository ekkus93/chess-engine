from pathlib import Path

IMPLEMENTATION_SHA = "781e876563e8b21bb50e6fa83af6afe92b260910"
RUST_RUN = "30855596855"
RUST_JOB = "91825754603"
ANDROID_RUN = "30855596897"
HOST_JOB = "91825818389"
EMULATOR_JOB = "91825818440"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one occurrence of {old!r}, found {count}")
    path.write_text(text.replace(old, new, 1))


def main() -> None:
    definitions = Path("docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md")
    for item in (
        "Choose Polyglot or a versioned project-specific indexed format.",
        "Document version and endianness.",
        "Validate checksums/schema where applicable.",
        "Reject corrupt input loudly.",
    ):
        replace_once(definitions, f"- [ ] {item}", f"- [x] {item}")

    summary = Path("docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md")
    replace_once(summary, "**Updated:** 2026-08-02", "**Updated:** 2026-08-03")
    replace_once(
        summary,
        "| 19–24 | **Not started**. |",
        "| 19 | **In progress** — opening-book abstraction and versioned indexed format complete. |\n| 20–24 | **Not started**. |",
    )
    replace_once(
        summary,
        "- Task 19.1 opening-book abstraction is complete. Task 19.2 backend format is next.",
        "- Task 19.2 versioned indexed opening-book format is complete. Task 19.3 selection policies are next.",
    )
    replace_once(summary, "- [ ] 19.2 Format.", "- [x] 19.2 Format.")

    ralph = Path("docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md")
    replace_once(
        ralph,
        "**Current phase:** Task 19.1 opening-book abstraction complete; Task 19.2 backend format is next",
        "**Current phase:** Task 19.2 versioned indexed format complete; Task 19.3 selection policies are next",
    )
    row_19_1 = "| 19.1 | `6ce31141d0d4516696f1e9d17ee018606ef7bd4b` | Rust `30852253445` / `91814805656`; Android `30852253399` / `91814815286`, `91814815151` | adapter-neutral `chess-book` crate, typed `OpeningBook`/`BookProvider`, generic weighted `BookMove`, four focused tests, no core/search I/O dependencies; 310 Rust tests and Android regressions green |"
    row_19_2 = f"| 19.2 | `{IMPLEMENTATION_SHA}` | Rust `{RUST_RUN}` / `{RUST_JOB}`; Android `{ANDROID_RUN}` / `{HOST_JOB}`, `{EMULATOR_JOB}` | version-1 project-specific fixed-record indexed format, canonical four-field FEN keys, little-endian schema, header/payload CRC-32, strict structural corruption rejection, seven focused tests; 317 Rust tests and Android regressions green |"
    replace_once(ralph, row_19_1, f"{row_19_1}\n{row_19_2}")

    contract = Path("docs/RUST_OPENING_BOOK_FORMAT.md")
    text = contract.read_text()
    if "## Completion evidence" in text:
        raise SystemExit(f"{contract}: completion evidence already exists")
    evidence = f"""

## Completion evidence

- Exact validated implementation SHA: `{IMPLEMENTATION_SHA}`.
- Permanent Rust validation: run `{RUST_RUN}`, job `{RUST_JOB}`.
- Permanent Android regression validation: run `{ANDROID_RUN}`, host JVM job `{HOST_JOB}`, API-35 emulator job `{EMULATOR_JOB}`.
- Seven focused indexed-format tests passed; the complete workspace executed 317 non-doc Rust tests with zero failures.
- Lockfile regeneration, workspace metadata, rustfmt, all-target/all-feature compilation, strict Clippy with warnings denied, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and the independent differential oracle passed.
- Differential validation covered 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- The unchanged Android gate rebuilt and verified both JNI ABIs, passed host JVM tests, rebuilt the AAR/test APK, and passed the API-35 emulator lifecycle.
- Validation corrections were limited to canonical rustfmt output and removal of one unused constant. No format rule, corruption check, lower-layer behavior, or validation gate was weakened.
- Task 19.2 is complete. Tasks 19.3–19.5 and the overall Task 19 gate remain open.
"""
    contract.write_text(text.rstrip() + evidence)


if __name__ == "__main__":
    main()
