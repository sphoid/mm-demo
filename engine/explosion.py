from pygame import sprite
from pygame.sprite import Rect
from pygame.math import Vector2
import copy
from .animation import *

class Explosions:
	def __init__(self, spritesheet_loader):
		self.spritesheet_loader = spritesheet_loader
		self.explosion_sprite_group = sprite.Group()
		self.spritesheet = self.spritesheet_loader.load(self.get_spritesheet_filename())

	def get_spritesheet_filename(self):
		return 'weapon-sprites-2.png'

	def explode(self, view, position):
		explosion = Explosion(self.spritesheet, view, position)
		self.explosion_sprite_group.add(explosion)

	def big_explode(self, view, position):
		vs = [Vector2(0, -2), Vector2(1, -1), Vector2(2, 0), Vector2(1, 1), Vector2(0, 2), Vector2(-1, 1), Vector2(-2, -0), Vector2(-1, -1)]
		for v in vs:
			self.explosion_sprite_group.add(Explosion(self.spritesheet, view, position, loop=True, velocity=v))

	def update(self, delta):
		self.explosion_sprite_group.update(delta)

	def draw(self, surface):
		self.explosion_sprite_group.draw(surface)

class Explosion(sprite.Sprite):
	def __init__(self, spritesheet, view, position, loop=False, velocity=None):
		super().__init__()
		self.spritesheet = spritesheet
		self.position = copy.deepcopy(position)
		self.view = view
		self.animation = None
		self.velocity = velocity
		self.loop = loop
		self.current_time = 0

		# print('v=%d,%d'%(velocity.x, velocity.y))

		self.load_sprites()

	def load_sprites(self):
		image_at = self.spritesheet.image_at

		self.animation = Animation([
			dict(duration=0.1, image=image_at(Rect((48, 10), (16, 16)), -1)),
			dict(duration=0.1, image=image_at(Rect((67, 13), (12, 12)), -1)),
			dict(duration=0.1, image=image_at(Rect((82, 13), (10, 10)), -1)),
			dict(duration=0.1, image=image_at(Rect((84, 16), (4, 4)), -1), callback=self.remove)
		])

		start_frame = self.animation.current()
		self.image = start_frame['image']
		self.rect = self.image.get_rect()

	def remove(self):
		if not self.loop:
			self.kill()

	def update_position(self):
		if self.velocity is not None:
			p, v = self.position, self.velocity
			p.x += v.x
			p.y += v.y

	def update(self, delta):
		self.update_position()

		animation = self.animation
		self.current_time += delta
		if self.current_time >= animation.next_time:
			prev_center = self.rect.center
			self.image = animation.next(0)['image']
			self.rect.width = self.image.get_rect().width
			self.rect.center = prev_center
			self.current_time = 0

		p = self.position
		offset = self.view.get_offset()
		self.rect.center = p.x - offset.x, p.y - offset.y