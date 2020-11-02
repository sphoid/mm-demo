from pygame import sprite
from pygame.sprite import Rect
from pygame.math import Vector2
import copy
from .animation import *

class Entity(sprite.Sprite):
	def __init__(self, spritesheet=None, view=None, position=None, velocity=None, gravity=False, clip=False):
		super().__init__()

		self.rect = Rect(0, 0, 0, 0)
		self.spritesheet = spritesheet
		self.position = Vector2(0, 0) if position is None else Vector2(position[0], position[1])
		self.velocity = Vector2(0, 0) if velocity is None else Vector2(velocity[0], velocity[1])
		self.view = view

		self.gravity = gravity
		self.falling = False
		self.clip = clip

		self.current_time = 0
		self.animation_state = None
		self.reset_animation = False
		self.image = None
		self.rect = None

		if self.spritesheet is not None:
			self.load_sprites()

	def get_animation_states(self):
		return dict()

	def load_sprites(self):
		animations = self.get_animation_states()
		if not animations:
			return

		image_at = self.spritesheet.image_at
		self.animations = dict()
		states = animations['states'] or None

		if states is None:
			return

		for state in states.keys():
			frames = states[state]
			self.animations[state] = Animation(list(map(lambda frame: dict(
				duration=frame['duration'],
				image=image_at(Rect((frame['at'][0], frame['at'][1]), (frame['size'][0], frame['size'][1])), colorkey=frame['colorkey'] if 'colorky' in frame else -1, flip=frame['flip'] if 'flip' in frame else None, alpha=frame['alpha'] if 'alpha' in frame else False),
				callback=frame['callback'] if 'callback' in frame else None
			), frames)))

		self.animation_state = animations['default']

		animation = self.animations[self.animation_state]
		start_frame = animation.current()
		self.image = start_frame['image']
		self.rect = self.image.get_rect()

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

	def get_animation_state(self):
		return None

	def update_state(self, delta):
		pass

	def update_position(self, delta):
		v = self.velocity
		self.position.x += v.x
		self.position.y += v.y

	def update_sprite(self, delta):
		animation = self.animations[self.animation_state] if self.animation_state in self.animations else None

		if animation is None:
			raise SystemError('Invalid animation state')

		if self.reset_animation:
			animation.reset()
			self.reset_animation = False

		self.current_time += delta
		if self.current_time >= animation.next_time:
			prev_center = self.rect.center
			self.image = animation.next(0)['image']
			self.rect.width = self.image.get_rect().width
			self.rect.center = prev_center
			self.current_time = 0

		p = self.position
		offset = self.view.get_offset()
		self.rect.center = int(p.x - offset.x), int(p.y - offset.y)

	def update(self, delta):
		self.update_state(delta)
		self.update_position(delta)
		self.update_sprite(delta)