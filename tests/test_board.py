"""Testes para Board."""

from simple_chess.color import Color
from simple_chess.pieces.bishop import Bishop
from simple_chess.pieces.king import King
from simple_chess.pieces.knight import Knight
from simple_chess.pieces.pawn import Pawn
from simple_chess.pieces.queen import Queen
from simple_chess.pieces.rook import Rook
from simple_chess.position import Position


class TestBoardBasics:
    def test_empty_board(self, empty_board):
        """Tabuleiro vazio deve ter todas as casas None."""
        for row in range(8):
            for col in range(8):
                assert empty_board.piece_at(Position(row, col)) is None

    def test_in_bounds(self, empty_board):
        """Verificar limites do tabuleiro."""
        assert empty_board.in_bounds(Position(0, 0))
        assert empty_board.in_bounds(Position(7, 7))
        assert empty_board.in_bounds(Position(3, 3))
        assert not empty_board.in_bounds(Position(-1, 0))
        assert not empty_board.in_bounds(Position(8, 0))
        assert not empty_board.in_bounds(Position(0, -1))
        assert not empty_board.in_bounds(Position(0, 8))

    def test_piece_at_out_of_bounds(self, empty_board):
        """piece_at fora dos limites deve retornar None."""
        assert empty_board.piece_at(Position(-1, 0)) is None
        assert empty_board.piece_at(Position(8, 0)) is None

    def test_is_empty(self, empty_board):
        """Casas vazias devem retornar True."""
        assert empty_board.is_empty(Position(3, 3))
        assert not empty_board.is_empty(Position(-1, 0))

    def test_place_and_piece_at(self, empty_board):
        """Colocar e recuperar peça."""
        pawn = Pawn(Color.WHITE)
        empty_board.place(Position(3, 3), pawn)
        assert empty_board.piece_at(Position(3, 3)) is pawn
        assert empty_board.is_empty(Position(3, 3)) is False

    def test_move_piece(self, empty_board):
        """Mover peça de uma casa para outra."""
        pawn = Pawn(Color.WHITE)
        empty_board.place(Position(6, 4), pawn)
        captured = empty_board.move(Position(6, 4), Position(4, 4))
        assert captured is None
        assert empty_board.piece_at(Position(4, 4)) is pawn
        assert empty_board.piece_at(Position(6, 4)) is None
        assert pawn.has_moved

    def test_move_captures_piece(self, empty_board):
        """Mover peça para casa com inimigo deve capturar."""
        white_pawn = Pawn(Color.WHITE)
        black_pawn = Pawn(Color.BLACK)
        empty_board.place(Position(6, 4), white_pawn)
        empty_board.place(Position(4, 4), black_pawn)
        captured = empty_board.move(Position(6, 4), Position(4, 4))
        assert captured is black_pawn
        assert empty_board.piece_at(Position(4, 4)) is white_pawn
        assert empty_board.piece_at(Position(6, 4)) is None

    def test_move_no_piece_raises(self, empty_board):
        """Mover de casa vazia deve levantar erro."""
        try:
            empty_board.move(Position(3, 3), Position(4, 4))
            assert False, "Deveria ter levantado ValueError"
        except ValueError:
            pass

    def test_has_enemy(self, empty_board):
        """Verificar peça inimiga."""
        white_pawn = Pawn(Color.WHITE)
        black_pawn = Pawn(Color.BLACK)
        empty_board.place(Position(3, 3), white_pawn)
        empty_board.place(Position(4, 4), black_pawn)
        assert empty_board.has_enemy(Position(4, 4), Color.WHITE)
        assert not empty_board.has_enemy(Position(3, 3), Color.WHITE)
        assert not empty_board.has_enemy(Position(4, 4), Color.BLACK)

    def test_is_square_light(self, empty_board):
        """Verificar cores das casas."""
        # a1 (7,0) é escura, h1 (7,7) é clara
        assert not empty_board.is_square_light(Position(7, 0))
        assert empty_board.is_square_light(Position(7, 7))
        assert empty_board.is_square_light(Position(0, 0))
        assert not empty_board.is_square_light(Position(0, 1))


class TestBoardSetup:
    def test_initial_position_white_pawns(self, initial_board):
        """Peões brancos na fileira 6."""
        for col in range(8):
            piece = initial_board.piece_at(Position(6, col))
            assert isinstance(piece, Pawn)
            assert piece.color == Color.WHITE

    def test_initial_position_black_pawns(self, initial_board):
        """Peões pretos na fileira 1."""
        for col in range(8):
            piece = initial_board.piece_at(Position(1, col))
            assert isinstance(piece, Pawn)
            assert piece.color == Color.BLACK

    def test_initial_position_white_back_rank(self, initial_board):
        """Peças brancas na fileira 7."""
        expected = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for col, expected_class in enumerate(expected):
            piece = initial_board.piece_at(Position(7, col))
            assert isinstance(piece, expected_class)
            assert piece.color == Color.WHITE

    def test_initial_position_black_back_rank(self, initial_board):
        """Peças pretas na fileira 0."""
        expected = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for col, expected_class in enumerate(expected):
            piece = initial_board.piece_at(Position(0, col))
            assert isinstance(piece, expected_class)
            assert piece.color == Color.BLACK

    def test_initial_position_empty_rows(self, initial_board):
        """Fileiras 2-5 devem estar vazias."""
        for row in range(2, 6):
            for col in range(8):
                assert initial_board.piece_at(Position(row, col)) is None

    def test_total_pieces(self, initial_board):
        """32 peças no total."""
        count = 0
        for row in range(8):
            for col in range(8):
                if initial_board.piece_at(Position(row, col)) is not None:
                    count += 1
        assert count == 32


