import math, random
from pygame import sprite, time
from pygame.sprite import Rect
from pygame.math import Vector2
from .entity import *
from .constants import *
from .animation import *
from .explosion import *
from .util import *

class Pellet(sprite.Sprite):
	def __init__(self, image, view, damage, velocity, *position):
		super().__init__()
		self.image = image
		self.rect = image.get_rect()
		self.position = Vector2(position[0], position[1])
		self.damage = damage
		self.view = view
		self.velocity = velocity

	def get_rect(self):
		return Rect((self.get_left(), self.get_top()), (self.get_width(), self.get_height()))

	def get_width(self):
		return self.rect.width

	def get_height(self):
		return self.rect.height

	def get_position(self):
		return self.position

	def get_bottom(self):
		return int(self.position.y + int(self.rect.height / 2))

	def get_top(self):
		return int(self.position.y - int(self.rect.height / 2))

	def get_left(self):
		return int(self.position.x - int(self.rect.width / 2))

	def get_right(self):
		return int(self.position.x + int(self.rect.width / 2))

	def collides_with(self, rect):
		return self.get_rect().colliderect(rect)

	def get_damage(self):
		return self.damage

	def update_position(self):
		v = self.velocity
		self.position.x += v.x
		self.position.y += v.y

	def update(self, delta):
		self.update_position()

		offset = self.view.get_offset()
		self.rect.center = int(self.position.x - offset.x), int(self.position.y - offset.y)

class Enemy(Entity):
	def __init__(self, name, spritesheet, view, sounds, enemies, player, stage, *position, **attributes):
		self.name = name
		self.enemies = enemies
		self.player = player
		self.stage = stage
		self.sounds = sounds

		self.falling = False
		self.dead = False
		self.last_hit_by = None

		if 'clip' in attributes:
			clip = attributes['clip']
		else:
			clip = self.get_default_clip()

		if 'gravity' in attributes:
			gravity = attributes['gravity']
		else:
			gravity = self.get_default_gravity()

		if 'direction' in attributes:
			self.direction = attributes['direction']
		else:
			self.direction = self.get_default_direction()

		if 'move_speed_x' in attributes:
			self.move_speed_x = attributes['move_speed_x']
		else:
			self.move_speed_x = self.get_default_move_x_speed()

		if 'move_speed_y' in attributes:
			self.move_speed_y = attributes['move_speed_y']
		else:
			self.move_speed_y = self.get_default_move_y_speed()

		if 'moving' in attributes:
			moving = attributes['moving']
		else:
			moving = self.get_default_moving()

		if moving:
			if self.direction == 1:
				velocity = Vector2(self.move_speed_x, 0)
			elif self.direction == 0:
				velocity = Vector2(-self.move_speed_x, 0)
		else:
			velocity = Vector2(0, 0)

		if 'hit_points' in attributes:
			self.hit_points = attributes['hit_points']
		else:
			self.hit_points = self.get_default_hit_points()

		if 'damage' in attributes:
			self.damage = attributes['damage']
		else:
			self.damage = self.get_default_damage()

		if 'points' in attributes:
			self.points = attributes['points']
		else:
			self.points = self.get_default_points()

		if 'zone' in attributes:
			self.zone = attributes['zone']
		else:
			self.zone = None

		super().__init__(view=view, spritesheet=spritesheet, velocity=velocity, gravity=gravity, clip=clip)

		self.start_position = Vector2(position[0] + (self.get_width() / 2), position[1] + (self.get_height() / 2))
		self.position = Vector2(position[0] + (self.get_width() / 2), position[1] + (self.get_height() / 2))

		print("SPAWN: %s direction=%d position=%r velocity=%r"%(self.name, self.direction, self.position, self.velocity))

	def get_default_clip(self):
		return False

	def get_default_gravity(self):
		return False

	def get_default_move_x_speed(self):
		return 0

	def get_default_move_y_speed(self):
		return 0

	def get_default_direction(self):
		return 0

	def get_default_moving(self):
		return False

	def get_default_hit_points(self):
		return 1

	def get_default_damage(self):
		return 1

	def get_default_points(self):
		return 500

	def get_name(self):
		return self.name

	def get_zone(self):
		return self.zone

	def get_start_position(self):
		return self.start_position

	def move_right(self):
		self.direction = 1
		self.accelerate(self.move_speed_x, 0)

	def move_left(self):
		self.direction = 0
		self.accelerate(-self.move_speed_x, 0)

	def move_down(self):
		self.accelerate(0, self.move_speed_y)

	def move_up(self):
		self.accelerate(0, -self.move_speed_y)

	def hit(self, pew, entity):
		damage = pew.get_damage()
		self.hit_points -= damage
		self.last_hit_by = entity

		self.sounds.play_sound('edamage')

	def get_damage(self):
		return self.damage

	def get_random_loot_type(self, number):
		if number > 2 and number < 50:
			return 'redbonus'
		elif number >= 20 and number <= 22:
			return 'extralife'

		return None

	def react(self, delta):
		pass

	def update_status(self):
		if self.hit_points <= 0 and not self.dead:
			if self.last_hit_by is not None:
				self.last_hit_by.add_points(self.points)
			self.enemies.explode(self)
			self.enemies.kill(self)
			self.dead = True

	def check_off_screen(self):
		pass

	def update(self, delta):
		self.react(delta)
		self.update_status()
		self.check_off_screen()

		super().update(delta)

