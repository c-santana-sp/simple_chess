"""Fixtures compartilhadas para todos os testes da engine."""

import pytest

from simple_chess.board import Board
from simple_chess.color import Color
from simple_chess.game import Game


def create_empty_board() -> Board:
    """Cria um tabuleiro vazio."""
    return Board()


def create_initial_board() -> Board:
    """Cria um tabuleiro com posição inicial."""
    board = Board()
    board.setup_initial_position()
    return board


def create_game() -> Game:
    """Cria um jogo com posição inicial."""
    board = create_initial_board()
    return Game(board, [Color.WHITE, Color.BLACK])


@pytest.fixture
def empty_board():
    return create_empty_board()


@pytest.fixture
def initial_board():
    return create_initial_board()


@pytest.fixture
def game():
    return create_game()
