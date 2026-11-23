from typing import TYPE_CHECKING

from simple_chess.pieces.piece import Piece, slide_moves
from simple_chess.position import Position


if TYPE_CHECKING:
	from simple_chess.board import Board

class Rook(Piece):
	symbol = "r"

	def valid_moves(self, pos: Position, board: "Board") -> list[Position]:
		# 4 direções ortogonais (cima, baixo, esquerda, direita)
		directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
		return slide_moves(pos, board, self.color, directions)