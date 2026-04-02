"""Debug en passant."""
from chess_game.chess.board import Board, create_piece
from chess_game.chess.constants import ROW_3, ROW_2, COL_D, COL_E, Color, PieceType
from chess_game.chess.constants import ConstantSquare

board = Board()

row3_colE = ConstantSquare(row=ROW_3, col=COL_E)
row2_colD = ConstantSquare(row=ROW_2, col=COL_D)

board.set_piece(row3_colE, create_piece(Color.WHITE, PieceType.PAWN))
board.set_piece(row2_colD, create_piece(Color.BLACK, PieceType.PAWN))

board.turn = Color.BLACK
print('Before move')
result = board.make_move(row2_colD, row3_colE)
print('Move result:', result)
print('en_passant_target:', board.en_passant_target)
