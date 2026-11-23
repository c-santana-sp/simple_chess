from simple_chess.color import Color
from simple_chess.pieces.bishop import Bishop
from simple_chess.pieces.king import King
from simple_chess.pieces.knight import Knight
from simple_chess.pieces.pawn import Pawn
from simple_chess.pieces.piece import Piece
from simple_chess.pieces.queen import Queen
from simple_chess.pieces.rook import Rook
from simple_chess.position import Position


class Board:
	def __init__(self):
		self.grid: list[list[Piece | None]] = [[None for _ in range(8)] for _ in range(8)]
		# En passant — posição do peão que avançou 2 casas no turno anterior
		self.last_double_pawn_move: Position | None = None

	def in_bounds(self, pos: Position) -> bool:
		return 0 <= pos.row < 8 and 0 <= pos.col < 8

	def piece_at(self, pos: Position) -> Piece | None:
		if not self.in_bounds(pos):
			return None
		return self.grid[pos.row][pos.col]

	def is_empty(self, pos: Position) -> bool:
		return self.in_bounds(pos) and self.piece_at(pos) is None

	def is_square_light(self, pos: Position) -> bool:
		return (pos.row + pos.col)   % 2 == 0

	def place(self, pos: Position, piece: Piece | None):
		if self.in_bounds(pos):
			self.grid[pos.row][pos.col] = piece

	def move(self, origin_pos: Position, end_pos: Position) -> Piece | None:
		if not self.in_bounds(end_pos):
			raise ValueError("Invalid end position")

		piece = self.piece_at(origin_pos)
		if piece is None:
			raise ValueError(f"No piece found on position (row:{origin_pos.row}, col:{origin_pos.col}")

		captured = self.piece_at(end_pos)
		self.place(origin_pos, None)
		self.place(end_pos, piece)
		piece.has_moved = True
		return captured

	def setup_initial_position(self):
		# Limpa para n ter chance de problema
		self.grid: list[list[Piece | None]] = [[None for _ in range(8)] for _ in range(8)]

		back_rank_pieces = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
		for col, piece_class in enumerate(back_rank_pieces):
			self.place(Position(0, col), piece_class(Color.BLACK))
			self.place(Position(1, col), Pawn(Color.BLACK))

		for col, piece_class in enumerate(back_rank_pieces):
			self.place(Position(7, col), piece_class(Color.WHITE))
			self.place(Position(6, col), Pawn(Color.WHITE))


	def render_row(self, perspective: Color = Color.WHITE) -> list[str]:
		rows = range(8) if perspective == Color.WHITE else range(7, -1, -1)
		cols = range(8) if perspective == Color.WHITE else range(7, -1, -1)

		lines = []
		for r in rows:
			cells = [str(self.grid[r][c]) if self.grid[r][c] is not None else "." for c in cols]
			lines.append(f"{8 - r} " + " ".join(cells))
		col_labels = "abcdefgh"
		labels_list = list(col_labels) if perspective == Color.WHITE else list(reversed(col_labels))
		lines.append("  " + " ".join(labels_list))
		return lines

	def has_enemy(self, pos: Position, player_color: Color) -> bool:
		piece = self.piece_at(pos)
		return piece is not None and piece.color != player_color

	def find_king(self, color: Color) -> Position | None:
		"""Localiza o rei da cor especificada no grid.

		Returns:
			Position do rei ou None se não encontrado.
		"""
		for row in range(8):
			for col in range(8):
				piece = self.grid[row][col]
				if piece is not None and isinstance(piece, King) and piece.color == color:
					return Position(row, col)
		return None

	def is_check(self, color: Color) -> bool:
		"""Verifica se o rei da cor está em xeque.

		Puramente geométrico: varre todas as peças inimigas e verifica
		se alguma pode atacar a posição do rei usando valid_moves().

		Returns:
			True se o rei está sendo atacado, False caso contrário.
		"""
		king_pos = self.find_king(color)
		if king_pos is None:
			return False

		# Cor inimiga
		enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE

		# Varre todas as peças inimigas
		for row in range(8):
			for col in range(8):
				piece = self.grid[row][col]
				if piece is not None and piece.color == enemy_color:
					moves = piece.valid_moves(Position(row, col), self)
					if king_pos in moves:
						return True
		return False
