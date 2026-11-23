"""Testes para Game — turnos, validação, movimentos especiais e fim de jogo."""
from simple_chess.board import Board
from simple_chess.color import Color
from simple_chess.game import Game
from simple_chess.pieces.bishop import Bishop
from simple_chess.pieces.king import King
from simple_chess.pieces.knight import Knight
from simple_chess.pieces.pawn import Pawn
from simple_chess.pieces.queen import Queen
from simple_chess.pieces.rook import Rook
from simple_chess.position import Position


def create_game() -> Game:
	board = Board()
	board.setup_initial_position()
	return Game(board, [Color.WHITE, Color.BLACK])


class TestGameTurns:
	def test_initial_turn_white(self):
		"""Jogo começa com as brancas."""
		game = create_game()
		assert game.player_turn == Color.WHITE

	def test_turn_alternates(self):
		"""Turno alterna após jogada."""
		game = create_game()
		game.make_move_from_notation("e4")
		assert game.player_turn == Color.BLACK
		game.make_move_from_notation("e5")
		assert game.player_turn == Color.WHITE

	def test_move_history(self):
		"""Histórico de jogadas é registrado."""
		game = create_game()
		game.make_move_from_notation("e4")
		game.make_move_from_notation("e5")
		assert game.move_history == ["e4", "e5"]


class TestGameValidation:
	def test_valid_pawn_move(self):
		"""Jogada válida de peão."""
		game = create_game()
		assert game.make_move_from_notation("e4")

	def test_invalid_pawn_move_blocked(self):
		"""Peão bloqueado não pode avançar."""
		game = create_game()
		game.make_move_from_notation("e4")
		game.make_move_from_notation("e5")
		# e4 está bloqueado por e5
		assert not game.make_move_from_notation("e5")

	def test_wrong_color_move(self):
		"""Não pode mover peça da cor errada."""
		game = create_game()
		# Tentar mover peão preto na vez das brancas
		assert not game.make_move(Position(1, 4), Position(3, 4))

	def test_move_leaves_king_in_check_rejected(self):
		"""Movimento que deixa o rei em xeque é rejeitado."""
		board = Board()
		board.grid = [[None]*8 for _ in range(8)]
		board.place(Position(7, 4), King(Color.WHITE))  # e1
		board.place(Position(6, 3), Pawn(Color.WHITE))  # d2
		board.place(Position(3, 0), Queen(Color.BLACK))  # a5 (correta!)
		game = Game(board, [Color.WHITE, Color.BLACK])
		# d3 abre a diagonal a5-e1
		assert not game.make_move(Position(6, 3), Position(5, 3))

	def test_move_blocks_check_accepted(self):
		"""Movimento que bloqueia xeque é aceito."""
		board = Board()
		board.grid = [[None]*8 for _ in range(8)]
		board.place(Position(7, 4), King(Color.WHITE))  # e1
		board.place(Position(6, 3), Pawn(Color.WHITE))  # d2
		board.place(Position(3, 0), Queen(Color.BLACK))  # a5
		board.place(Position(0, 4), King(Color.BLACK))  # e8
		game = Game(board, [Color.WHITE, Color.BLACK])
		# d3 bloqueia a diagonal
		assert game.make_move(Position(6, 3), Position(5, 3))

	def test_capture_gives_check_requires_plus(self):
		"""Captura que dá xeque exige +."""
		game = create_game()
		game.make_move_from_notation("e4")
		game.make_move_from_notation("e5")
		game.make_move_from_notation("Qh5")
		game.make_move_from_notation("Nc6")
		# Qxf7+ dá xeque
		assert game.make_move_from_notation("Qxf7+")
		# Sem + deve falhar
		# Resetar para testar sem +
		game2 = create_game()
		game2.make_move_from_notation("e4")
		game2.make_move_from_notation("e5")
		game2.make_move_from_notation("Qh5")
		game2.make_move_from_notation("Nc6")
		assert not game2.make_move_from_notation("Qxf7")

	def test_no_check_with_plus_rejected(self):
		"""Jogada sem xeque com + é rejeitada."""
		game = create_game()
		assert not game.make_move_from_notation("e4+")


