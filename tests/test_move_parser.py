"""Testes para MoveParser — parse de notação PGN."""
from simple_chess.board import Board
from simple_chess.color import Color
from simple_chess.game import Game
from simple_chess.move_parser import parse_move_notation, parse_position
from simple_chess.pieces.king import King
from simple_chess.pieces.knight import Knight
from simple_chess.pieces.pawn import Pawn
from simple_chess.position import Position


def create_game() -> Game:
	board = Board()
	board.setup_initial_position()
	return Game(board, [Color.WHITE, Color.BLACK])


class TestParsePosition:
	def test_parse_a1(self):
		"""a1 → Position(7, 0)."""
		assert parse_position("a1") == Position(7, 0)

	def test_parse_h8(self):
		"""h8 → Position(0, 7)."""
		assert parse_position("h8") == Position(0, 7)

	def test_parse_e4(self):
		"""e4 → Position(4, 4)."""
		assert parse_position("e4") == Position(4, 4)

	def test_parse_d4(self):
		"""d4 → Position(4, 3)."""
		assert parse_position("d4") == Position(4, 3)

	def test_parse_uppercase(self):
		"""Parse é case-insensitive."""
		assert parse_position("E4") == Position(4, 4)
		assert parse_position("e4") == Position(4, 4)

	def test_parse_invalid(self):
		"""Notação inválida retorna None."""
		assert parse_position("i1") is None
		assert parse_position("a9") is None
		assert parse_position("a") is None
		assert parse_position("abc") is None
		assert parse_position("") is None

	def test_parse_all_files(self):
		"""Todas as colunas a-h."""
		assert parse_position("a1").col == 0
		assert parse_position("b1").col == 1
		assert parse_position("c1").col == 2
		assert parse_position("d1").col == 3
		assert parse_position("e1").col == 4
		assert parse_position("f1").col == 5
		assert parse_position("g1").col == 6
		assert parse_position("h1").col == 7

	def test_parse_all_ranks(self):
		"""Todas as fileiras 1-8."""
		assert parse_position("a1").row == 7
		assert parse_position("a2").row == 6
		assert parse_position("a3").row == 5
		assert parse_position("a4").row == 4
		assert parse_position("a5").row == 3
		assert parse_position("a6").row == 2
		assert parse_position("a7").row == 1
		assert parse_position("a8").row == 0


class TestPawnNotation:
	def test_pawn_short_move(self):
		"""Notação curta de peão."""
		game = create_game()
		result = parse_move_notation("e4", game)
		assert result is not None
		origin, end, suffix = result
		assert origin == Position(6, 4)
		assert end == Position(4, 4)
		assert suffix == ""

	def test_pawn_all_files(self):
		"""Peão em todas as colunas."""
		game = create_game()
		for file_char in "abcdefgh":
			result = parse_move_notation(f"{file_char}4", game)
			assert result is not None

	def test_pawn_capture_required_x(self):
		"""Captura de peão exige x."""
		game = create_game()
		game.make_move_from_notation("e4")
		game.make_move_from_notation("d5")
		# e4 captura d5
		result = parse_move_notation("exd5", game)
		assert result is not None
		origin, end, suffix = result
		assert end == Position(3, 3)  # d5

	def test_pawn_no_capture_without_x(self):
		"""Sem x, não é captura."""
		game = create_game()
		game.make_move_from_notation("e4")
		game.make_move_from_notation("d5")
		# "e5" sem x não deve ser aceito como captura
		result = parse_move_notation("e5", game)
		# e5 é movimento válido, não captura
		assert result is not None


