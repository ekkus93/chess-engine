#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"{path}: expected exactly one replacement witness")
    target.write_text(text.replace(old, new), encoding="utf-8")


replace_once(
    "fuzz/src/lib.rs",
    "use chess_core::{Game, Position, UciMove};",
    "use chess_core::{static_exchange_evaluation, Game, Position, UciMove};",
)
replace_once(
    "fuzz/src/lib.rs",
    "/// Exercises game-owned move, repetition, draw, and reverse-history state.\npub fn fuzz_game_history",
    "/// Exercises deterministic standalone SEE over legal exchange events and exact roots.\npub fn fuzz_static_exchange(data: &[u8]) {\n    let mut position = Position::starting();\n\n    for (ply, selector) in data.iter().copied().take(64).enumerate() {\n        let root = position.clone();\n        let moves = position\n            .legal_moves()\n            .unwrap_or_else(|error| panic!(\"SEE ply {ply}: legal generation failed: {error}\"));\n        if moves.is_empty() {\n            break;\n        }\n\n        for current in moves.iter() {\n            if !current.kind().is_capture() && current.promotion().is_none() {\n                continue;\n            }\n            let first = static_exchange_evaluation(&position, current)\n                .unwrap_or_else(|error| panic!(\"SEE ply {ply} {} failed: {error}\", current.to_uci()));\n            let second = static_exchange_evaluation(&position, current).unwrap_or_else(|error| {\n                panic!(\"SEE ply {ply} repeated {} failed: {error}\", current.to_uci())\n            });\n            assert_eq!(first, second, \"SEE was nondeterministic at ply {ply}\");\n            assert!(\n                first.centipawns().unsigned_abs() <= 60_000,\n                \"SEE escaped its documented material domain at ply {ply}\"\n            );\n            assert_eq!(position, root, \"SEE mutated the position at ply {ply}\");\n            assert_position(&position, \"SEE root\");\n        }\n\n        let current = moves\n            .get(usize::from(selector) % moves.len())\n            .expect(\"bounded SEE sequence index exists\");\n        position.make_move(current).unwrap_or_else(|error| {\n            panic!(\n                \"SEE ply {ply}: generated move {} failed: {error}\",\n                current.to_uci()\n            )\n        });\n        assert_position(&position, &format!(\"SEE sequence ply {ply}\"));\n    }\n}\n\n/// Exercises game-owned move, repetition, draw, and reverse-history state.\npub fn fuzz_game_history",
)
replace_once(
    "fuzz/src/lib.rs",
    """        fuzz_c_abi_buffers_and_handles, fuzz_fen_parser, fuzz_game_history, fuzz_legal_sequence,
        fuzz_opening_book_parser, fuzz_uci_move_parser, fuzz_weight_parser,""",
    """        fuzz_c_abi_buffers_and_handles, fuzz_fen_parser, fuzz_game_history, fuzz_legal_sequence,
        fuzz_opening_book_parser, fuzz_static_exchange, fuzz_uci_move_parser, fuzz_weight_parser,""",
)
replace_once(
    "fuzz/src/lib.rs",
    """        fuzz_legal_sequence(&[0, 1, 2, 3, 5, 8, 13, 21, 34, 55]);
        fuzz_game_history""",
    """        fuzz_legal_sequence(&[0, 1, 2, 3, 5, 8, 13, 21, 34, 55]);
        fuzz_static_exchange(&[12, 7, 19, 3, 41, 5, 23, 9, 31, 2, 47, 11]);
        fuzz_game_history""",
)

cargo = ROOT / "fuzz/Cargo.toml"
cargo_text = cargo.read_text(encoding="utf-8")
if 'name = "static_exchange"' in cargo_text:
    raise RuntimeError("fuzz static_exchange bin already present")
cargo.write_text(
    cargo_text
    + """
[[bin]]
name = "static_exchange"
path = "fuzz_targets/static_exchange.rs"
test = false
doc = false
bench = false
required-features = ["fuzzing"]
""",
    encoding="utf-8",
)