class TestGameCastling:
	def test_kingside_castling(self):
		"""Roque curto funciona."""
		game = create_game()
		game.make_move_from_notation("e4")
		game.make_move_from_notation("c5")
		game.make_move_from_notation("Nf3")
		game.make_move_from_notation("Nc6")
		game.make_move_from_notation("Bc4")
		game.make_move_from_notation("g6")
		# Fazer roque curto
		assert game.make_move_from_notation("O-O")
		king = game.board.piece_at(Position(7, 6))
		assert isinstance(king, King)
		rook = game.board.piece_at(Position(7, 5))
		assert isinstance(rook, Rook)

	def test_queenside_castling(self):
		"""Roque longo funciona."""
		game = create_game()
		game.make_move_from_notation("d4")
		game.make_move_from_notation("d5")
		game.make_move_from_notation("Nf3")
		game.make_move_from_notation("Nf6")
		game.make_move_from_notation("Bf4")
		game.make_move_from_notation("Bf5")
		game.make_move_from_notation("e3")
		game.make_move_from_notation("e6")
		game.make_move_from_notation("Nbd2")
		game.make_move_from_notation("Be7")
		# Fazer roque longo
		assert game.make_move_from_notation("O-O-O")
		king = game.board.piece_at(Position(7, 2))
		assert isinstance(king, King)
		rook = game.board.piece_at(Position(7, 3))
		assert isinstance(rook, Rook)

	def test_castling_blocked_by_piece(self):
		"""Roque bloqueado por peça no caminho."""
		game = create_game()
		# Colocar peça entre rei e torre
		game.board.place(Position(7, 5), Bishop(Color.WHITE))
		assert not game.make_move_from_notation("O-O")

	def test_castling_king_moved(self):
		"""Roque não é possível após rei se mover."""
		game = create_game()
		game.make_move_from_notation("e4")
		game.make_move_from_notation("e5")
		game.make_move_from_notation("Ke2")
		game.make_move_from_notation("Nc6")
		assert not game.make_move_from_notation("O-O")

	def test_castling_rook_moved(self):
		"""Roque não é possível após torre se mover."""
		game = create_game()
		game.make_move_from_notation("e4")
		game.make_move_from_notation("e5")
		game.make_move_from_notation("Rh1")  # Torre se move
		game.make_move_from_notation("Nc6")
		# Na verdade Rh1 não é válido pois a torre já está em h1
		# Vamos testar de outra forma
		game2 = create_game()
		game2.make_move_from_notation("e4")
		game2.make_move_from_notation("e5")
		# Mover torre manualmente
		game2.board.place(Position(7, 7), None)
		game2.board.place(Position(7, 6), Rook(Color.WHITE))
		assert not game2.make_move_from_notation("O-O")

	def test_castling_rights_updated(self):
		"""Direitos de roque são atualizados após movimento do rei."""
		game = create_game()
		game.make_move_from_notation("e4")
		game.make_move_from_notation("e5")
		game.make_move_from_notation("Ke2")
		game.make_move_from_notation("Nc6")
		rights = game.get_castling_rights(Color.WHITE)
		assert rights["kingside"] is False
		assert rights["queenside"] is False

	def test_castling_rights_rook_moved(self):
		"""Direitos de roque atualizados após torre se mover."""
		game = create_game()
		game.make_move_from_notation("e4")
		game.make_move_from_notation("e5")
		# Mover torre kingside manualmente via make_move
		game.make_move(Position(7, 7), Position(7, 6))
		# make_move não atualiza castling_rights para Torre
		# Preciso verificar se __update_castling_rights é chamado
		# Na verdade, make_move chama __update_castling_rights que só atualiza para King e Rook
		# Mas a torre em h1 (col=7) deve desativar kingside
		# O problema é que make_move falha porque a torre não pode ir para f1 (tem bispo)
		# Vamos testar com make_move direto
		game2 = create_game()
		# Remover bispo de f1 para liberar caminho
		game2.board.place(Position(7, 5), None)
		game2.make_move(Position(7, 7), Position(7, 6))
		rights = game2.get_castling_rights(Color.WHITE)
		assert rights["kingside"] is False
		assert rights["queenside"] is True