class TestPieceNotation:
	def test_knight_notation(self):
		"""Notação de Cavalo."""
		game = create_game()
		# Nf3 é jogada das brancas, turno ainda é WHITE
		result = parse_move_notation("Nf3", game)
		assert result is not None
		origin, end, suffix = result
		assert origin == Position(7, 6)  # g1
		assert end == Position(5, 5)  # f3

	def test_bishop_notation(self):
		"""Notação de Bispo."""
		game = create_game()
		game.make_move_from_notation("e4")
		game.make_move_from_notation("e5")
		# Bc4 é jogada das brancas
		result = parse_move_notation("Bc4", game)
		assert result is not None
		origin, end, suffix = result
		assert end == Position(4, 2)  # c4

	def test_queen_notation(self):
		"""Notação de Rainha."""
		game = create_game()
		game.make_move_from_notation("e4")
		game.make_move_from_notation("e5")
		# Qh5 é jogada das brancas
		result = parse_move_notation("Qh5", game)
		assert result is not None
		origin, end, suffix = result
		assert end == Position(3, 7)  # h5

	def test_rook_notation(self):
		"""Notação de Torre."""
		game = create_game()
		game.make_move_from_notation("e4")
		game.make_move_from_notation("e5")
		game.make_move_from_notation("Nf3")
		game.make_move_from_notation("Nc6")
		game.make_move_from_notation("Bc4")
		game.make_move_from_notation("Bc5")
		game.make_move_from_notation("Qe2")
		game.make_move_from_notation("Qe7")
		# Rh1 não é válido pois torre já está em h1
		result = parse_move_notation("Rh1", game)
		assert result is None

	def test_king_notation(self):
		"""Notação de Rei."""
		game = create_game()
		game.make_move_from_notation("e4")
		game.make_move_from_notation("e5")
		# Ke2 é jogada das brancas
		result = parse_move_notation("Ke2", game)
		assert result is not None
		origin, end, suffix = result
		assert origin == Position(7, 4)  # e1
		assert end == Position(6, 4)  # e2

	def test_piece_lowercase(self):
		"""Letras minúsculas são aceitas."""
		game = create_game()
		# nf3 é jogada das brancas
		result = parse_move_notation("nf3", game)
		assert result is not None

	def test_piece_capture(self):
		"""Captura de peça com x."""
		game = create_game()
		game.make_move_from_notation("e4")
		game.make_move_from_notation("e5")
		game.make_move_from_notation("Nf3")
		game.make_move_from_notation("Nc6")
		# Nxe5 é jogada das brancas
		result = parse_move_notation("Nxe5", game)
		assert result is not None
		origin, end, suffix = result
		assert end == Position(4, 4)  # e5


class TestCastlingNotation:
	def test_kingside_castling(self):
		"""Roque curto O-O."""
		game = create_game()
		result = parse_move_notation("O-O", game)
		assert result is not None
		origin, end, suffix = result
		assert origin == Position(7, 4)  # e1
		assert end == Position(7, 6)  # g1

	def test_queenside_castling(self):
		"""Roque longo O-O-O."""
		game = create_game()
		result = parse_move_notation("O-O-O", game)
		assert result is not None
		origin, end, suffix = result
		assert origin == Position(7, 4)  # e1
		assert end == Position(7, 2)  # c1

	def test_castling_lowercase(self):
		"""Roque com letras minúsculas."""
		game = create_game()
		result = parse_move_notation("o-o", game)
		assert result is not None

	def test_castling_black(self):
		"""Roque das pretas."""
		game = create_game()
		game.make_move_from_notation("e4")
		result = parse_move_notation("O-O", game)
		assert result is not None
		origin, end, suffix = result
		assert origin == Position(0, 4)  # e8
		assert end == Position(0, 6)  # g8


class TestPromotionNotation:
	def test_promotion_queen(self):
		"""Promoção para Rainha."""
		board = Board()
		board.grid = [[None]*8 for _ in range(8)]
		board.place(Position(7, 4), King(Color.WHITE))
		board.place(Position(0, 4), King(Color.BLACK))
		board.place(Position(1, 4), Pawn(Color.WHITE))
		game = Game(board, [Color.WHITE, Color.BLACK])
		result = parse_move_notation("e8=Q", game)
		assert result is not None
		origin, end, suffix = result
		assert origin == Position(1, 4)
		assert end == Position(0, 4)

	def test_promotion_rook(self):
		"""Promoção para Torre."""
		board = Board()
		board.grid = [[None]*8 for _ in range(8)]
		board.place(Position(7, 4), King(Color.WHITE))
		board.place(Position(0, 4), King(Color.BLACK))
		board.place(Position(1, 4), Pawn(Color.WHITE))
		game = Game(board, [Color.WHITE, Color.BLACK])
		result = parse_move_notation("e8=R", game)
		assert result is not None

	def test_promotion_bishop(self):
		"""Promoção para Bispo."""
		board = Board()
		board.grid = [[None]*8 for _ in range(8)]
		board.place(Position(7, 4), King(Color.WHITE))
		board.place(Position(0, 4), King(Color.BLACK))
		board.place(Position(1, 4), Pawn(Color.WHITE))
		game = Game(board, [Color.WHITE, Color.BLACK])
		result = parse_move_notation("e8=B", game)
		assert result is not None

	def test_promotion_knight(self):
		"""Promoção para Cavalo."""
		board = Board()
		board.grid = [[None]*8 for _ in range(8)]
		board.place(Position(7, 4), King(Color.WHITE))
		board.place(Position(0, 4), King(Color.BLACK))
		board.place(Position(1, 4), Pawn(Color.WHITE))
		game = Game(board, [Color.WHITE, Color.BLACK])
		result = parse_move_notation("e8=N", game)
		assert result is not None

	def test_promotion_capture(self):
		"""Promoção com captura."""
		board = Board()
		board.grid = [[None]*8 for _ in range(8)]
		board.place(Position(7, 4), King(Color.WHITE))
		board.place(Position(0, 4), King(Color.BLACK))
		board.place(Position(1, 3), Pawn(Color.WHITE))  # d7
		board.place(Position(0, 4), Pawn(Color.BLACK))  # e8
		game = Game(board, [Color.WHITE, Color.BLACK])
		result = parse_move_notation("dxe8=Q", game)
		assert result is not None


