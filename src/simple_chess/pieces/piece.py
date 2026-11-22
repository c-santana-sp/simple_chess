from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from simple_chess.color import Color
from simple_chess.position import Position


if TYPE_CHECKING:
	from simple_chess.board import Board

class Piece(ABC):
	symbol: str = ""

	def __init__(self, color: Color, has_moved: bool = False):
		self.color = color
		self.has_moved = has_moved

	@abstractmethod
	def valid_moves(self, pos: Position, board: "Board") -> list[Position]:
		...

	def __str__(self) -> str:
		char = self.symbol or "?"  # fallback seguro: nunca retorna None
		return char.upper() if self.color == Color.WHITE else char.lower()