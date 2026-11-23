"""Testes para Position e Color."""
from simple_chess.color import Color
from simple_chess.position import Position


class TestPosition:
	def test_position_creation(self):
		pos = Position(3, 4)
		assert pos.row == 3
		assert pos.col == 4

	def test_position_equality(self):
		assert Position(2, 3) == Position(2, 3)
		assert Position(2, 3) != Position(3, 2)
		assert Position(0, 0) != Position(7, 7)

	def test_position_hash(self):
		"""Position deve ser hashable para uso em sets e dicts."""
		pos1 = Position(3, 4)
		pos2 = Position(3, 4)
		assert hash(pos1) == hash(pos2)
		assert pos1 in {pos2}

	def test_position_corners(self):
		a1 = Position(7, 0)
		h1 = Position(7, 7)
		a8 = Position(0, 0)
		h8 = Position(0, 7)
		assert a1.row == 7 and a1.col == 0
		assert h1.row == 7 and h1.col == 7
		assert a8.row == 0 and a8.col == 0
		assert h8.row == 0 and h8.col == 7


class TestColor:
	def test_white(self):
		assert Color.WHITE is Color.WHITE

	def test_black(self):
		assert Color.BLACK is Color.BLACK

	def test_colors_different(self):
		assert Color.WHITE != Color.BLACK