class Heli(Enemy):
	def __init__(self, name, spritesheet, view, sounds, enemies, player, stage, *position, **attributes):
		attributes['direction'] = 0 if position[0] > player.get_position().x else 1

		self.swooping = False
		self.swoop_direction = 0
		self.swoop_target_y = 0
		self.swoop_original_y = 0
		self.swoop_cooling_down = False
		self.swoop_cooldown_time = 0

		super().__init__(name, spritesheet, view, sounds, enemies, player, stage, *position, **attributes)


	def get_default_clip(self):
		return True

	def get_default_move_x_speed(self):
		return 1

	def get_default_move_y_speed(self):
		return 2

	def get_default_moving(self):
		return True

	def get_default_hit_points(self):
		return 1

	def get_default_damage(self):
		return 4

	def swoop_up(self, y):
		self.swooping = True
		self.swoop_cooling_down = False
		self.move_up()
		self.swoop_direction = 0
		self.swoop_original_y = self.position.y + self.player.get_height()
		self.swoop_target_y = y

	def swoop_down(self, y):
		self.swooping = True
		self.swoop_cooling_down = False
		self.move_down()
		self.swoop_direction = 1
		self.swoop_original_y = self.position.y - self.player.get_height()
		self.swoop_target_y = y

	def move_up(self):
		if self.velocity.y != 0:
			self.velocity.y = -(self.move_speed_y * 2)
		else:
			self.velocity.y = -self.move_speed_y

	def move_down(self):
		if self.velocity.y != 0:
			self.velocity.y = +(self.move_speed_y * 2)
		else:
			self.velocity.y = +self.move_speed_y

	def stop_swooping(self):
		self.velocity.y = 0
		self.swooping = False
		self.swoop_cooling_down = True
		self.swoop_cooldown_time = 0

	def react(self, delta):
		player = self.player
		v = self.get_velocity()
		pv = player.get_velocity()
		p = player.get_position()
		x, y = self.position.x, self.position.y

		if not self.swooping and (not self.swoop_cooling_down or self.swoop_cooldown_time >= 2):
			if player.get_bottom() < y and abs(x - p.x) < 25: # player above
				self.swoop_up(p.y)
			elif player.get_top() > y and abs(x - p.x) < 25: # player below
				self.swoop_down(p.y)

	def update_state(self, delta):
		if self.dead:
			self.enemies.kill(self)
			return

		if self.swooping:
			v = self.velocity
			y = self.position.y
			if self.swoop_direction == 1:
				if v.y > 0 and y >= self.swoop_target_y:
					self.move_up()
				elif v.y < 0 and y <= self.swoop_original_y:
					self.stop_swooping()
			else:
				if v.y < 0 and y <= self.swoop_target_y:
					self.move_down()
				elif v.y > 0 and y >= self.swoop_original_y:
					self.stop_swooping()
		elif self.swoop_cooling_down:
			self.swoop_cooldown_time += delta

		self.animation_state = 'move_right' if self.direction == 1 else 'move_left'

class BlueHeli(Heli):
	def get_animation_states(self):
		return dict(
			states=dict(
				move_left = [
					dict(at=(376, 329), size=(16, 20), duration=0.05),
					dict(at=(416, 329), size=(16, 20), duration=0.05),
				],
				move_right = [
					dict(at=(376, 329), size=(16, 20), duration=0.05, flip='x'),
					dict(at=(416, 329), size=(16, 20), duration=0.05, flip='x'),
				]
			),
			default = 'move_right' if self.direction == 1 else 'move_left'
		)

class GreenHeli(Heli):
	def get_animation_states(self):
		return dict(
			states=dict(
				move_left = [
					dict(at=(296, 329), size=(16, 20), duration=0.05),
					dict(at=(336, 329), size=(16, 20), duration=0.05),
				],
				move_right = [
					dict(at=(292, 329), size=(16, 20), duration=0.05, flip='x'),
					dict(at=(336, 329), size=(16, 20), duration=0.05, flip='x'),
				]
			),
			default = 'move_right' if self.direction == 1 else 'move_left'
		)

