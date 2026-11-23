from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from simple_chess.color import Color
from simple_chess.position import Position

if TYPE_CHECKING:
    from simple_chess.board import Board


def slide_moves(
    pos: Position, board: "Board", color: Color, directions: list[tuple[int, int]]
) -> list[Position]:
    """Calcula movimentos deslizantes nas direções dadas.

    Para cada direção, avança casa a casa até encontrar a borda ou uma peça.
    Se a peça encontrada for inimiga, ela pode ser capturada (última casa).
    Se for amiga, a direção para sem incluir essa casa.
    """
    moves = []
    for dr, dc in directions:
        row, col = pos.row + dr, pos.col + dc
        while 0 <= row < 8 and 0 <= col < 8:
            current = Position(row, col)
            if board.is_empty(current):
                moves.append(current)
            elif board.has_enemy(current, color):
                moves.append(current)
                break
            else:
                break
            row += dr
            col += dc
    return moves


class Piece(ABC):
    symbol: str = ""

    def __init__(self, color: Color, has_moved: bool = False):
        self.color = color
        self.has_moved = has_moved

    @abstractmethod
    def valid_moves(self, pos: Position, board: "Board") -> list[Position]: ...

    def __str__(self) -> str:
        char = self.symbol or "?"  # fallback seguro: nunca retorna None
        return char.upper() if self.color == Color.WHITE else char.lower()
