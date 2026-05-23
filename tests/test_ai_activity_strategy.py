"""Regression coverage for real activity, empty checks, and unsafe king drift."""

from chess_game.chess import ai
from chess_game.chess.ai import get_evaluation_breakdown
from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType
from tests.test_ai_quality import _move_order_score
from tests.helpers import sq


def _build_board(pieces: list[tuple[str, Color, PieceType]], turn: Color = Color.WHITE) -> Board:
    board = Board()
    board.clear_board()
    for square, color, kind in pieces:
        board.set_piece(sq(square), create_piece(color, kind))
    board.turn = turn
    return board


def test_quiet_move_order_penalizes_repeated_queen_shuffle_without_new_pressure() -> None:
    """A repeat queen swing with no new pressure should lose to development."""

    board = _build_board(
        [
            ("e1", Color.WHITE, PieceType.KING),
            ("a5", Color.WHITE, PieceType.QUEEN),
            ("g1", Color.WHITE, PieceType.KNIGHT),
            ("c1", Color.WHITE, PieceType.BISHOP),
            ("g8", Color.BLACK, PieceType.KING),
            ("g7", Color.BLACK, PieceType.PAWN),
            ("h7", Color.BLACK, PieceType.PAWN),
        ]
    )

    queen_shuffle = ai.Move(start=sq("a5"), end=sq("h5"))
    developing_move = ai.Move(start=sq("g1"), end=sq("f3"))

    assert _move_order_score(board, developing_move, None) > _move_order_score(
        board,
        queen_shuffle,
        None,
    )


def test_quiet_move_order_penalizes_rook_swing_that_abandons_file_defense() -> None:
    """A rook swing should lose when it abandons a contested invasion file."""

    board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("a2", Color.WHITE, PieceType.ROOK),
            ("e2", Color.WHITE, PieceType.QUEEN),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.ROOK),
        ]
    )

    hold_file = ai.Move(start=sq("a2"), end=sq("d2"))
    rook_swing = ai.Move(start=sq("a2"), end=sq("a7"))

    assert _move_order_score(board, hold_file, None) > _move_order_score(
        board,
        rook_swing,
        None,
    )


def test_development_breakdown_prefers_central_pawn_structure_over_flank_activity() -> None:
    """Opening scoring should favor central structure over speculative flank pushes."""

    central_board = Board()
    central_board.clear_square(sq("d2"))
    central_board.clear_square(sq("e2"))
    central_board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.PAWN))
    central_board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.PAWN))

    flank_board = Board()
    flank_board.clear_square(sq("g2"))
    flank_board.clear_square(sq("h2"))
    flank_board.set_piece(sq("g4"), create_piece(Color.WHITE, PieceType.PAWN))
    flank_board.set_piece(sq("h4"), create_piece(Color.WHITE, PieceType.PAWN))

    assert (
        get_evaluation_breakdown(central_board)["development"]
        > get_evaluation_breakdown(flank_board)["development"]
    )


def test_king_breakdowns_penalize_leaving_shelter_without_compensation() -> None:
    """A king that leaves its shelter in a queen-rich middlegame should be penalized."""

    sheltered_board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("f2", Color.WHITE, PieceType.PAWN),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("d1", Color.WHITE, PieceType.QUEEN),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("f1", Color.WHITE, PieceType.ROOK),
            ("g8", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.QUEEN),
            ("a8", Color.BLACK, PieceType.ROOK),
        ]
    )

    exposed_board = sheltered_board.clone()
    exposed_board.clear_square(sq("g1"))
    exposed_board.clear_square(sq("f1"))
    exposed_board.clear_square(sq("f2"))
    exposed_board.clear_square(sq("g2"))
    exposed_board.set_piece(sq("e2"), create_piece(Color.WHITE, PieceType.KING))
    exposed_board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))

    assert (
        get_evaluation_breakdown(sheltered_board)["king_safety"]
        > get_evaluation_breakdown(exposed_board)["king_safety"]
    )
    assert (
        get_evaluation_breakdown(sheltered_board)["king_exposure"]
        > get_evaluation_breakdown(exposed_board)["king_exposure"]
    )


def test_quiet_move_order_prefers_back_rank_box_check_over_side_check() -> None:
    """Useful checks that tighten the king box should beat broad side checks."""

    board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("d1", Color.WHITE, PieceType.QUEEN),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("c4", Color.WHITE, PieceType.BISHOP),
            ("g8", Color.BLACK, PieceType.KING),
            ("g7", Color.BLACK, PieceType.PAWN),
            ("h7", Color.BLACK, PieceType.PAWN),
        ]
    )

    back_rank_check = ai.Move(start=sq("d1"), end=sq("d8"))
    side_check = ai.Move(start=sq("a1"), end=sq("a8"))

    assert _move_order_score(board, back_rank_check, None) > _move_order_score(
        board,
        side_check,
        None,
    )