class ScrewDriver(Enemy):
	def __init__(self, name, spritesheet, view, sounds, enemies, player, stage, *position, **attributes):
		self.active = False
		self.deactivating = False
		self.pellet_speed = 1
		self.shots = 0
		self.cooldown_time = 0

		super().__init__(name, spritesheet, view, sounds, enemies, player, stage, position[0], position[1], **attributes)

	def get_default_hit_points(self):
		return 3

	def get_default_damage(self):
		return 4

	def activate(self):
		self.active = True
		self.shots = 0
		self.reset_animation = True

	def start_deactivating(self):
		self.deactivating = True

	def deactivate(self):
		if self.deactivating:
			self.deactivating = False
			self.active = False
			self.cooldown_time = 3
			self.reset_animation = True

	def calculate_pellet_velocity(self, angle):
		shoot_speed = 1
		radians = math.radians(angle)
		vx = shoot_speed * math.cos(radians)
		vy = shoot_speed * math.sin(radians)

		return Vector2(vx, vy)

	def shoot(self):
		if self.direction == 1:
			angles = [45, 90, 135, 180, 360]
		else:
			angles = [180, 225, 270, 315, 360]

		p = self.position
		for angle in angles:
			v = calculate_velocity(self.pellet_speed, angle)
			pellet = Pellet(self.pellet_image, self.view, self.damage, v, p.x, p.y)
			self.enemies.shoot(pellet)

		self.shots += 1
		if self.shots == 2:
			self.start_deactivating()

		self.sounds.play_sound('eshoot')

	def react(self, delta):
		if not self.active and self.cooldown_time > 0:
			return

		view = self.view
		ppos = self.player.get_position()
		pos = self.get_position()

		if abs(pos.x - ppos.x) <= 75 and not self.active and not self.deactivating:
			self.activate()

	def update_state(self, delta):
		if self.cooldown_time > 0:
			self.cooldown_time -= delta

		if self.active:
			self.animation_state = 'active_down' if self.direction == 1 else 'active_up'
		else:
			self.animation_state = 'inactive_down' if self.direction == 1 else 'inactive_up'

	def update_sprite(self, delta):
		super().update_sprite(delta)

		if self.active:
			offset = 0
		else:
			offset = -1 if self.direction == 1 else 9

		self.rect.center = self.rect.center[0], self.rect.center[1] + offset

class OrangeScrewDriver(ScrewDriver):
	def load_sprites(self):
		image_at = self.spritesheet.image_at
		self.pellet_image = image_at(Rect((281, 96), (6, 6)), colorkey=-1)
		super().load_sprites()

	def get_animation_states(self):
		return dict(
			states=dict(
				active_up = [
					dict(at=(296, 91), size=(16, 16), duration=0.1),
					dict(at=(335, 91), size=(16, 16), duration=0.1),
					dict(at=(376, 91), size=(16, 16), duration=0.1),
					dict(at=(296, 91), size=(16, 16), duration=0.1),
					dict(at=(335, 91), size=(16, 16), duration=0.1),
					dict(at=(376, 91), size=(16, 16), duration=0.1, callback=self.shoot),
					dict(at=(296, 91), size=(16, 16), duration=0.1),
					dict(at=(335, 91), size=(16, 16), duration=0.1),
					dict(at=(376, 91), size=(16, 16), duration=0.1),
					dict(at=(296, 91), size=(16, 16), duration=0.1),
					dict(at=(335, 91), size=(16, 16), duration=0.1),
					dict(at=(376, 91), size=(16, 16), duration=0.1, callback=self.deactivate)
				],
				inactive_up = [
					dict(at=(416, 95), size=(16,8), duration=0.1),
				],
				active_down = [
					dict(at=(296, 91), size=(16, 16), duration=0.1, flip='y'),
					dict(at=(335, 91), size=(16, 16), duration=0.1, flip='y'),
					dict(at=(376, 91), size=(16, 16), duration=0.1, flip='y'),
					dict(at=(296, 91), size=(16, 16), duration=0.1, flip='y'),
					dict(at=(335, 91), size=(16, 16), duration=0.1, flip='y'),
					dict(at=(376, 91), size=(16, 16), duration=0.1, flip='y', callback=self.shoot),
					dict(at=(296, 91), size=(16, 16), duration=0.1, flip='y'),
					dict(at=(335, 91), size=(16, 16), duration=0.1, flip='y'),
					dict(at=(376, 91), size=(16, 16), duration=0.1, flip='y'),
					dict(at=(296, 91), size=(16, 16), duration=0.1, flip='y'),
					dict(at=(335, 91), size=(16, 16), duration=0.1, flip='y'),
					dict(at=(376, 91), size=(16, 16), duration=0.1, flip='y', callback=self.deactivate)
				],
				inactive_down = [
					dict(at=(416, 95), size=(16,8), duration=0.1, flip='y'),
				],
			),
			default = 'inactive_down' if self.direction == 1 else 'inactive_up'
		)

