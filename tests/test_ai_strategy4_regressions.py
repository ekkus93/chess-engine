"""Strategy 4 regressions for self-restraint and conversion discipline."""

from chess_game.chess import ai
from chess_game.chess.ai import get_best_move, get_evaluation_breakdown, position_key
from chess_game.chess.ai_search_helpers import RepetitionPolicy, repetition_score
from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import LegalMove
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq
from tests.test_ai_quality import _move_order_score


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


def test_king_safety_penalizes_g_pawn_recapture_that_opens_king() -> None:
    """An unforced g-pawn recapture should lose shelter and pawn-structure credit."""

    sheltered_board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("d1", Color.WHITE, PieceType.QUEEN),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("f1", Color.WHITE, PieceType.ROOK),
            ("f2", Color.WHITE, PieceType.PAWN),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("e4", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.QUEEN),
            ("c5", Color.BLACK, PieceType.BISHOP),
            ("b6", Color.BLACK, PieceType.KNIGHT),
        ]
    )
    opened_board = sheltered_board.clone()
    opened_board.clear_square(sq("g2"))
    opened_board.set_piece(sq("f3"), create_piece(Color.WHITE, PieceType.PAWN))

    sheltered_breakdown = get_evaluation_breakdown(sheltered_board)
    opened_breakdown = get_evaluation_breakdown(opened_board)

    assert sheltered_breakdown["king_safety"] > opened_breakdown["king_safety"]
    assert sheltered_breakdown["pawn_structure"] > opened_breakdown["pawn_structure"]


def test_development_penalizes_flank_queen_sortie_over_center_tension() -> None:
    """Early queen flank sorties should lose to keeping the queen central."""

    centered_board = Board()
    centered_board.clear_square(sq("e2"))
    centered_board.set_piece(sq("e3"), create_piece(Color.WHITE, PieceType.PAWN))
    flank_sortie_board = centered_board.clone()
    flank_sortie_board.clear_square(sq("d1"))
    flank_sortie_board.set_piece(sq("h5"), create_piece(Color.WHITE, PieceType.QUEEN))

    assert (
        get_evaluation_breakdown(centered_board)["development"]
        > get_evaluation_breakdown(flank_sortie_board)["development"]
    )


def test_search_rejects_rook_lift_that_drops_back_rank_safety() -> None:
    """Under pressure, luft should beat a rook lift that abandons the back rank."""

    board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("d1", Color.WHITE, PieceType.QUEEN),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("h1", Color.WHITE, PieceType.ROOK),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("h4", Color.BLACK, PieceType.QUEEN),
            ("e8", Color.BLACK, PieceType.ROOK),
        ]
    )

    assert get_best_move(board, depth=1) == LegalMove(start=sq("g2"), end=sq("g3"))


def test_king_breakdowns_penalize_middlegame_king_drift_from_defenders() -> None:
    """A middlegame king drift should lose safety and exposure credit."""

    coordinated_board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("e2", Color.WHITE, PieceType.QUEEN),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("f1", Color.WHITE, PieceType.ROOK),
            ("f2", Color.WHITE, PieceType.PAWN),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h3", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.QUEEN),
            ("h8", Color.BLACK, PieceType.ROOK),
        ]
    )
    drifted_board = coordinated_board.clone()
    drifted_board.clear_square(sq("g1"))
    drifted_board.clear_square(sq("h3"))
    drifted_board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.KING))
    drifted_board.set_piece(sq("g3"), create_piece(Color.WHITE, PieceType.PAWN))

    coordinated_breakdown = get_evaluation_breakdown(coordinated_board)
    drifted_breakdown = get_evaluation_breakdown(drifted_board)

    assert coordinated_breakdown["king_safety"] > drifted_breakdown["king_safety"]
    assert coordinated_breakdown["king_exposure"] > drifted_breakdown["king_exposure"]


def test_quiet_move_order_prefers_sealing_entry_file_before_harmless_check() -> None:
    """Stopping a file invasion should beat a cosmetic attack elsewhere."""

    board = _build_board(
        [
            ("d1", Color.WHITE, PieceType.KING),
            ("a2", Color.WHITE, PieceType.ROOK),
            ("e2", Color.WHITE, PieceType.QUEEN),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.ROOK),
        ]
    )

    seal_entry = ai.Move(start=sq("a2"), end=sq("d2"))
    cosmetic_check = ai.Move(start=sq("e2"), end=sq("e8"))

    assert _move_order_score(board, seal_entry, None) > _move_order_score(
        board,
        cosmetic_check,
        None,
    )