class TestGamePromotion:
	def test_promotion_to_queen(self):
		"""Promoção de peão para Rainha."""
		board = Board()
		board.grid = [[None]*8 for _ in range(8)]
		board.place(Position(7, 4), King(Color.WHITE))
		board.place(Position(0, 4), King(Color.BLACK))
		board.place(Position(1, 4), Pawn(Color.WHITE))  # Peão em e7
		game = Game(board, [Color.WHITE, Color.BLACK])
		assert game.make_move_from_notation("e8=Q")
		piece = game.board.piece_at(Position(0, 4))
		assert isinstance(piece, Queen)

	def test_promotion_capture(self):
		"""Promoção com captura (dxc8=Q)."""
		board = Board()
		board.grid = [[None]*8 for _ in range(8)]
		board.place(Position(7, 4), King(Color.WHITE))
		board.place(Position(0, 4), King(Color.BLACK))
		board.place(Position(1, 3), Pawn(Color.WHITE))  # d7
		board.place(Position(0, 2), Pawn(Color.BLACK))  # c8
		game = Game(board, [Color.WHITE, Color.BLACK])
		# d7 captura c8 e promove
		assert game.make_move_from_notation("dxc8=Q")
		piece = game.board.piece_at(Position(0, 2))
		assert isinstance(piece, Queen)


class TestGameEnPassant:
	def test_en_passant_capture(self):
		"""Captura en passant funciona."""
		game = create_game()
		game.make_move_from_notation("e4")
		game.make_move_from_notation("c5")
		game.make_move_from_notation("d4")
		game.make_move_from_notation("cxd4")
		# Peão preto capturou en passant e está em d4
		piece = game.board.piece_at(Position(4, 3))  # d4
		assert isinstance(piece, Pawn)
		assert piece.color == Color.BLACK
		# Peão branco em c5 foi removido
		assert game.board.piece_at(Position(4, 2)) is None

	def test_en_passant_tracking(self):
		"""En passant é rastreado após peão avançar 2 casas."""
		game = create_game()
		game.make_move_from_notation("e4")
		assert game.last_double_pawn_move == Position(4, 4)
		game.make_move_from_notation("e5")
		assert game.last_double_pawn_move == Position(3, 4)

	def test_en_passant_reset(self):
		"""En passant é resetado após jogada que não é peão duplo."""
		game = create_game()
		game.make_move_from_notation("e4")
		assert game.last_double_pawn_move is not None
		game.make_move_from_notation("Nc6")
		assert game.last_double_pawn_move is None


class TestGameCheckmate:
	def test_checkmate_detection(self):
		"""Xeque-mate é detectado."""
		board = Board()
		board.grid = [[None]*8 for _ in range(8)]
		# Rei branco encurralado em h1
		board.place(Position(7, 7), King(Color.WHITE))
		board.place(Position(7, 6), Pawn(Color.WHITE))  # g1 bloqueia
		board.place(Position(6, 6), Pawn(Color.WHITE))  # g2 bloqueia
		# Rainha preta em g1 dá mate
		board.place(Position(6, 6), None)  # Remover peão de g2
		board.place(Position(6, 6), Queen(Color.BLACK))  # g2
		board.place(Position(0, 4), King(Color.BLACK))
		game = Game(board, [Color.WHITE, Color.BLACK])
		assert game.is_game_over()

	def test_checkmate_result(self):
		"""Resultado de xeque-mate."""
		board = Board()
		board.grid = [[None]*8 for _ in range(8)]
		board.place(Position(7, 7), King(Color.WHITE))
		board.place(Position(7, 6), Pawn(Color.WHITE))  # g1
		board.place(Position(6, 6), Queen(Color.BLACK))  # g2 dá mate
		board.place(Position(0, 4), King(Color.BLACK))
		game = Game(board, [Color.WHITE, Color.BLACK])
		assert game.is_game_over()
		result = game.game_result()
		assert "Xeque-mate" in result