class TestBoardFindKing:
    def test_find_white_king_initial(self, initial_board):
        """Rei branco em e1 (7, 4)."""
        king_pos = initial_board.find_king(Color.WHITE)
        assert king_pos == Position(7, 4)

    def test_find_black_king_initial(self, initial_board):
        """Rei preto em e8 (0, 4)."""
        king_pos = initial_board.find_king(Color.BLACK)
        assert king_pos == Position(0, 4)

    def test_find_king_after_move(self, initial_board):
        """Rei após mover."""
        king = initial_board.piece_at(Position(7, 4))
        initial_board.place(Position(7, 4), None)
        initial_board.place(Position(7, 5), king)
        king_pos = initial_board.find_king(Color.WHITE)
        assert king_pos == Position(7, 5)

    def test_find_king_not_found(self, empty_board):
        """Rei não encontrado em tabuleiro vazio."""
        assert empty_board.find_king(Color.WHITE) is None


class TestBoardIsCheck:
    def test_no_check_initial(self, initial_board):
        """Nenhum rei em xeque na posição inicial."""
        assert not initial_board.is_check(Color.WHITE)
        assert not initial_board.is_check(Color.BLACK)

    def test_check_by_queen(self, empty_board):
        """Xeque por Rainha na mesma coluna."""
        white_king = King(Color.WHITE)
        black_queen = Queen(Color.BLACK)
        empty_board.place(Position(7, 4), white_king)
        empty_board.place(Position(0, 4), black_queen)
        assert empty_board.is_check(Color.WHITE)

    def test_check_by_queen_blocked(self, empty_board):
        """Xeque bloqueado por peça amiga."""
        white_king = King(Color.WHITE)
        black_queen = Queen(Color.BLACK)
        white_pawn = Pawn(Color.WHITE)
        empty_board.place(Position(7, 4), white_king)
        empty_board.place(Position(0, 4), black_queen)
        empty_board.place(Position(4, 4), white_pawn)
        assert not empty_board.is_check(Color.WHITE)

    def test_check_by_rook(self, empty_board):
        """Xeque por Torre na mesma linha."""
        white_king = King(Color.WHITE)
        black_rook = Rook(Color.BLACK)
        empty_board.place(Position(7, 4), white_king)
        empty_board.place(Position(7, 0), black_rook)
        assert empty_board.is_check(Color.WHITE)

    def test_check_by_bishop(self, empty_board):
        """Xeque por Bispo na diagonal."""
        white_king = King(Color.WHITE)
        black_bishop = Bishop(Color.BLACK)
        empty_board.place(Position(7, 4), white_king)
        # Bispo em a1 (7,0) ataca diagonal até h8 (0,7)
        # e1 (7,4) está na diagonal a1-h8? 7-4=3, 0-7=-7 → não
        # Bispo em c3 (5,2): diagonal para e1 (7,4)? 7-5=2, 4-2=2 → sim!
        empty_board.place(Position(5, 2), black_bishop)
        assert empty_board.is_check(Color.WHITE)

    def test_check_by_knight(self, empty_board):
        """Xeque por Cavalo."""
        white_king = King(Color.WHITE)
        black_knight = Knight(Color.BLACK)
        empty_board.place(Position(7, 4), white_king)
        empty_board.place(Position(5, 5), black_knight)
        assert empty_board.is_check(Color.WHITE)

    def test_check_by_pawn(self, empty_board):
        """Xeque por Peão."""
        white_king = King(Color.WHITE)
        black_pawn = Pawn(Color.BLACK)
        empty_board.place(Position(7, 4), white_king)
        empty_board.place(Position(6, 3), black_pawn)
        assert empty_board.is_check(Color.WHITE)

    def test_check_by_king(self, empty_board):
        """Xeque por Rei adjacente."""
        white_king = King(Color.WHITE)
        black_king = King(Color.BLACK)
        empty_board.place(Position(7, 4), white_king)
        empty_board.place(Position(6, 5), black_king)
        assert empty_board.is_check(Color.WHITE)

    def test_no_check_king_missing(self, empty_board):
        """Sem rei não há xeque."""
        assert not empty_board.is_check(Color.WHITE)
