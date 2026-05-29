"""Transcript-driven regressions for STRATEGY8 opening discipline priorities."""

from chess_game.chess import ai
from chess_game.chess.ai import _move_order_score, get_best_move
from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, LegalMove, PieceType
from tests.helpers import sq


def _board_from_moves(moves: list[tuple[str, str]]) -> Board:
    board = Board()
    for start, end in moves:
        board.make_move(sq(start), sq(end))
    return board


def _transcript_opening_probe_board() -> Board:
    return _board_from_moves(
        [
            ("b1", "c3"),
            ("e7", "e5"),
            ("g1", "f3"),
            ("b8", "c6"),
            ("c3", "e4"),
            ("d7", "d5"),
            ("f3", "d4"),
            ("c6", "d4"),
            ("e4", "c3"),
            ("f8", "b4"),
            ("c3", "b1"),
            ("e5", "e4"),
            ("c2", "c3"),
            ("c8", "g4"),
            ("d1", "a4"),
            ("g4", "d7"),
        ]
    )


def test_strategy8_order_prefers_development_over_followup_queen_redeploy() -> None:
    """The opening probe should develop before making another quiet queen move."""

    board = _transcript_opening_probe_board()
    develop = ai.Move(start=sq("f1"), end=sq("e2"))
    queen_redeploy = ai.Move(start=sq("a4"), end=sq("d1"))

    assert _move_order_score(board, develop, None) > _move_order_score(
        board,
        queen_redeploy,
        None,
    )


def test_strategy8_order_penalizes_minor_retreat_before_king_is_settled() -> None:
    """Retreating a developed minor should lose to fresh development when uncastled."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("c4"), create_piece(Color.WHITE, PieceType.BISHOP))
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("f2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("f8"), create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.turn = Color.WHITE

    develop = ai.Move(start=sq("g1"), end=sq("f3"))
    retreat = ai.Move(start=sq("c4"), end=sq("f1"))

    assert _move_order_score(board, develop, None) > _move_order_score(board, retreat, None)


def test_strategy8_search_demotes_flank_poke_when_castling_is_available() -> None:
    """Near-equal opening roots should not prefer an aimless flank poke."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("f3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("e2"), create_piece(Color.WHITE, PieceType.BISHOP))
    board.set_piece(sq("a2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("f2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("f8"), create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.set_piece(sq("c5"), create_piece(Color.BLACK, PieceType.BISHOP))
    board.turn = Color.WHITE

    castle = ai.Move(start=sq("e1"), end=sq("g1"))
    flank_poke = ai.Move(start=sq("a2"), end=sq("a4"))

    assert _move_order_score(board, castle, None) > _move_order_score(board, flank_poke, None)

    best_move = get_best_move(board, depth=2)

    assert best_move != LegalMove(start=sq("a2"), end=sq("a4"))


def test_strategy8_conversion_prefers_simplification_over_side_activity() -> None:
    """When clearly ahead, practical simplification should beat side drift."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.set_piece(sq("a8"), create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE

    simplify = ai.Move(start=sq("d1"), end=sq("d8"))
    drift = ai.Move(start=sq("g2"), end=sq("g4"))

    assert _move_order_score(board, simplify, None) > _move_order_score(board, drift, None)
    assert get_best_move(board, depth=2) == LegalMove(start=sq("d1"), end=sq("d8"))