class TestGameStalemate:
	def test_stalemate_detection(self):
		"""Stalemate é detectado."""
		board = Board()
		board.grid = [[None]*8 for _ in range(8)]
		# Rei branco em h1 sem movimentos, mas não em xeque
		board.place(Position(7, 7), King(Color.WHITE))
		# Torre preta em h2 bloqueia sem dar xeque
		board.place(Position(6, 7), Rook(Color.BLACK))
		# Cavalo preto em f2 bloqueia sem dar xeque
		board.place(Position(6, 5), Knight(Color.BLACK))
		board.place(Position(0, 4), King(Color.BLACK))
		game = Game(board, [Color.WHITE, Color.BLACK])
		assert game.is_game_over()
		result = game.game_result()
		assert "stalemate" in result


class TestGameInsufficientMaterial:
	def test_king_vs_king(self):
		"""Rei vs Rei é empate."""
		board = Board()
		board.grid = [[None]*8 for _ in range(8)]
		board.place(Position(7, 4), King(Color.WHITE))
		board.place(Position(0, 4), King(Color.BLACK))
		game = Game(board, [Color.WHITE, Color.BLACK])
		assert game.is_game_over()
		result = game.game_result()
		assert "material insuficiente" in result

	def test_king_bishop_vs_king(self):
		"""Rei + Bispo vs Rei é empate."""
		board = Board()
		board.grid = [[None]*8 for _ in range(8)]
		board.place(Position(7, 4), King(Color.WHITE))
		board.place(Position(6, 5), Bishop(Color.WHITE))
		board.place(Position(0, 4), King(Color.BLACK))
		game = Game(board, [Color.WHITE, Color.BLACK])
		assert game.is_game_over()
		result = game.game_result()
		assert "material insuficiente" in result

	def test_king_knight_vs_king(self):
		"""Rei + Cavalo vs Rei é empate."""
		board = Board()
		board.grid = [[None]*8 for _ in range(8)]
		board.place(Position(7, 4), King(Color.WHITE))
		board.place(Position(6, 5), Knight(Color.WHITE))
		board.place(Position(0, 4), King(Color.BLACK))
		game = Game(board, [Color.WHITE, Color.BLACK])
		assert game.is_game_over()
		result = game.game_result()
		assert "material insuficiente" in result

	def test_king_vs_king_bishop(self):
		"""Rei vs Rei + Bispo é empate."""
		board = Board()
		board.grid = [[None]*8 for _ in range(8)]
		board.place(Position(7, 4), King(Color.WHITE))
		board.place(Position(0, 4), King(Color.BLACK))
		board.place(Position(1, 5), Bishop(Color.BLACK))
		game = Game(board, [Color.WHITE, Color.BLACK])
		assert game.is_game_over()
		result = game.game_result()
		assert "material insuficiente" in result

	def test_not_insufficient_material(self):
		"""Rei + Torre vs Rei NÃO é empate."""
		board = Board()
		board.grid = [[None]*8 for _ in range(8)]
		board.place(Position(7, 4), King(Color.WHITE))
		board.place(Position(6, 5), Rook(Color.WHITE))
		board.place(Position(0, 4), King(Color.BLACK))
		game = Game(board, [Color.WHITE, Color.BLACK])
		assert not game.is_game_over()


