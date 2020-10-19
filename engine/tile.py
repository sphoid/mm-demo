from pygame import sprite
from pygame.math import Vector2

class Tile(sprite.Sprite):
	def __init__(self, image, stage, *grid_position):
		super().__init__()
		self.image = image
		self.rect = image.get_rect()
		self.position = Vector2(grid_position[0], grid_position[1])
		self.stage = stage

	def get_width(self):
		return self.rect.width

	def get_height(self):
		return self.rect.height

	def get_grid_position(self):
		return self.grid_position

	def get_position(self):
		return self.position

	def get_bottom(self):
		return self.position.y + self.rect.height

	def get_top(self):
		return self.position.y

	def get_left(self):
		return self.position.x

	def get_right(self):
		return self.position.x + self.rect.width

	def update(self, delta):
		p = self.position
		offset = self.stage.get_view().get_offset()
		self.rect.topleft = int(p.x - offset.x), int(p.y - offset.y)
