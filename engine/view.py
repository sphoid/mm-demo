from pygame.math import Vector2
from pygame.sprite import Rect

class View:
	def __init__(self, *size):
		self.stage = None
		self.player = None
		self.size = size
		self.offset = Vector2(0, 0)

	def get_size(self):
		return self.size

	def get_width(self):
		w, _ = self.size
		return w

	def get_height(self):
		_, h = self.size
		return h

	def set_offset(self, offset):
		self.offset = offset

	def get_offset(self):
		return self.offset

	def in_view(self, rect):
		vrect = Rect((self.offset.x, self.offset.y), (self.size[0], self.size[1]))
		return rect.colliderect(vrect)
		# return rect.left > self.offset.x and rect.bottom > self.offset.y and rect.top < self.offset.y + self.get_height()

	def in_range(self, rect, distance):
		right = self.offset.x + self.get_width()
		left = self.offset.x
		right_distance = abs(rect.left - right)
		left_distance = abs(left - rect.right)

		return (right_distance < distance and rect.left > right) or (left_distance < distance and rect.right < left)

	def out_of_range(self, rect, distance):
		right = self.offset.x + self.get_width()
		left = self.offset.x
		right_distance = rect.left - right
		left_distance = left - rect.right

		return right_distance > distance or left_distance > distance

	def update(self):
		pass