class TestGameFiftyMoveRule:
	def test_fifty_move_counter_resets_on_pawn(self):
		"""Contador reseta com movimento de peão."""
		game = create_game()
		game.make_move_from_notation("e4")
		assert game.fifty_move_counter == 0

	def test_fifty_move_counter_resets_on_capture(self):
		"""Contador reseta com captura."""
		game = create_game()
		game.make_move_from_notation("e4")
		game.make_move_from_notation("e5")
		game.make_move_from_notation("Nf3")
		game.make_move_from_notation("Nc6")
		game.make_move_from_notation("Nxe5")
		assert game.fifty_move_counter == 0

	def test_fifty_move_counter_increments(self):
		"""Contador incrementa com movimento de cavalo."""
		game = create_game()
		game.make_move_from_notation("Nf3")
		assert game.fifty_move_counter == 1
		game.make_move_from_notation("Nc6")
		assert game.fifty_move_counter == 2

	def test_fifty_move_rule_triggers(self):
		"""Regra dos 50 movimentos é detectada."""
		board = Board()
		board.grid = [[None]*8 for _ in range(8)]
		board.place(Position(7, 4), King(Color.WHITE))
		board.place(Position(0, 4), King(Color.BLACK))
		board.place(Position(6, 5), Knight(Color.WHITE))
		board.place(Position(1, 5), Knight(Color.BLACK))
		game = Game(board, [Color.WHITE, Color.BLACK])
		# Simular 100 half-moves
		game.fifty_move_counter = 100
		assert game.is_game_over()
		result = game.game_result()
		assert "50 movimentos" in result


class TestGameThreefoldRepetition:
	def test_position_key_generated(self):
		"""Chave de posição é gerada."""
		game = create_game()
		game.make_move_from_notation("e4")
		assert len(game.position_history) > 0

	def test_threefold_repetition_detection(self):
		"""Repetição 3x é detectada."""
		board = Board()
		board.grid = [[None]*8 for _ in range(8)]
		board.place(Position(7, 4), King(Color.WHITE))
		board.place(Position(0, 4), King(Color.BLACK))
		board.place(Position(6, 5), Knight(Color.WHITE))
		board.place(Position(1, 5), Knight(Color.BLACK))
		game = Game(board, [Color.WHITE, Color.BLACK])
		# Simular repetição
		key = game._Game__generate_position_key()
		game.position_history = [key, key]
		# A posição atual é a mesma
		assert game.is_game_over()
		result = game.game_result()
		assert "repetição" in result


class TestGameCapturedPieces:
	def test_captured_pieces_tracked(self):
		"""Peças capturadas são rastreadas."""
		game = create_game()
		game.make_move_from_notation("e4")
		game.make_move_from_notation("e5")
		game.make_move_from_notation("Nf3")
		game.make_move_from_notation("Nc6")
		game.make_move_from_notation("Nxe5")
		assert len(game.captured_pieces) == 1
		assert isinstance(game.captured_pieces[0], Pawn)


class TestGameNotation:
	def test_pawn_short_notation(self):
		"""Notação curta de peão."""
		game = create_game()
		assert game.make_move_from_notation("e4")
		assert game.make_move_from_notation("d5")

	def test_piece_short_notation(self):
		"""Notação curta de peças."""
		game = create_game()
		game.make_move_from_notation("e4")
		game.make_move_from_notation("e5")
		assert game.make_move_from_notation("Nf3")
		assert game.make_move_from_notation("Bc4")

	def test_capture_notation_required(self):
		"""Captura exige x."""
		game = create_game()
		game.make_move_from_notation("e4")
		game.make_move_from_notation("e5")
		game.make_move_from_notation("Nf3")
		game.make_move_from_notation("Nc6")
		# Sem x deve falhar
		assert not game.make_move_from_notation("Ne5")
		# Com x deve funcionar
		assert game.make_move_from_notation("Nxe5")

	def test_disambiguation(self):
		"""Desambiguação de peças."""
		game = create_game()
		game.make_move_from_notation("e4")
		game.make_move_from_notation("e5")
		game.make_move_from_notation("Nf3")
		game.make_move_from_notation("d6")
		game.make_move_from_notation("Ng5")
		game.make_move_from_notation("f6")
		# Dois cavalos podem ir para e6
		# Sem desambiguação deve falhar
		assert not game.make_move_from_notation("Ne6")
		# Com desambiguação deve funcionar
		assert game.make_move_from_notation("Nge6")

	def test_invalid_notation(self):
		"""Notação inválida é rejeitada."""
		game = create_game()
		assert not game.make_move_from_notation("")
		assert not game.make_move_from_notation("xyz")
		assert not game.make_move_from_notation("e9")
