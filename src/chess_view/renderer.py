"""Protocolo de renderização — desacopla a engine da visualização."""

from abc import ABC, abstractmethod

from simple_chess.game import Game
from simple_chess.position import Position


class Renderer(ABC):
    """Interface que qualquer visualização do jogo deve implementar."""

    @abstractmethod
    def render(
        self,
        game: Game,
        selected: Position | None = None,
        valid_moves: list[Position] | None = None,
    ) -> None:
        """Renderiza o estado atual do jogo.

        Args:
            game: Estado atual do jogo.
            selected: Casa selecionada pelo jogador (opcional).
            valid_moves: Jogadas válidas para a peça selecionada (opcional).
        """
        ...
