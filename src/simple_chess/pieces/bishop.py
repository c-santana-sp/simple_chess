from typing import TYPE_CHECKING

from simple_chess.pieces.piece import Piece, slide_moves
from simple_chess.position import Position

if TYPE_CHECKING:
	from simple_chess.board import Board


class Bishop(Piece):
	symbol = "b"

	def valid_moves(self, pos: Position, board: "Board") -> list[Position]:
		# 4 direções diagonais
		directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
		return slide_moves(pos, board, self.color, directions)