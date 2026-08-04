from pathlib import Path


path = Path(".github/task21-5-weighted-search.py")
text = path.read_text()
old = '''def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    old = dedent(old)
    new = dedent(new)
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one match, found {count}: {old[:160]!r}")
    path.write_text(text.replace(old, new, 1))
'''
new = '''def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    old = dedent(old).strip("\\n")
    new = dedent(new).strip("\\n")
    count = text.count(old)
    if count == 1:
        path.write_text(text.replace(old, new, 1))
        return
    if count > 1:
        raise SystemExit(f"{path}: expected one match, found {count}: {old[:160]!r}")

    source_lines = text.splitlines()
    old_lines = old.splitlines()
    matches = []
    for index in range(len(source_lines) - len(old_lines) + 1):
        if all(
            source_lines[index + offset].strip() == expected.strip()
            for offset, expected in enumerate(old_lines)
        ):
            matches.append(index)
    if len(matches) != 1:
        raise SystemExit(
            f"{path}: expected one structural match, found {len(matches)}: {old[:160]!r}"
        )

    start = matches[0]
    first = source_lines[start]
    indentation = first[: len(first) - len(first.lstrip())]
    replacement = [indentation + line if line else "" for line in new.splitlines()]
    updated = source_lines[:start] + replacement + source_lines[start + len(old_lines):]
    suffix = "\\n" if text.endswith("\\n") else ""
    path.write_text("\\n".join(updated) + suffix)
'''
if text.count(old) != 1:
    raise SystemExit("unexpected replace_once implementation")
text = text.replace(old, new, 1)

wrong_call = '''replace_once(
    i,
    """
    policy,
    transposition_table,
    &mut controller,
    """,
    """
    policy,
    transposition_table,
    weights,
    &mut controller,
    """,
)'''
corrected_call = '''replace_once(
    i,
    """
    IterationSearchPolicy {
        half_width_centipawns: DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS,
        check_extension_enabled,
    },
    transposition_table,
    &mut controller,
    """,
    """
    IterationSearchPolicy {
        half_width_centipawns: DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS,
        check_extension_enabled,
    },
    transposition_table,
    weights,
    &mut controller,
    """,
)'''
if text.count(wrong_call) != 1:
    raise SystemExit("unexpected controller-call patch")
text = text.replace(wrong_call, corrected_call, 1)

old_retry = '''text = i.read_text()
old = dedent(
    """
    policy.check_extension_enabled,
    transposition_table,
    cancellation,
    )?;
    """
)
new = dedent(
    """
    policy.check_extension_enabled,
    transposition_table,
    weights,
    cancellation,
    )?;
    """
)
if text.count(old) != 2:
    raise SystemExit(f"{i}: expected two run_attempt calls, found {text.count(old)}")
text = text.replace(old, new)
i.write_text(text)'''
new_retry = '''text = i.read_text()
retry_patterns = (
    (
        "        policy.check_extension_enabled,\\n        transposition_table,\\n        cancellation,\\n    )?;",
        "        policy.check_extension_enabled,\\n        transposition_table,\\n        weights,\\n        cancellation,\\n    )?;",
    ),
    (
        "                policy.check_extension_enabled,\\n                transposition_table,\\n                cancellation,\\n            )?;",
        "                policy.check_extension_enabled,\\n                transposition_table,\\n                weights,\\n                cancellation,\\n            )?;",
    ),
)
for old_retry_call, new_retry_call in retry_patterns:
    if text.count(old_retry_call) != 1:
        raise SystemExit(f"{i}: unexpected run_attempt call: {old_retry_call!r}")
    text = text.replace(old_retry_call, new_retry_call, 1)
i.write_text(text)'''
if text.count(old_retry) != 1:
    raise SystemExit("unexpected retry-call patch")
path.write_text(text.replace(old_retry, new_retry, 1))
