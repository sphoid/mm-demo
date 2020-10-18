from pygame import sprite, math
from pygame.sprite import Rect
from .constants import *
from .animation import *

class Enemies:
	def __init__(self, spritesheet_loader, sounds, stage):
		self.spritesheet = spritesheet_loader.load(self.get_spritesheet_filename())
		self.stage = stage
		self.sounds = sounds
		self.spawn_range = 50
		self.enemies = dict()
		self.area = Rect(0, 0, round(SCREEN_W / 2), round(SCREEN_H / 2))

	def get_spritesheet_filename(self):
		return 'enemies.png'

	def load(self, name, type, *start_position, **attributes):
		self.enemies[name] = dict(start_position=start_position, type=type, count=0, attributes=attributes)

	def spawn_nearby(self, x, player):
		area, stage = self.area, self.stage
		view = stage.get_view()
		vw = view.get_width()
		offset = view.get_offset()
		
		# TODO: handle zoning

		enemies = list()
		for name, enemy in self.enemies.items():
			start_position = enemy['start_position']
			count = enemy['count']
			if count == 0:
				if abs(start_position[0] - (offset.x + vw)) < self.spawn_range and start_position[0] > (offset.x + vw):
					enemy['count'] += 1
					enemies.append(self.spawn(enemy['type'], name, player, start_position[0], start_position[1], enemy['attributes']))

		return enemies

	def spawn(self, type, name, player, *start_position):
		if type == 'bhc':
			enemy_class = BlueHeliChomper
		elif type == 'ghc':
			enemy_class = GreenHeliChomper
		elif type == 'bws':
			enemy_class = BlueWallShooter
		elif type == 'rws':
			enemy_class = RedWallShooter
		else:
			SystemExit('Invalid enemy type %s'%type)

		enemy = enemy_class(name, self.spritesheet, self.stage, self.sounds, self, player, start_position[0], start_position[1])

		# print('spawn: %s pos=%d,%d'%(enemy.name, start_position[0], start_position[1]))

		return enemy

	def kill(self, enemy):
		name = enemy.get_name()
		self.enemies[name]['count'] -= 1
		enemy.kill()
		# print('KILL %s count=%d'%(name, self.enemies[name]['count']))

class Enemy(sprite.Sprite):
	def __init__(self, name, spritesheet, stage, sounds, enemies, player, *position, **attributes):
		super().__init__()
		self.name = name
		self.spritesheet = spritesheet
		self.enemies = enemies
		self.player = player

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
				self.velocity = math.Vector2(self.move_speed_x, 0)
			elif self.direction == 0:
				self.velocity = math.Vector2(-self.move_speed_x, 0)
		else:
			self.velocity = math.Vector2(0, 0)

		if 'hit_points' in attributes:
			self.hit_points = attributes['hit_points']
		else:
			self.hit_points = self.get_default_hit_points()

		if 'damage' in attributes:
			self.damage = attributes['damage']
		else:
			self.damage = self.get_default_damage()

		self.start_position = math.Vector2(position[0], position[1])
		self.position = self.start_position
		self.stage = stage
		self.sounds = sounds
		self.pew_sprite_group = sprite.Group()

		self.area = Rect(0, 0, round(SCREEN_W / 2), round(SCREEN_H / 2))

		self.reset_animation = False
		self.current_time = 0

		self.dead = False

		print("SPAWN: %s direction=%d"%(self.name, self.direction))

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

	def get_name(self):
		return self.name

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

	def react(self):
		pass

	def update_position(self):
		v = self.get_velocity()
		self.position.x += v.x
		self.position.y += v.y

	def update_status(self):
		if self.hit_points <= 0:
			self.die()

	def update_pew_positions(self):
		for pew in self.pew_sprite_group:
			pew.update_position()
			p = pew.get_position()
			view = self.stage.get_view()
			offset = view.get_offset()

			if p.x - offset.x > view.get_width() or p.x < offset.x:
				pew.kill()

	def check_hits(self):
		player = self.player
		for pew in self.pew_sprite_group:
			hit = pew.collides_with(player.get_rect())
			if hit:
				player.damage(pew.get_damage())
				pew.kill()

	def check_off_screen(self):
		p = self.position
		view = self.stage.get_view()
		vw = view.get_width()
		offset = view.get_offset()
		if p.x < offset.x - int(vw / 2) or p.x > (offset.x + vw + int(vw / 2)):
			self.enemies.kill(self)

	def update(self, delta):
		self.react()
		self.update_position()
		self.update_status()
		self.update_pew_positions()
		self.check_hits()
		self.check_off_screen()

		self.pew_sprite_group.update(delta)

