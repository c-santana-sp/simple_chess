"""Pacote chess_view — visualização e CLI do xadrez, totalmente desacoplado da engine."""

from chess_view.renderer import Renderer
from chess_view.rich_view import RichView

__all__ = ["Renderer", "RichView"]
