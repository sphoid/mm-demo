from pygame import sprite, math
from pygame.sprite import Rect
from .constants import *
from .animation import *
from .weapon import *

class Player(sprite.Sprite):
	def __init__(self, spritesheet_loader, sounds):
		super().__init__()
		self.spritesheet_loader = spritesheet_loader
		self.sounds = sounds
		self.move_speed = 2
		self.climb_speed = 2
		self.jump_speed = 8
		self.max_hit_points = 28
		self.hit_points = self.max_hit_points
		self.stage = None

		self.damage_time = 0
		self.arrive_time = 0

		self.max_height = 48
		self.max_width = 48

		self.velocity = math.Vector2(0, 0)
		self.position = math.Vector2(PLAYER_HALF_WIDTH, PLAYER_HALF_HEIGHT)
		self.view = None

		self.current_time = 0
		self.direction = 1
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
				dict(duration=0.05, image=image_at(Rect((224, 0), (16, 32)), -1)),
				dict(duration=0.05, image=image_at(Rect((224, 0), (16, 32)), -1, flip=True)),
			], self.toggle_climb_hand_side),
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

	def toggle_climb_hand_side(self, index):
		self.climb_hand_side = int(not self.climb_hand_side)

	def set_stage(self, stage):
		self.stage = stage
		self.map_size = stage.get_map_size()
		print(stage.get_warp_start_position())
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

	def get_rect(self):
		return Rect((self.get_left(), self.get_top()), (self.get_width(), self.get_height()))

	def get_width(self):
		if self.climbing or self.falling:
			return 16
		else:
			return 24

		return self.rect.width

	def get_height(self):
		return self.rect.height

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
		return int(self.position.x - int(self.get_width() / 2))

	def get_right(self):
		return int(self.position.x + int(self.get_width() / 2))

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
			self.sounds.play_sound('land')
		else:
			self.falling = False
			self.reset_animation = True
			self.sounds.play_sound('land')

		print('collide bottom y=%d pos=%d,%d'%(y, self.position.x, self.position.y))

	def collide_bottom_right(self, x, y):
		self.set_velocity(0, 0)
		self.position.x = int(x - int(self.rect.width / 2))
		self.position.y = int(y - int(self.rect.height / 2))
		self.falling = False
		self.reset_animation = True
		self.sounds.play_sound('land')
		print('collide bottom_right x=%d y=%d pos=%d,%d'%(x, y, self.position.x, self.position.y))

	def collide_bottom_left(self, x, y):
		self.set_velocity(0, 0)
		self.position.x = int(x + int(self.rect.width / 2))
		self.position.y = int(y - int(self.rect.height / 2))
		self.falling = False
		self.reset_animation = True
		self.sounds.play_sound('land')
		print('collide bottom_left x=%d y=%d pos=%d,%d'%(x, y, self.position.x, self.position.y))

	def collide_top(self, y):
		self.velocity.y = 0
		self.position.y = int(y + int(self.rect.height / 2))
		self.falling = True
		print('collide top y=%d pos=%d,%d'%(y, self.position.x, self.position.y))

	def collide_top_right(self, x, y):
		self.set_velocity(0, 0)
		self.position.x = int(x - int(self.rect.width / 2))
		self.position.y = int(y + int(self.rect.height / 2))
		self.reset_animation = True
		self.sounds.play_sound('land')
		print('collide top_right x=%d y=%d pos=%d,%d'%(x, y, self.position.x, self.position.y))

	def collide_top_left(self, x, y):
		self.set_velocity(0, 0)
		self.position.x = int(x + int(self.rect.width / 2))
		self.position.y = int(y + int(self.rect.height / 2))
		self.reset_animation = True
		self.sounds.play_sound('land')
		print('collide top_left x=%d y=%d pos=%d,%d'%(x, y, self.position.x, self.position.y))

	def collide_right(self, x):
		self.velocity.x = 0
		self.position.x = int(x - int(self.rect.width / 2))
		self.reset_animation = True
		print('collide right x=%d pos=%d,%d'%(x, self.position.x, self.position.y))

	def collide_left(self, x):
		self.velocity.x = 0
		self.position.x = int(x + int(self.rect.width / 2))
		self.reset_animation = True

		print('collide_left new pos=%d,%d'%(self.position.x, self.position.y))

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
		self.accelerate(self.move_speed, 0)

	def move_left(self):
		self.direction = 0
		self.accelerate(-self.move_speed, 0)

	def stop_x(self):
		self.set_velocity_x(0)
		self.reset_animation = True

	def is_climbing(self):
		return self.climbing

	def is_climbing_over(self):
		return self.climbing_over

	def grab_ladder(self, ladder, going_down=False):
		self.velocity.x = 0
		self.position.x = ladder.get_left() + int(ladder.get_width() / 2)
		if going_down:
			self.rect.width = 16
			self.position.y += int(self.rect.height / 2)
		self.climbing = True
		self.reset_animation = True

	def release_ladder(self):
		self.climbing = False
		self.falling = True
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
		self.reset_animation = True

	def climb_up(self):
		self.accelerate(0, -self.climb_speed)

	def climb_down(self):
		self.accelerate(0, self.climb_speed)

	def stop_climbing(self):
		self.velocity.y = 0
		self.reset_animation = True

	def warp(self, start_position):
		self.set_position(start_position.x, start_position.y)
		self.warping = True

	def arrive(self, y):
		self.velocity.y = 0
		self.position.y = int(y - int(self.rect.height / 2))
		self.arrive_time = 0
		self.warping = False
		self.arriving = True
		self.reset_animation = True
		self.sounds.play_sound('warp')

	def is_arriving(self):
		return self.arriving

	def stop_arriving(self):
		self.arriving = False
		self.reset_animation = True

	def is_warping(self):
		return self.warping

	def fall(self):
		self.falling = True

	def is_falling(self):
		return self.falling

	def is_warping(self):
		return self.warping

	def jump(self):
		if self.climbing:
			self.release_ladder()
		elif not self.falling:
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

	def stop_shooting(self):
		self.shooting = False
		self.reset_animation = True

	def get_map_offset(self):
		return self.stage.get_scroll_offset_x()

	def update_position(self):
		v = self.get_velocity()
		self.position.x += v.x
		self.position.y += v.y

	def update_status(self, delta):
		if self.arriving:
			self.arrive_time += delta
			print('arrive time %f'%self.arrive_time)
			if self.arrive_time >= 0.05:
				self.arriving = False
				self.reset_animation = True

		if self.damaged:
			self.damage_time += delta
			if self.damage_time >= 0.2:
				self.damaged = False
				self.stop_x()
				self.reset_animation = True

		if self.hit_points <= 0:
			self.die()

	def set_view(self, view):
		self.view = view

	def get_view(self):
		return self.view

	def update(self, delta):
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
					animation = self.animations['climb_still_right'] if self.climb_hand_side == 1 else self.animations['climb_still_left']
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