from simple_chess.board import Board
from simple_chess.color import Color
from simple_chess.game import Game
from simple_chess.position import Position


def main():
    board = Board()
    board.setup_initial_position()
    players = [Color.WHITE, Color.BLACK]
    game = Game(board, players)

    game.render_game()

    start = Position(6, 4)
    end = Position(4, 4)
    piece = board.piece_at(start)
    print("Peça em (6,4):", type(piece), piece.color if piece else None)
    print("Movimentos calculados:", piece.valid_moves(start, board) if piece else None)

    moved = game.make_move(start, end)
    print("Moveu?", moved)

    print("-" * 30)
    game.render_game()


if __name__ == '__main__':
    main()

