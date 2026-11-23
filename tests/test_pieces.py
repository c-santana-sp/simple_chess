"""Testes para as peças individuais."""
from simple_chess.board import Board
from simple_chess.color import Color
from simple_chess.pieces.bishop import Bishop
from simple_chess.pieces.king import King
from simple_chess.pieces.knight import Knight
from simple_chess.pieces.pawn import Pawn
from simple_chess.pieces.queen import Queen
from simple_chess.pieces.rook import Rook
from simple_chess.position import Position


class TestPawn:
	def test_white_pawn_one_step(self, empty_board):
		"""Peão branco avança 1 casa."""
		pawn = Pawn(Color.WHITE)
		empty_board.place(Position(6, 4), pawn)
		moves = pawn.valid_moves(Position(6, 4), empty_board)
		assert Position(5, 4) in moves

	def test_white_pawn_two_steps(self, empty_board):
		"""Peão branco avança 2 casas desde a posição inicial."""
		pawn = Pawn(Color.WHITE)
		empty_board.place(Position(6, 4), pawn)
		moves = pawn.valid_moves(Position(6, 4), empty_board)
		assert Position(4, 4) in moves

	def test_white_pawn_two_steps_blocked(self, empty_board):
		"""Peão não avança 2 casas se há peça no caminho."""
		pawn = Pawn(Color.WHITE)
		blocker = Pawn(Color.BLACK)
		empty_board.place(Position(6, 4), pawn)
		empty_board.place(Position(5, 4), blocker)
		moves = pawn.valid_moves(Position(6, 4), empty_board)
		assert Position(4, 4) not in moves
		assert Position(5, 4) not in moves

	def test_white_pawn_one_step_blocked(self, empty_board):
		"""Peão não avança 1 casa se há peça no caminho."""
		pawn = Pawn(Color.WHITE)
		blocker = Pawn(Color.BLACK)
		empty_board.place(Position(6, 4), pawn)
		empty_board.place(Position(5, 4), blocker)
		moves = pawn.valid_moves(Position(6, 4), empty_board)
		assert Position(5, 4) not in moves

	def test_white_pawn_capture_diagonal(self, empty_board):
		"""Peão branco captura na diagonal."""
		pawn = Pawn(Color.WHITE)
		enemy = Pawn(Color.BLACK)
		empty_board.place(Position(6, 4), pawn)
		empty_board.place(Position(5, 3), enemy)
		moves = pawn.valid_moves(Position(6, 4), empty_board)
		assert Position(5, 3) in moves

	def test_white_pawn_capture_right(self, empty_board):
		"""Peão branco captura na diagonal direita."""
		pawn = Pawn(Color.WHITE)
		enemy = Pawn(Color.BLACK)
		empty_board.place(Position(6, 4), pawn)
		empty_board.place(Position(5, 5), enemy)
		moves = pawn.valid_moves(Position(6, 4), empty_board)
		assert Position(5, 5) in moves

	def test_white_pawn_no_capture_straight(self, empty_board):
		"""Peão não captura na frente."""
		pawn = Pawn(Color.WHITE)
		enemy = Pawn(Color.BLACK)
		empty_board.place(Position(6, 4), pawn)
		empty_board.place(Position(5, 4), enemy)
		moves = pawn.valid_moves(Position(6, 4), empty_board)
		assert Position(5, 4) not in moves

	def test_white_pawn_no_capture_empty_diagonal(self, empty_board):
		"""Peão não captura casa vazia na diagonal."""
		pawn = Pawn(Color.WHITE)
		empty_board.place(Position(6, 4), pawn)
		moves = pawn.valid_moves(Position(6, 4), empty_board)
		assert Position(5, 3) not in moves
		assert Position(5, 5) not in moves

	def test_black_pawn_one_step(self, empty_board):
		"""Peão preto avança 1 casa."""
		pawn = Pawn(Color.BLACK)
		empty_board.place(Position(1, 4), pawn)
		moves = pawn.valid_moves(Position(1, 4), empty_board)
		assert Position(2, 4) in moves

	def test_black_pawn_two_steps(self, empty_board):
		"""Peão preto avança 2 casas desde a posição inicial."""
		pawn = Pawn(Color.BLACK)
		empty_board.place(Position(1, 4), pawn)
		moves = pawn.valid_moves(Position(1, 4), empty_board)
		assert Position(3, 4) in moves

	def test_black_pawn_capture(self, empty_board):
		"""Peão preto captura na diagonal."""
		pawn = Pawn(Color.BLACK)
		enemy = Pawn(Color.WHITE)
		empty_board.place(Position(1, 4), pawn)
		empty_board.place(Position(2, 3), enemy)
		moves = pawn.valid_moves(Position(1, 4), empty_board)
		assert Position(2, 3) in moves

	def test_pawn_not_from_start_one_step(self, empty_board):
		"""Peão fora da posição inicial avança apenas 1 casa."""
		pawn = Pawn(Color.WHITE)
		empty_board.place(Position(4, 4), pawn)
		moves = pawn.valid_moves(Position(4, 4), empty_board)
		assert Position(3, 4) in moves
		assert Position(2, 4) not in moves

	def test_pawn_at_edge(self, empty_board):
		"""Peão na borda tem menos movimentos."""
		pawn = Pawn(Color.WHITE)
		empty_board.place(Position(6, 0), pawn)
		moves = pawn.valid_moves(Position(6, 0), empty_board)
		assert Position(5, 0) in moves
		assert Position(4, 0) in moves
		# Não pode capturar à esquerda
		assert Position(5, -1) not in moves

	def test_pawn_blocked_by_friend(self, empty_board):
		"""Peão bloqueado por peça amiga."""
		pawn = Pawn(Color.WHITE)
		friend = Pawn(Color.WHITE)
		empty_board.place(Position(6, 4), pawn)
		empty_board.place(Position(5, 4), friend)
		moves = pawn.valid_moves(Position(6, 4), empty_board)
		assert Position(5, 4) not in moves
		assert Position(4, 4) not in moves


