"""Strategy 4 regressions for self-restraint and conversion discipline."""

from chess_game.chess.ai import get_evaluation_breakdown, position_key
from chess_game.chess.ai_search_helpers import RepetitionPolicy, repetition_score
from chess_game.chess.board import Board, create_piece
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


def test_king_safety_penalizes_early_h_pawn_push_with_queens_on() -> None:
    """Castled shelter loosening should be worse while queens remain."""

    sheltered_board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("d1", Color.WHITE, PieceType.QUEEN),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("f1", Color.WHITE, PieceType.ROOK),
            ("f2", Color.WHITE, PieceType.PAWN),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.QUEEN),
            ("a8", Color.BLACK, PieceType.ROOK),
        ]
    )
    loosened_board = sheltered_board.clone()
    loosened_board.clear_square(sq("h2"))
    loosened_board.set_piece(sq("h3"), create_piece(Color.WHITE, PieceType.PAWN))

    assert (
        get_evaluation_breakdown(sheltered_board)["king_safety"]
        > get_evaluation_breakdown(loosened_board)["king_safety"]
    )


def test_development_penalizes_early_h_pawn_push_before_coordination() -> None:
    """Opening development should reject shelter pawn pushes before minors are ready."""

    healthy_board = Board()
    healthy_board.clear_square(sq("e1"))
    healthy_board.clear_square(sq("h1"))
    healthy_board.clear_square(sq("g1"))
    healthy_board.clear_square(sq("f1"))
    healthy_board.clear_square(sq("e2"))
    healthy_board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    healthy_board.set_piece(sq("f1"), create_piece(Color.WHITE, PieceType.ROOK))
    healthy_board.set_piece(sq("f3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    healthy_board.set_piece(sq("e2"), create_piece(Color.WHITE, PieceType.BISHOP))
    loosened_board = healthy_board.clone()
    loosened_board.clear_square(sq("h2"))
    loosened_board.set_piece(sq("h3"), create_piece(Color.WHITE, PieceType.PAWN))

    assert (
        get_evaluation_breakdown(healthy_board)["development"]
        > get_evaluation_breakdown(loosened_board)["development"]
    )


def test_repetition_score_scales_up_for_large_winning_margin() -> None:
    """A repeated draw should be much worse when the side to move is clearly winning."""

    board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("d4", Color.WHITE, PieceType.QUEEN),
            ("g8", Color.BLACK, PieceType.KING),
        ]
    )
    key = position_key(board)

    assert (
        repetition_score(
            board,
            None,
            (key, key, key),
            RepetitionPolicy(
                position_key=position_key,
                evaluate=lambda _board: 480,
                progress=lambda _board: 96,
                threshold=120,
                progress_threshold=24,
                penalty=32,
            ),
        )
        == -128
    )
