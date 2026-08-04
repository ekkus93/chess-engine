#!/usr/bin/env python3
"""Fail-closed Task 19.5 audit for explicit opening-book I/O boundaries."""

from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    path = ROOT / relative_path
    if not path.is_file():
        raise AssertionError(f"required file is missing: {relative_path}")
    return path.read_text(encoding="utf-8")


def read_manifest(relative_path: str) -> dict[str, object]:
    path = ROOT / relative_path
    if not path.is_file():
        raise AssertionError(f"required manifest is missing: {relative_path}")
    with path.open("rb") as handle:
        return tomllib.load(handle)


def require_snippets(relative_path: str, snippets: tuple[str, ...]) -> str:
    text = read_text(relative_path)
    missing = [snippet for snippet in snippets if snippet not in text]
    if missing:
        raise AssertionError(
            f"{relative_path} is missing explicit-boundary witnesses: {missing}"
        )
    return text


def reject_snippets(relative_path: str, snippets: tuple[str, ...]) -> None:
    text = read_text(relative_path)
    found = [snippet for snippet in snippets if snippet in text]
    if found:
        raise AssertionError(
            f"{relative_path} contains forbidden auto-discovery/I/O tokens: {found}"
        )


def rust_sources(relative_directory: str) -> list[str]:
    directory = ROOT / relative_directory
    if not directory.is_dir():
        raise AssertionError(f"required source directory is missing: {relative_directory}")
    return [
        path.relative_to(ROOT).as_posix()
        for path in sorted(directory.rglob("*.rs"))
    ]


def main() -> None:
    book_manifest = read_manifest("crates/chess-book/Cargo.toml")
    book_dependencies = book_manifest.get("dependencies", {})
    if set(book_dependencies) != {"chess-core"}:
        raise AssertionError(
            "chess-book must depend only on chess-core; found "
            f"{sorted(book_dependencies)}"
        )

    for manifest_path in (
        "crates/chess-core/Cargo.toml",
        "crates/chess-search/Cargo.toml",
    ):
        manifest = read_manifest(manifest_path)
        dependencies = manifest.get("dependencies", {})
        if "chess-book" in dependencies:
            raise AssertionError(
                f"{manifest_path} must not depend on the outward chess-book adapter crate"
            )

    pure_book_forbidden = (
        "std::fs",
        "std::env",
        "std::net",
        "std::path",
        "std::process",
        "fs::read",
        "File::open",
        "PathBuf",
        "env::args",
        "env::var",
        "current_dir",
        "current_exe",
        "include_bytes!",
        "include_str!",
    )
    for source_path in rust_sources("crates/chess-book/src"):
        reject_snippets(source_path, pure_book_forbidden)

    adapter_forbidden = (
        "std::fs",
        "std::env",
        "std::path",
        "fs::read",
        "File::open",
        "PathBuf",
        "env::args",
        "env::var",
        "current_dir",
        "current_exe",
        "include_bytes!",
        "include_str!",
    )
    for source_directory in (
        "crates/chess-ffi/src",
        "crates/chess-jni/src",
    ):
        for source_path in rust_sources(source_directory):
            reject_snippets(source_path, adapter_forbidden)

    uci_path = "crates/chess-uci/src/main.rs"
    uci_text = require_snippets(
        uci_path,
        (
            "load_opening_book(env::args_os().skip(1))",
            'if flag != "--book"',
            "let bytes = fs::read(&path)?;",
            "IndexedBook::from_bytes(&bytes)",
        ),
    )
    if uci_text.count("fs::read(&path)") != 1:
        raise AssertionError(
            "the UCI adapter must perform exactly one read of the explicitly supplied --book path"
        )
    for forbidden in (
        "env::var(",
        "env::var_os(",
        "env::current_dir",
        "env::current_exe",
        "dirs::",
        "home::",
        "ProjectDirs",
        "BaseDirs",
        "include_bytes!",
        "DEFAULT_BOOK",
        "BOOK_PATH",
    ):
        if forbidden in uci_text:
            raise AssertionError(
                f"{uci_path} contains forbidden auto-discovery token {forbidden!r}"
            )

    safe_path = "crates/chess-ffi/src/safe.rs"
    require_snippets(
        safe_path,
        (
            "pub fn new_with_opening_book(",
            "pub fn new_with_indexed_book_bytes(",
            "IndexedBook::from_bytes(bytes)?;",
        ),
    )

    kotlin_path = (
        "crates/chess-jni/kotlin/src/main/kotlin/"
        "com/ekkus93/chessengine/ChessEngine.kt"
    )
    require_snippets(
        kotlin_path,
        (
            "fun createWithIndexedBook(",
            "indexedBook: ByteArray",
            "NativeChessEngineBindings.nativeCreateWithIndexedBook(",
        ),
    )
    reject_snippets(
        kotlin_path,
        (
            "System.getenv",
            "System.getProperty",
            "ClassLoader",
            "getResource(",
            "java.io.File",
            "java.nio.file",
        ),
    )

    asset_factory_path = (
        "android-harness/android-smoke/src/main/kotlin/"
        "com/ekkus93/chessengine/harness/ChessEngineAssetFactory.kt"
    )
    require_snippets(
        asset_factory_path,
        (
            "context.assets.open(assetName)",
            "ChessEngine.createWithIndexedBook(",
        ),
    )
    reject_snippets(
        asset_factory_path,
        (
            "System.getenv",
            "System.getProperty",
            "ClassLoader",
            "getResource(",
            "java.io.File",
            "java.nio.file",
        ),
    )

    print(
        "Task 19.5 opening-book audit passed: pure book/core/search boundaries, "
        "explicit UCI path injection, explicit byte/JNI injection, and explicit "
        "Android asset injection verified"
    )


if __name__ == "__main__":
    main()
