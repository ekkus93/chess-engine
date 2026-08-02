#!/usr/bin/env python3
"""Differential legal-move, child-FEN, perft, and playout validation."""

from __future__ import annotations

import argparse
import random
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

import chess

EXPECTED_CHESS_VERSION = "1.11.2"


@dataclass(frozen=True)
class CorpusEntry:
    name: str
    fen: str
    perft_depth: int


class RustOracle:
    def __init__(self, binary: Path) -> None:
        self._process = subprocess.Popen(
            [str(binary), "oracle"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        if self._process.stdin is None or self._process.stdout is None:
            raise RuntimeError("failed to open chess-tools oracle pipes")
        self._stdin: TextIO = self._process.stdin
        self._stdout: TextIO = self._process.stdout

    def request(self, *fields: str) -> str:
        if any("\t" in field or "\n" in field or "\r" in field for field in fields):
            raise ValueError("oracle protocol fields cannot contain tabs or newlines")
        self._stdin.write("\t".join(fields) + "\n")
        self._stdin.flush()
        response = self._stdout.readline()
        if not response:
            stderr = ""
            if self._process.stderr is not None:
                stderr = self._process.stderr.read()
            raise RuntimeError(
                f"chess-tools oracle exited unexpectedly with code "
                f"{self._process.poll()}: {stderr.strip()}"
            )
        status, separator, payload = response.rstrip("\n").partition("\t")
        if not separator:
            raise RuntimeError(f"malformed oracle response: {response!r}")
        if status == "error":
            raise RuntimeError(payload)
        if status != "ok":
            raise RuntimeError(f"unknown oracle status {status!r}")
        return payload

    def legal(self, fen: str) -> list[str]:
        payload = self.request("legal", fen)
        return [] if not payload else payload.split(",")

    def play(self, fen: str, move: str) -> str:
        return self.request("play", move, fen)

    def perft(self, fen: str, depth: int) -> int:
        return int(self.request("perft", str(depth), fen))

    def close(self) -> None:
        if self._process.poll() is not None:
            return
        acknowledgement = self.request("quit")
        if acknowledgement != "bye":
            raise RuntimeError(f"unexpected oracle shutdown response: {acknowledgement!r}")
        return_code = self._process.wait(timeout=10)
        if return_code != 0:
            raise RuntimeError(f"chess-tools oracle exited with code {return_code}")

    def __enter__(self) -> RustOracle:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()


def load_corpus(path: Path) -> list[CorpusEntry]:
    entries: list[CorpusEntry] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line_number == 1:
            if line != "name\tfen\tperft_depth":
                raise ValueError(f"unexpected corpus header in {path}: {line!r}")
            continue
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) != 3:
            raise ValueError(f"invalid corpus row {line_number}: {line!r}")
        entries.append(CorpusEntry(fields[0], fields[1], int(fields[2])))
    if not entries:
        raise ValueError(f"differential corpus {path} is empty")
    return entries


def canonical_fen(board: chess.Board) -> str:
    return board.fen(en_passant="fen")


def python_perft(board: chess.Board, depth: int) -> int:
    if depth == 0:
        return 1
    nodes = 0
    for move in list(board.legal_moves):
        board.push(move)
        nodes += python_perft(board, depth - 1)
        board.pop()
    return nodes


def assert_equal(name: str, category: str, fen: str, expected: object, actual: object) -> None:
    if expected != actual:
        raise AssertionError(
            f"{name}: {category} mismatch\n"
            f"FEN: {fen}\n"
            f"expected: {expected!r}\n"
            f"actual:   {actual!r}"
        )


def validate_corpus_entry(oracle: RustOracle, entry: CorpusEntry) -> tuple[int, int]:
    board = chess.Board(entry.fen)
    if not board.is_valid():
        raise AssertionError(f"{entry.name}: python-chess rejects corpus FEN {entry.fen}")

    python_moves = sorted(move.uci() for move in board.legal_moves)
    rust_moves = oracle.legal(entry.fen)
    assert_equal(entry.name, "legal move set", entry.fen, python_moves, rust_moves)

    child_count = 0
    for move_text in python_moves:
        move = chess.Move.from_uci(move_text)
        board.push(move)
        expected_child = canonical_fen(board)
        board.pop()
        actual_child = oracle.play(entry.fen, move_text)
        assert_equal(
            entry.name,
            f"child FEN after {move_text}",
            entry.fen,
            expected_child,
            actual_child,
        )
        child_count += 1

    expected_nodes = python_perft(board, entry.perft_depth)
    actual_nodes = oracle.perft(entry.fen, entry.perft_depth)
    assert_equal(
        entry.name,
        f"perft depth {entry.perft_depth}",
        entry.fen,
        expected_nodes,
        actual_nodes,
    )
    return child_count, expected_nodes


def validate_random_playouts(
    oracle: RustOracle,
    roots: list[CorpusEntry],
    games: int,
    max_plies: int,
    seed: int,
) -> int:
    generator = random.Random(seed)
    validated_plies = 0
    for game_index in range(games):
        root = roots[game_index % len(roots)]
        board = chess.Board(root.fen)
        for ply in range(max_plies):
            fen = canonical_fen(board)
            python_moves = sorted(move.uci() for move in board.legal_moves)
            rust_moves = oracle.legal(fen)
            assert_equal(
                f"random game {game_index} ply {ply}",
                "legal move set",
                fen,
                python_moves,
                rust_moves,
            )
            if not python_moves:
                break
            move_text = generator.choice(python_moves)
            board.push_uci(move_text)
            expected_child = canonical_fen(board)
            actual_child = oracle.play(fen, move_text)
            assert_equal(
                f"random game {game_index} ply {ply}",
                f"child FEN after {move_text}",
                fen,
                expected_child,
                actual_child,
            )
            validated_plies += 1
    return validated_plies


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--games", type=int, default=12)
    parser.add_argument("--plies", type=int, default=48)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0xC0FFEE)
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    if chess.__version__ != EXPECTED_CHESS_VERSION:
        raise RuntimeError(
            f"expected chess {EXPECTED_CHESS_VERSION}, found {chess.__version__}"
        )
    if arguments.games < 0 or arguments.plies < 0:
        raise ValueError("games and plies must be non-negative")
    if not arguments.binary.is_file():
        raise FileNotFoundError(arguments.binary)

    corpus = load_corpus(arguments.corpus)
    total_children = 0
    total_perft_nodes = 0
    with RustOracle(arguments.binary) as oracle:
        for entry in corpus:
            children, nodes = validate_corpus_entry(oracle, entry)
            total_children += children
            total_perft_nodes += nodes
        random_plies = validate_random_playouts(
            oracle,
            corpus,
            arguments.games,
            arguments.plies,
            arguments.seed,
        )

    print(
        "differential validation passed: "
        f"{len(corpus)} corpus positions, "
        f"{total_children} child FENs, "
        f"{total_perft_nodes} oracle perft nodes, "
        f"{random_plies} seeded plies, "
        f"seed={arguments.seed}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
