from pygame import sprite
from pygame.sprite import Rect
from pygame.math import Vector2
import copy

class Entity(sprite.Sprite):
	def __init__(self, view=None):
		super().__init__()

		self.position = Vector2(0, 0)
		self.velocity = Vector2(0, 0)
		self.view = view

		self.gravity = False
		self.falling = False
		self.clip = False

		self.reset_animation = False

	def is_clip_enabled(self):
		return self.clip

	def is_gravity_enabled(self):
		return self.gravity

	def is_falling(self):
		return self.falling

	def fall(self):
		self.falling = True

	def set_view(self, view):
		self.view = view

	def get_view(self):
		return self.view

	def get_position(self):
		return self.position

	def set_position(self, *position):
		self.position.x = position[0]
		self.position.y = position[1]

	def get_bottom(self):
		return int(self.position.y + int(self.get_height() / 2))

	def get_top(self):
		return int(self.position.y - int(self.get_height() / 2))

	def get_left(self):
		return int(self.position.x - int(self.get_width() / 2))

	def get_right(self):
		return int(self.position.x + int(self.get_width() / 2))

	def get_rect(self):
		return Rect((self.get_left(), self.get_top()), (self.get_width(), self.get_height()))

	def get_width(self):
		return self.rect.width

	def get_height(self):
		return self.rect.height

	def accelerate(self, *v):
		self.velocity.x += v[0]
		self.velocity.y += v[1]

	def deccelerate(self, *v):
		self.velocity.x -= v[0]
		self.velocity.y -= v[1]

	def get_velocity(self):
		return self.velocity

	def set_velocity(self, *v):
		self.velocity.x = v[0]
		self.velocity.y = v[1]

	def set_velocity_x(self, v):
		self.velocity.x = v

	def set_velocity_y(self, v):
		self.velocity.y = v

	def stop_x(self):
		self.velocity.x = 0
		self.reset_animation = True

	def stop_y(self):
		self.velocity.y = 0
		self.reset_animation = True

	def collide_bottom(self, y):
		self.velocity.y = 0
		self.position.y = round(y - (self.get_height() / 2))
		self.falling = False
		self.reset_animation = True

	def collide_top(self, y):
		self.velocity.y = 0
		self.position.y = round(y + (self.get_height() / 2))
		self.falling = True
		self.reset_animation = True

	def collide_right(self, x):
		if self.velocity.x > 0:
			self.velocity.x = 0
		self.position.x = round(x - (self.get_width() / 2))
		self.reset_animation = True

	def collide_left(self, x):
		if self.velocity.x < 0:
			self.velocity.x = 0
		self.position.x = round(x + (self.get_width() / 2))
		self.reset_animation = True

	def fall(self):
		self.falling = True

	def collides_with(self, rect):
		return self.get_rect().colliderect(rect)

	def update_position(self, delta):
		v = self.velocity
		self.position.x += v.x
		self.position.y += v.y