class Blaster(Enemy):
	def __init__(self, name, spritesheet, view, sounds, enemies, player, stage, *position, **attributes):
		self.active = False
		self.deactivating = False
		self.shooting = False
		self.open = False
		self.shots_fired = 0
		self.shoot_time = 0
		self.shot_frequency = 0.75
		self.max_shots = 4
		self.pellet_speed = 1

		super().__init__(name, spritesheet, view, sounds, enemies, player, stage, position[0], position[1], **attributes)

	def get_default_hit_points(self):
		return 1

	def get_default_damage(self):
		return 2

	def set_open(self):
		self.open = True

	def set_closed(self):
		self.open = False

	def close_and_deactivate(self):
		self.set_closed()

		if self.deactivating:
			self.set_inactive()

	def start_shooting(self):
		if self.direction == 0:
			self.angles = [130, 160, 190, 220]
		else:
			self.angles = [50, 20, 350, 320]

		self.shooting = True
		self.shoot_time = 0
		self.shots_fired = 0

	def calculate_pellet_velocity(self, angle):
		shoot_speed = 1
		radians = math.radians(angle)
		vx = shoot_speed * math.cos(radians)
		vy = shoot_speed * math.sin(radians)

		return Vector2(vx, vy)

	def shoot(self):
		v = calculate_velocity(self.pellet_speed, self.angles.pop())
		p = self.position
		pellet = Pellet(self.pellet_image, self.view, self.damage, v, p.x, p.y)
		self.enemies.shoot(pellet)
		self.sounds.play_sound('eshoot')
		self.shoot_time = 0
		self.shots_fired += 1

	def stop_shooting(self):
		self.shooting = False

	def activate(self):
		self.deactivating = False
		self.active = True
		self.reset_animation = True

	def set_inactive(self):
		self.active = False
		self.deactivating = False

	def deactivate(self):
		self.deactivating = True

	def react(self, delta):
		view = self.view
		ppos = self.player.get_position()
		pos = self.get_position()

		if abs(pos.x - ppos.x) <= 100 and not self.active:
			self.activate()
		elif self.active:
			self.deactivate()

	def hit(self, pew, entity):
		if self.open:
			super().hit(pew, entity)
		else:
			self.sounds.play_sound('dink')

	def check_pew_off_screen(self):
		for pew in self.pew_sprite_group:
			if not self.view.in_view(pew.get_rect()):
				pew.kill()

	def update_state(self, delta):
		if self.dead:
			return

		if self.active:
			self.animation_state = 'shoot_right' if self.direction == 1 else 'shoot_left'

			if self.shooting:
				self.shoot_time += delta

				if self.shots_fired == 0 or self.shoot_time >= self.shot_frequency:
					self.shoot()

				if self.shots_fired == self.max_shots:
					self.stop_shooting()
		else:
			self.animation_state = 'still_right' if self.direction == 1 else 'still_left'

class BlueBlaster(Blaster):
	def load_sprites(self):
		image_at = self.spritesheet.image_at
		self.pellet_image = image_at(Rect((281, 296), (6, 6)), colorkey=-1)
		super().load_sprites()

	def get_animation_states(self):
		return dict(
			states=dict(
				shoot_left = [
					dict(at=(412, 291), size=(16, 16), duration=1.5, callback=self.set_closed),
					dict(at=(372, 291), size=(16, 16), duration=0.25, callback=self.set_open),
					dict(at=(332, 291), size=(16, 16), duration=0.25),
					dict(at=(295, 291), size=(16, 16), duration=3.5, callback=self.start_shooting),
					dict(at=(332, 291), size=(16, 16), duration=0.25),
					dict(at=(372, 291), size=(16, 16), duration=0.25),
					dict(at=(412, 291), size=(16, 16), duration=0.5, callback=self.close_and_deactivate),
				],
				shoot_right = [
					dict(at=(412, 291), size=(16, 16), duration=1.5, flip='x', callback=self.set_closed),
					dict(at=(372, 291), size=(16, 16), duration=0.25, flip='x', callback=self.set_open),
					dict(at=(332, 291), size=(16, 16), duration=0.25, flip='x',),
					dict(at=(295, 291), size=(16, 16), duration=3.5, flip='x', callback=self.start_shooting),
					dict(at=(332, 291), size=(16, 16), duration=0.25, flip='x',),
					dict(at=(372, 291), size=(16, 16), duration=0.25, flip='x',),
					dict(at=(412, 291), size=(16, 16), duration=0.5, flip='x', callback=self.close_and_deactivate),
				],
				still_left = [
					dict(at=(412, 291), size=(16, 16), duration=1.0),
				],
				still_right = [
					dict(at=(412, 291), size=(16, 16), duration=1.0, flip='x'),
				]
			),
			default = 'still_right' if self.direction == 1 else 'still_left'
		)

class RedBlaster(Blaster):
	def load_sprites(self):
		image_at = self.spritesheet.image_at
		self.pellet_image = image_at(Rect((281, 256), (6, 6)), colorkey=-1)
		super().load_sprites()

	def get_animation_states(self):
		return dict(
			states=dict(
				shoot_left = [
					dict(at=(412, 251), size=(16, 16), duration=1.5, callback=self.set_closed),
					dict(at=(332, 251), size=(16, 16), duration=0.25, callback=self.set_open),
					dict(at=(372, 251), size=(16, 16), duration=0.25),
					dict(at=(295, 251), size=(16, 16), duration=3.5, callback=self.start_shooting),
					dict(at=(372, 251), size=(16, 16), duration=0.25),
					dict(at=(332, 251), size=(16, 16), duration=0.25),
					dict(at=(412, 251), size=(16, 16), duration=0.5, callback=self.close_and_deactivate),
				],
				shoot_right = [
					dict(at=(412, 251), size=(16, 16), duration=1.5, flip='x', callback=self.set_closed),
					dict(at=(332, 251), size=(16, 16), duration=0.25, flip='x', callback=self.set_open),
					dict(at=(372, 251), size=(16, 16), duration=0.25, flip='x'),
					dict(at=(295, 251), size=(16, 16), duration=3.5, flip='x', callback=self.start_shooting),
					dict(at=(372, 251), size=(16, 16), duration=0.25, flip='x'),
					dict(at=(332, 251), size=(16, 16), duration=0.25, flip='x'),
					dict(at=(412, 251), size=(16, 16), duration=0.5, flip='x', callback=self.close_and_deactivate),
				],
				still_left = [
					dict(at=(412, 251), size=(16,16), duration=1.0),
				],
				still_right = [
					dict(at=(412, 251), size=(16,16), duration=1.0, flip='x'),
				]
			),
			default = 'still_right' if self.direction == 1 else 'still_left'
		)

