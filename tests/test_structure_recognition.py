"""Unit tests for Task 5 structure recognition helpers."""

from chess_game.chess.board import Board, create_piece
from chess_game.chess.structure_recognition import structure_profile
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


def _build_board(
    pieces: list[tuple[str, Color, PieceType]],
    turn: Color = Color.WHITE,
) -> Board:
    board = Board()
    board.clear_board()
    for square, color, kind in pieces:
        board.set_piece(sq(square), create_piece(color, kind))
    board.turn = turn
    return board


def test_structure_profile_recognizes_open_and_closed_centers() -> None:
    """Task 5 helpers should distinguish open from locked centers."""

    open_center_board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("g8", Color.BLACK, PieceType.KING),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("a8", Color.BLACK, PieceType.ROOK),
        ]
    )
    closed_center_board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("g8", Color.BLACK, PieceType.KING),
            ("d4", Color.WHITE, PieceType.PAWN),
            ("e5", Color.WHITE, PieceType.PAWN),
            ("d5", Color.BLACK, PieceType.PAWN),
            ("e6", Color.BLACK, PieceType.PAWN),
        ]
    )

    open_profile = structure_profile(open_center_board)
    closed_profile = structure_profile(closed_center_board)

    assert open_profile.open_center
    assert not open_profile.closed_center
    assert closed_profile.closed_center
    assert not closed_profile.open_center


def test_structure_profile_recognizes_iqp_hanging_pawns_and_opposite_castling() -> None:
    """Task 5 helpers should surface the main middlegame structure families."""

    iqp_board = _build_board(
        [
            ("c1", Color.WHITE, PieceType.KING),
            ("g8", Color.BLACK, PieceType.KING),
            ("d5", Color.BLACK, PieceType.PAWN),
        ]
    )
    hanging_board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("g8", Color.BLACK, PieceType.KING),
            ("c5", Color.BLACK, PieceType.PAWN),
            ("d5", Color.BLACK, PieceType.PAWN),
        ]
    )

    iqp_profile = structure_profile(iqp_board)
    hanging_profile = structure_profile(hanging_board)

    assert iqp_profile.opposite_side_castling
    assert [target.col for target in iqp_profile.black.isolated_queen_pawns] == [3]
    assert [target.col for target in hanging_profile.black.hanging_pawns] == [2, 3]


def test_structure_profile_recognizes_rook_endgame_passer_plans() -> None:
    """Task 5 helpers should notice outside or protected passers in rook endgames."""

    board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("g8", Color.BLACK, PieceType.KING),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("a8", Color.BLACK, PieceType.ROOK),
            ("a5", Color.WHITE, PieceType.PAWN),
            ("b4", Color.WHITE, PieceType.PAWN),
        ]
    )

    profile = structure_profile(board)

    assert profile.rook_endgame_with_passer_plan
    assert profile.white.outside_passed_files == (0,)
    assert profile.white.protected_passed_files == (0,)