class HeliChomper(Enemy):
	def __init__(self, name, spritesheet, stage, sounds, enemies, player, *position, **attributes):
		attributes['direction'] = 0 if position[0] > player.get_position().x else 1
		super().__init__(name, spritesheet, stage,sounds, enemies, player, position[0], position[1], attributes)
		self.swooping = False
		self.swoop_direction = 0
		self.swoop_target_y = 0
		self.swoop_original_y = 0
		self.swoop_cooling_down = False
		self.swoop_cooldown_time = 0

		self.load_sprites()

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

	def load_sprites(self):
		pass

	def swoop_up(self, y):
		# print('HC: Swoop up')
		self.swooping = True
		self.swoop_cooling_down = False
		self.move_up()
		self.swoop_direction = 0
		self.swoop_original_y = self.position.y + self.player.get_height()
		self.swoop_target_y = y

	def swoop_down(self, y):
		# print('HC: Swoop down')
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
		# print('HC: Stop swooping')
		self.velocity.y = 0
		self.swooping = False
		self.swoop_cooling_down = True
		self.swoop_cooldown_time = 0

	def react(self):
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

	def update(self, delta):
		if self.swooping:
			v = self.velocity
			y = self.position.y
			if self.swoop_direction == 1:
				if v.y > 0 and y >= self.swoop_target_y:
					# print('HC: Reverse up')
					self.move_up()
				elif v.y < 0 and y <= self.swoop_original_y:
					self.stop_swooping()
			else:
				if v.y < 0 and y <= self.swoop_target_y:
					# print('HC: Reverse down')
					self.move_down()
				elif v.y > 0 and y >= self.swoop_original_y:
					self.stop_swooping()
		elif self.swoop_cooling_down:
			self.swoop_cooldown_time += delta

		super().update(delta)

		if self.dead:
			self.enemies.kill(self)
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
			view = self.stage.get_view()
			offset = view.get_offset()
			self.rect.topleft = int(p.x - offset.x), int(p.y - offset.y)

			if self.rect.top > self.area.height:
				self.enemies.kill(self)

class BlueHeliChomper(HeliChomper):
	def load_sprites(self):
		image_at = self.spritesheet.image_at

		self.animations = dict(
			move_left=Animation([
				dict(duration=0.05, image=image_at(Rect((376, 329), (16, 20)), -1)),
				dict(duration=0.05, image=image_at(Rect((416, 329), (16, 20)), -1)),
			]),
			move_right=Animation([
				dict(duration=0.05, image=image_at(Rect((376, 329), (16, 20)), -1, flip=True)),
				dict(duration=0.05, image=image_at(Rect((416, 329), (16, 20)), -1, flip=True)),
			])
		)

		start_frame = self.animations['move_right'].current() if self.direction == 1 else  self.animations['move_left'].current()
		self.image = start_frame['image']
		self.rect = self.image.get_rect()

class GreenHeliChomper(HeliChomper):
	def load_sprites(self):
		image_at = self.spritesheet.image_at

		self.animations = dict(
			move_left=Animation([
				dict(duration=0.05, image=image_at(Rect((296, 329), (16, 20)), -1)),
				dict(duration=0.05, image=image_at(Rect((336, 329), (16, 20)), -1)),
			]),
			move_right=Animation([
				dict(duration=0.05, image=image_at(Rect((292, 326), (16, 20)), -1, flip=True)),
				dict(duration=0.05, image=image_at(Rect((336, 329), (16, 20)), -1, flip=True)),
			])
		)

		start_frame = self.animations['move_right'].current() if self.direction == 1 else  self.animations['move_left'].current()
		self.image = start_frame['image']
		self.rect = self.image.get_rect()