class TestSuffixNotation:
	def test_check_suffix(self):
		"""Sufixo + é extraído."""
		game = create_game()
		result = parse_move_notation("e4+", game)
		assert result is not None
		origin, end, suffix = result
		assert suffix == "+"

	def test_checkmate_suffix(self):
		"""Sufixo # é extraído."""
		game = create_game()
		result = parse_move_notation("e4#", game)
		assert result is not None
		origin, end, suffix = result
		assert suffix == "#"

	def test_capture_with_check(self):
		"""Captura com xeque."""
		game = create_game()
		game.make_move_from_notation("e4")
		game.make_move_from_notation("e5")
		game.make_move_from_notation("Qh5")
		game.make_move_from_notation("Nc6")
		result = parse_move_notation("Qxf7+", game)
		assert result is not None
		origin, end, suffix = result
		assert suffix == "+"


class TestDisambiguation:
	def test_file_disambiguation(self):
		"""Desambiguação por coluna."""
		game = create_game()
		game.make_move_from_notation("e4")
		game.make_move_from_notation("e5")
		game.make_move_from_notation("Nf3")
		game.make_move_from_notation("d6")
		game.make_move_from_notation("Ng5")
		game.make_move_from_notation("f6")
		# Nge6 — cavalo em g5 vai para e6 (jogada das brancas)
		result = parse_move_notation("Nge6", game)
		assert result is not None
		origin, end, suffix = result
		assert origin == Position(3, 6)  # g5

	def test_rank_disambiguation(self):
		"""Desambiguação por fileira."""
		board = Board()
		board.grid = [[None]*8 for _ in range(8)]
		board.place(Position(7, 4), King(Color.WHITE))
		board.place(Position(0, 4), King(Color.BLACK))
		board.place(Position(7, 1), Knight(Color.WHITE))  # b1
		board.place(Position(5, 1), Knight(Color.WHITE))  # b3
		game = Game(board, [Color.WHITE, Color.BLACK])
		# Ambos podem ir para a3 (5, 0)
		result = parse_move_notation("N1a3", game)
		assert result is not None

	def test_no_disambiguation_needed(self):
		"""Sem desambiguação quando só há 1 candidato."""
		game = create_game()
		# Nf3 sem desambiguação (apenas g1 pode ir)
		result = parse_move_notation("Nf3", game)
		assert result is not None


class TestInvalidNotation:
	def test_empty_string(self):
		"""String vazia retorna None."""
		game = create_game()
		assert parse_move_notation("", game) is None

	def test_whitespace_only(self):
		"""Apenas espaços retorna None."""
		game = create_game()
		assert parse_move_notation("   ", game) is None

	def test_invalid_characters(self):
		"""Caracteres inválidos retornam None."""
		game = create_game()
		assert parse_move_notation("xyz", game) is None
		assert parse_move_notation("@#$", game) is None

	def test_invalid_position(self):
		"""Posição inválida retorna None."""
		game = create_game()
		assert parse_move_notation("e9", game) is None
		assert parse_move_notation("i1", game) is None
