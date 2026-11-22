from typing import TYPE_CHECKING

from simple_chess.color import Color
from simple_chess.pieces.piece import Piece
from simple_chess.position import Position

if TYPE_CHECKING:
	from simple_chess.board import Board


class Pawn(Piece):
	symbol = "p"

	def valid_moves(self, pos: Position, board: "Board") -> list[Position]:
		# Assumindo linha 6 para peões brancos subindo (-1) e linha 1 para pretos descendo (+1)
		direction = -1 if self.color == Color.WHITE else 1
		start_row = 6 if self.color == Color.WHITE else 1
		moves: list[Position] = []

		one_step = Position(pos.row + direction, pos.col)
		if board.in_bounds(one_step) and board.is_empty(one_step):
			moves.append(one_step)

			two_steps = Position(pos.row + 2 * direction, pos.col)
			if pos.row == start_row and board.is_empty(two_steps):
				moves.append(two_steps)

		for d_col in (-1, 1):
			diag = Position(pos.row + direction, pos.col + d_col)
			if board.in_bounds(diag) and board.has_enemy(diag, self.color):
				moves.append(diag)

		print(moves)
		return moves