from pygame.sprite import Rect
from pygame.math import Vector2

class GameObject:
	def __init__(self, rect, name=None, attributes=dict()):
		self.name = name
		self.rect = rect
		self.flagged = False
		self.attributes = attributes

	def is_flagged(self):
		return self.flagged

	def flag(self):
		self.flagged = True

	def unflag(self):
		self.flag = False

	def get_name(self):
		return self.name

	def get_rect(self):
		return Rect((self.get_left(), self.get_top()), (self.get_width(), self.get_height()))

	def get_position(self):
		return Vector2(self.get_left(), self.get_top())

	def get_bottom(self):
		return self.rect.bottom

	def get_top(self):
		return self.rect.top

	def get_left(self):
		return self.rect.left

	def get_right(self):
		return self.rect.right

	def get_width(self):
		return self.rect.width

	def get_height(self):
		return self.rect.height

	def get_size(self):
		return self.get_width(), self.get_height()

	def collides_with(self, rect):
		return self.get_rect().colliderect(rect)