class OrangeBlaster(Blaster):
	def load_sprites(self):
		image_at = self.spritesheet.image_at
		self.pellet_image = image_at(Rect((281, 216), (6, 6)), colorkey=-1)
		super().load_sprites()

	def get_animation_states(self):
		return dict(
			states=dict(
				shoot_left = [
					dict(at=(412, 211), size=(16, 16), duration=1.5, callback=self.set_closed),
					dict(at=(372, 211), size=(16, 16), duration=0.25, callback=self.set_open),
					dict(at=(332, 211), size=(16, 16), duration=0.25),
					dict(at=(295, 211), size=(16, 16), duration=3.5, callback=self.start_shooting),
					dict(at=(332, 211), size=(16, 16), duration=0.25),
					dict(at=(372, 211), size=(16, 16), duration=0.25),
					dict(at=(412, 211), size=(16, 16), duration=0.5, callback=self.close_and_deactivate),
				],
				shoot_right = [
					dict(at=(412, 211), size=(16, 16), duration=1.5, flip='x', callback=self.set_closed),
					dict(at=(372, 211), size=(16, 16), duration=0.25, flip='x', callback=self.set_open),
					dict(at=(332, 211), size=(16, 16), duration=0.25, flip='x',),
					dict(at=(295, 211), size=(16, 16), duration=3.5, flip='x', callback=self.start_shooting),
					dict(at=(332, 211), size=(16, 16), duration=0.25, flip='x',),
					dict(at=(372, 211), size=(16, 16), duration=0.25, flip='x',),
					dict(at=(412, 211), size=(16, 16), duration=0.5, flip='x', callback=self.close_and_deactivate),
				],
				still_left = [
					dict(at=(412, 211), size=(16,16), duration=1.0),
				],
				still_right = [
					dict(at=(412, 211), size=(16,16), duration=1.0, flip='x'),
				]
			),
			default = 'still_right' if self.direction == 1 else 'still_left'
		)

class Cutter(Enemy):
	def __init__(self, name, spritesheet, view, sounds, enemies, player, stage, *position, **attributes):
		attributes['direction'] = 0 if position[0] > player.get_position().x else 1

		super().__init__(name, spritesheet, view, sounds, enemies, player, stage, position[0], position[1], **attributes)

		if self.direction:
			self.angle = 45
		else:
			self.angle = -45

		self.jumping = False
		self.move_time = 0

	def get_default_clip(self):
		return True

	def get_default_move_x_speed(self):
		return 5

	def get_default_move_y_speed(self):
		return 5

	def get_default_hit_points(self):
		return 3

	def get_default_damage(self):
		return 8

	def get_animation_states(self):
		return dict(
			states=dict(
				move_left = [
					dict(at=(216, 9), size=(16,20), duration=0.1),
					dict(at=(176, 12), size=(16,20), duration=0.1),
				],
				move_right = [
					dict(at=(216, 9), size=(16,20), duration=0.1, flip='x'),
					dict(at=(176, 12), size=(16,20), duration=0.1, flip='x'),
				],
			),
			default = 'move_right' if self.direction == 1 else 'move_left'
		)

	def jump(self, angle, target, delta):
		self.jumping = True
		self.angle = angle
		self.jump_start_time = delta
		self.jump_time = 0
		self.jump_velocity = 17

	def react(self, delta):
		if not self.jumping:
			player = self.player
			p = player.get_position()
			x, y = self.position.x, self.position.y

			if p.x < x and x - p.x < 75:
				self.jump(-45, p, delta)
			elif p.x > x and p.x - x < 75:
				self.jump(45, p, delta)

	def update_position(self, delta):
		if self.jumping:
			self.jump_time += delta
			time_diff = (self.jump_time - self.jump_start_time) * 7
			if time_diff > 0:
				half_gravity_time_squared = GRAVITY * (time_diff * time_diff) * 0.5
				displacement_x = self.jump_velocity * math.sin(self.angle) * time_diff
				displacement_y = self.jump_velocity * math.cos(self.angle) * time_diff - half_gravity_time_squared

				start_x, start_y = self.start_position.x, self.start_position.y

				self.position.x = start_x + int(displacement_x)
				self.position.y = start_y - int(displacement_y)

	def update_state(self, delta):
		self.animation_state = 'move_right' if self.direction == 1 else 'move_left'