class WallShooterPellet(sprite.Sprite):
	def __init__(self, image, view, direction, *position):
		super().__init__()
		self.image = image
		self.rect = image.get_rect()
		self.position = math.Vector2(position[0], position[1])
		self.direction = direction
		self.speed = 1
		self.damage = 2
		self.view = view

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
		if self.direction == 1:
			self.position.x += self.speed
		else:
			self.position.x -= self.speed

	def update(self, delta):
		self.update_position()

		offset = self.view.get_offset()
		self.rect.center = int(self.position.x - offset.x), int(self.position.y - offset.y)

class WallShooter(Enemy):
	def __init__(self, name, spritesheet, stage, sounds, enemies, player, *position, **attributes):
		super().__init__(name, spritesheet, stage,sounds, enemies, player, position[0], position[1], attributes)
		self.active = False
		self.deactivating = False
		self.shooting = False
		self.open = False
		self.shots_fired = 0
		self.shoot_time = 0
		self.shot_frequency = 0.75
		self.max_shots = 4

		self.load_sprites()

	def get_default_hit_points(self):
		return 1

	def get_default_damage(self):
		return 4

	def load_sprites(self):
		pass

	def set_open(self):
		self.open = True

	def set_closed(self):
		self.open = False

	def close_and_deactivate(self):
		self.set_closed()

		if self.deactivating:
			self.set_inactive()

	def start_shooting(self):
		self.shooting = True
		self.shoot_time = 0
		self.shots_fired = 0

	def shoot(self):
		# print('WS: Shoot')
		view = self.stage.get_view()
		start_pos_x = self.get_right() if self.direction else self.get_left()
		start_pos_y = self.get_top() + self.rect.height
		pellet = WallShooterPellet(self.pellet_image, view, self.direction, start_pos_x, start_pos_y)
		self.pew_sprite_group.add(pellet)
		self.sounds.play_sound('eshoot')
		self.shoot_time = 0
		self.shots_fired += 1

	def stop_shooting(self):
		# print('WS: Stop Shooting')
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

	def react(self):
		ppos = self.player.get_position()
		pos = self.get_position()

		if abs(pos.x - ppos.x) <= 100 and not self.active:
			self.activate()
		elif self.active:
			self.deactivate()

	def hit(self, pew):
		if self.open:
			super().hit(pew)
		else:
			self.sounds.play_sound('dink')

	def update(self, delta):
		super().update(delta)

		if self.dead:
			self.enemies.kill(self)
		else:
			if self.active:
				animation = self.animations['shoot_right'] if self.direction == 1 else self.animations['shoot_left']

				if self.shooting:
					self.shoot_time += delta

					if self.shots_fired == 0 or self.shoot_time >= self.shot_frequency:
						self.shoot()

					if self.shots_fired == self.max_shots:
						self.stop_shooting()
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

			p = self.position
			view = self.stage.get_view()
			offset = view.get_offset()
			self.rect.topleft = int(p.x - offset.x), int(p.y - offset.y)

