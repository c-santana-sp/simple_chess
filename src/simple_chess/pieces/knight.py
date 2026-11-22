from typing import TYPE_CHECKING

from simple_chess.pieces.piece import Piece
from simple_chess.position import Position


if TYPE_CHECKING:
	from simple_chess.board import Board

class Knight(Piece):
	symbol = "n"
	def valid_moves(self, pos: Position, board: "Board") -> list[Position]:
		pass