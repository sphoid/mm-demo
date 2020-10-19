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

	def update(self):
		pass
