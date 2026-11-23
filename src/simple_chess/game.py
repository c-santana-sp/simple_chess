from simple_chess.board import Board
from simple_chess.color import Color
from simple_chess.pieces.bishop import Bishop
from simple_chess.pieces.king import King
from simple_chess.pieces.knight import Knight
from simple_chess.pieces.piece import Piece
from simple_chess.pieces.queen import Queen
from simple_chess.pieces.rook import Rook
from simple_chess.position import Position


class Game:
	def __init__(self, board: Board, players: list[Color]):
		self.board = board
		self.players = players
		self.turn_index = 0
		self.captured_pieces = []
		self.move_history: list[str] = []

		# Direitos de roque — cada cor começa com ambos os lados disponíveis
		self.castling_rights: dict[Color, dict[str, bool]] = {
			Color.WHITE: {"kingside": True, "queenside": True},
			Color.BLACK: {"kingside": True, "queenside": True},
		}

		# En passant — armazena a posição do peão após um movimento de 2 casas
		self.last_double_pawn_move: Position | None = None

		# Regra dos 50 movimentos — contador de movimentos sem captura ou peão
		self.fifty_move_counter: int = 0

		# Repetição de posição — histórico de posições para detectar empate por 3x
		self.position_history: list[str] = []

	@property
	def player_turn(self) -> Color:
		return self.players[self.turn_index]

	def make_move(
		self,
		origin_pos: Position,
		end_pos: Position,
		notation: str = "",
		promotion_piece: str | None = None,
	) -> bool:
		if self.__is_valid_move(origin_pos, end_pos):
			piece = self.board.piece_at(origin_pos)

			# Detectar en passant — peão captura ao passar
			is_en_passant = self.__is_en_passant(piece, origin_pos, end_pos)
			captured = None
			if is_en_passant:
				# Remover o peão capturado (está na posição adjacente, não no destino)
				captured_pawn_pos = Position(end_pos.row + 1 if piece.color == Color.WHITE else end_pos.row - 1, end_pos.col)
				captured = self.board.piece_at(captured_pawn_pos)
				self.board.place(captured_pawn_pos, None)
				if captured is not None:
					self.captured_pieces.append(captured)
				# Mover o peão para a posição de destino
				self.board.move(origin_pos, end_pos)
			else:
				captured = self.board.move(origin_pos, end_pos)
				if captured is not None:
					self.captured_pieces.append(captured)

			# Atualiza direitos de roque após o movimento
			if piece is not None:
				self.__update_castling_rights(piece, origin_pos, end_pos)

			# Rastrear en passant — peão que avança 2 casas
			self.__update_double_pawn_move(piece, origin_pos, end_pos)

			# Promoção de peão — substituir peão pela peça escolhida
			if promotion_piece is not None:
				self.__promote_pawn(end_pos, promotion_piece)

			# Atualizar regra dos 50 movimentos
			self.__update_fifty_move_counter(piece, captured is not None)

			# Registrar posição para repetição (após todas as mudanças)
			self.__record_position()

			if notation:
				self.move_history.append(notation)

			self.turn_index = (self.turn_index + 1) % len(self.players)
			return True
		return False

	def __is_en_passant(
		self, piece: "Piece", origin_pos: Position, end_pos: Position
	) -> bool:
		"""Verifica se o movimento é uma captura en passant."""
		from simple_chess.pieces.pawn import Pawn

		if not isinstance(piece, Pawn):
			return False

		if self.last_double_pawn_move is None:
			return False

		# En passant: destino é a casa ao lado do peão que avançou 2 casas
		# O peão capturado está na mesma coluna que o destino, mas na fileira do peão atual
		enemy_pos = self.last_double_pawn_move
		if end_pos.col == enemy_pos.col and end_pos.row == origin_pos.row + (-1 if piece.color == Color.WHITE else 1):
			# Verificar que não há peça no destino (en passant captura uma casa vazia)
			if self.board.is_empty(end_pos):
				return True
		return False

	def __update_castling_rights(
		self, piece: "Piece", origin_pos: Position, end_pos: Position
	) -> None:
		"""Atualiza os direitos de roque quando rei ou torre se movem.

		- Rei se move → perde ambos os direitos da cor.
		- Torre se move → perde o lado correspondente (kingside ou queenside).
		"""
		from simple_chess.pieces.king import King
		from simple_chess.pieces.rook import Rook

		color = piece.color

		if isinstance(piece, King):
			# Rei se moveu → perde ambos os direitos
			self.castling_rights[color]["kingside"] = False
			self.castling_rights[color]["queenside"] = False

		elif isinstance(piece, Rook):
			# Torre se moveu → identificar qual lado
			# Brancas: a1=(7,0)=queenside, h1=(7,7)=kingside
			# Pretas: a8=(0,0)=queenside, h8=(0,7)=kingside
			if origin_pos.col == 0:
				self.castling_rights[color]["queenside"] = False
			elif origin_pos.col == 7:
				self.castling_rights[color]["kingside"] = False

	def get_castling_rights(self, color: Color) -> dict[str, bool]:
		"""Retorna os direitos de roque de uma cor.

		Returns:
			Dicionário com 'kingside' e 'queenside' como booleanos.
		"""
		return dict(self.castling_rights.get(color, {"kingside": False, "queenside": False}))

	def __is_castling_move(self, origin: Position, end: Position) -> bool:
		"""Detecta se o movimento é um roque.

		Roque = rei move 2 casas horizontalmente na mesma fileira.
		"""
		if origin.row != end.row:
			return False
		if abs(end.col - origin.col) != 2:
			return False
		piece = self.board.piece_at(origin)
		if piece is None:
			return False
		from simple_chess.pieces.king import King
		return isinstance(piece, King)

	def __execute_castling(
		self, kingside: bool, user_suffix: str, notation: str
	) -> bool:
		"""Executa o roque completo: valida caminho, move rei e torre.

		Args:
			kingside: True para roque curto (O-O), False para roque longo (O-O-O).
			user_suffix: Sufixo digitado pelo jogador (+ ou #).
			notation: Notação original para o histórico.

		Returns:
			True se o roque foi executado com sucesso.
		"""
		from simple_chess.pieces.king import King
		from simple_chess.pieces.rook import Rook

		color = self.player_turn
		enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE

		# Verificar direitos de roque
		rights = self.castling_rights[color]
		if kingside:
			if not rights["kingside"]:
				return False
		else:
			if not rights["queenside"]:
				return False

		# Posições do rei e da torre
		if color == Color.WHITE:
			king_row = 7
		else:
			king_row = 0

		king_origin = Position(king_row, 4)
		if kingside:
			king_end = Position(king_row, 6)
			rook_origin = Position(king_row, 7)
			rook_end = Position(king_row, 5)
			# Casas que o rei passa: f1/f8
			passed_squares = [Position(king_row, 5)]
			# Casas entre rei e torre: f1/f8, g1/g8
			path_squares = [Position(king_row, 5), Position(king_row, 6)]
		else:
			king_end = Position(king_row, 2)
			rook_origin = Position(king_row, 0)
			rook_end = Position(king_row, 3)
			# Casas que o rei passa: d1/d8, c1/c8
			passed_squares = [Position(king_row, 3), Position(king_row, 2)]
			# Casas entre rei e torre: b1/b8, c1/c8, d1/d8
			path_squares = [Position(king_row, 1), Position(king_row, 2), Position(king_row, 3)]

		# Verificar que o rei está na posição inicial
		king_piece = self.board.piece_at(king_origin)
		if king_piece is None or not isinstance(king_piece, King):
			return False

		# Verificar que a torre está na posição inicial
		rook_piece = self.board.piece_at(rook_origin)
		if rook_piece is None or not isinstance(rook_piece, Rook):
			return False

		# Verificar que o caminho entre rei e torre está livre
		for pos in path_squares:
			if self.board.piece_at(pos) is not None:
				return False

		# Verificar que o rei não está em xeque
		if self.board.is_check(color):
			return False

		# Verificar que o rei não passa por xeque
		# Simula o rei em cada casa que passa
		original_grid = self.board.grid
		self.board.grid = [row[:] for row in original_grid]
		self.board.place(king_origin, None)

		for pos in passed_squares:
			self.board.place(pos, king_piece)
			if self.board.is_check(color):
				self.board.grid = original_grid
				return False
			self.board.place(pos, None)

		self.board.grid = original_grid

		# Executar o roque — mover rei e torre
		self.board.move(king_origin, king_end)
		self.board.move(rook_origin, rook_end)

		# Desativar ambos os direitos de roque da cor
		self.castling_rights[color]["kingside"] = False
		self.castling_rights[color]["queenside"] = False

		# Atualizar regra dos 50 movimentos (roque = movimento de rei, não reseta)
		self.fifty_move_counter += 1

		# Registrar posição para repetição
		self.__record_position()

		# Verificar se o roque dá xeque ou xeque-mate
		gives_check = self.board.is_check(enemy_color)
		gives_checkmate = False
		if gives_check:
			gives_checkmate = self.__is_checkmate(enemy_color)

		# Validar o sufixo
		if gives_checkmate and user_suffix != "#":
			# Desfazer o roque
			self.board.move(king_end, king_origin)
			self.board.move(rook_end, rook_origin)
			self.castling_rights[color]["kingside"] = True
			self.castling_rights[color]["queenside"] = True
			return False
		if gives_check and user_suffix != "+" and user_suffix != "#":
			# Desfazer o roque
			self.board.move(king_end, king_origin)
			self.board.move(rook_end, rook_origin)
			self.castling_rights[color]["kingside"] = True
			self.castling_rights[color]["queenside"] = True
			return False
		if not gives_check and user_suffix in ("+", "#"):
			# Desfazer o roque
			self.board.move(king_end, king_origin)
			self.board.move(rook_end, rook_origin)
			self.castling_rights[color]["kingside"] = True
			self.castling_rights[color]["queenside"] = True
			return False

		# Registrar no histórico
		self.move_history.append(notation)
		self.turn_index = (self.turn_index + 1) % len(self.players)
		return True

	def __update_double_pawn_move(
		self, piece: "Piece", origin_pos: Position, end_pos: Position
	) -> None:
		"""Atualiza o tracking de en passant quando peão avança 2 casas.

		Sincroniza com Board.last_double_pawn_move para que Pawn.valid_moves()
		possa acessar via board.
		"""
		from simple_chess.pieces.pawn import Pawn

		if not isinstance(piece, Pawn):
			self.last_double_pawn_move = None
			self.board.last_double_pawn_move = None
			return

		# Peão branco avança de row 6 para row 4 (2 casas)
		# Peão preto avança de row 1 para row 3 (2 casas)
		if piece.color == Color.WHITE and origin_pos.row == 6 and end_pos.row == 4:
			self.last_double_pawn_move = end_pos
			self.board.last_double_pawn_move = end_pos
		elif piece.color == Color.BLACK and origin_pos.row == 1 and end_pos.row == 3:
			self.last_double_pawn_move = end_pos
			self.board.last_double_pawn_move = end_pos
		else:
			self.last_double_pawn_move = None
			self.board.last_double_pawn_move = None

	def __parse_promotion_piece(self, notation: str) -> str | None:
		"""Extrai a peça de promoção da notação (ex: e8=Q -> 'Queen').

		Returns:
			Nome da classe da peça ou None se não for promoção.
		"""
		import re
		match = re.search(r"=([KQRNBkqrnb])", notation)
		if match:
			letter = match.group(1)
			piece_map = {
				"K": "King", "k": "King",
				"Q": "Queen", "q": "Queen",
				"R": "Rook", "r": "Rook",
				"B": "Bishop", "b": "Bishop",
				"N": "Knight", "n": "Knight",
			}
			return piece_map.get(letter)
		return None

	def __promote_pawn(self, pos: Position, piece_class_name: str) -> None:
		"""Substitui o peão na posição pela peça de promoção.

		Args:
			pos: Posição onde o peão foi promovido.
			piece_class_name: Nome da classe da peça (ex: 'Queen').
		"""
		piece = self.board.piece_at(pos)
		if piece is None:
			return

		# Criar a nova peça com a cor do peão
		piece_classes = {
			"King": King,
			"Queen": Queen,
			"Rook": Rook,
			"Bishop": Bishop,
			"Knight": Knight,
		}
		piece_class = piece_classes.get(piece_class_name)
		if piece_class is None:
			return

		new_piece = piece_class(piece.color)
		self.board.place(pos, new_piece)

	def make_move_from_notation(self, notation: str) -> bool:
		"""Executa um movimento a partir de notação algébrica PGN.

		Suporta:
		- "e4" -> peão avança para e4
		- "Nf3" -> Cavalo para f3
		- "Bc4" -> Bispo para c4
		- "Qh5" -> Rainha para h5
		- "Rh1" -> Torre para h1
		- "Ke2" -> Rei para e2
		- "exd5" -> peão em e captura em d5 (obrigatório para capturas)
		- "Nxf3" -> Cavalo captura em f3 (obrigatório para capturas)
		- "e4+" -> movimento que dá xeque (sufixo obrigatório)
		- "e4#" -> movimento que dá xeque-mate (sufixo obrigatório)
		- "O-O" -> roque curto
		- "O-O-O" -> roque longo
		- "e8=Q" -> promoção de peão

		Args:
			notation: String com a notação do movimento.

		Returns:
			True se o movimento foi executado com sucesso.
		"""
		from simple_chess.move_parser import parse_move_notation

		result = parse_move_notation(notation, self)
		if result is None:
			return False

		origin, end, user_suffix = result

		# Detectar roque — O-O e O-O-O
		# O parser retorna origem e destino do rei; o roque é tratado separadamente
		if self.__is_castling_move(origin, end):
			kingside = end.col > origin.col  # kingside = rei vai para a direita
			return self.__execute_castling(kingside, user_suffix, notation)

		# Detectar promoção de peão
		promotion_piece = self.__parse_promotion_piece(notation)

		# Valida o movimento primeiro
		if not self.__is_valid_move(origin, end):
			return False

		# Simula o movimento para verificar se dá xeque ou xeque-mate
		my_color = self.player_turn
		enemy_color = Color.BLACK if my_color == Color.WHITE else Color.WHITE

		# Cria cópia do grid para simulação
		original_grid = self.board.grid
		self.board.grid = [row[:] for row in original_grid]

		# Simula o movimento
		piece = self.board.piece_at(origin)
		self.board.place(origin, None)

		# Se for promoção, simular com a peça promovida
		if promotion_piece is not None:
			piece_classes = {
				"King": King,
				"Queen": Queen,
				"Rook": Rook,
				"Bishop": Bishop,
				"Knight": Knight,
			}
			piece_class = piece_classes.get(promotion_piece)
			if piece_class:
				piece = piece_class(my_color)
		self.board.place(end, piece)

		# Verifica se dá xeque no oponente
		gives_check = self.board.is_check(enemy_color)

		# Verifica se dá xeque-mate (xeque + sem movimentos legais)
		gives_checkmate = False
		if gives_check:
			gives_checkmate = self.__is_checkmate(enemy_color)

		# Restaura o grid original
		self.board.grid = original_grid

		# Valida o sufixo
		if gives_checkmate and user_suffix != "#":
			# Xeque-mate exige "#"
			return False
		if gives_check and user_suffix != "+" and user_suffix != "#":
			# Xeque exige "+" ou "#"
			return False
		if not gives_check and user_suffix in ("+", "#"):
			# Não dá xeque mas o jogador colocou sufixo
			return False

		# Executa o movimento real com promoção se aplicável
		return self.make_move(origin, end, notation, promotion_piece)

	def __is_checkmate(self, color: Color) -> bool:
		"""Verifica se a cor está em xeque-mate.

		Xeque-mate = rei em xeque e sem nenhum movimento legal.
		"""
		if not self.board.is_check(color):
			return False

		# Verifica se a cor tem algum movimento legal
		if self.__has_legal_moves(color):
			return False

		# Nenhum movimento legal encontrado — é xeque-mate
		return True

	def __is_stalemate(self, color: Color) -> bool:
		"""Verifica se a cor está em stalemate (empate).

		Stalemate = rei NÃO em xeque e sem nenhum movimento legal.
		"""
		if self.board.is_check(color):
			return False

		# Verifica se a cor tem algum movimento legal
		if self.__has_legal_moves(color):
			return False

		# Nenhum movimento legal e não está em xeque — é stalemate
		return True

	def __has_legal_moves(self, color: Color) -> bool:
		"""Verifica se a cor tem pelo menos um movimento legal.

		Inclui movimentos normais, en passant e roque.

		Returns:
			True se existe pelo menos um movimento legal.
		"""
		# 1. Movimentos normais de todas as peças
		for row in range(8):
			for col in range(8):
				pos = Position(row, col)
				piece = self.board.piece_at(pos)
				if piece is None or piece.color != color:
					continue
				moves = piece.valid_moves(pos, self.board)
				if moves is None:
					continue
				for move in moves:
					# Simula o movimento
					original_grid = self.board.grid
					self.board.grid = [r[:] for r in original_grid]
					captured = self.board.piece_at(move)
					self.board.place(pos, None)
					self.board.place(move, piece)

					# Verifica se sai do xeque
					in_check = self.board.is_check(color)

					# Restaura
					self.board.grid = original_grid

					if not in_check:
						return True

		# 2. En passant — simular captura ao passar
		# Se há um peão que avançou 2 casas, verificar se um peão inimigo pode capturá-lo
		if self.last_double_pawn_move is not None:
			enemy_pos = self.last_double_pawn_move
			enemy_piece = self.board.piece_at(enemy_pos)
			if enemy_piece is not None:
				from simple_chess.pieces.pawn import Pawn
				# Buscar peões da cor que podem capturar en passant
				for row in range(8):
					for col in range(8):
						pos = Position(row, col)
						piece = self.board.piece_at(pos)
						if piece is None or piece.color != color:
							continue
						if not isinstance(piece, Pawn):
							continue
						moves = piece.valid_moves(pos, self.board)
						if moves is None:
							continue
						for move in moves:
							# Verificar se este movimento é en passant
							if self.__is_en_passant(piece, pos, move):
								# Simular en passant: mover peão e remover peão capturado
								original_grid = self.board.grid
								self.board.grid = [r[:] for r in original_grid]
								# Remover o peão capturado
								captured_pawn_pos = Position(
									move.row + 1 if piece.color == Color.WHITE else move.row - 1,
									move.col
								)
								self.board.place(captured_pawn_pos, None)
								self.board.place(pos, None)
								self.board.place(move, piece)
								in_check = self.board.is_check(color)
								self.board.grid = original_grid
								if not in_check:
									return True

		# 3. Roque — verificar se a cor pode fazer roque
		if self.__can_castling(color, kingside=True):
			return True
		if self.__can_castling(color, kingside=False):
			return True

		return False

	def __can_castling(self, color: Color, kingside: bool) -> bool:
		"""Verifica se a cor pode executar roque (sem executá-lo).

		Usado por __has_legal_moves para não dar falso positivo de mate/stalemate.
		"""
		from simple_chess.pieces.king import King
		from simple_chess.pieces.rook import Rook

		# Verificar direitos de roque
		rights = self.castling_rights[color]
		if kingside:
			if not rights["kingside"]:
				return False
		else:
			if not rights["queenside"]:
				return False

		# Posições do rei e da torre
		if color == Color.WHITE:
			king_row = 7
		else:
			king_row = 0

		king_origin = Position(king_row, 4)
		if kingside:
			king_end = Position(king_row, 6)
			rook_origin = Position(king_row, 7)
			rook_end = Position(king_row, 5)
			passed_squares = [Position(king_row, 5)]
			path_squares = [Position(king_row, 5), Position(king_row, 6)]
		else:
			king_end = Position(king_row, 2)
			rook_origin = Position(king_row, 0)
			rook_end = Position(king_row, 3)
			passed_squares = [Position(king_row, 3), Position(king_row, 2)]
			path_squares = [Position(king_row, 1), Position(king_row, 2), Position(king_row, 3)]

		# Verificar que o rei está na posição inicial
		king_piece = self.board.piece_at(king_origin)
		if king_piece is None or not isinstance(king_piece, King):
			return False

		# Verificar que a torre está na posição inicial
		rook_piece = self.board.piece_at(rook_origin)
		if rook_piece is None or not isinstance(rook_piece, Rook):
			return False

		# Verificar que o caminho está livre
		for pos in path_squares:
			if self.board.piece_at(pos) is not None:
				return False

		# Verificar que o rei não está em xeque
		if self.board.is_check(color):
			return False

		# Verificar que o rei não passa por xeque
		original_grid = self.board.grid
		self.board.grid = [row[:] for row in original_grid]
		self.board.place(king_origin, None)

		for pos in passed_squares:
			self.board.place(pos, king_piece)
			if self.board.is_check(color):
				self.board.grid = original_grid
				return False
			self.board.place(pos, None)

		self.board.grid = original_grid
		return True

	def __update_fifty_move_counter(
		self, piece: "Piece", was_capture: bool
	) -> None:
		"""Atualiza o contador da regra dos 50 movimentos.

		Reseta se houver captura ou movimento de peão.
		Incrementa caso contrário.
		"""
		from simple_chess.pieces.pawn import Pawn

		if was_capture or isinstance(piece, Pawn):
			self.fifty_move_counter = 0
		else:
			self.fifty_move_counter += 1

	def __record_position(self) -> None:
		"""Registra a posição atual do tabuleiro para detectar repetição.

		Gera uma string que representa o estado do tabuleiro incluindo
		peças, direitos de roque e en passant.
		"""
		position_key = self.__generate_position_key()
		self.position_history.append(position_key)

	def __generate_position_key(self) -> str:
		"""Gera uma string única que representa a posição atual.

		Inclui:
		- Posição de todas as peças no tabuleiro
		- Direitos de roque
		- En passant disponível
		- Cor do jogador atual
		"""
		parts = []

		# Peças no tabuleiro
		for row in range(8):
			for col in range(8):
				piece = self.board.piece_at(Position(row, col))
				if piece is not None:
					piece_type = type(piece).__name__[0]  # K, Q, R, B, N, P
					color_char = "W" if piece.color == Color.WHITE else "B"
					parts.append(f"{piece_type}{color_char}{row}{col}")

		# Direitos de roque
		for color in [Color.WHITE, Color.BLACK]:
			rights = self.castling_rights[color]
			color_char = "W" if color == Color.WHITE else "B"
			if rights["kingside"]:
				parts.append(f"{color_char}K")
			if rights["queenside"]:
				parts.append(f"{color_char}Q")

		# En passant
		if self.last_double_pawn_move is not None:
			parts.append(f"EP{self.last_double_pawn_move.row}{self.last_double_pawn_move.col}")

		# Cor do jogador atual
		parts.append("W" if self.player_turn == Color.WHITE else "B")

		return "|".join(parts)

	def __is_insufficient_material(self) -> bool:
		"""Verifica se o material no tabuleiro é insuficiente para xeque-mate.

		Casos de empate:
		- Rei vs Rei
		- Rei + Bispo vs Rei
		- Rei + Cavalo vs Rei
		"""
		white_pieces: list["Piece"] = []
		black_pieces: list["Piece"] = []

		for row in range(8):
			for col in range(8):
				piece = self.board.piece_at(Position(row, col))
				if piece is not None:
					if piece.color == Color.WHITE:
						white_pieces.append(piece)
					else:
						black_pieces.append(piece)

		# Classificar peças por tipo (excluindo reis)
		white_non_kings = [p for p in white_pieces if not isinstance(p, King)]
		black_non_kings = [p for p in black_pieces if not isinstance(p, King)]

		# Rei vs Rei
		if not white_non_kings and not black_non_kings:
			return True

		# Rei + Bispo vs Rei
		if (len(white_non_kings) == 1 and isinstance(white_non_kings[0], Bishop)
				and not black_non_kings):
			return True

		# Rei + Cavalo vs Rei
		if (len(white_non_kings) == 1 and isinstance(white_non_kings[0], Knight)
				and not black_non_kings):
			return True

		# Rei vs Rei + Bispo
		if (not white_non_kings and len(black_non_kings) == 1
				and isinstance(black_non_kings[0], Bishop)):
			return True

		# Rei vs Rei + Cavalo
		if (not white_non_kings and len(black_non_kings) == 1
				and isinstance(black_non_kings[0], Knight)):
			return True

		return False

	def __is_threefold_repetition(self) -> bool:
		"""Verifica se a posição atual ocorreu 3 vezes (repetição de posição).

		Returns:
			True se a posição atual apareceu 3 ou mais vezes no histórico.
		"""
		current_key = self.__generate_position_key()
		count = self.position_history.count(current_key)
		return count >= 3

	def __is_fifty_move_rule(self) -> bool:
		"""Verifica se 50 movimentos foram feitos sem captura ou movimento de peão.

		Returns:
			True se o contador atingiu 100 (50 movimentos de cada lado = 100 half-moves).
		"""
		return self.fifty_move_counter >= 100

	def is_game_over(self) -> bool:
		"""Verifica se o jogo terminou.

		Verifica:
		- Xeque-mate
		- Stalemate
		- Material insuficiente
		- Repetição de posição (3x)
		- Regra dos 50 movimentos

		Returns:
			True se o jogo terminou.
		"""
		color = self.player_turn
		if self.__is_checkmate(color) or self.__is_stalemate(color):
			return True
		if self.__is_insufficient_material():
			return True
		if self.__is_threefold_repetition():
			return True
		if self.__is_fifty_move_rule():
			return True
		return False

	def game_result(self) -> str | None:
		"""Retorna o resultado do jogo, se terminou.

		Returns:
			String com o resultado ou None se o jogo continua.
		"""
		color = self.player_turn
		if self.__is_checkmate(color):
			winner = Color.BLACK if color == Color.WHITE else Color.WHITE
			winner_text = "Pretas" if winner == Color.BLACK else "Brancas"
			return f"Xeque-mate — {winner_text} vencem!"
		if self.__is_stalemate(color):
			return "Empate por stalemate!"
		if self.__is_insufficient_material():
			return "Empate por material insuficiente!"
		if self.__is_threefold_repetition():
			return "Empate por repetição de posição (3x)!"
		if self.__is_fifty_move_rule():
			return "Empate por regra dos 50 movimentos!"
		return None

	def __is_valid_move(self, origin_pos: Position, end_pos: Position) -> bool:
		if not (self.board.in_bounds(origin_pos) or self.board.in_bounds(end_pos)):
			return False

		piece = self.board.piece_at(origin_pos)
		if piece is None or piece.color != self.player_turn:
			return False

		if end_pos not in piece.valid_moves(origin_pos, self.board):
			return False

		# Simula o movimento para verificar se deixa o rei em xeque
		my_color = piece.color

		# Cria uma cópia rasa do grid
		original_grid = self.board.grid
		self.board.grid = [row[:] for row in original_grid]

		# Simula o movimento na cópia
		captured = self.board.piece_at(end_pos)
		self.board.place(origin_pos, None)
		self.board.place(end_pos, piece)

		# Verifica se o rei ficou em xeque
		leaves_in_check = self.board.is_check(my_color)

		# Restaura o grid original
		self.board.grid = original_grid

		if leaves_in_check:
			return False

		return True

	def render_game(self):
		# for l in self.board.render_row(self.player_turn):
		for l in self.board.render_row(Color.WHITE):
			print(l)