class Flea(Enemy):
	def __init__(self, name, spritesheet, view, sounds, enemies, player, stage, *position, **attributes):
		self.jump_speed = 8
		self.jumping = False
		self.compressed = False

		attributes['direction'] = 0 if position[0] > player.get_position().x else 1
		super().__init__(name, spritesheet, view, sounds, enemies, player, stage, position[0], position[1], **attributes)

	def get_default_gravity(self):
		return True

	def get_default_moving(self):
		return False

	def get_default_move_x_speed(self):
		return 2

	def get_default_hit_points(self):
		return 1

	def get_default_damage(self):
		return 4

	def collide_bottom(self, y):
		self.compressed = True
		self.stop_x()

		super().collide_bottom(y)

	def get_height(self):
		return 16

	def jump(self):
		self.jumping = True
		self.compressed = False
		x_speed = self.move_speed_x if self.direction == 1 else -self.move_speed_x
		self.accelerate(x_speed, -self.jump_speed)

	def react(self, delta):
		player = self.player
		p = player.get_position()
		x, y = self.position.x, self.position.y

		if p.x < x:
			self.direction = 0
		elif p.x > x:
			self.direction = 1

	def update_state(self, delta):
		self.animation_state = 'compressed' if self.compressed else 'uncompressed'

class BlueFlea(Flea):
	def get_animation_states(self):
		return dict(
			states=dict(
				compressed = [
					dict(at=(137, 165), size=(14, 19), duration=0.75),
					dict(at=(137, 165), size=(14, 19), duration=0.5, callback=self.jump),
				],
				uncompressed = [
					dict(at=(177, 169), size=(14, 19), duration=0.75),
				],
			),
			default = 'uncompressed'
		)

class RedFlea(Flea):
	def get_animation_states(self):
		return dict(
			states=dict(
				compressed = [
					dict(at=(137, 125), size=(14, 19), duration=0.75),
					dict(at=(137, 125), size=(14, 19), duration=0.5, callback=self.jump),
				],
				uncompressed = [
					dict(at=(177, 129), size=(14, 19), duration=0.75),
				],
			),
			default = 'uncompressed'
		)

class OctoBattery(Enemy):
	def __init__(self, name, spritesheet, view, sounds, enemies, player, stage, *position, **attributes):
		self.transitioning = False
		self.open = False
		self.opening = False
		self.closing = False

		if 'axis' in attributes:
			self.axis = attributes['axis']
		else:
			self.axis = self.get_default_axis()

		super().__init__(name, spritesheet, view, sounds, enemies, player, stage, position[0], position[1], **attributes)

	def get_default_axis(self):
		return 'x'

	def get_default_move_x_speed(self):
		return 2

	def get_default_move_y_speed(self):
		return 2

	def get_default_hit_points(self):
		return 5

	def get_default_damage(self):
		return 8

	def get_random_loot_type(self, number):
		return None

	def collide_bottom(self, y):
		super().collide_bottom(y)
		self.direction = 0
		self.start_closing()

	def collide_top(self, y):
		super().collide_top(y)
		self.direction = 1
		self.start_closing()

	def collide_right(self, x):
		super().collide_right(x)
		self.direction = 0
		self.start_closing()

	def collide_left(self, x):
		super().collide_left(x)
		self.direction = 1
		self.start_closing()

	def start_opening(self):
		self.open = False
		self.opening = True
		self.closing = False
		self.reset_animation = True

	def start_closing(self):
		self.open = False
		self.opening = False
		self.closing = True
		self.reset_animation = True

	def open_eye(self):
		self.opening = False
		self.closing = False
		self.open = True
		self.reset_animation = True

	def close_eye(self):
		self.opening = False
		self.closing = False
		self.open = False
		self.reset_animation = True

	def move(self):
		self.start_opening()
		self.reset_animation = True

		if self.axis == 'x':
			x_speed = self.move_speed_x if self.direction == 1 else -self.move_speed_x
			y_speed = 0
		elif self.axis == 'y':
			x_speed = 0
			y_speed = self.move_speed_y if self.direction == 1 else -self.move_speed_y

		self.accelerate(x_speed, y_speed)
		self.start_opening()

	def update_state(self, delta):
		if self.opening:
			self.animation_state = 'opening'
		elif self.closing:
			self.animation_state = 'closing'
		elif self.open:
			self.animation_state = 'open'
		else:
			self.animation_state = 'closed'

class RedOctoBattery(OctoBattery):
	def get_animation_states(self):
		return dict(
			states=dict(
				closed = [
					dict(at=(96, 131), size=(16, 16), duration=2),
					dict(at=(96, 131), size=(16, 16), duration=2, callback=self.move),
				],
				opening = [
					dict(at=(57, 131), size=(16, 16), duration=0.5, callback=self.open_eye),
				],
				closing = [
					dict(at=(57, 131), size=(16, 16), duration=0.5, callback=self.close_eye),
				],
				open = [
					dict(at=(16, 131), size=(16, 16), duration=0.5),
				],
			),
			default = 'closed'
		)

class BlueOctoBattery(OctoBattery):
	def get_animation_states(self):
		return dict(
			states=dict(
				closed = [
					dict(at=(96, 171), size=(16, 16), duration=2),
					dict(at=(96, 171), size=(16, 16), duration=2, callback=self.move),
				],
				opening = [
					dict(at=(57, 131), size=(16, 16), duration=0.5, callback=self.open_eye),
				],
				closing = [
					dict(at=(57, 171), size=(16, 16), duration=0.5, callback=self.close_eye),
				],
				open = [
					dict(at=(16, 171), size=(16, 16), duration=0.5),
				],
			),
			default = 'closed'
		)