def test_quiet_move_order_prefers_stopping_knight_outpost_before_pawn_push() -> None:
    """Prophylaxis against a knight outpost should beat a loose flank advance."""

    board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("d1", Color.WHITE, PieceType.QUEEN),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("f1", Color.WHITE, PieceType.ROOK),
            ("c3", Color.WHITE, PieceType.KNIGHT),
            ("f3", Color.WHITE, PieceType.KNIGHT),
            ("d3", Color.WHITE, PieceType.PAWN),
            ("e4", Color.WHITE, PieceType.PAWN),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("f6", Color.BLACK, PieceType.KNIGHT),
            ("d7", Color.BLACK, PieceType.PAWN),
            ("e7", Color.BLACK, PieceType.PAWN),
        ]
    )

    stop_outpost = ai.Move(start=sq("g2"), end=sq("g3"))
    flank_push = ai.Move(start=sq("h2"), end=sq("h4"))

    assert _move_order_score(board, stop_outpost, None) > _move_order_score(
        board,
        flank_push,
        None,
    )


def test_quiet_move_order_prefers_rook_centralization_over_side_check() -> None:
    """Improving the rook should beat a low-value side check."""

    board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("e2", Color.WHITE, PieceType.QUEEN),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.ROOK),
        ]
    )

    centralize = ai.Move(start=sq("a1"), end=sq("d1"))
    side_check = ai.Move(start=sq("a1"), end=sq("a8"))

    assert _move_order_score(board, centralize, None) > _move_order_score(
        board,
        side_check,
        None,
    )


def test_quiet_move_order_prefers_bishop_reroute_over_loose_queen_poke() -> None:
    """A bishop reroute should beat a loose queen poke with no new pressure."""

    board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("d1", Color.WHITE, PieceType.QUEEN),
            ("c1", Color.WHITE, PieceType.BISHOP),
            ("f3", Color.WHITE, PieceType.KNIGHT),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("f6", Color.BLACK, PieceType.KNIGHT),
            ("g7", Color.BLACK, PieceType.PAWN),
            ("h7", Color.BLACK, PieceType.PAWN),
        ]
    )

    bishop_reroute = ai.Move(start=sq("c1"), end=sq("b2"))
    queen_poke = ai.Move(start=sq("d1"), end=sq("h5"))

    assert _move_order_score(board, bishop_reroute, None) > _move_order_score(
        board,
        queen_poke,
        None,
    )


def test_pawn_structure_penalizes_loose_shelter_pawn_advances() -> None:
    """Pawn structure should dislike castled-king shelter pawns racing forward."""

    stable_board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("d1", Color.WHITE, PieceType.QUEEN),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("f1", Color.WHITE, PieceType.ROOK),
            ("f2", Color.WHITE, PieceType.PAWN),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("d4", Color.WHITE, PieceType.PAWN),
            ("e4", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.QUEEN),
        ]
    )
    loose_board = stable_board.clone()
    loose_board.clear_square(sq("g2"))
    loose_board.clear_square(sq("h2"))
    loose_board.set_piece(sq("g4"), create_piece(Color.WHITE, PieceType.PAWN))
    loose_board.set_piece(sq("h4"), create_piece(Color.WHITE, PieceType.PAWN))

    assert (
        get_evaluation_breakdown(stable_board)["pawn_structure"]
        > get_evaluation_breakdown(loose_board)["pawn_structure"]
    )


def test_pawn_structure_prefers_central_integrity_over_side_grab_structure() -> None:
    """Holding the center should beat a side-grab structure with retreated central pawns."""

    central_board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("d1", Color.WHITE, PieceType.QUEEN),
            ("c3", Color.WHITE, PieceType.KNIGHT),
            ("f3", Color.WHITE, PieceType.KNIGHT),
            ("c4", Color.WHITE, PieceType.BISHOP),
            ("e2", Color.WHITE, PieceType.BISHOP),
            ("d4", Color.WHITE, PieceType.PAWN),
            ("e4", Color.WHITE, PieceType.PAWN),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.QUEEN),
        ]
    )
    side_grab_board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("h5", Color.WHITE, PieceType.QUEEN),
            ("c3", Color.WHITE, PieceType.KNIGHT),
            ("f3", Color.WHITE, PieceType.KNIGHT),
            ("c4", Color.WHITE, PieceType.BISHOP),
            ("e2", Color.WHITE, PieceType.BISHOP),
            ("d2", Color.WHITE, PieceType.PAWN),
            ("e3", Color.WHITE, PieceType.PAWN),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.QUEEN),
        ]
    )

    assert (
        get_evaluation_breakdown(central_board)["pawn_structure"]
        > get_evaluation_breakdown(side_grab_board)["pawn_structure"]
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
