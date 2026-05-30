"""Transcript-driven regressions for STRATEGY9 conversion and opening discipline."""

from chess_game.chess.ai_search_helpers import _pawn_structure_change_root_bonus
from chess_game.chess.board import Board, create_piece
from chess_game.chess.conversion_guidance import (
    _conversion_context,
    _passer_advance_bonus,
)
from chess_game.chess.endgame_evaluation import (
    _heavy_endgame_king_activity_bonus,
    evaluate_endgame_technique,
    evaluate_progress,
)
from chess_game.chess.move import Move
from chess_game.chess.opening_move_ordering import (
    _is_repeated_minor_piece_move,
    opening_discipline_order_score,
)
from chess_game.chess.passer_race_guidance import _passes_material_gate
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


def _build_board(
    pieces: list[tuple[str, Color, PieceType]],
    turn: Color,
) -> Board:
    board = Board()
    board.clear_board()
    for square, color, kind in pieces:
        board.set_piece(sq(square), create_piece(color, kind))
    board.turn = turn
    return board


def _opening_knight_tour_seed() -> Board:
    """Position after 1. Nc3 Nc6 2. Nd5 from the transcript opening."""

    return _build_board(
        [
            ("e1", Color.WHITE, PieceType.KING),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("h1", Color.WHITE, PieceType.ROOK),
            ("c1", Color.WHITE, PieceType.BISHOP),
            ("f1", Color.WHITE, PieceType.BISHOP),
            ("d1", Color.WHITE, PieceType.QUEEN),
            ("d5", Color.WHITE, PieceType.KNIGHT),
            ("g1", Color.WHITE, PieceType.KNIGHT),
            ("a2", Color.WHITE, PieceType.PAWN),
            ("b2", Color.WHITE, PieceType.PAWN),
            ("c2", Color.WHITE, PieceType.PAWN),
            ("d2", Color.WHITE, PieceType.PAWN),
            ("e2", Color.WHITE, PieceType.PAWN),
            ("f2", Color.WHITE, PieceType.PAWN),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("e8", Color.BLACK, PieceType.KING),
            ("a8", Color.BLACK, PieceType.ROOK),
            ("h8", Color.BLACK, PieceType.ROOK),
            ("c8", Color.BLACK, PieceType.BISHOP),
            ("f8", Color.BLACK, PieceType.BISHOP),
            ("d8", Color.BLACK, PieceType.QUEEN),
            ("c6", Color.BLACK, PieceType.KNIGHT),
            ("g8", Color.BLACK, PieceType.KNIGHT),
            ("a7", Color.BLACK, PieceType.PAWN),
            ("b7", Color.BLACK, PieceType.PAWN),
            ("c7", Color.BLACK, PieceType.PAWN),
            ("d7", Color.BLACK, PieceType.PAWN),
            ("e7", Color.BLACK, PieceType.PAWN),
            ("f7", Color.BLACK, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.PAWN),
            ("h7", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.BLACK,
    )


def _drift_position_move_60() -> Board:
    """Drift seed around move 60: Black shuffled ...Re7 instead of passer pressure."""

    return _build_board(
        [
            ("b2", Color.WHITE, PieceType.KING),
            ("d2", Color.WHITE, PieceType.ROOK),
            ("d4", Color.WHITE, PieceType.KNIGHT),
            ("b4", Color.WHITE, PieceType.PAWN),
            ("d3", Color.WHITE, PieceType.PAWN),
            ("e3", Color.WHITE, PieceType.PAWN),
            ("f3", Color.WHITE, PieceType.PAWN),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h3", Color.WHITE, PieceType.PAWN),
            ("f7", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.ROOK),
            ("e7", Color.BLACK, PieceType.ROOK),
            ("d7", Color.BLACK, PieceType.BISHOP),
            ("a7", Color.BLACK, PieceType.PAWN),
            ("c6", Color.BLACK, PieceType.PAWN),
            ("e6", Color.BLACK, PieceType.PAWN),
            ("d5", Color.BLACK, PieceType.PAWN),
            ("f5", Color.BLACK, PieceType.PAWN),
            ("g5", Color.BLACK, PieceType.PAWN),
            ("h4", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.WHITE,
    )


def _drift_position_move_70() -> Board:
    """Drift seed around move 70: Black played ...a6 instead of forcing progress."""

    return _build_board(
        [
            ("b2", Color.WHITE, PieceType.KING),
            ("e2", Color.WHITE, PieceType.ROOK),
            ("d4", Color.WHITE, PieceType.KNIGHT),
            ("b4", Color.WHITE, PieceType.PAWN),
            ("d3", Color.WHITE, PieceType.PAWN),
            ("e3", Color.WHITE, PieceType.PAWN),
            ("f3", Color.WHITE, PieceType.PAWN),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h3", Color.WHITE, PieceType.PAWN),
            ("f7", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.ROOK),
            ("e8", Color.BLACK, PieceType.ROOK),
            ("d7", Color.BLACK, PieceType.BISHOP),
            ("a6", Color.BLACK, PieceType.PAWN),
            ("c6", Color.BLACK, PieceType.PAWN),
            ("e6", Color.BLACK, PieceType.PAWN),
            ("b5", Color.BLACK, PieceType.PAWN),
            ("d5", Color.BLACK, PieceType.PAWN),
            ("f5", Color.BLACK, PieceType.PAWN),
            ("g5", Color.BLACK, PieceType.PAWN),
            ("h4", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.WHITE,
    )


def _drift_position_move_90() -> Board:
    """Drift seed around move 90: central passer exists but loops continued."""

    return _build_board(
        [
            ("b2", Color.WHITE, PieceType.KING),
            ("d2", Color.WHITE, PieceType.ROOK),
            ("e2", Color.WHITE, PieceType.KNIGHT),
            ("b4", Color.WHITE, PieceType.PAWN),
            ("d3", Color.WHITE, PieceType.PAWN),
            ("f3", Color.WHITE, PieceType.PAWN),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h3", Color.WHITE, PieceType.PAWN),
            ("e5", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.ROOK),
            ("e8", Color.BLACK, PieceType.ROOK),
            ("d7", Color.BLACK, PieceType.BISHOP),
            ("a6", Color.BLACK, PieceType.PAWN),
            ("c6", Color.BLACK, PieceType.PAWN),
            ("e6", Color.BLACK, PieceType.PAWN),
            ("b5", Color.BLACK, PieceType.PAWN),
            ("d4", Color.BLACK, PieceType.PAWN),
            ("f4", Color.BLACK, PieceType.PAWN),
            ("h4", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.WHITE,
    )


def _drift_position_move_110() -> Board:
    """Drift seed around move 110 before final conversion finally accelerated."""

    return _build_board(
        [
            ("c2", Color.WHITE, PieceType.KING),
            ("d2", Color.WHITE, PieceType.ROOK),
            ("c3", Color.WHITE, PieceType.KNIGHT),
            ("b4", Color.WHITE, PieceType.PAWN),
            ("f3", Color.WHITE, PieceType.PAWN),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h3", Color.WHITE, PieceType.PAWN),
            ("c7", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.ROOK),
            ("e6", Color.BLACK, PieceType.BISHOP),
            ("d3", Color.BLACK, PieceType.ROOK),
            ("a6", Color.BLACK, PieceType.PAWN),
            ("c6", Color.BLACK, PieceType.PAWN),
            ("b5", Color.BLACK, PieceType.PAWN),
            ("e5", Color.BLACK, PieceType.PAWN),
            ("f4", Color.BLACK, PieceType.PAWN),
            ("h4", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.WHITE,
    )


def test_strategy9_task0_transcript_fixtures_are_constructible() -> None:
    boards = [
        _opening_knight_tour_seed(),
        _drift_position_move_60(),
        _drift_position_move_70(),
        _drift_position_move_90(),
        _drift_position_move_110(),
    ]
    assert all(board.find_king(Color.WHITE) is not None for board in boards)
    assert all(board.find_king(Color.BLACK) is not None for board in boards)


def test_strategy9_passer_race_fires_in_rook_endgame() -> None:
    board = _build_board(
        [
            ("b2", Color.WHITE, PieceType.KING),
            ("d2", Color.WHITE, PieceType.ROOK),
            ("h2", Color.WHITE, PieceType.ROOK),
            ("f3", Color.WHITE, PieceType.BISHOP),
            ("a4", Color.WHITE, PieceType.PAWN),
            ("b4", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("a8", Color.BLACK, PieceType.ROOK),
            ("d8", Color.BLACK, PieceType.ROOK),
            ("d5", Color.BLACK, PieceType.PAWN),
            ("a6", Color.BLACK, PieceType.PAWN),
            ("b5", Color.BLACK, PieceType.PAWN),
            ("c6", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.BLACK,
    )
    assert _passes_material_gate(board)


def test_strategy9_conversion_rewards_main_passer_advance() -> None:
    board = _build_board(
        [
            ("b2", Color.WHITE, PieceType.KING),
            ("d2", Color.WHITE, PieceType.ROOK),
            ("g7", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.ROOK),
            ("f6", Color.BLACK, PieceType.BISHOP),
            ("d5", Color.BLACK, PieceType.PAWN),
            ("a6", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.BLACK,
    )
    advance = Move(start=sq("d5"), end=sq("d4"))
    context = _conversion_context(board)
    assert context is not None
    assert _passer_advance_bonus(board, advance, context) > 0
    side_push = Move(start=sq("a6"), end=sq("a5"))
    assert _passer_advance_bonus(board, side_push, context) == 0


def test_strategy9_root_prefers_pawn_push_over_shuffle_when_winning() -> None:
    board = _build_board(
        [
            ("b2", Color.WHITE, PieceType.KING),
            ("g7", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.ROOK),
            ("f6", Color.BLACK, PieceType.BISHOP),
            ("d4", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.BLACK,
    )
    pawn_push = Move(start=sq("d4"), end=sq("d3"))
    king_move = Move(start=sq("g7"), end=sq("f7"))
    assert _pawn_structure_change_root_bonus(board, pawn_push, Color.BLACK) > 0
    assert _pawn_structure_change_root_bonus(board, king_move, Color.BLACK) == 0


def test_strategy9_passer_advance_improves_endgame_progress() -> None:
    board = _build_board(
        [
            ("b2", Color.WHITE, PieceType.KING),
            ("d2", Color.WHITE, PieceType.ROOK),
            ("g7", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.ROOK),
            ("f6", Color.BLACK, PieceType.BISHOP),
            ("d4", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.BLACK,
    )
    child = board.clone()
    assert child.apply_legal_move(sq("d4"), sq("d3"))
    assert evaluate_progress(child, 80) > evaluate_progress(board, 80)


def test_strategy9_king_activates_in_heavy_piece_endgame() -> None:
    active_king = _build_board(
        [
            ("b2", Color.WHITE, PieceType.KING),
            ("d2", Color.WHITE, PieceType.ROOK),
            ("e5", Color.BLACK, PieceType.KING),
            ("d6", Color.BLACK, PieceType.ROOK),
            ("f6", Color.BLACK, PieceType.BISHOP),
        ],
        turn=Color.BLACK,
    )
    passive_king = active_king.clone()
    passive_king.set_piece(sq("e5"), None)
    passive_king.set_piece(sq("h7"), create_piece(Color.BLACK, PieceType.KING))
    endgame_phase = 80
    assert _heavy_endgame_king_activity_bonus(
        active_king,
        Color.BLACK,
    ) > _heavy_endgame_king_activity_bonus(passive_king, Color.BLACK)
    assert evaluate_endgame_technique(
        active_king,
        endgame_phase,
    ) < evaluate_endgame_technique(passive_king, endgame_phase)


def test_strategy9_opening_penalises_knight_tour_moves() -> None:
    board = Board()
    board.make_move(sq("b1"), sq("c3"))
    board.make_move(sq("b8"), sq("c6"))
    knight_tour = Move(start=sq("c3"), end=sq("d5"))
    develop = Move(start=sq("g1"), end=sq("f3"))
    assert opening_discipline_order_score(
        board,
        PieceType.KNIGHT,
        knight_tour,
    ) < opening_discipline_order_score(board, PieceType.KNIGHT, develop)


def test_strategy9_opening_allows_settled_knight_repositioning() -> None:
    board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("f1", Color.WHITE, PieceType.ROOK),
            ("d1", Color.WHITE, PieceType.QUEEN),
            ("c3", Color.WHITE, PieceType.KNIGHT),
            ("f3", Color.WHITE, PieceType.KNIGHT),
            ("c4", Color.WHITE, PieceType.BISHOP),
            ("b2", Color.WHITE, PieceType.BISHOP),
            ("g8", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.QUEEN),
        ],
        turn=Color.WHITE,
    )
    move = Move(start=sq("c3"), end=sq("e4"))
    assert not _is_repeated_minor_piece_move(
        board,
        PieceType.KNIGHT,
        move,
        undeveloped=0,
        unsettled_king=False,
    )
