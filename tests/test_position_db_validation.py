"""Texel fail-loud: PositionDB.load validates every row with line-numbered errors.

Valid old/new JSONL still loads and aggregates; malformed rows raise a ValueError
that names the file path and the offending line number.
"""

from pathlib import Path

import pytest

from chess_game.texel.position_db import PositionDB

_VALID_FIRST_LINE = '{"pos": "fen1", "outcome": 0.5}'


def _db_file(tmp_path: Path, *lines: str) -> Path:
    path = tmp_path / "db.jsonl"
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8")
    return path


def _assert_line_error(tmp_path: Path, bad_row: str, line_no: int = 2) -> str:
    """A valid first line + the bad row at *line_no*; assert a line-numbered error."""
    path = _db_file(tmp_path, _VALID_FIRST_LINE, bad_row)
    with pytest.raises(ValueError) as exc:
        PositionDB.load(path)
    message = str(exc.value)
    assert f"{path}:{line_no}:" in message, message
    return message


# ---- valid data still loads ----

def test_valid_old_format_loads(tmp_path: Path) -> None:
    path = _db_file(tmp_path, '{"pos": "a", "outcome": 1.0}', '{"pos": "b", "outcome": 0.0}')
    db = PositionDB.load(path)
    assert len(db) == 2
    assert dict(db.all_pairs()) == {"a": 1.0, "b": 0.0}


def test_valid_old_duplicates_aggregate(tmp_path: Path) -> None:
    path = _db_file(tmp_path, '{"pos": "a", "outcome": 1.0}', '{"pos": "a", "outcome": 0.0}')
    db = PositionDB.load(path)
    assert dict(db.all_pairs()) == {"a": 0.5}


def test_valid_new_format_loads(tmp_path: Path) -> None:
    path = _db_file(tmp_path, '{"pos": "a", "total": 3.0, "count": 4}')
    db = PositionDB.load(path)
    assert dict(db.all_pairs()) == {"a": 0.75}


def test_blank_lines_skipped(tmp_path: Path) -> None:
    path = _db_file(tmp_path, '{"pos": "a", "outcome": 0.5}', "", "   ")
    assert len(PositionDB.load(path)) == 1


# ---- invalid data raises line-numbered errors ----

def test_invalid_json_raises(tmp_path: Path) -> None:
    _assert_line_error(tmp_path, "{ not valid json")


def test_non_object_row_raises(tmp_path: Path) -> None:
    _assert_line_error(tmp_path, "[1, 2, 3]")


def test_missing_pos_raises(tmp_path: Path) -> None:
    _assert_line_error(tmp_path, '{"outcome": 0.5}')


def test_empty_pos_raises(tmp_path: Path) -> None:
    _assert_line_error(tmp_path, '{"pos": "", "outcome": 0.5}')


def test_non_string_pos_raises(tmp_path: Path) -> None:
    _assert_line_error(tmp_path, '{"pos": 123, "outcome": 0.5}')


def test_neither_outcome_nor_stats_raises(tmp_path: Path) -> None:
    _assert_line_error(tmp_path, '{"pos": "a"}')


def test_outcome_below_zero_raises(tmp_path: Path) -> None:
    _assert_line_error(tmp_path, '{"pos": "a", "outcome": -0.1}')


def test_outcome_above_one_raises(tmp_path: Path) -> None:
    _assert_line_error(tmp_path, '{"pos": "a", "outcome": 1.5}')


def test_non_finite_outcome_raises(tmp_path: Path) -> None:
    _assert_line_error(tmp_path, '{"pos": "a", "outcome": Infinity}')


def test_count_zero_raises(tmp_path: Path) -> None:
    _assert_line_error(tmp_path, '{"pos": "a", "total": 0.0, "count": 0}')


def test_negative_count_raises(tmp_path: Path) -> None:
    _assert_line_error(tmp_path, '{"pos": "a", "total": 0.0, "count": -1}')


def test_non_int_count_raises(tmp_path: Path) -> None:
    _assert_line_error(tmp_path, '{"pos": "a", "total": 1.0, "count": 2.0}')


def test_total_below_zero_raises(tmp_path: Path) -> None:
    _assert_line_error(tmp_path, '{"pos": "a", "total": -1.0, "count": 2}')


def test_total_greater_than_count_raises(tmp_path: Path) -> None:
    _assert_line_error(tmp_path, '{"pos": "a", "total": 3.0, "count": 2}')


def test_non_finite_total_raises(tmp_path: Path) -> None:
    _assert_line_error(tmp_path, '{"pos": "a", "total": NaN, "count": 2}')


def test_ambiguous_old_and_new_row_raises(tmp_path: Path) -> None:
    _assert_line_error(tmp_path, '{"pos": "a", "outcome": 0.5, "total": 1.0, "count": 2}')