class TestKnight:
	def test_knight_center_moves(self, empty_board):
		"""Cavalo no centro tem 8 movimentos."""
		knight = Knight(Color.WHITE)
		empty_board.place(Position(3, 3), knight)
		moves = knight.valid_moves(Position(3, 3), empty_board)
		assert len(moves) == 8

	def test_knight_corner_moves(self, empty_board):
		"""Cavalo no canto tem 2 movimentos."""
		knight = Knight(Color.WHITE)
		empty_board.place(Position(0, 0), knight)
		moves = knight.valid_moves(Position(0, 0), empty_board)
		assert len(moves) == 2
		assert Position(1, 2) in moves
		assert Position(2, 1) in moves

	def test_knight_edge_moves(self, empty_board):
		"""Cavalo na borda tem 4 movimentos."""
		knight = Knight(Color.WHITE)
		empty_board.place(Position(0, 3), knight)
		moves = knight.valid_moves(Position(0, 3), empty_board)
		assert len(moves) == 4

	def test_knight_blocked_by_friend(self, empty_board):
		"""Cavalo não pode pular peça amiga."""
		knight = Knight(Color.WHITE)
		friend = Pawn(Color.WHITE)
		empty_board.place(Position(3, 3), knight)
		empty_board.place(Position(1, 2), friend)
		moves = knight.valid_moves(Position(3, 3), empty_board)
		assert Position(1, 2) not in moves

	def test_knight_captures_enemy(self, empty_board):
		"""Cavalo pode capturar peça inimiga."""
		knight = Knight(Color.WHITE)
		enemy = Pawn(Color.BLACK)
		empty_board.place(Position(3, 3), knight)
		empty_board.place(Position(1, 2), enemy)
		moves = knight.valid_moves(Position(3, 3), empty_board)
		assert Position(1, 2) in moves

	def test_knight_offsets(self, empty_board):
		"""Verificar todos os 8 offsets do cavalo."""
		knight = Knight(Color.WHITE)
		empty_board.place(Position(3, 3), knight)
		moves = knight.valid_moves(Position(3, 3), empty_board)
		expected = [
			Position(1, 2), Position(1, 4),
			Position(2, 1), Position(2, 5),
			Position(4, 1), Position(4, 5),
			Position(5, 2), Position(5, 4),
		]
		for pos in expected:
			assert pos in moves


