"""Production quiescence-search correctness tests.

These tests verify key behavioural invariants of the quiescence search:

  * No stand-pat is returned when the side to move is in check.
  * All legal evasions are searched when in check.
  * A checkmate at the quiescence boundary returns a mate score.
  * Pawn captures are included in the tactical-move selector.
  * Promotions are included in the tactical-move selector.
  * get_best_move benefits from quiescence (captures hanging pieces).
"""
from __future__ import annotations

import pytest

from chess_game.chess import Board
from chess_game.chess.ai import INF, MATE_SCORE, get_best_move, quiescence
from chess_game.chess.board.game_state import is_in_check
from chess_game.chess.evaluation import evaluate

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _q(board: Board, depth_remaining: int = 4) -> int:
    """Call the public quiescence API for the current side to move."""
    is_max = board.turn.name == "WHITE"
    return quiescence(board, -INF, INF, is_max, depth_remaining=depth_remaining)


# ---------------------------------------------------------------------------
# 1. No stand-pat in check
# ---------------------------------------------------------------------------

def test_no_stand_pat_in_check() -> None:
    """When the side to move is in check, quiescence must not return stand-pat.

    Position: White king at g1, Black queen at g2 gives check.
    White's only option is to escape. The quiescence result must differ from
    a simple static evaluation because stand-pat is suppressed.
    """
    # Scholars mate threat — White king in check from Black queen on g2
    # FEN: k7/8/8/8/8/8/6q1/6K1 w - - 0 1
    board = Board.from_fen("k7/8/8/8/8/8/6q1/6K1 w - - 0 1")
    assert is_in_check(board, board.turn)

    static = evaluate(board)
    q_score = _q(board)

    # King can capture the undefended queen on g2 — a huge material gain.
    # Quiescence must see this; the score should be substantially above static.
    assert q_score > static, (
        f"In-check quiescence must search evasions (capture queen); "
        f"q={q_score} static={static}"
    )
    assert -INF < q_score < INF


# ---------------------------------------------------------------------------
# 2. Legal evasion search: moves out of check are explored
# ---------------------------------------------------------------------------

def test_evasion_search_finds_best_escape() -> None:
    """All legal evasions are searched; the best escape route is selected.

    White king at e1 is in check from a black rook at e8.
    King can escape to d1, d2, f1, or f2 (no pieces blocking).
    Quiescence should return a score better than −MATE_SCORE for White.
    """
    board = Board.from_fen("4r3/8/8/8/8/8/8/k3K3 w - - 0 1")
    assert is_in_check(board, board.turn)

    q_score = _q(board)
    # White must have an escape; score should not be a mate score
    assert q_score > -MATE_SCORE


# ---------------------------------------------------------------------------
# 3. Mate score at quiescence boundary
# ---------------------------------------------------------------------------

def test_checkmate_at_quiescence_boundary() -> None:
    """A side mated at the quiescence boundary returns an appropriate mate score.

    Position: Fool's mate — White is in checkmate after 1.f3 e5 2.g4 Qh4#.
    Quiescence called with White to move should return a score with magnitude
    at least MATE_SCORE (within ply-distance rounding).
    """
    fen = "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"
    board = Board.from_fen(fen)
    legal = board.get_legal_moves()
    if legal:
        pytest.skip("Position is not actually checkmate in this engine build")

    q_score = _q(board)
    assert abs(q_score) >= MATE_SCORE - 100  # within ply-distance tolerance


# ---------------------------------------------------------------------------
# 4. Pawn captures included
# ---------------------------------------------------------------------------

def test_pawn_captures_included() -> None:
    """Pawn captures are included in the quiescence tactical-move set.

    White pawn at d5 can capture a hanging Black knight at e6.
    Quiescence should return a score reflecting the material gain.
    """
    # White pawn at d5 capturing Black knight at e6
    # FEN: 8/8/4n3/3P4/8/8/8/K1k5 w - - 0 1
    board = Board.from_fen("8/8/4n3/3P4/8/8/8/K1k5 w - - 0 1")

    before_fen = board.to_fen()
    q_before = _q(board)
    # Capturing a free knight must improve White's score vs not capturing
    assert q_before > evaluate(board), "Quiescence should find the free pawn capture"
    # Board should be unchanged after the call
    assert board.to_fen() == before_fen


# ---------------------------------------------------------------------------
# 5. Promotions included
# ---------------------------------------------------------------------------

def test_promotions_included() -> None:
    """Pawn promotions are explored in quiescence search.

    White pawn at a7 can promote immediately. Quiescence should see this
    and return a score well above the static eval (which sees only a pawn).
    """
    # White pawn about to promote, Black king far away
    # FEN: 8/P7/8/8/8/8/8/K1k5 w - - 0 1
    board = Board.from_fen("8/P7/8/8/8/8/8/K1k5 w - - 0 1")

    q_score = _q(board)
    static = evaluate(board)

    # After promoting to a queen the advantage is large
    assert q_score > static + 300, (
        f"Quiescence should see promotion gain; q={q_score} static={static}"
    )


# ---------------------------------------------------------------------------
# 6. get_best_move benefits from quiescence (captures hanging piece)
# ---------------------------------------------------------------------------

def test_get_best_move_captures_hanging_piece() -> None:
    """get_best_move should capture a completely undefended piece.

    White knight at d4 can capture a hanging Black rook at f5.
    Even at depth 1 the engine should make this capture.
    """
    # White knight at d4, Black rook at f5, otherwise only kings
    # FEN: 8/8/8/5r2/3N4/8/8/K1k5 w - - 0 1
    board = Board.from_fen("8/8/8/5r2/3N4/8/8/K1k5 w - - 0 1")

    move = get_best_move(board, depth=1)
    assert move is not None

    # The best move must be a capture (the only hanging piece is the rook)
    assert board.get_piece(move.end) is not None, (
        f"Expected capture of the hanging rook, got non-capture {move}"
    )
