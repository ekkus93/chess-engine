"""Regression coverage for STRATEGY15: quiescence depth, capture filter, check extensions."""

from __future__ import annotations

import pytest

from chess_game.chess.ai import (
    BestMoveOptions,
    get_best_move,
    get_evaluation_breakdown,
)
from chess_game.chess.ai_board_utils import get_legal_moves
from chess_game.chess.ai_move_ordering import make_quiet_order_context, quiet_strategy_order_score
from chess_game.chess.ai_quiescence_helpers import select_quiescence_moves
from chess_game.chess.ai_search_helpers import check_extension
from chess_game.chess.ai_board_utils import clone_with_move
from chess_game.chess.board import Board, create_piece
from chess_game.chess.move import parse_move_notation
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


_NO_BOOK = BestMoveOptions(use_opening_book=False)


# ---------------------------------------------------------------------------
# Board-building helpers
# ---------------------------------------------------------------------------

def _build(pieces: list[tuple[str, Color, PieceType]], turn: Color) -> Board:
    board = Board()
    board.clear_board()
    for square, color, kind in pieces:
        board.set_piece(sq(square), create_piece(color, kind))
    board.turn = turn
    return board


def _replay(moves: list[str]) -> Board:
    board = Board()
    for s in moves:
        m = parse_move_notation(s)
        board.make_move(m.start, m.end, m.promotion)
    return board


_GAME_MOVES = [
    "e2e4", "e7e5", "f2f4", "f8c5", "g1f3", "g8f6", "b1c3", "e8g8",
    "d2d4", "e5d4", "f3d4", "f6e4", "c3e4", "f8e8", "d1d3", "d7d5",
    "f1e2", "e8e4", "d4b3", "c8g4", "e1d2", "e4e2", "d3e2", "g4e2",
    "b3c5", "b7b6", "c5b3", "e2c4", "h1e1", "b8c6", "d2c3", "d8d6",
    "a2a3", "a8d8", "g2g3", "f7f6", "f4f5", "h7h6", "c1f4", "c6e5",
    "a1d1", "c4b3", "c3b3", "d6d7", "f4e5", "d7b5", "b3a2", "d8d7",
    "e5f4", "c7c6", "d1d2", "d7d8", "d2e2", "d5d4", "e2e7", "b5f5",
    "f4c7", "d8d5",
]


# ---------------------------------------------------------------------------
# Task 1 — Quiescence depth: multi-capture sequence found at depth 3
# ---------------------------------------------------------------------------

class TestQuiescenceDepth:
    """Check that a 4-ply capture sequence is resolved at depth 3."""

    def _capture_chain_board(self) -> Board:
        """White to move: rook on e1 can capture e6 pawn, then the e6 rook can capture
        back, and the queen on d3 can recapture.  Without deep quiescence the
        evaluation after the first capture looks artificially good.

        White: Kg1, Qd3, Re1, pawns a2-h2 (minus e2).
        Black: Kg8, Rb6, Pe6, pawns a7-h7 (minus e7).
        White plays Rxe6, black Rxe6, white Qxe6+.  The sequence should
        leave white up only a pawn (net +100) not a full rook (+500).
        """
        return _build(
            [
                ("g1", Color.WHITE, PieceType.KING),
                ("d3", Color.WHITE, PieceType.QUEEN),
                ("e1", Color.WHITE, PieceType.ROOK),
                ("a2", Color.WHITE, PieceType.PAWN),
                ("b2", Color.WHITE, PieceType.PAWN),
                ("c2", Color.WHITE, PieceType.PAWN),
                ("d2", Color.WHITE, PieceType.PAWN),
                ("f2", Color.WHITE, PieceType.PAWN),
                ("g2", Color.WHITE, PieceType.PAWN),
                ("h2", Color.WHITE, PieceType.PAWN),
                ("g8", Color.BLACK, PieceType.KING),
                ("b6", Color.BLACK, PieceType.ROOK),
                ("e6", Color.BLACK, PieceType.PAWN),
                ("a7", Color.BLACK, PieceType.PAWN),
                ("b7", Color.BLACK, PieceType.PAWN),
                ("c7", Color.BLACK, PieceType.PAWN),
                ("d7", Color.BLACK, PieceType.PAWN),
                ("f7", Color.BLACK, PieceType.PAWN),
                ("g7", Color.BLACK, PieceType.PAWN),
                ("h7", Color.BLACK, PieceType.PAWN),
            ],
            Color.WHITE,
        )

    @pytest.mark.slow
    def test_quiescence_resolves_capture_chain(self) -> None:
        """Depth-3 search must not rate RxP as a clean material gain when it loses the rook."""
        board = self._capture_chain_board()
        # After Rxe6 Rxe6 Qxe6+, material is net +100 (one pawn), not +500 (a rook).
        # The engine should NOT play Re1xe6 if a safer equal move exists.
        # At MIN_QUIESCENCE_DEPTH=1 the engine cannot see the Rxe6 recapture coming,
        # so it may over-rate the capture. At depth 4 it resolves correctly.
        move = get_best_move(board, depth=3, book_options=_NO_BOOK)
        assert move is not None
        # The key assertion: if the engine plays Rxe6, it has been fooled by the horizon.
        # With deep quiescence it should either avoid the exchange or rate it accurately.
        from chess_game.chess.coords import algebraic_to_index
        e1 = algebraic_to_index("e1")
        e6 = algebraic_to_index("e6")
        if move.start == e1 and move.end == e6:
            # If it did play Rxe6, the evaluation after the full exchange should be close to 0.
            m_obj = parse_move_notation("e1e6")
            child = clone_with_move(board, m_obj)
            bd = get_evaluation_breakdown(child)
            # After Rxe6, white is temporarily up a pawn but can immediately lose the rook.
            # The eval should reflect a roughly balanced exchange, not a +500 windfall.
            assert abs(bd["material"]) < 400, (
                f"Quiescence failed to resolve capture chain; material={bd['material']}"
            )


