from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    content = target.read_text(encoding="utf-8")
    count = content.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one anchor, found {count}: {old!r}")
    target.write_text(content.replace(old, new, 1), encoding="utf-8")


TODO = "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
DEFINITIONS = "docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md"
RALPH = "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"
ADAPTER = "docs/RUST_OPENING_BOOK_ADAPTER_INTEGRATION.md"

replace_once(
    TODO,
    "| 19 | **In progress** — opening-book abstraction, versioned indexed format, and selection policies complete. |",
    "| 19 | **In progress** — opening-book abstraction, versioned indexed format, selection policies, and adapter integration complete. |",
)
replace_once(
    TODO,
    "- Task 19.3 opening-book selection policies are complete. Task 19.4 adapter integration is next.",
    "- Task 19.4 opening-book adapter integration is complete. Task 19.5 opening-book tests are next.",
)
replace_once(TODO, "- [ ] 19.4 Integration.", "- [x] 19.4 Integration.")

for old, new in [
    ("- [ ] UCI option to enable/disable book.", "- [x] UCI option to enable/disable book."),
    ("- [ ] Safe API configuration.", "- [x] Safe API configuration."),
    ("- [ ] Android asset-supplied book example.", "- [x] Android asset-supplied book example."),
    ("- [ ] Normal operation when no book exists.", "- [x] Normal operation when no book exists."),
]:
    replace_once(DEFINITIONS, old, new)

replace_once(
    RALPH,
    "**Current phase:** Task 19.3 opening-book selection policies complete; Task 19.4 adapter integration is next",
    "**Current phase:** Task 19.4 opening-book adapter integration complete; Task 19.5 opening-book tests are next",
)
row_19_3 = "| 19.3 | `82b5100f501fe4e4a845d5fb3bdbb1c8fe7d34ef` | Rust `30859905206` / `91839380997`; Android `30859905203` / `91839428990`, `91839429013` | exact indexed UCI-to-legal-move resolution, generic candidate revalidation, deterministic highest-weight policy with canonical tie ordering, explicit local-seed SplitMix64 weighted policy, six focused tests; 323 Rust tests and Android regressions green |"
row_19_4 = "| 19.4 | `5b8e2117c64922e97cbe356caa44a51075da7b52` | Rust `30863525297` / `91850371126`; Android `30863525289` / `91850370864`, `91850370917` | explicit UCI `OwnBook` and `--book` injection, safe-facade policy/configuration, additive C ABI/JNI byte injection, Android asset adapter, and disabled/absent/no-entry search fallback; 328 Rust tests and Android regressions green |"
replace_once(RALPH, row_19_3, row_19_3 + "\n" + row_19_4)

completion = """

## Completion evidence

- Exact merged implementation SHA: `5b8e2117c64922e97cbe356caa44a51075da7b52`.
- Exact validated implementation head before rebase merge: `d7f70e21fea900171ef5539f6ee9ee4b00c34d18`.
- Permanent Rust validation: run `30863525297`, job `91850371126`.
- Permanent Android validation: run `30863525289`, host JVM job `91850370864`, API-35 emulator job `91850370917`.
- The workspace executed 328 non-documentation Rust tests with zero failures, including focused safe-facade, additive C ABI, JNI declaration, UCI option, book-hit, disabled-book, absent-book, no-entry, and corrupt-book coverage.
- Committed lockfile verification, workspace metadata, rustfmt, all-target/all-feature compilation, strict Clippy with warnings denied, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and the independent differential oracle passed.
- Differential validation covered 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Host JVM JNI passed, ARM64/x86_64 native artifacts and exported symbols were verified, the Android AAR/test APK built, and the API-35 instrumentation lifecycle—including the packaged indexed-book asset example—passed.
- Task 19.4 is complete. Task 19.5 and the overall Task 19 gate remain open.
"""
adapter_path = Path(ADAPTER)
adapter_content = adapter_path.read_text(encoding="utf-8")
if "## Completion evidence" in adapter_content:
    raise SystemExit("adapter completion evidence already exists")
adapter_path.write_text(adapter_content.rstrip() + completion, encoding="utf-8")

# Closure invariants: only 19.4 closes; 19.5 and Task 19 remain open.
updated_todo = Path(TODO).read_text(encoding="utf-8")
for required in [
    "- [x] 19.4 Integration.",
    "- [ ] 19.5 Tests.",
    "- [ ] Task 19 gate.",
]:
    if required not in updated_todo:
        raise SystemExit(f"missing required tracker state: {required}")

print("Task 19.4 tracker closure applied")
