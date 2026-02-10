# Game logic and turn management

from .board import Board
from .move import Move
from typing import List

class Engine:
    def __init__(self):
        self.board = Board()
        self.turn = "white"

    def make_move(self, move: Move) -> None:
        piece = self.board.get_piece(move.start)
        if piece is None:
            raise ValueError(f"No piece at {move.start}")
        if self.turn == "white" and piece.islower():
            raise ValueError("White's turn but moving a black piece")
        if self.turn == "black" and piece.isupper():
            raise ValueError("Black's turn but moving a white piece")
        self.board.apply_move(move)
        if move.promotion:
            # promotion piece must match side
            promo_piece = move.promotion.upper() if self.turn == "white" else move.promotion.lower()
            self.board.set_piece(move.end, promo_piece)
        self.turn = "black" if self.turn == "white" else "white"

    def is_game_over(self) -> bool:
        return False

    # --------------------------------------------------------------
    # Move generation (very light – enough for our current tasks)
    # --------------------------------------------------------------
    def generate_moves(self, color: str) -> List[Move]:
        moves: List[Move] = []
        side = "white" if color == "white" else "black"
        def get_piece_at(coord: str):
            return self.board.get_piece(coord)
        for rank in "87654321":
            for file in "abcdefgh":
                coord = file + rank
                piece = get_piece_at(coord)
                if not piece:
                    continue
                if (side == "white" and piece.isupper()) or (side == "black" and piece.islower()):
                    moves.extend(self._generate_piece_moves(coord, piece))
        # castling (simplified)
        if color == "white":
            if self.board.castling_rights["K"] and all(self.board.get_piece(c) is None for c in ["f1", "g1"]):
                moves.append(Move("e1", "g1"))
            if self.board.castling_rights["Q"] and all(self.board.get_piece(c) is None for c in ["d1", "c1", "b1"]):
                moves.append(Move("e1", "c1"))
        else:
            if self.board.castling_rights["k"] and all(self.board.get_piece(c) is None for c in ["f8", "g8"]):
                moves.append(Move("e8", "g8"))
            if self.board.castling_rights["q"] and all(self.board.get_piece(c) is None for c in ["d8", "c8", "b8"]):
                moves.append(Move("e8", "c8"))
        return moves

    def _generate_piece_moves(self, coord: str, piece: str) -> List[Move]:
        moves: List[Move] = []
        direction = -1 if piece.isupper() else 1
        file, rank = coord[0], int(coord[1])
        file_idx = ord(file) - ord('a')
        rank_idx = int(rank)
        def on_board(f: int, r: int):
            return 0 <= f < 8 and 1 <= r <= 8
        if piece.upper() == "P":
            fwd_rank = rank + direction
            fwd_coord = f"{file}{fwd_rank}"
            if on_board(file_idx, fwd_rank) and self.board.get_piece(fwd_coord) is None:
                if fwd_rank == (8 if piece.isupper() else 1):
                    for promo in ["Q", "R", "B", "N"]:
                        moves.append(Move(coord, fwd_coord, promotion=promo))
                else:
                    moves.append(Move(coord, fwd_coord))
                start_rank = 2 if piece.isupper() else 7
                if rank == start_rank:
                    double_rank = rank + 2 * direction
                    double_coord = f"{file}{double_rank}"
                    if self.board.get_piece(double_coord) is None:
                        moves.append(Move(coord, double_coord))
            for df in [-1, 1]:
                fwd_file_idx = file_idx + df
                if on_board(fwd_file_idx, fwd_rank):
                    cap_coord = f"{chr(ord('a') + fwd_file_idx)}{fwd_rank}"
                    target = self.board.get_piece(cap_coord)
                    if target and (target.islower() != piece.islower()):
                        if fwd_rank == (8 if piece.isupper() else 1):
                            for promo in ["Q", "R", "B", "N"]:
                                moves.append(Move(coord, cap_coord, promotion=promo))
                        else:
                            moves.append(Move(coord, cap_coord))
            if self.board.ep_square:
                ep_file, ep_rank = self.board.ep_square[0], int(self.board.ep_square[1])
                if ep_file == file and ep_rank == fwd_rank:
                    moves.append(Move(coord, self.board.ep_square))
        else:
            if piece.upper() == "K":
                for df in [-1, 0, 1]:
                    for dr in [-1, 0, 1]:
                        if df == 0 and dr == 0:
                            continue
                        fwd_file_idx = file_idx + df
                        fwd_rank = rank_idx + dr
                        if on_board(fwd_file_idx, fwd_rank):
                            dest = f"{chr(ord('a') + fwd_file_idx)}{fwd_rank}"
                            target = self.board.get_piece(dest)
                            if not target or (target.islower() != piece.islower()):
                                moves.append(Move(coord, dest))
        return moves