replace_once(
    "crates/chess-core/tests/miri_core.rs",
    "use chess_core::{Position, UciMove};",
    "use chess_core::{static_exchange_evaluation, Position, UciMove};",
)
miri = ROOT / "crates/chess-core/tests/miri_core.rs"
miri.write_text(miri.read_text(encoding="utf-8") + "\n#[test]\nfn miri_static_exchange_is_deterministic_non_mutating_and_bounded() {\n    let mut position =\n        Position::from_fen(\"3r2k1/8/8/3pP3/8/8/8/6K1 w - d6 0 1\")\n            .expect(\"SEE fixture FEN is valid\");\n    let requested = \"e5d6\".parse::<UciMove>().expect(\"SEE UCI parses\");\n    let current = position\n        .legal_moves()\n        .expect(\"SEE fixture legal generation succeeds\")\n        .iter()\n        .find(|current| requested.matches(*current))\n        .expect(\"SEE fixture move is legal\");\n    let root = position.clone();\n    let first = static_exchange_evaluation(&position, current).expect(\"SEE succeeds\");\n    let second = static_exchange_evaluation(&position, current).expect(\"repeated SEE succeeds\");\n    assert_eq!(first, second);\n    assert_eq!(first.centipawns(), 0);\n    assert_eq!(position, root);\n    assert_eq!(position.zobrist(), position.recomputed_zobrist());\n}\n", encoding="utf-8")

replace_once(
    ".github/workflows/robustness.yml",
    """            legal_sequence
            game_history""",
    """            legal_sequence
            static_exchange
            game_history""",
)
replace_once(
    ".github/workflows/robustness.yml",
    "      - name: Run AddressSanitizer and LeakSanitizer lifecycle tests\n",
    """      - name: Run AddressSanitizer and LeakSanitizer SEE tests
        env:
          RUSTFLAGS: -Zsanitizer=address -Adeprecated
          RUSTDOCFLAGS: -Zsanitizer=address -Adeprecated
          ASAN_OPTIONS: detect_leaks=1:halt_on_error=1:abort_on_error=1
        run: >-
          cargo +nightly-2026-08-01 test -Zbuild-std --locked
          --target x86_64-unknown-linux-gnu
          -p chess-core --lib --all-features see::tests

      - name: Run AddressSanitizer and LeakSanitizer lifecycle tests
""",
)

run("chmod", "+x", "scripts/task_s2_4_see_audit.sh")
run("cargo", "fmt", "--all")
run("cargo", "fmt", "--all", "--", "--check")
run("cargo", "check", "--locked", "--workspace", "--all-targets", "--all-features")
run("cargo", "clippy", "--locked", "--workspace", "--all-targets", "--all-features", "--", "-D", "warnings")
run("cargo", "test", "--locked", "--workspace", "--all-targets", "--all-features")
run("cargo", "generate-lockfile", "--manifest-path", "fuzz/Cargo.toml")
run("git", "diff", "--exit-code", "--", "fuzz/Cargo.lock")
run("cargo", "fmt", "--manifest-path", "fuzz/Cargo.toml", "--", "--check")
run("cargo", "clippy", "--manifest-path", "fuzz/Cargo.toml", "--locked", "--lib", "--tests", "--", "-D", "warnings")
run("cargo", "test", "--manifest-path", "fuzz/Cargo.toml", "--locked", "--lib", "--tests")
run("cargo", "build", "--locked", "--release", "-p", "chess-tools", "--bin", "s2_4_see_benchmark")
run("target/release/s2_4_see_benchmark", "3")

Path(__file__).unlink()
run("git", "config", "user.name", "Phillip Chin")
run("git", "config", "user.email", "ekkus93@gmail.com")
run("git", "add", "-A")
run("git", "commit", "-m", "test: add S2-4 SEE robustness and performance evidence")
run("git", "push", "origin", "HEAD:master")
