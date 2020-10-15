from pygame.sprite import Rect

class GameObject:
	def __init__(self, rect):
		self.rect = rect

	def get_rect(self):
		return Rect((self.get_left(), self.get_top()), (self.get_width(), self.get_height()))

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

	def collides_with(self, rect):
		return self.get_rect().colliderect(rect)
