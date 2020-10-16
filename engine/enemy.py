import copy
from pygame import sprite, math
from pygame.sprite import Rect
from .constants import *
from .animation import *

class Enemies:
	def __init__(self, spritesheet_loader, sounds, stage):
		self.spritesheet = spritesheet_loader.load(self.get_spritesheet_filename())
		self.stage = stage
		self.sounds = sounds
		self.spawn_range = 100
		self.enemies = dict()
		self.area = Rect(0, 0, round(SCREEN_W / 2), round(SCREEN_H / 2))

	def get_spritesheet_filename(self):
		return 'enemies.png'

	def load(self, name, type, *start_position):
		self.enemies[name] = dict(start_position=start_position, type=type, count=0)

	def spawn_nearby(self, x):
		area, stage = self.area, self.stage

		enemies = list()
		for name, enemy in self.enemies.items():
			start_position = enemy['start_position']
			count = enemy['count']
			if count == 0 and abs(start_position[0] - x) < self.spawn_range and start_position[0] > stage.get_map_right():
				enemy['count'] += 1
				enemies.append(self.spawn(enemy['type'], name, start_position[0], start_position[1]))

		return enemies

	def spawn(self, type, name, *start_position):
		if type == 'spinner':
			print('spawn: spinner pos=%d,%d'%(start_position[0], start_position[1]))
			return Spinner(name, self.spritesheet, self.stage, self.sounds, self, start_position[0], start_position[1])
		else:
			SystemExit('Invalid enemy type %s'%type)

	def kill(self, name):
		self.enemies[name]['count'] -= 1

class Enemy(sprite.Sprite):
	def __init__(self, name, spritesheet, stage, sounds, enemies, *position, **attributes):
		super().__init__()
		self.name = name
		self.spritesheet = spritesheet
		self.enemies = enemies

		if 'direction' in attributes:
			self.direction = attributes['direction']
		else:
			self.direction = 0

		if 'move_speed_x' in attributes:
			self.move_speed_x = attributes['move_speed_x']
		else:
			self.move_speed_x = 0

		if 'move_speed_y' in attributes:
			self.move_speed_y = attributes['move_speed_y']
		else:
			self.move_speed_y = 0

		if 'moving' in attributes and attributes['moving']:
			if self.direction == 1:
				self.velocity = math.Vector2(self.move_speed_x, 0)
			elif self.direction == 0:
				self.velocity = math.Vector2(-self.move_speed_x, 0)
		else:
			self.velocity = math.Vector2(0, 0)

		if 'hit_points' in attributes:
			self.hit_points = attributes['hit_points']
		else:
			self.hit_points = 1

		if 'damage' in attributes:
			self.damage = attributes['damage']
		else:
			self.damage = 1

		self.start_position = math.Vector2(position[0], position[1])
		self.position = self.start_position
		self.stage = stage
		self.sounds = sounds

		self.area = Rect(0, 0, round(SCREEN_W / 2), round(SCREEN_H / 2))

		self.reset_animation = False
		self.current_time = 0

		self.dead = False

	def get_rect(self):
		return Rect((self.get_left(), self.get_top()), (self.get_width(), self.get_height()))

	def get_width(self):
		return self.rect.width

	def get_height(self):
		return self.rect.height

	def get_start_position(self):
		return self.start_position

	def get_position(self):
		return self.position

	def set_position(self, *position):
		self.position.x = int(position[0])
		self.position.y = int(position[1])

	def get_bottom(self):
		return int(self.position.y + int(self.rect.height / 2))

	def get_top(self):
		return int(self.position.y - int(self.rect.height / 2))

	def get_left(self):
		return int(self.position.x - int(self.rect.width / 2))

	def get_right(self):
		return int(self.position.x + int(self.rect.width / 2))

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

	def move_right(self):
		self.direction = 1
		self.accelerate(self.move_speed_x, 0)

	def move_left(self):
		self.direction = 0
		self.accelerate(-self.move_speed_x, 0)

	def stop_x(self):
		self.set_velocity_x(0)

	def move_down(self):
		self.accelerate(0, self.move_speed_y)

	def move_up(self):
		self.accelerate(0, -self.move_speed_y)

	def hit(self, pew):
		damage = pew.get_damage()
		self.hit_points -= damage

		self.sounds.play_sound('edamage')

	def get_damage(self):
		return self.damage

	def die(self):
		self.dead = True

	def collides_with(self, rect):
		return self.get_rect().colliderect(rect)

	def update_position(self):
		v = self.get_velocity()
		self.position.x += v.x
		self.position.y += v.y

	def update_status(self):
		if self.hit_points <= 0:
			self.die()

class Spinner(Enemy):
	def __init__(self, name, spritesheet, stage, sounds, enemies, *position):
		super().__init__(name, spritesheet, stage,sounds, enemies, position[0], position[1], direction=0, move_speed_x=2, move_speed_y=5, moving=True, hit_points=1, damage=4)

		self.load_sprites()

	def load_sprites(self):
		image_at = self.spritesheet.image_at

		self.animations = dict(
			move_left=Animation([
				dict(duration=0.05, image=image_at(Rect((292, 326), (24, 26)), -1)),
				dict(duration=0.05, image=image_at(Rect((332, 326), (24, 26)), -1)),
			]),
			move_right=Animation([
				dict(duration=0.05, image=image_at(Rect((292, 326), (24, 26)), -1, flip=True)),
				dict(duration=0.05, image=image_at(Rect((332, 326), (24, 26)), -1, flip=True)),
			])
		)

		start_frame = self.animations['move_right'].current() if self.direction == 1 else  self.animations['move_left'].current()
		self.image = start_frame['image']
		self.rect = self.image.get_rect()

	def react(self, player):
		v = self.get_velocity()
		pv = player.get_velocity()

		if pv.x > 0 and player.get_right() > self.get_left() - 25 and v.y == 0:
			self.stop_x()
			self.move_down()
		elif pv.x == 0 and player.get_position().x >= self.get_left() and v.y == 0:
			self.stop_x()
			self.move_down()

	def update(self, delta):
		if self.dead:
			self.kill()
			self.enemies.kill(self.name)
		else:
			animation = self.animations['move_right'] if self.direction == 1 else self.animations['move_left']

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
			self.rect.center = int(p.x + self.stage.get_scroll_offset()), int(p.y)

			if self.rect.top > self.area.height:
				self.kill()
				self.enemies.kill(self.name)