class OrangeOctoBattery(OctoBattery):
	def get_animation_states(self):
		return dict(
			states=dict(
				closed = [
					dict(at=(96, 91), size=(16, 16), duration=2),
					dict(at=(96, 91), size=(16, 16), duration=2, callback=self.move),
				],
				opening = [
					dict(at=(57, 91), size=(16, 16), duration=0.5, callback=self.open_eye),
				],
				closing = [
					dict(at=(57, 91), size=(16, 16), duration=0.5, callback=self.close_eye),
				],
				open = [
					dict(at=(16, 91), size=(16, 16), duration=0.5),
				],
			),
			default = 'closed'
		)

class Mambu(Enemy):
	def __init__(self, name, spritesheet, view, sounds, enemies, player, stage, *position, **attributes):
		self.pellet_speed = 1

		super().__init__(name, spritesheet, view, sounds, enemies, player, stage, position[0], position[1], **attributes)

	def get_default_clip(self):
		return True

	def get_default_moving(self):
		return True

	def get_default_move_x_speed(self):
		return 1

	def get_default_hit_points(self):
		return 1

	def get_default_damage(self):
		return 2

	def load_sprites(self):
		image_at = self.spritesheet.image_at
		self.pellet_image = image_at(Rect((121, 96), (6, 6)), -1)
		super().load_sprites()

	def get_animation_states(self):
		return dict(
			states=dict(
				default = [
					dict(at=(136, 91), size=(16, 16), duration=1),
					dict(at=(136, 91), size=(16, 16), duration=0.5, callback=self.stop),
					dict(at=(176, 88), size=(17, 21), duration=0.5, callback=self.shoot),
					dict(at=(176, 88), size=(17, 21), duration=0.5, callback=self.move),
				],
			),
			default = 'default'
		)

	def stop(self):
		self.velocity.x = 0

	def shoot(self):
		angles = [45, 90, 135, 180, 225, 270, 315, 360]
		p = self.position
		for angle in angles:
			v = calculate_velocity(self.pellet_speed, angle)
			pellet = Pellet(self.pellet_image, self.view, self.damage, v, p.x, p.y)
			self.enemies.shoot(pellet)

		self.sounds.play_sound('eshoot')

	def move(self):
		vx = -self.move_speed_x if self.direction == 0 else self.move_speed_x
		self.accelerate(vx, 0)

	def hit(self, pew, entity):
		if self.moving:
			self.sounds.play_sound('dink')
		else:
			super().hit(pew, entity)

class BigEye(Enemy):
	def __init__(self, name, spritesheet, view, sounds, enemies, player, stage, *position, **attributes):
		self.normal_jump_speed = 4
		self.high_jump_speed = 8
		self.jumping = False
		self.compressed = False

		attributes['direction'] = 0 if position[0] > player.get_position().x else 1
		super().__init__(name, spritesheet, view, sounds, enemies, player, stage, position[0], position[1], **attributes)

	def get_default_gravity(self):
		return True

	def get_default_moving(self):
		return False

	def get_default_move_x_speed(self):
		return 1

	def get_default_hit_points(self):
		return 24

	def get_default_damage(self):
		return 14

	def collide_bottom(self, y):
		self.compressed = True
		self.stop_x()

		super().collide_bottom(y)

	def get_jump_speed(self):
		num = random.randint(1, 3)
		return self.high_jump_speed if num == 3 else self.normal_jump_speed

	def jump(self):
		self.jumping = True
		self.compressed = False
		rect = self.get_rect()

		if self.direction == 1:
			x_speed = 0 if self.stage.platform_right_adjacent(rect) else self.move_speed_x
		elif self.direction == 0:
			x_speed = 0 if self.stage.platform_left_adjacent(rect) else -self.move_speed_x

		self.accelerate(x_speed, -self.get_jump_speed())

	def react(self, delta):
		player = self.player
		p = player.get_position()
		x, y = self.position.x, self.position.y

		if p.x < x:
			self.direction = 0
		elif p.x > x:
			self.direction = 1

	def update_state(self, delta):
		if self.compressed:
			self.animation_state = 'compressed_right' if self.direction == 1 else 'compressed_left'
		else:
			self.animation_state = 'uncompressed_right' if self.direction == 1 else 'uncompressed_left'

class RedBigEye(BigEye):
	def get_animation_states(self):
		return dict(
			states=dict(
				compressed_left = [
					dict(at=(88, 201), size=(32, 48), duration=0.75),
					dict(at=(88, 201), size=(32, 48), duration=0.5, callback=self.jump),
				],
				compressed_right = [
					dict(at=(88, 201), size=(32, 48), duration=0.75, flip='x'),
					dict(at=(88, 201), size=(32, 48), duration=0.5, flip='x', callback=self.jump),
				],
				uncompressed_left = [
					dict(at=(88, 265), size=(32, 48), duration=0.1),
				],
				uncompressed_right = [
					dict(at=(88, 265), size=(32, 48), duration=0.1, flip='x'),
				],
			),
			default = 'uncompressed_right' if self.direction == 1 else 'uncompressed_left'
		)