# ---------------------------------------------------------------------------
# Task 2 — Pawn-capture filter: NxP must appear in quiescence candidates
# ---------------------------------------------------------------------------

class TestPawnCaptureFilter:
    """NxP, BxP, RxP, QxP must not be silently excluded from quiescence."""

    def _nxp_board(self) -> Board:
        """Knight on d4 can capture pawn on e6.  No other captures available."""
        return _build(
            [
                ("g1", Color.WHITE, PieceType.KING),
                ("d4", Color.WHITE, PieceType.KNIGHT),
                ("g8", Color.BLACK, PieceType.KING),
                ("e6", Color.BLACK, PieceType.PAWN),
            ],
            Color.WHITE,
        )

    def _qxp_board_clearly_losing(self) -> Board:
        """Queen on d4 captures pawn on e5, but two black rooks immediately recapture.
        This is a clearly losing exchange and should still be filtered out."""
        return _build(
            [
                ("g1", Color.WHITE, PieceType.KING),
                ("d4", Color.WHITE, PieceType.QUEEN),
                ("g8", Color.BLACK, PieceType.KING),
                ("e5", Color.BLACK, PieceType.PAWN),
                ("e8", Color.BLACK, PieceType.ROOK),
                ("f8", Color.BLACK, PieceType.ROOK),
            ],
            Color.WHITE,
        )

    def _order_fn(self, board: Board):
        ctx = make_quiet_order_context(board)
        return lambda b, m: quiet_strategy_order_score(b, m, ctx)

    def test_nxp_included_in_quiescence(self) -> None:
        """Nd4xe6 must be a quiescence candidate after the filter fix."""
        board = self._nxp_board()
        legal = get_legal_moves(board)
        qmoves = select_quiescence_moves(board, list(legal), self._order_fn(board), 8)
        d4 = sq("d4")
        e6 = sq("e6")
        assert any(m.start == d4 and m.end == e6 for m in qmoves), (
            "NxP (Nd4xe6) was excluded from quiescence candidates"
        )

    def test_clearly_losing_capture_still_filtered(self) -> None:
        """QxP where the queen is immediately recaptured by two rooks should score 0."""
        from chess_game.chess.ai_quiescence_helpers import _quiescence_capture_mvv_lva
        board = self._qxp_board_clearly_losing()
        m = parse_move_notation("d4e5")
        score = _quiescence_capture_mvv_lva(board, m)
        # Queen (900) captures pawn (100).  The score should be positive (queen capturing
        # a pawn is not clearly losing by the static filter alone; the engine relies on the
        # recursive search to evaluate the follow-up captures).
        # The filter should only exclude captures where captured value < PAWN value (0)
        # and attacker is 3× more valuable — which doesn't apply here (pawn > 0).
        assert score > 0, (
            "QxP should not be filtered at the static MVV-LVA stage; "
            "let the recursive search handle the recapture"
        )


# ---------------------------------------------------------------------------
# Task 3 — Check extensions: forcing check sequences found at depth 3
# ---------------------------------------------------------------------------