class BlueWallShooter(WallShooter):
	def load_sprites(self):
		image_at = self.spritesheet.image_at

		self.animations = dict(
			shoot_left=Animation([
				dict(duration=1.0, image=image_at(Rect((412, 291), (16, 16)), -1), callback=self.set_closed),
				dict(duration=0.1, image=image_at(Rect((372, 291), (16, 16)), -1), callback=self.set_open),
				dict(duration=0.1, image=image_at(Rect((332, 291), (16, 16)), -1)),
				dict(duration=3.5, image=image_at(Rect((295, 291), (16, 16)), -1), callback=self.start_shooting),
				dict(duration=0.1, image=image_at(Rect((332, 291), (16, 16)), -1)),
				dict(duration=0.1, image=image_at(Rect((372, 291), (16, 16)), -1)),
				dict(duration=0.5, image=image_at(Rect((412, 291), (16, 16)), -1), callback=self.close_and_deactivate),
			]),
			shoot_right=Animation([
				dict(duration=1.5, image=image_at(Rect((412, 291), (16, 16)), -1, flip=True), callback=self.set_closed),
				dict(duration=0.25, image=image_at(Rect((372, 291), (16, 16)), -1, flip=True), callback=self.set_open),
				dict(duration=0.25, image=image_at(Rect((332, 291), (16, 16)), -1, flip=True)),
				dict(duration=3.5, image=image_at(Rect((295, 291), (16, 16)), -1, flip=True), callback=self.start_shooting),
				dict(duration=0.25, image=image_at(Rect((332, 291), (16, 16)), -1, flip=True)),
				dict(duration=0.25, image=image_at(Rect((372, 291), (16, 16)), -1, flip=True)),
				dict(duration=0.5, image=image_at(Rect((412, 291), (16, 16)), -1, flip=True), callback=self.close_and_deactivate),
			]),
			still_left=Animation([
				dict(duration=1.0, image=image_at(Rect((412, 291), (16, 16)), -1)),
			]),
			still_right=Animation([
				dict(duration=1.0, image=image_at(Rect((412, 291), (16, 16)), -1, flip=True)),
			])
		)

		self.pellet_image = image_at(Rect((281, 296), (6, 6)), -1)

		start_frame = self.animations['still_right'].current() if self.direction == 1 else  self.animations['still_left'].current()
		self.image = start_frame['image']
		self.rect = self.image.get_rect()

class RedWallShooter(WallShooter):
	def load_sprites(self):
		image_at = self.spritesheet.image_at

		# TODO: Fix animation glitch
		self.animations = dict(
			shoot_left=Animation([
				dict(duration=1.0, image=image_at(Rect((412, 251), (16, 16)), -1), callback=self.set_closed),
				dict(duration=0.1, image=image_at(Rect((372, 251), (16, 16)), -1), callback=self.set_open),
				dict(duration=0.1, image=image_at(Rect((332, 251), (16, 16)), -1)),
				dict(duration=3.5, image=image_at(Rect((295, 251), (16, 16)), -1), callback=self.start_shooting),
				dict(duration=0.1, image=image_at(Rect((332	,251), (16, 16)), -1)),
				dict(duration=0.1, image=image_at(Rect((372, 251), (16, 16)), -1)),
				dict(duration=0.5, image=image_at(Rect((412, 251), (16, 16)), -1), callback=self.close_and_deactivate),
			]),
			shoot_right=Animation([
				dict(duration=1.5, image=image_at(Rect((412, 251), (16, 16)), -1, flip=True), callback=self.set_closed),
				dict(duration=0.25, image=image_at(Rect((372, 251), (16, 16)), -1, flip=True), callback=self.set_open),
				dict(duration=0.25, image=image_at(Rect((332, 251), (16, 16)), -1, flip=True)),
				dict(duration=3.5, image=image_at(Rect((295, 251), (16, 16)), -1, flip=True), callback=self.start_shooting),
				dict(duration=0.25, image=image_at(Rect((332, 251), (16, 16)), -1, flip=True)),
				dict(duration=0.25, image=image_at(Rect((372, 251), (16, 16)), -1, flip=True)),
				dict(duration=0.5, image=image_at(Rect((412, 251), (16, 16)), -1, flip=True), callback=self.close_and_deactivate),
			]),
			still_left=Animation([
				dict(duration=1.0, image=image_at(Rect((412, 251), (16, 16)), -1)),
			]),
			still_right=Animation([
				dict(duration=1.0, image=image_at(Rect((412, 251), (16, 16)), -1, flip=True)),
			])
		)

		self.pellet_image = image_at(Rect((281, 256), (6, 6)), -1)

		start_frame = self.animations['still_right'].current() if self.direction == 1 else  self.animations['still_left'].current()
		self.image = start_frame['image']
		self.rect = self.image.get_rect()
