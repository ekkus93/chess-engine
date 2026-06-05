"""Unit tests for chess_game.chess.pawn_structure_evaluation."""

from __future__ import annotations

from chess_game.chess.board.board import Board, create_piece
from chess_game.chess.evaluation_tables import (
    CENTER_FILES,
    CENTRAL_DUO_BONUS,
    DOUBLED_PAWN_PENALTY,
    ISOLATED_PAWN_PENALTY,
    PAWN_ISLAND_PENALTY,
)
from chess_game.chess.pawn_structure_evaluation import (
    _central_duo_bonus,
    _pawn_file_penalty,
    _pawn_island_penalty,
    collect_pawn_positions,
    evaluate_pawn_structure,
)
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


# ---------------------------------------------------------------------------
# collect_pawn_positions
# ---------------------------------------------------------------------------


class TestCollectPawnPositions:
    """Tests for collect_pawn_positions."""

    def test_starting_position_counts(self) -> None:
        """Starting position has 8 White pawns on rank 2 and 8 Black on rank 7."""
        board = Board()
        positions = collect_pawn_positions(board)
        assert len(positions[Color.WHITE]) == 8
        assert len(positions[Color.BLACK]) == 8
        assert all(row == 6 for row, _ in positions[Color.WHITE])
        assert all(row == 1 for row, _ in positions[Color.BLACK])

    def test_empty_board_no_pawns(self) -> None:
        """Cleared board returns empty lists for both colors."""
        board = Board()
        board.clear_board()
        positions = collect_pawn_positions(board)
        assert positions[Color.WHITE] == []
        assert positions[Color.BLACK] == []


# ---------------------------------------------------------------------------
# evaluate_pawn_structure — symmetric baseline
# ---------------------------------------------------------------------------


class TestEvaluatePawnStructureBaseline:
    """evaluate_pawn_structure baseline and symmetry tests."""

    def test_starting_position_is_zero(self) -> None:
        """Symmetric starting position scores 0."""
        assert evaluate_pawn_structure(Board(), endgame_phase=0) == 0

    def test_white_passed_pawn_positive(self) -> None:
        """Board with White advanced passer and no Black pawns scores > 0."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e5"), create_piece(Color.WHITE, PieceType.PAWN))
        board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
        assert evaluate_pawn_structure(board, endgame_phase=0) > 0

    def test_more_advanced_passer_scores_higher(self) -> None:
        """White passer on e6 (rank 3) scores more than one on e5 (rank 4)."""
        def score_with_passer(square_name: str) -> int:
            board = Board()
            board.clear_board()
            board.set_piece(sq(square_name), create_piece(Color.WHITE, PieceType.PAWN))
            board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
            board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
            return evaluate_pawn_structure(board, endgame_phase=0)

        assert score_with_passer("e6") > score_with_passer("e5")

    def test_phase_sensitivity(self) -> None:
        """Score changes between full middlegame and full endgame for a castled position."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
        board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
        score_mid = evaluate_pawn_structure(board, endgame_phase=0)
        score_end = evaluate_pawn_structure(board, endgame_phase=100)
        assert score_mid != score_end


# ---------------------------------------------------------------------------
# _pawn_file_penalty
# ---------------------------------------------------------------------------


class TestPawnFilePenalty:
    """Tests for _pawn_file_penalty."""

    def test_doubled_and_isolated_pawn(self) -> None:
        """Two pawns on the same file with no adjacent pawns incur both penalties."""
        file_map = {4: [3, 4]}
        penalty = _pawn_file_penalty(file_map, 4)
        assert penalty == DOUBLED_PAWN_PENALTY + ISOLATED_PAWN_PENALTY

    def test_doubled_not_isolated(self) -> None:
        """Two pawns on e-file with a pawn on d-file incur only doubled penalty."""
        file_map = {4: [3, 4], 3: [5]}
        penalty = _pawn_file_penalty(file_map, 4)
        assert penalty == DOUBLED_PAWN_PENALTY

    def test_isolated_not_doubled(self) -> None:
        """Single pawn on e-file with no adjacent pawns incurs only isolated penalty."""
        file_map = {4: [4]}
        penalty = _pawn_file_penalty(file_map, 4)
        assert penalty == ISOLATED_PAWN_PENALTY

    def test_healthy_pawn_no_penalty(self) -> None:
        """Single pawn on e-file with a neighbor on d-file incurs no penalty."""
        file_map = {4: [4], 3: [5]}
        penalty = _pawn_file_penalty(file_map, 4)
        assert penalty == 0


# ---------------------------------------------------------------------------
# _pawn_island_penalty
# ---------------------------------------------------------------------------


class TestPawnIslandPenalty:
    """Tests for _pawn_island_penalty."""

    def test_no_pawns_returns_zero(self) -> None:
        """Empty file map has no islands."""
        assert _pawn_island_penalty({}) == 0

    def test_one_island_returns_zero(self) -> None:
        """A single connected group of pawns counts as one island — no penalty."""
        assert _pawn_island_penalty({3: [4], 4: [4], 5: [4]}) == 0

    def test_two_islands(self) -> None:
        """Pawns on e- and a-files (two islands) incur one island penalty."""
        penalty = _pawn_island_penalty({0: [6], 4: [4]})
        assert penalty == PAWN_ISLAND_PENALTY

    def test_three_islands(self) -> None:
        """Pawns on a-, d-, and g-files (three islands) incur two island penalties."""
        penalty = _pawn_island_penalty({0: [6], 3: [4], 6: [5]})
        assert penalty == 2 * PAWN_ISLAND_PENALTY


# ---------------------------------------------------------------------------
# _central_duo_bonus
# ---------------------------------------------------------------------------


class TestCentralDuoBonus:
    """Tests for _central_duo_bonus."""

    def test_d4_e4_central_duo(self) -> None:
        """Pawns on d4 and e4 form a central duo (both on center files, adjacent)."""
        positions = [(4, 3), (4, 4)]
        assert _central_duo_bonus(positions) == CENTRAL_DUO_BONUS

    def test_non_central_pawns_no_bonus(self) -> None:
        """Pawns on a- and h-files are not on center files — no bonus."""
        positions = [(4, 0), (4, 7)]
        assert _central_duo_bonus(positions) == 0

    def test_center_pawn_without_neighbor_no_bonus(self) -> None:
        """A lone pawn on e4 without an adjacent center pawn earns no duo bonus."""
        positions = [(4, 4)]
        assert _central_duo_bonus(positions) == 0

    def test_center_files_match_constants(self) -> None:
        """CENTER_FILES covers d and e columns (3 and 4)."""
        assert CENTER_FILES == {3, 4}
