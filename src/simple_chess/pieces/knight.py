from typing import TYPE_CHECKING

from simple_chess.pieces.piece import Piece
from simple_chess.position import Position


if TYPE_CHECKING:
	from simple_chess.board import Board

class Knight(Piece):
	symbol = "n"

	def valid_moves(self, pos: Position, board: "Board") -> list[Position]:
		# 8 movimentos em L do cavalo
		offsets = [
			(-2, -1), (-2, 1), (-1, -2), (-1, 2),
			(1, -2), (1, 2), (2, -1), (2, 1),
		]
		moves = []
		for dr, dc in offsets:
			new_pos = Position(pos.row + dr, pos.col + dc)
			if board.in_bounds(new_pos):
				if board.is_empty(new_pos) or board.has_enemy(new_pos, self.color):
					moves.append(new_pos)
		return moves