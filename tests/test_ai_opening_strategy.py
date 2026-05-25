"""Opening-discipline regressions for STRATEGY4 opening heuristics."""

from chess_game.chess import ai
from chess_game.chess.ai import get_best_move, get_evaluation_breakdown
from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, LegalMove, PieceType
from tests.test_ai_quality import _empty_board_with_kings, _move_order_score
from tests.helpers import sq


def test_development_breakdown_rewards_early_central_control() -> None:
    """Opening development should prefer central pawn/minor control over passive setup."""

    central_board = Board()
    central_board.clear_square(sq("b1"))
    central_board.clear_square(sq("g1"))
    central_board.clear_square(sq("d2"))
    central_board.clear_square(sq("e2"))
    central_board.set_piece(sq("c3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    central_board.set_piece(sq("f3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    central_board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.PAWN))
    central_board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.PAWN))

    passive_board = Board()
    passive_board.clear_square(sq("b1"))
    passive_board.clear_square(sq("g1"))
    passive_board.clear_square(sq("d2"))
    passive_board.clear_square(sq("e2"))
    passive_board.set_piece(sq("a3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    passive_board.set_piece(sq("h3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    passive_board.set_piece(sq("d3"), create_piece(Color.WHITE, PieceType.PAWN))
    passive_board.set_piece(sq("e3"), create_piece(Color.WHITE, PieceType.PAWN))

    assert (
        get_evaluation_breakdown(central_board)["development"]
        > get_evaluation_breakdown(passive_board)["development"]
    )


def test_development_breakdown_rewards_coordinated_minor_setup() -> None:
    """Opening development should prefer coordinated central minors over scattered pieces."""

    coordinated_board = Board()
    coordinated_board.clear_square(sq("f1"))
    coordinated_board.clear_square(sq("g1"))
    coordinated_board.set_piece(sq("c4"), create_piece(Color.WHITE, PieceType.BISHOP))
    coordinated_board.set_piece(sq("f3"), create_piece(Color.WHITE, PieceType.KNIGHT))

    scattered_board = Board()
    scattered_board.clear_square(sq("f1"))
    scattered_board.clear_square(sq("g1"))
    scattered_board.set_piece(sq("a2"), create_piece(Color.WHITE, PieceType.BISHOP))
    scattered_board.set_piece(sq("h3"), create_piece(Color.WHITE, PieceType.KNIGHT))

    assert (
        get_evaluation_breakdown(coordinated_board)["development"]
        > get_evaluation_breakdown(scattered_board)["development"]
    )


def test_development_breakdown_penalizes_flank_queen_raid_before_castling() -> None:
    """A flank queen raid before king safety is fixed should be penalized."""

    restrained_board = Board()
    raiding_board = Board()
    raiding_board.clear_square(sq("d1"))
    raiding_board.set_piece(sq("a6"), create_piece(Color.WHITE, PieceType.QUEEN))

    assert (
        get_evaluation_breakdown(restrained_board)["development"]
        > get_evaluation_breakdown(raiding_board)["development"]
    )


def test_development_breakdown_penalizes_early_flank_pawn_poke() -> None:
    """An early flank pawn lunge should score worse than a compact opening."""

    restrained_board = Board()
    poking_board = Board()
    assert poking_board.apply_legal_move(sq("a2"), sq("a4"))

    assert (
        get_evaluation_breakdown(restrained_board)["development"]
        > get_evaluation_breakdown(poking_board)["development"]
    )


def test_quiet_move_order_penalizes_repeated_queen_move_while_minors_sleep() -> None:
    """Once the queen is out early, moving it again should lose to development."""

    board = _empty_board_with_kings()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("h5"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.BISHOP))
    board.turn = Color.WHITE

    queen_repeat = ai.Move(start=sq("h5"), end=sq("a5"))
    developing_move = ai.Move(start=sq("g1"), end=sq("f3"))

    assert _move_order_score(board, developing_move, None) > _move_order_score(
        board,
        queen_repeat,
        None,
    )


def test_search_prefers_central_recapture_over_showy_queen_pressure() -> None:
    """Opening search should recapture in the center over a flashy queen move."""

    board = _empty_board_with_kings()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("f1"), create_piece(Color.WHITE, PieceType.BISHOP))
    board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d5"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("h7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE

    best_move = get_best_move(board, depth=1)

    assert best_move == LegalMove(start=sq("e4"), end=sq("d5"))


# ---------------------------------------------------------------------------
# Task 8.3 opening-plan tests
# ---------------------------------------------------------------------------

def test_quiet_move_order_prefers_development_over_flank_pawn_poke() -> None:
    """Completing development should outscore a flank pawn poke while minors sleep."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KNIGHT))  # undeveloped
    board.set_piece(sq("b1"), create_piece(Color.WHITE, PieceType.KNIGHT))  # undeveloped
    board.set_piece(sq("a2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("f2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("a7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("b7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("h7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE

    develop = ai.Move(start=sq("g1"), end=sq("f3"))
    flank_poke = ai.Move(start=sq("a2"), end=sq("a4"))

    assert _move_order_score(board, develop, None) > _move_order_score(board, flank_poke, None)


def test_quiet_move_order_prefers_classical_opening_guidance_move() -> None:
    """Very early positions should prefer simple classical setup moves."""

    board = Board()

    classical = ai.Move(start=sq("e2"), end=sq("e4"))
    flank_poke = ai.Move(start=sq("a2"), end=sq("a4"))

    assert _move_order_score(board, classical, None) > _move_order_score(board, flank_poke, None)


def test_quiet_move_order_prefers_castling_over_speculative_knight_sortie() -> None:
    """Castling for king safety should outscore a speculative knight advance."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("f3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.BISHOP))
    board.set_piece(sq("f2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g3"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("f6"), create_piece(Color.BLACK, PieceType.KNIGHT))
    board.set_piece(sq("c5"), create_piece(Color.BLACK, PieceType.BISHOP))
    board.turn = Color.WHITE

    castle = ai.Move(start=sq("e1"), end=sq("g1"))
    knight_sortie = ai.Move(start=sq("f3"), end=sq("g5"))

    assert _move_order_score(board, castle, None) > _move_order_score(board, knight_sortie, None)


def test_search_prefers_central_recapture_over_flank_pawn_push() -> None:
    """The engine should recapture centrally rather than push a flank pawn."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("c3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("f3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d5"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE

    best_move = get_best_move(board, depth=1)

    assert best_move == LegalMove(start=sq("e4"), end=sq("d5"))


def test_quiet_move_order_prefers_preserving_kingside_structure_over_pawn_lunge() -> None:
    """Keeping the kingside compact should outscore a loose early pawn lunge."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("b1"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("h7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE

    develop = ai.Move(start=sq("b1"), end=sq("c3"))
    pawn_lunge = ai.Move(start=sq("g2"), end=sq("g4"))

    assert _move_order_score(board, develop, None) > _move_order_score(board, pawn_lunge, None)


def test_quiet_move_order_penalizes_early_rook_wander() -> None:
    """Developing a piece should outscore walking a rook before minors are ready."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("b1"), create_piece(Color.WHITE, PieceType.KNIGHT))  # undeveloped
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KNIGHT))  # undeveloped
    board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.WHITE

    develop = ai.Move(start=sq("b1"), end=sq("c3"))
    rook_wander = ai.Move(start=sq("a1"), end=sq("a3"))

    assert _move_order_score(board, develop, None) > _move_order_score(board, rook_wander, None)