def test_quiet_move_order_downgrades_flank_check_that_can_be_chased() -> None:
    """A flashy flank check should lose to a more forcing central check."""

    board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("d1", Color.WHITE, PieceType.QUEEN),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("c4", Color.WHITE, PieceType.BISHOP),
            ("g8", Color.BLACK, PieceType.KING),
            ("f6", Color.BLACK, PieceType.KNIGHT),
            ("g7", Color.BLACK, PieceType.PAWN),
            ("h7", Color.BLACK, PieceType.PAWN),
        ]
    )

    central_check = ai.Move(start=sq("d1"), end=sq("d8"))
    flank_check = ai.Move(start=sq("d1"), end=sq("h5"))

    assert _move_order_score(board, central_check, None) > _move_order_score(
        board,
        flank_check,
        None,
    )


def test_quiet_move_order_prefers_improving_worst_rook_over_side_check() -> None:
    """A misplaced rook should be improved before giving a cosmetic side check."""

    board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("e2", Color.WHITE, PieceType.QUEEN),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("f1", Color.WHITE, PieceType.ROOK),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.ROOK),
            ("g7", Color.BLACK, PieceType.PAWN),
            ("h7", Color.BLACK, PieceType.PAWN),
        ]
    )

    improve_rook = ai.Move(start=sq("a1"), end=sq("d1"))
    side_check = ai.Move(start=sq("a1"), end=sq("a8"))

    assert _move_order_score(board, improve_rook, None) > _move_order_score(
        board,
        side_check,
        None,
    )


def test_quiet_move_order_prefers_reconnecting_rooks_before_side_plan() -> None:
    """Rook coordination should beat an idle wing pawn plan."""

    board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("d2", Color.WHITE, PieceType.QUEEN),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("f1", Color.WHITE, PieceType.ROOK),
            ("c4", Color.WHITE, PieceType.BISHOP),
            ("f3", Color.WHITE, PieceType.KNIGHT),
            ("f2", Color.WHITE, PieceType.PAWN),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.QUEEN),
            ("g7", Color.BLACK, PieceType.PAWN),
            ("h7", Color.BLACK, PieceType.PAWN),
        ]
    )

    reconnect_rooks = ai.Move(start=sq("a1"), end=sq("e1"))
    side_plan = ai.Move(start=sq("h2"), end=sq("h4"))

    assert _move_order_score(board, reconnect_rooks, None) > _move_order_score(
        board,
        side_plan,
        None,
    )


def test_quiet_move_order_prefers_bishop_reroute_to_long_diagonal_before_pawn_race() -> None:
    """A blocked bishop should reach the long diagonal before a loose pawn race."""

    board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("d1", Color.WHITE, PieceType.QUEEN),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("f1", Color.WHITE, PieceType.ROOK),
            ("c1", Color.WHITE, PieceType.BISHOP),
            ("f3", Color.WHITE, PieceType.KNIGHT),
            ("d3", Color.WHITE, PieceType.PAWN),
            ("e4", Color.WHITE, PieceType.PAWN),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.QUEEN),
            ("g7", Color.BLACK, PieceType.PAWN),
            ("h7", Color.BLACK, PieceType.PAWN),
        ]
    )

    bishop_reroute = ai.Move(start=sq("c1"), end=sq("b2"))
    pawn_race = ai.Move(start=sq("h2"), end=sq("h4"))

    assert _move_order_score(board, bishop_reroute, None) > _move_order_score(
        board,
        pawn_race,
        None,
    )


def test_quiet_move_order_prefers_queen_centralization_that_supports_coordination() -> None:
    """A queen move that supports the team should beat a loose flank drift."""

    board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("f1", Color.WHITE, PieceType.ROOK),
            ("b3", Color.WHITE, PieceType.QUEEN),
            ("c4", Color.WHITE, PieceType.BISHOP),
            ("f3", Color.WHITE, PieceType.KNIGHT),
            ("f2", Color.WHITE, PieceType.PAWN),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.QUEEN),
            ("g7", Color.BLACK, PieceType.PAWN),
            ("h7", Color.BLACK, PieceType.PAWN),
        ]
    )

    support_move = ai.Move(start=sq("b3"), end=sq("e2"))
    flank_drift = ai.Move(start=sq("b3"), end=sq("h3"))

    assert _move_order_score(board, support_move, None) > _move_order_score(
        board,
        flank_drift,
        None,
    )
