from pygame.math import Vector2

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
		return rect.left > self.offset.x and rect.right < self.offset.x + self.get_width() and rect.top > self.offset.y and rect.bottom < self.offset.y + self.get_height()

	def update(self):
		pass