class TestKing:
	def test_king_center_moves(self, empty_board):
		"""Rei no centro tem 8 movimentos."""
		king = King(Color.WHITE)
		empty_board.place(Position(3, 3), king)
		moves = king.valid_moves(Position(3, 3), empty_board)
		assert len(moves) == 8

	def test_king_corner_moves(self, empty_board):
		"""Rei no canto tem 3 movimentos."""
		king = King(Color.WHITE)
		empty_board.place(Position(0, 0), king)
		moves = king.valid_moves(Position(0, 0), empty_board)
		assert len(moves) == 3
		assert Position(0, 1) in moves
		assert Position(1, 0) in moves
		assert Position(1, 1) in moves

	def test_king_edge_moves(self, empty_board):
		"""Rei na borda tem 5 movimentos."""
		king = King(Color.WHITE)
		empty_board.place(Position(0, 3), king)
		moves = king.valid_moves(Position(0, 3), empty_board)
		assert len(moves) == 5

	def test_king_blocked_by_friend(self, empty_board):
		"""Rei não pode mover para casa com peça amiga."""
		king = King(Color.WHITE)
		friend = Pawn(Color.WHITE)
		empty_board.place(Position(3, 3), king)
		empty_board.place(Position(3, 4), friend)
		moves = king.valid_moves(Position(3, 3), empty_board)
		assert Position(3, 4) not in moves

	def test_king_captures_enemy(self, empty_board):
		"""Rei pode capturar peça inimiga."""
		king = King(Color.WHITE)
		enemy = Pawn(Color.BLACK)
		empty_board.place(Position(3, 3), king)
		empty_board.place(Position(3, 4), enemy)
		moves = king.valid_moves(Position(3, 3), empty_board)
		assert Position(3, 4) in moves

	def test_king_offsets(self, empty_board):
		"""Verificar todos os 8 offsets do rei."""
		king = King(Color.WHITE)
		empty_board.place(Position(3, 3), king)
		moves = king.valid_moves(Position(3, 3), empty_board)
		expected = [
			Position(2, 2), Position(2, 3), Position(2, 4),
			Position(3, 2), Position(3, 4),
			Position(4, 2), Position(4, 3), Position(4, 4),
		]
		for pos in expected:
			assert pos in moves


class TestBishop:
	def test_bishop_center_moves(self, empty_board):
		"""Bispo no centro tem 13 movimentos."""
		bishop = Bishop(Color.WHITE)
		empty_board.place(Position(3, 3), bishop)
		moves = bishop.valid_moves(Position(3, 3), empty_board)
		assert len(moves) == 13

	def test_bishop_diagonals_only(self, empty_board):
		"""Bispo move apenas nas diagonais."""
		bishop = Bishop(Color.WHITE)
		empty_board.place(Position(3, 3), bishop)
		moves = bishop.valid_moves(Position(3, 3), empty_board)
		# Não pode mover ortogonalmente
		assert Position(3, 4) not in moves
		assert Position(4, 3) not in moves
		# Pode mover diagonalmente
		assert Position(2, 2) in moves
		assert Position(2, 4) in moves
		assert Position(4, 2) in moves
		assert Position(4, 4) in moves

	def test_bishop_blocked_by_friend(self, empty_board):
		"""Bispo para antes de peça amiga."""
		bishop = Bishop(Color.WHITE)
		friend = Pawn(Color.WHITE)
		empty_board.place(Position(3, 3), bishop)
		empty_board.place(Position(4, 4), friend)
		moves = bishop.valid_moves(Position(3, 3), empty_board)
		assert Position(4, 4) not in moves
		assert Position(5, 5) not in moves

	def test_bishop_captures_enemy(self, empty_board):
		"""Bispo pode capturar peça inimiga."""
		bishop = Bishop(Color.WHITE)
		enemy = Pawn(Color.BLACK)
		empty_board.place(Position(3, 3), bishop)
		empty_board.place(Position(4, 4), enemy)
		moves = bishop.valid_moves(Position(3, 3), empty_board)
		assert Position(4, 4) in moves
		assert Position(5, 5) not in moves

	def test_bishop_corner_moves(self, empty_board):
		"""Bispo no canto tem 7 movimentos."""
		bishop = Bishop(Color.WHITE)
		empty_board.place(Position(0, 0), bishop)
		moves = bishop.valid_moves(Position(0, 0), empty_board)
		assert len(moves) == 7

	def test_bishop_color_constraint(self, empty_board):
		"""Bispo mantém a cor da casa."""
		bishop = Bishop(Color.WHITE)
		empty_board.place(Position(0, 0), bishop)
		moves = bishop.valid_moves(Position(0, 0), empty_board)
		# a8 (0,0) é clara; todas as casas devem ser claras
		for pos in moves:
			assert (pos.row + pos.col) % 2 == 0