ENEMY_CLASS=dict(
	blueheli = BlueHeli,
	greenheli = GreenHeli,
	bluebblaster = BlueBlaster,
	redblaster = RedBlaster,
	orangeblaster = OrangeBlaster,
	cutter = Cutter,
	blueflea = BlueFlea,
	redflea = RedFlea,
	blueoctobattery = BlueOctoBattery,
	redoctobattery = RedOctoBattery,
	orangeoctobattery = OrangeOctoBattery,
	mambu = Mambu,
	redbigeye = RedBigEye,
	orangescrewdriver = OrangeScrewDriver,
)

class Enemies:
	def __init__(self, spritesheet_loader, sounds, view, stage, explosions, items):
		self.spritesheet = spritesheet_loader.load(self.get_spritesheet_filename())
		self.view = view
		self.sounds = sounds
		self.spawn_range = 50
		self.enemies = dict()
		self.explosions = explosions
		self.items = items
		self.stage = stage
		self.enemy_sprite_group = sprite.Group()
		self.pew_sprite_group = sprite.Group()

	def get_spritesheet_filename(self):
		return 'enemies.png'

	def load(self, name, type, *start_position, **attributes):
		self.enemies[name] = dict(start_position=start_position, type=type, count=0, attributes=attributes)

	def spawn_nearby(self, player, zone, zoned):
		view = self.view
		vw, vh = view.get_width(), view.get_height()
		offset = view.get_offset()

		zenemies = list(filter((lambda name: 'zone' in self.enemies[name]['attributes'] and self.enemies[name]['attributes']['zone'] == zone.get_name()), self.enemies.keys()))

		enemies = list()
		for name in zenemies:
			enemy = self.enemies[name]
			start_position = enemy['start_position']
			count = enemy['count']
			spawn_in_view = enemy['attributes']['spawn_in_view'] if 'spawn_in_view' in enemy['attributes'] else False
			if count == 0:
				spawn = False
				if zoned or spawn_in_view:
					spawn_range = enemy['attributes']['spawn_range'] if 'spawn_range' in enemy['attributes'] else -1
					in_view = view.in_view(Rect((start_position[0], start_position[1]), (16, 16)))
					if (spawn_range > -1 and in_view and abs(start_position[0] - player.get_position().x) < self.spawn_range) or (spawn_range == -1 and in_view):
						spawn = True
				elif view.in_range(Rect((start_position[0], start_position[1]), (16, 16)), self.spawn_range):
					spawn = True

				if spawn:
					enemy['count'] += 1
					spawned_enemy = self.spawn(enemy['type'], name, player, start_position[0], start_position[1], **enemy['attributes'])
					if spawned_enemy is not None:
						enemies.append(spawned_enemy)

	def spawn(self, type, name, player, *start_position, **attributes):
		if type in ENEMY_CLASS:
			enemy_class = ENEMY_CLASS[type]
		else:
			print('ERROR: Unknown enemy type %s'%type)
			return None

		enemy = enemy_class(name, self.spritesheet, self.view, self.sounds, self, player, self.stage, start_position[0], start_position[1], **attributes)

		self.enemy_sprite_group.add(enemy)

	def get_enemies(self):
		return self.enemy_sprite_group

	def shoot(self, pew):
		self.pew_sprite_group.add(pew)

	def explode(self, enemy):
		x, y = enemy.get_rect().center
		self.explosions.explode(self.view, Vector2(x, y))

	def update_pew_positions(self):
		for pew in self.pew_sprite_group:
			pew.update_position()
			p = pew.get_position()
			view = self.view
			offset = view.get_offset()

			if p.x - offset.x > view.get_width() or p.x < offset.x:
				pew.kill()

	def check_hits(self, player):
		for pew in self.pew_sprite_group:
			hit = pew.collides_with(player.get_rect())
			if hit:
				player.damage(pew.get_damage())
				pew.kill()

	def generate_loot(self, enemy):
		num = random.randint(1, 100)
		loot_type = enemy.get_random_loot_type(num)
		if loot_type == None:
			return
		pos = enemy.get_position()
		self.items.load(loot_type, pos.x, pos.y)

	def kill(self, enemy):
		name = enemy.get_name()
		self.enemies[name]['count'] -= 1
		enemy.kill()
		self.generate_loot(enemy)
		print('KILL %s count=%d'%(name, self.enemies[name]['count']))

	def check_off_screen(self):
		for enemy in self.enemy_sprite_group:
			if self.view.out_of_range(enemy.get_rect(), int(self.view.get_width() / 2)):
				self.kill(enemy)

		for pew in self.pew_sprite_group:
			if not self.view.in_view(pew.get_rect()):
				pew.kill()

	def update(self, delta):
		self.update_pew_positions()
		self.pew_sprite_group.update(delta)
		self.enemy_sprite_group.update(delta)
		self.explosions.update(delta)
		self.check_off_screen()

	def draw(self, surface):
		self.pew_sprite_group.draw(surface)
		self.enemy_sprite_group.draw(surface)
		self.explosions.draw(surface)