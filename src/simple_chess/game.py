from simple_chess.board import Board
from simple_chess.color import Color
from simple_chess.position import Position


class Game:
	def __init__(self, board: Board, players: list[Color]):
		self.board = board
		self.players = players
		self.turn_index = 0
		self.captured_pieces = []

	@property
	def player_turn(self) -> Color:
		return self.players[self.turn_index]

	def make_move(self, origin_pos: Position, end_pos: Position) -> bool:
		print(self.__is_valid_move(origin_pos, end_pos))
		if self.__is_valid_move(origin_pos, end_pos):
			captured = self.board.move(origin_pos, end_pos)
			if captured is not None:
				self.captured_pieces.append(captured)

			self.turn_index = (self.turn_index + 1) % len(self.players)
			return True
		return False

	def __is_valid_move(self, origin_pos: Position, end_pos: Position):
		if not (self.board.in_bounds(origin_pos) or self.board.in_bounds(end_pos)):
			print("Origin or End position out of board bounds")
			return False

		piece = self.board.piece_at(origin_pos)
		if piece is None or piece.color != self.player_turn:
			print("No piece found on given position or not current player turn")
			return False

		if end_pos not in piece.valid_moves(origin_pos, self.board):
			print("End position is not a valid move")
			return False
		return True

	def render_game(self):
		# for l in self.board.render_row(self.player_turn):
		for l in self.board.render_row(Color.WHITE):
			print(l)