class TestRook:
	def test_rook_center_moves(self, empty_board):
		"""Torre no centro tem 14 movimentos."""
		rook = Rook(Color.WHITE)
		empty_board.place(Position(3, 3), rook)
		moves = rook.valid_moves(Position(3, 3), empty_board)
		assert len(moves) == 14

	def test_rook_orthogonal_only(self, empty_board):
		"""Torre move apenas ortogonalmente."""
		rook = Rook(Color.WHITE)
		empty_board.place(Position(3, 3), rook)
		moves = rook.valid_moves(Position(3, 3), empty_board)
		# Não pode mover diagonalmente
		assert Position(2, 2) not in moves
		assert Position(2, 4) not in moves
		# Pode mover ortogonalmente
		assert Position(3, 4) in moves
		assert Position(4, 3) in moves

	def test_rook_blocked_by_friend(self, empty_board):
		"""Torre para antes de peça amiga."""
		rook = Rook(Color.WHITE)
		friend = Pawn(Color.WHITE)
		empty_board.place(Position(3, 3), rook)
		empty_board.place(Position(3, 4), friend)
		moves = rook.valid_moves(Position(3, 3), empty_board)
		assert Position(3, 4) not in moves
		assert Position(3, 5) not in moves

	def test_rook_captures_enemy(self, empty_board):
		"""Torre pode capturar peça inimiga."""
		rook = Rook(Color.WHITE)
		enemy = Pawn(Color.BLACK)
		empty_board.place(Position(3, 3), rook)
		empty_board.place(Position(3, 4), enemy)
		moves = rook.valid_moves(Position(3, 3), empty_board)
		assert Position(3, 4) in moves
		assert Position(3, 5) not in moves

	def test_rook_corner_moves(self, empty_board):
		"""Torre no canto tem 14 movimentos."""
		rook = Rook(Color.WHITE)
		empty_board.place(Position(0, 0), rook)
		moves = rook.valid_moves(Position(0, 0), empty_board)
		assert len(moves) == 14


class TestQueen:
	def test_queen_center_moves(self, empty_board):
		"""Rainha no centro tem 27 movimentos."""
		queen = Queen(Color.WHITE)
		empty_board.place(Position(3, 3), queen)
		moves = queen.valid_moves(Position(3, 3), empty_board)
		assert len(moves) == 27

	def test_queen_all_directions(self, empty_board):
		"""Rainha move em todas as 8 direções."""
		queen = Queen(Color.WHITE)
		empty_board.place(Position(3, 3), queen)
		moves = queen.valid_moves(Position(3, 3), empty_board)
		# Diagonal
		assert Position(2, 2) in moves
		# Ortogonal
		assert Position(3, 4) in moves
		assert Position(4, 3) in moves

	def test_queen_blocked_by_friend(self, empty_board):
		"""Rainha para antes de peça amiga."""
		queen = Queen(Color.WHITE)
		friend = Pawn(Color.WHITE)
		empty_board.place(Position(3, 3), queen)
		empty_board.place(Position(3, 4), friend)
		moves = queen.valid_moves(Position(3, 3), empty_board)
		assert Position(3, 4) not in moves
		assert Position(3, 5) not in moves

	def test_queen_captures_enemy(self, empty_board):
		"""Rainha pode capturar peça inimiga."""
		queen = Queen(Color.WHITE)
		enemy = Pawn(Color.BLACK)
		empty_board.place(Position(3, 3), queen)
		empty_board.place(Position(3, 4), enemy)
		moves = queen.valid_moves(Position(3, 3), empty_board)
		assert Position(3, 4) in moves
		assert Position(3, 5) not in moves

	def test_queen_corner_moves(self, empty_board):
		"""Rainha no canto tem 21 movimentos."""
		queen = Queen(Color.WHITE)
		empty_board.place(Position(0, 0), queen)
		moves = queen.valid_moves(Position(0, 0), empty_board)
		assert len(moves) == 21


class TestPieceStr:
	def test_white_piece_uppercase(self, empty_board):
		"""Peças brancas são maiúsculas."""
		pawn = Pawn(Color.WHITE)
		assert str(pawn) == "P"
		knight = Knight(Color.WHITE)
		assert str(knight) == "N"
		bishop = Bishop(Color.WHITE)
		assert str(bishop) == "B"
		rook = Rook(Color.WHITE)
		assert str(rook) == "R"
		queen = Queen(Color.WHITE)
		assert str(queen) == "Q"
		king = King(Color.WHITE)
		assert str(king) == "K"

	def test_black_piece_lowercase(self, empty_board):
		"""Peças pretas são minúsculas."""
		pawn = Pawn(Color.BLACK)
		assert str(pawn) == "p"
		knight = Knight(Color.BLACK)
		assert str(knight) == "n"
		bishop = Bishop(Color.BLACK)
		assert str(bishop) == "b"
		rook = Rook(Color.BLACK)
		assert str(rook) == "r"
		queen = Queen(Color.BLACK)
		assert str(queen) == "q"
		king = King(Color.BLACK)
		assert str(king) == "k"

	def test_piece_has_moved(self, empty_board):
		"""Peça começa com has_moved=False."""
		pawn = Pawn(Color.WHITE)
		assert not pawn.has_moved
		empty_board.place(Position(6, 4), pawn)
		empty_board.move(Position(6, 4), Position(4, 4))
		assert pawn.has_moved
