from typing import TYPE_CHECKING

from simple_chess.pieces.piece import Piece, slide_moves
from simple_chess.position import Position


if TYPE_CHECKING:
	from simple_chess.board import Board

class Queen(Piece):
	symbol = "q"

	def valid_moves(self, pos: Position, board: "Board") -> list[Position]:
		# 8 direções (combina Bispo + Torre)
		directions = [
			(-1, -1), (-1, 0), (-1, 1),
			(0, -1),           (0, 1),
			(1, -1),  (1, 0),  (1, 1),
		]
		return slide_moves(pos, board, self.color, directions)