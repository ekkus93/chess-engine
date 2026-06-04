"""Regressions for WHITE_IMPROVEMENTS1: luft creation, h2 exposure, pseudo-fork, passive bishop.

Positions are constructed directly rather than loaded from transcript files so
the tests remain self-contained and do not depend on game artifacts in tmp/.
"""

from __future__ import annotations

from chess_game.chess.ai_capture_ordering import capture_order_score
from chess_game.chess.ai_board_utils import clone_with_move
from chess_game.chess.ai_move_ordering import quiet_strategy_order_score
from chess_game.chess.board.board import Board, create_piece
from chess_game.chess.defensive_priorities import h_pawn_exposure_penalty, king_danger_index
from chess_game.chess.move import Move, parse_move_notation
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


def _m(notation: str) -> Move:
    p = parse_move_notation(notation)
    return Move(start=p.start, end=p.end, promotion=p.promotion)


# ---------------------------------------------------------------------------
# Constructed positions
# ---------------------------------------------------------------------------


def _pos_h2_threatened() -> Board:
    """White castled at g1 with h2 pawn; Black bishop at d6 threatens h2."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("f1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
    # d6 threatens h2 via d6-e5-f4-g3-h2 diagonal (all squares empty)
    board.set_piece(sq("d6"), create_piece(Color.BLACK, PieceType.BISHOP))
    board.turn = Color.WHITE
    return board


def _pos_no_h2_threat() -> Board:
    """White castled at g1 with h2 pawn; Black bishop at f8 (not threatening h2)."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("f1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.set_piece(sq("f8"), create_piece(Color.BLACK, PieceType.BISHOP))  # not diagonal to h2
    board.turn = Color.WHITE
    return board


def _pos_nxe5_pseudo_fork() -> Board:
    """White Nf3 can capture Black pawn at e5, which is defended by Black pawn at d6."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("f3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.set_piece(sq("e5"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("d6"), create_piece(Color.BLACK, PieceType.PAWN))  # defends e5
    board.turn = Color.WHITE
    return board


def _pos_bishop_at_f4() -> Board:
    """White bishop at f4 can retreat to d2 (second rank) or advance to e3."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("f4"), create_piece(Color.WHITE, PieceType.BISHOP))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.turn = Color.WHITE
    return board


# ---------------------------------------------------------------------------
# Task 1 & 2: Luft creation / h-pawn exposure
# ---------------------------------------------------------------------------


def test_h_pawn_exposure_fires_when_bishop_aims_at_h2() -> None:
    """h_pawn_exposure_penalty should return ≥ 30 when a Black bishop targets h2."""
    board = _pos_h2_threatened()
    assert board.turn == Color.WHITE
    penalty = h_pawn_exposure_penalty(board, Color.WHITE)
    assert penalty >= 30, f"Expected ≥ 30, got {penalty}"


def test_king_danger_elevated_when_bishop_aims_at_h2() -> None:
    """king_danger_index should reach DANGEROUS threshold when h2 is targeted."""
    board = _pos_h2_threatened()
    from chess_game.chess.ai_search_helpers import DANGEROUS_KING_PRESSURE_THRESHOLD

    danger = king_danger_index(board, Color.WHITE)
    assert danger >= DANGEROUS_KING_PRESSURE_THRESHOLD, (
        f"Expected danger ≥ {DANGEROUS_KING_PRESSURE_THRESHOLD}, got {danger}"
    )


def test_h3_luft_scores_higher_than_passive_rook_when_h2_threatened() -> None:
    """h2-h3 should outscore passive rook moves when a bishop threatens h2."""
    board = _pos_h2_threatened()
    h3 = _m("h2h3")
    re1 = _m("f1e1")
    assert quiet_strategy_order_score(board, h3, None) > quiet_strategy_order_score(
        board, re1, None
    ), "h2-h3 luft should rank above passive Rf1-e1 when h2 is threatened"


def test_h_pawn_exposure_zero_without_diagonal_threat() -> None:
    """h_pawn_exposure_penalty should be 0 when no bishop targets h2."""
    board = _pos_no_h2_threat()
    penalty = h_pawn_exposure_penalty(board, Color.WHITE)
    assert penalty == 0, f"Expected 0 (bishop not on h2 diagonal), got {penalty}"


# ---------------------------------------------------------------------------
# Task 3: Pseudo-fork / pawn-recapture blindness
# ---------------------------------------------------------------------------


def test_nxe5_pseudo_fork_penalised() -> None:
    """Nxe5 capture should score very low because d6-pawn immediately recaptures."""
    board = _pos_nxe5_pseudo_fork()
    assert board.turn == Color.WHITE
    nxe5 = _m("f3e5")
    score = capture_order_score(board, nxe5, clone_with_move)
    assert score < 0, f"Nxe5 pseudo-fork should score negative, got {score}"


def test_nxe5_much_lower_than_safe_capture() -> None:
    """Nxe5 should score far below a safe capture with no pawn recapture risk."""
    board = _pos_nxe5_pseudo_fork()
    nxe5 = _m("f3e5")
    nxe5_score = capture_order_score(board, nxe5, clone_with_move)
    nxg4 = _m("f3g4") if board.get_piece(sq("g4")) else None
    if nxg4:
        nxg4_score = capture_order_score(board, nxg4, clone_with_move)
        assert nxe5_score < nxg4_score, (
            f"Nxe5 ({nxe5_score}) should score below Nxg4 ({nxg4_score})"
        )


# ---------------------------------------------------------------------------
# Task 4: Passive bishop retreat to second rank
# ---------------------------------------------------------------------------


def test_bf4d2_retreat_penalised() -> None:
    """Bf4-d2 second-rank retreat should score lower than an active bishop move."""
    board = _pos_bishop_at_f4()
    assert board.turn == Color.WHITE
    bf4d2 = _m("f4d2")
    bf4e3 = _m("f4e3")
    assert board.get_piece(sq("f4")) is not None, "Bishop should be at f4"
    d2_score = quiet_strategy_order_score(board, bf4d2, None)
    e3_score = quiet_strategy_order_score(board, bf4e3, None)
    assert d2_score < e3_score, (
        f"Bf4-d2 ({d2_score}) should score below Bf4-e3 ({e3_score})"
    )


def test_bishop_second_rank_penalty_fires() -> None:
    """The second-rank bishop retreat penalty should apply for Bf4-d2."""
    from chess_game.chess.ai_move_ordering import _bishop_passive_retreat_penalty

    board = _pos_bishop_at_f4()
    bf4d2 = _m("f4d2")
    assert board.get_piece(sq("f4")) is not None, "Bishop should be at f4"
    penalty = _bishop_passive_retreat_penalty(board, bf4d2, Color.WHITE)
    assert penalty > 0, f"Expected positive penalty for Bf4-d2, got {penalty}"