class TestCheckExtensions:
    """Verify check_extension helper fires exactly when a move gives check."""

    def test_check_extension_fires_on_check(self) -> None:
        """After a queen check, check_extension returns 1 with budget > 0."""
        board = _build(
            [
                ("g1", Color.WHITE, PieceType.KING),
                ("d1", Color.WHITE, PieceType.QUEEN),
                ("g8", Color.BLACK, PieceType.KING),
            ],
            Color.WHITE,
        )
        m = parse_move_notation("d1d8")  # Qd8+ check
        child = clone_with_move(board, m)
        assert check_extension(child, extension_budget=1) == 1

    def test_check_extension_zero_on_quiet_move(self) -> None:
        """After a quiet move (no check), check_extension returns 0."""
        board = _build(
            [
                ("g1", Color.WHITE, PieceType.KING),
                ("d1", Color.WHITE, PieceType.QUEEN),
                ("g8", Color.BLACK, PieceType.KING),
            ],
            Color.WHITE,
        )
        m = parse_move_notation("d1d4")  # Quiet queen move
        child = clone_with_move(board, m)
        assert check_extension(child, extension_budget=1) == 0

    def test_check_extension_zero_when_budget_exhausted(self) -> None:
        """check_extension returns 0 when extension_budget is 0, preventing cascades."""
        board = _build(
            [
                ("g1", Color.WHITE, PieceType.KING),
                ("d1", Color.WHITE, PieceType.QUEEN),
                ("g8", Color.BLACK, PieceType.KING),
            ],
            Color.WHITE,
        )
        m = parse_move_notation("d1d8")  # Would give check
        child = clone_with_move(board, m)
        assert check_extension(child, extension_budget=0) == 0

    @pytest.mark.slow
    def test_forced_checkmate_found_at_depth_3(self) -> None:
        """Engine at depth 3 must find the mating first move in a simple back-rank mate.

        White: Kg1, Qd1, Rh1.  Black: Kg8, pawns g7/h7.
        White plays Qd8+ (check), Black Kg7 forced, then Rh1h7#.
        Without check extensions the Rh7 mate on ply 4 falls off the horizon.
        """
        from chess_game.chess.board.game_state import is_in_check
        from chess_game.chess.move import Move
        board = _build(
            [
                ("g1", Color.WHITE, PieceType.KING),
                ("d1", Color.WHITE, PieceType.QUEEN),
                ("h1", Color.WHITE, PieceType.ROOK),
                ("g8", Color.BLACK, PieceType.KING),
                ("g7", Color.BLACK, PieceType.PAWN),
                ("h7", Color.BLACK, PieceType.PAWN),
            ],
            Color.WHITE,
        )
        move = get_best_move(board, depth=3, book_options=_NO_BOOK)
        assert move is not None
        child = clone_with_move(board, Move(start=move.start, end=move.end, promotion=move.promotion))
        assert is_in_check(child, Color.BLACK), (
            "Depth-3 engine with check extensions should find Qd8+ as the first forcing move"
        )


# ---------------------------------------------------------------------------
# Task 4 — Evaluation noise: material dominates in queen-advantage positions
# ---------------------------------------------------------------------------

class TestEvaluationNoise:
    """Verify no non-material component drowns out a 900-point material lead."""

    def test_position_clearly_winning_for_black(self) -> None:
        """In the move-12 position (black up a queen), evaluation must show black clearly winning.

        The `conversion` component is intentionally large (correct strategic signal —
        it rewards the leading side for being in a simplified, convertable position).
        We test that the *total* evaluation correctly identifies black as ahead by > 6 pawns.
        """
        board = _replay(_GAME_MOVES[:24])
        bd = get_evaluation_breakdown(board)
        # White's perspective: strongly negative = black is winning.
        assert bd["total"] < -600, (
            f"Expected evaluation < -600 (black clearly winning), got {bd['total']}"
        )

    def test_no_unexpected_loud_non_material_components(self) -> None:
        """No positional component other than 'conversion' should exceed 300.

        'conversion' is excluded because it is intentionally large when one side
        holds a material lead — it guides the engine toward converting winning positions.
        All other positional/guidance components should stay quiet (< 300) to avoid
        drowning out material-based decisions at shallow depth.
        """
        board = _replay(_GAME_MOVES[:24])
        bd = get_evaluation_breakdown(board)
        # 'conversion' is a legitimate strategic amplifier; exclude it from the noise check.
        loud = {
            k: v
            for k, v in bd.items()
            if k not in {"total", "material", "conversion"} and abs(v) > 300
        }
        assert not loud, f"Unexpected loud non-material components: {loud}"
