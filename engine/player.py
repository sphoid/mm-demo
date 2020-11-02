from pygame import sprite
from pygame.sprite import Rect
from pygame.math import Vector2
from .entity import *
from .constants import *
from .animation import *
from .weapon import *

class Player(Entity):
	def __init__(self, spritesheet_loader, view, sounds, explosions, debug):
		spritesheet = spritesheet_loader.load(self.get_spritesheet_filename())
		# self.spritesheet_loader = spritesheet_loader
		self.direction = 1

		self.sounds = sounds
		self.move_speed = 2
		self.climb_speed = 2
		self.jump_speed = 8
		self.max_hit_points = 28
		self.max_lives = 3
		self.stage = None
		self.explosions = explosions
		self.debug = debug

		self.max_height = 48
		self.max_width = 48

		# self.velocity = Vector2(0, 0)

		self.moveable = True
		self.falling = False
		self.warping = False
		self.arriving = False
		self.climbing = False
		self.climbing_over = False
		self.dead = False
		self.shooting = False
		self.damaged = False
		self.healing = False
		self.healing_left = 0
		self.invincible = False
		self.immobilized = False

		self.invincible_time = 0
		self.heal_time = 0

		self.hit_points = self.max_hit_points
		self.score = 0
		self.bonus_points = 0
		self.lives = self.max_lives

		self.weapon = Weapon(spritesheet_loader, self.sounds, self)

		super().__init__(spritesheet=spritesheet, view=view, gravity=True)

	def get_spritesheet_filename(self):
		return 'megaman-sprites.png'

	def get_animation_states(self):
		return dict(
			states=dict(
				still_left = [
					dict(at=(0, 8), size=(24, 24), duration=2),
					dict(at=(25, 8), size=(24, 24), duration=0.1),
				],
				still_right = [
					dict(at=(0, 8), size=(24, 24), duration=2, flip='x'),
					dict(at=(25, 8), size=(24, 24), duration=0.1, flip='x'),
				],
				still_shoot_left = [
					dict(at=(291, 8), size=(32, 24), duration=0.2),
				],
				still_shoot_right = [
					dict(at=(291, 8), size=(32, 24), duration=0.2, flip='x'),
				],
				walk_left = [
					dict(at=(80, 8), size=(24, 24), duration=0.1),
					dict(at=(108, 8), size=(24, 24), duration=0.1),
					dict(at=(133, 8), size=(24, 24), duration=0.1),
				],
				walk_right = [
					dict(at=(80, 8), size=(24, 24), duration=0.1, flip='x'),
					dict(at=(108, 8), size=(24, 24), duration=0.1, flip='x'),
					dict(at=(133, 8), size=(24, 24), duration=0.1, flip='x'),
				],
				walk_shoot_left = [
					dict(at=(324, 8), size=(32, 24), duration=0.1),
					dict(at=(357, 8), size=(32, 24), duration=0.1),
					dict(at=(390, 8), size=(32, 24), duration=0.1),
				],
				walk_shoot_right = [
					dict(at=(324, 8), size=(32, 24), duration=0.1, flip='x'),
					dict(at=(357, 8), size=(32, 24), duration=0.1, flip='x'),
					dict(at=(390, 8), size=(32, 24), duration=0.1, flip='x'),
				],
				climb_still_right = [
					dict(at=(224, 0), size=(16, 32), duration=0.2),
				],
				climb_still_left = [
					dict(at=(224, 0), size=(16, 32), duration=0.2, flip='x'),
				],
				climb_shoot_left = [
					dict(at=(456, 0), size=(24, 32), duration=0.2),
				],
				climb_shoot_right = [
					dict(at=(456, 0), size=(24, 32), duration=0.2, flip='x'),
				],
				climb = [
					dict(at=(224, 0), size=(16, 32), duration=0.2, callback=self.set_direction_right),
					dict(at=(224, 0), size=(16, 32), duration=0.2, flip='x', callback=self.set_direction_left),
				],
				climb_over = [
					dict(at=(241, 8), size=(16, 24), duration=0),
				],
				jump_left = [
					dict(at=(194, 0), size=(26, 30), duration=0),
				],
				jump_right = [
					dict(at=(194, 0), size=(26, 30), duration=0, flip='x'),
				],
				jump_shoot_left = [
					dict(at=(423, 0), size=(32, 32), duration=0),
				],
				jump_shoot_right = [
					dict(at=(423, 0), size=(32, 32), duration=0, flip='x'),
				],
				warp = [
					dict(at=(670, 0), size=(8, 32), duration=0),
				],
				warp_arrive = [
					dict(at=(680, 0), size=(24, 32), duration=0.05),
					dict(at=(705, 0), size=(24, 32), duration=0.05, callback=self.stop_arrive),
				],
				damaged_left = [
					dict(at=(258, 0), size=(32, 32), duration=0.25),
					dict(at=(258, 0), size=(32, 32), duration=0.1, callback=self.recover),
				],
				damaged_right = [
					dict(at=(258, 0), size=(32, 32), duration=0.25, flip='x'),
					dict(at=(258, 0), size=(32, 32), duration=0.1, flip='x', callback=self.recover),
				],
			),
			default = 'still_right' if self.direction == 1 else 'still_left'
		)

	def set_direction_left(self):
		self.direction = 0

	def set_direction_right(self):
		self.direction = 1

	def set_stage(self, stage):
		self.stage = stage
		self.warp(stage.get_warp_start_position())

	def get_stage(self):
		return self.stage

	def is_moveable(self):
		return self.moveable

	def is_dead(self):
		return self.dead

	def get_weapon(self):
		return self.weapon

	def get_max_hit_points(self):
		return self.max_hit_points

	def get_hit_points(self):
		return self.hit_points

	def heal(self, hit_points):
		if self.hit_points < self.max_hit_points:
			self.healing = True
			self.healing_left = hit_points

			self.sounds.play_sound('energy', True)

	def add_points(self, points):
		self.score += points

	def add_bonus_points(self, points):
		self.bonus_points += points

		self.sounds.play_sound('bonus')

	def get_score(self):
		return self.score

	def add_life(self):
		self.lives += 1

		self.sounds.play_sound('extralife')

	def get_width(self):
		return 16

	def get_height(self):
		return 24

	def get_direction(self):
		return self.direction

	def set_direction(self, direction):
		self.direction = direction

	def collide_bottom(self, y):
		self.velocity.y = 0
		self.position.y = int(y - int(self.rect.height / 2))

		if self.climbing:
			self.climbing = False
			self.climbing_over = False
			self.reset_animation = True
		else:
			self.falling = False
			self.reset_animation = True

		self.sounds.play_sound('land')

	def move_right(self):
		self.direction = 1
		if self.velocity.x < 0:
			self.accelerate(self.move_speed * 2, 0)
		else:
			self.accelerate(self.move_speed, 0)

	def move_left(self):
		self.direction = 0
		if self.velocity.x > 0:
			self.accelerate(-(self.move_speed * 2), 0)
		else:
			self.accelerate(-self.move_speed, 0)

	def is_climbing(self):
		return self.climbing

	def is_climbing_over(self):
		return self.climbing_over

	def is_warping(self):
		return self.warping

	def warp(self, start_position):
		self.position = copy.copy(start_position)
		self.warping = True
		self.falling = True
		self.gravity = True
		self.moveable = False

	def grab_ladder(self, ladder, going_down=False):
		self.velocity.x = 0
		self.velocity.y = 0
		self.position.x = ladder.get_left() + int(ladder.get_width() / 2)

		if going_down:
			self.rect.width = 16
			self.position.y += int(self.rect.height / 2)

		self.climbing = True
		self.gravity = False
		self.falling = False
		self.reset_animation = True

	def climb_over(self):
		self.climbing_over = True
		self.reset_animation = True

	def stop_climbing_over(self):
		self.climbing_over = False
		self.reset_animation = True

	def climb_off(self, y=None):
		self.velocity.y = 0
		if y is not None:
			self.position.y = int(y - PLAYER_HALF_HEIGHT)
		self.climbing = False
		self.climbing_over = False
		self.gravity = True
		self.reset_animation = True

	def climb_up(self):
		if self.climbing:
			self.accelerate(0, -self.climb_speed)

	def climb_down(self):
		if self.climbing:
			self.accelerate(0, self.climb_speed)

	def stop_climbing(self):
		self.velocity.y = 0
		self.reset_animation = True

	def is_arriving(self):
		return self.arriving

	def arrive(self, y):
		self.velocity.y = 0
		self.position.y = int(y - int(self.rect.height / 2))
		self.arrive_time = 0
		self.warping = False
		self.arriving = True
		self.reset_animation = True
		self.sounds.play_sound('warp')

	def stop_arrive(self):
		self.arriving = False
		self.moveable = True
		self.reset_animation = True

	def release_ladder(self):
		self.climbing = False
		self.gravity = True
		self.falling = True
		self.reset_animation = True

	def jump(self):
		if self.climbing:
			self.release_ladder()
		elif not self.falling:
			self.gravity = True
			self.rect.width = 16
			self.accelerate(0, -self.jump_speed)
			self.falling = True

	def shoot(self):
		self.shooting = True
		self.reset_animation = True

		return self.weapon.shoot()

	def recover(self):
		self.damaged = False
		self.moveable = True
		self.invincible = True
		self.invincible_time = 0
		self.stop_x()

	def damage(self, damage, force=1):
		self.damaged = True
		self.moveable = False

		if not self.debug['player_invincible']:
			self.hit_points -= damage
		self.stop_x()

		if self.hit_points <= 0:
			self.die()
		else:
			if self.climbing:
				self.release_ladder()

			if self.direction:
				self.accelerate(-force, 0)
			else:
				self.accelerate(force, 0)

			self.reset_animation = True

			self.sounds.play_sound('damage')

		print('hit_points=%d'%self.hit_points)

	def is_invincible(self):
		return self.invincible

	def is_damaged(self):
		return self.damaged

	def immobilize(self):
		self.set_velocity(0, 0)
		self.moveable = False
		self.gravity = False
		self.immobilized = True
		self.reset_animation = True

	def mobilize(self):
		self.moveable = True
		self.gravity = True
		self.immobilized = False
		self.reset_animation = True

	def die(self):
		self.dead = True
		self.kill()

	def stop_shooting(self):
		self.shooting = False
		self.reset_animation = True

	def update_status(self, delta):
		if self.hit_points <= 0 and not self.dead:
			self.kill()
			self.dead = True
			return

		if self.invincible:
			self.invincible_time += delta
			if self.invincible_time >= 1:
				self.invincible = False

		if self.healing:
			self.heal_time += delta
			if self.heal_time >= 0.05:
				self.heal_time = 0

				self.hit_points += 1
				self.healing_left -= 1

				if self.hit_points > self.max_hit_points:
					self.hit_points = self.max_hit_points

				if self.healing_left == 0:
					self.healing = False

	def update_state(self, delta):
		if self.warping:
			self.animation_state = 'warp'
		elif self.arriving:
			self.animation_state = 'warp_arrive'
		elif self.damaged:
			self.animation_state = 'damaged_right' if self.direction == 1 else 'damaged_left'
		elif self.immobilized:
			self.animation_state = 'jump_right' if self.direction == 1 else 'jump_left'
		elif self.climbing:
			if self.climbing_over:
				self.animation_state = 'climb_over'
			elif self.shooting:
				self.animation_state = 'climb_shoot_right' if self.direction == 1 else 'climb_shoot_left'
			elif self.velocity.y != 0:
				self.animation_state = 'climb'
			else:
				self.animation_state = 'climb_still_right' if self.direction == 1 else 'climb_still_left'
		else:
			if self.velocity.y != 0:
				if self.shooting:
					self.animation_state = 'jump_shoot_right' if self.direction == 1 else 'jump_shoot_left'
				else:
					self.animation_state = 'jump_right' if self.direction == 1 else 'jump_left'
			elif self.velocity.x != 0:
				if self.shooting:
					self.animation_state = 'walk_shoot_right' if self.direction == 1 else 'walk_shoot_left'
				else:
					self.animation_state = 'walk_right' if self.direction == 1 else 'walk_left'
			elif self.shooting:
				self.animation_state = 'still_shoot_right' if self.direction == 1 else 'still_shoot_left'
			else:
				self.animation_state = 'still_right' if self.direction == 1 else 'still_left'

	def update(self, delta):
		self.update_status(delta)
		self.weapon.update(delta)
		super().update(delta)