from simple_chess.board import Board
from simple_chess.color import Color
from simple_chess.position import Position


class Game:
	def __init__(self, board: Board, players: list[Color]):
		self.board = board
		self.players = players
		self.turn_index = 0
		self.captured_pieces = []
		self.move_history: list[str] = []

	@property
	def player_turn(self) -> Color:
		return self.players[self.turn_index]

	def make_move(self, origin_pos: Position, end_pos: Position, notation: str = "") -> bool:
		if self.__is_valid_move(origin_pos, end_pos):
			captured = self.board.move(origin_pos, end_pos)
			if captured is not None:
				self.captured_pieces.append(captured)

			if notation:
				self.move_history.append(notation)

			self.turn_index = (self.turn_index + 1) % len(self.players)
			return True
		return False

	def make_move_from_notation(self, notation: str) -> bool:
		"""Executa um movimento a partir de notação algébrica.

		Suporta:
		- "e4" -> peão avança para e4
		- "Cf3" / "Nf3" -> Cavalo para f3
		- "Bc4" -> Bispo para c4
		- "Qh5" / "Dh5" -> Rainha para h5
		- "Rh1" / "Th1" -> Torre para h1
		- "Ke2" -> Rei para e2
		- "exd5" -> peão em e captura em d5
		- "Cxf3" / "Nxf3" -> Cavalo captura em f3
		- "e2-e4" -> notação longa
		- "e2e4" -> notação completa

		Args:
			notation: String com a notação do movimento.

		Returns:
			True se o movimento foi executado com sucesso.
		"""
		from simple_chess.move_parser import parse_move_notation

		result = parse_move_notation(notation, self)
		if result is None:
			return False

		origin, end = result
		return self.make_move(origin, end, notation)

	def __is_valid_move(self, origin_pos: Position, end_pos: Position) -> bool:
		if not (self.board.in_bounds(origin_pos) or self.board.in_bounds(end_pos)):
			return False

		piece = self.board.piece_at(origin_pos)
		if piece is None or piece.color != self.player_turn:
			return False

		if end_pos not in piece.valid_moves(origin_pos, self.board):
			return False
		return True

	def render_game(self):
		# for l in self.board.render_row(self.player_turn):
		for l in self.board.render_row(Color.WHITE):
			print(l)