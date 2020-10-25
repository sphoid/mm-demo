from pygame import sprite
from pygame.sprite import Rect
from pygame.math import Vector2
from .entity import *
from .constants import *
from .animation import *
from .weapon import *

class Player(Entity):
	def __init__(self, spritesheet_loader, sounds, explosions):
		super().__init__()
		self.spritesheet_loader = spritesheet_loader
		self.sounds = sounds
		self.move_speed = 2
		self.climb_speed = 2
		self.jump_speed = 8
		self.max_hit_points = 28
		self.hit_points = self.max_hit_points
		self.stage = None
		self.explosions = explosions

		self.damage_time = 0
		self.arrive_time = 0

		self.max_height = 48
		self.max_width = 48

		self.velocity = Vector2(0, 0)
		self.position = Vector2(PLAYER_HALF_WIDTH, PLAYER_HALF_HEIGHT)
		self.view = None

		self.current_time = 0
		self.direction = 1
		self.gravity = True
		self.falling = False
		self.warping = False
		self.arriving = False
		self.climbing = False
		self.climbing_over = False
		self.climb_hand_side = 1
		self.dead = False
		self.shooting = False
		self.damaged = False

		self.weapon = Weapon(self.spritesheet_loader, self.sounds, self)

		self.reset_animation = False

		self.area = Rect(0, 0, round(SCREEN_W / 2), round(SCREEN_H / 2))
		self.map_size = None

		self.load_sprites()

	def get_spritesheet_filename(self):
		return 'megaman-sprites.png'

	def load_sprites(self):
		self.spritesheet = self.spritesheet_loader.load(self.get_spritesheet_filename())
		image_at = self.spritesheet.image_at

		# TODO: Add halo when getting damaged

		self.animations = dict(
			still_left=Animation([
				dict(duration=2, image=image_at(Rect((0, 8), (24, 24)), -1)),
				dict(duration=0.1, image=image_at(Rect((25, 8), (24, 24)), -1))
			]),
			still_right=Animation([
				dict(duration=2, image=image_at(Rect((0, 8), (24, 24)), -1, flip=True)),
				dict(duration=0.1, image=image_at(Rect((25, 8), (24, 24)), -1, flip=True))
			]),
			still_shoot_left=Animation([
				dict(duration=0.2, image=image_at(Rect((291, 8), (32, 24)), -1))
			]),
			still_shoot_right=Animation([
				dict(duration=0.2, image=image_at(Rect((291, 8), (32, 24)), -1, flip=True))
			]),
			walk_left=Animation([
				dict(duration=0.1, image=image_at(Rect((80, 8), (24, 24)), -1)),
				dict(duration=0.1, image=image_at(Rect((108, 8), (24, 24)), -1)),
				dict(duration=0.1, image=image_at(Rect((133, 8), (24, 24)), -1))
			]),
			walk_left_shoot=Animation([
				dict(duration=0.1, image=image_at(Rect((324, 8), (32, 24)), -1)),
				dict(duration=0.1, image=image_at(Rect((357, 8), (32, 24)), -1)),
				dict(duration=0.1, image=image_at(Rect((390, 8), (32, 24)), -1)),
			]),
			walk_right=Animation([
				dict(duration=0.1, image=image_at(Rect((80, 8), (24, 24)), -1, flip=True)),
				dict(duration=0.1, image=image_at(Rect((108, 8), (24, 24)), -1, flip=True)),
				dict(duration=0.1, image=image_at(Rect((133, 8), (24, 24)), -1, flip=True))
			]),
			walk_right_shoot=Animation([
				dict(duration=0.1, image=image_at(Rect((324, 8), (32, 24)), -1, flip=True)),
				dict(duration=0.1, image=image_at(Rect((357, 8), (32, 24)), -1, flip=True)),
				dict(duration=0.1, image=image_at(Rect((390, 8), (32, 24)), -1, flip=True)),
			]),
			climb_still_right=Animation([
				dict(duration=0, image=image_at(Rect((224, 0), (16, 32)), -1)),
			]),
			climb_still_left=Animation([
				dict(duration=0, image=image_at(Rect((224, 0), (16, 32)), -1, flip=True)),
			]),
			climb_shoot_left=Animation([
				dict(duration=0, image=image_at(Rect((456, 0), (24, 32)), -1)),
			]),
			climb_shoot_right=Animation([
				dict(duration=0, image=image_at(Rect((456, 0), (24, 32)), -1, flip=True)),
			]),
			climb=Animation([
				dict(duration=0.2, image=image_at(Rect((224, 0), (16, 32)), -1), callback=self.set_direction_right),
				dict(duration=0.2, image=image_at(Rect((224, 0), (16, 32)), -1, flip=True), callback=self.set_direction_left),
			]),
			climb_over=Animation([
				dict(duration=0, image=image_at(Rect((241, 8), (16, 24)), -1)),
			]),
			jump_left=Animation([
				dict(duration=0, image=image_at(Rect((194, 0), (26, 30)), -1))
			]),
			jump_left_shoot=Animation([
				dict(duration=0, image=image_at(Rect((423, 0), (32, 32)), -1))
			]),
			jump_right=Animation([
				dict(duration=0, image=image_at(Rect((194, 0), (26, 30)), -1, flip=True))
			]),
			jump_right_shoot=Animation([
				dict(duration=0, image=image_at(Rect((423, 0), (32, 32)), -1, flip=True))
			]),
			warp=Animation([
				dict(duration=0, image=image_at(Rect((670, 0), (8, 32)), -1))
			]),
			warp_arrive=Animation([
				dict(duration=0.05, image=image_at(Rect((680, 0), (24, 32)), -1)),
				dict(duration=0.05, image=image_at(Rect((705, 0), (24, 32)), -1))
			]),
			damaged_left=Animation([
				dict(duration=1, image=image_at(Rect((258, 0), (32, 32)), -1))
			]),
			damaged_right=Animation([
				dict(duration=1, image=image_at(Rect((258, 0), (32, 32)), -1, flip=True))
			])
		)

		start_frame = self.animations['still_right'].current() if self.direction == 1 else  self.animations['still_left'].current()
		self.image = start_frame['image']
		self.rect = self.image.get_rect()

	def set_direction_left(self):
		self.direction = 0

	def set_direction_right(self):
		self.direction = 1

	def set_stage(self, stage):
		self.stage = stage
		self.map_size = stage.get_map_size()
		self.warp(stage.get_warp_start_position())

	def get_stage(self):
		return self.stage

	def is_dead(self):
		return self.dead

	def get_weapon(self):
		return self.weapon

	def get_max_hit_points(self):
		return self.max_hit_points

	def get_hit_points(self):
		return self.hit_points

	def get_width(self):
		return 16

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

	def damage(self, damage, force=2):
		self.hit_points -= damage
		self.stop_x()

		if self.hit_points < 0:
			self.die()
		else:
			if self.climbing:
				self.release_ladder()

			if self.direction:
				self.accelerate(-force, 0)
			else:
				self.accelerate(force, 0)

			self.damage_time = 0
			self.damaged = True
			self.reset_animation = True

			self.sounds.play_sound('damage')

	def is_damaged(self):
		return self.damaged

	def die(self):
		self.dead = True
		self.kill()

	def stop_shooting(self):
		self.shooting = False
		self.reset_animation = True

	def update_status(self, delta):
		if self.arriving:
			self.arrive_time += delta
			if self.arrive_time >= 0.05:
				self.arriving = False
				self.reset_animation = True

		if self.damaged:
			self.damage_time += delta
			# TODO: Replace timer with animation frame callback
			if self.damage_time >= 0.2:
				self.damaged = False
				self.stop_x()
				self.reset_animation = True

	def update(self, delta):
		self.update_position(delta)
		self.update_status(delta)

		if self.dead:
			self.kill()

		if self.warping:
			animation = self.animations['warp']
		elif self.arriving:
			animation = self.animations['warp_arrive']
		elif self.damaged:
			animation = self.animations['damaged_right'] if self.direction == 1 else self.animations['damaged_left']
		elif self.climbing:
			if self.climbing_over:
				animation = self.animations['climb_over']
			elif self.shooting:
				animation = self.animations['climb_shoot_right'] if self.direction == 1 else self.animations['climb_shoot_left']
			else:
				v = self.velocity

				if v.y !=0:
					animation = self.animations['climb']
				else:
					animation = self.animations['climb_still_right'] if self.direction == 1 else self.animations['climb_still_left']
		else:
			v = self.velocity

			if v.y != 0:
				if self.shooting:
					animation = self.animations['jump_right_shoot'] if self.direction == 1 else self.animations['jump_left_shoot']
				else:
					animation = self.animations['jump_right'] if self.direction == 1 else self.animations['jump_left']
			elif v.x != 0:
				if self.shooting:
					animation = self.animations['walk_right_shoot'] if self.direction == 1 else self.animations['walk_left_shoot']
				else:
					animation = self.animations['walk_right'] if self.direction == 1 else self.animations['walk_left']
			else:
				if self.shooting:
					animation = self.animations['still_shoot_right'] if self.direction == 1 else self.animations['still_shoot_left']
				else:
					animation = self.animations['still_right'] if self.direction == 1 else self.animations['still_left']

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

		self.weapon.update(delta)

		p = self.position
		offset = self.view.get_offset()
		self.rect.center = p.x - offset.x, p.y - offset.y