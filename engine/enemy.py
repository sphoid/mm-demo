import math
from pygame import sprite, time
from pygame.sprite import Rect
from pygame.math import Vector2
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

	def spawn_nearby(self, player, zone, zoned):
		area, stage = self.area, self.stage
		view = stage.get_view()
		vw, vh = view.get_width(), view.get_height()
		offset = view.get_offset()

		# TODO: handle zoning

		zenemies = list(filter((lambda name: self.enemies[name]['attributes']['zone'] == zone.get_name()), self.enemies.keys()))

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
					if (spawn_range > -1 and view.in_view(Rect((start_position[0], start_position[1]), (16, 16))) and abs(start_position[0] - player.get_position().x) < self.spawn_range) or (spawn_range == -1 and view.in_view(Rect((start_position[0], start_position[1]), (16, 16)))):
						spawn = True
				elif view.in_range(Rect((start_position[0], start_position[1]), (16, 16)), self.spawn_range):
					spawn = True

				if spawn:
					enemy['count'] += 1
					enemies.append(self.spawn(enemy['type'], name, player, start_position[0], start_position[1], **enemy['attributes']))

		return enemies

	def spawn(self, type, name, player, *start_position, **attributes):
		if type == 'bhc':
			enemy_class = BlueHeliChomper
		elif type == 'ghc':
			enemy_class = GreenHeliChomper
		elif type == 'bws':
			enemy_class = BlueWallShooter
		elif type == 'rws':
			enemy_class = RedWallShooter
		elif type == 'snapper':
			enemy_class = Snapper
		else:
			SystemExit('Invalid enemy type %s'%type)

		enemy = enemy_class(name, self.spritesheet, self.stage, self.sounds, self, player, start_position[0], start_position[1], **attributes)

		# print('spawn: %s pos=%d,%d'%(enemy.name, start_position[0], start_position[1]))

		return enemy

	def kill(self, enemy):
		name = enemy.get_name()
		self.enemies[name]['count'] -= 1
		enemy.kill()
		# print('KILL %s count=%d'%(name, self.enemies[name]['count']))

class Enemy(sprite.Sprite):
	def __init__(self, name, spritesheet, stage, sounds, enemies, player, *position, **attributes):
		# print(attributes)
		super().__init__()
		self.name = name
		self.spritesheet = spritesheet
		self.enemies = enemies
		self.player = player
		self.view = player.get_view()

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
				self.velocity = Vector2(self.move_speed_x, 0)
			elif self.direction == 0:
				self.velocity = Vector2(-self.move_speed_x, 0)
		else:
			self.velocity = Vector2(0, 0)

		if 'hit_points' in attributes:
			self.hit_points = attributes['hit_points']
		else:
			self.hit_points = self.get_default_hit_points()

		if 'damage' in attributes:
			self.damage = attributes['damage']
		else:
			self.damage = self.get_default_damage()

		if 'zone' in attributes:
			self.zone = attributes['zone']
		else:
			self.zone = None

		self.start_position = Vector2(position[0], position[1])
		self.position = Vector2(self.start_position[0], self.start_position[1])
		self.stage = stage
		self.sounds = sounds
		self.pew_sprite_group = sprite.Group()

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

	def get_zone(self):
		return self.zone

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
		self.position = int(position[0]), int(position[1])

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

	def react(self, delta):
		pass

	def update_position(self, delta):
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
			view = self.view
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
		if not self.view.in_view(self.get_rect()):
			self.enemies.kill(self)

	def update(self, delta):
		self.react(delta)
		self.update_position(delta)
		self.update_status()
		self.update_pew_positions()
		self.check_hits()
		self.check_off_screen()

		self.pew_sprite_group.update(delta)

class HeliChomper(Enemy):
	def __init__(self, name, spritesheet, stage, sounds, enemies, player, *position, **attributes):
		attributes['direction'] = 0 if position[0] > player.get_position().x else 1
		super().__init__(name, spritesheet, stage,sounds, enemies, player, position[0], position[1], **attributes)
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

	def update(self, delta):
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
	def __init__(self, image, view, target, *position):
		super().__init__()
		self.image = image
		self.rect = image.get_rect()
		self.position = Vector2(position[0], position[1])
		self.target = target
		self.speed = 1
		self.damage = 2
		self.view = view
		self.velocity = self.calculate_velocity()

	def calculate_velocity(self):
		dx = self.position.x - self.target[0]
		dy = self.position.y - self.target[1]

		dz = math.sqrt(dx**2 + dy**2)

		speedx = dx/dz * self.speed
		speedy = dy/dz * self.speed

		return Vector2(speedx, speedy)

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

class WallShooter(Enemy):
	def __init__(self, name, spritesheet, stage, sounds, enemies, player, *position, **attributes):
		super().__init__(name, spritesheet, stage,sounds, enemies, player, position[0], position[1], **attributes)
		self.active = False
		self.deactivating = False
		self.shooting = False
		self.open = False
		self.shots_fired = 0
		self.shoot_time = 0
		self.shot_frequency = 0.75
		self.max_shots = 4
		self.targets = None

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
		self.targets = self.calculate_targets()
		self.shooting = True
		self.shoot_time = 0
		self.shots_fired = 0

	def calculate_targets(self):
		p = self.position
		view = self.view
		vw, vh = view.get_width(), view.get_height()
		offset = view.get_offset()

		if self.direction:
			target1 = p.x - (vw / 4), offset.y
			target2 = offset.x, p.y - (vh / 4)
			target3 = offset.x, p.y + (vh / 4)
			target4 = p.x - (vw / 4), offset.y + vh
		else:
			target1 = p.x + (vw / 4), offset.y
			target2 = offset.x + vw, p.y - (vh / 4)
			target3 = offset.x + vw, p.y + (vh / 4)
			target4 = p.x + (vw / 4), offset.y + vh

		return [target1, target2, target3, target4]

	def shoot(self):
		target = self.targets.pop()
		p = self.position
		pellet = WallShooterPellet(self.pellet_image, self.view, target, p.x, p.y + (self.get_height() / 2))
		self.pew_sprite_group.add(pellet)
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
		view = self.player.get_view()
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

	def check_pew_off_screen(self):
		for pew in self.pew_sprite_group:
			if not self.view.in_view(pew.get_rect()):
				pew.kill()

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
			view = self.view
			offset = view.get_offset()
			self.rect.topleft = int(p.x - offset.x), int(p.y - offset.y)

class BlueWallShooter(WallShooter):
	def load_sprites(self):
		image_at = self.spritesheet.image_at

		self.animations = dict(
			shoot_left=Animation([
				dict(duration=1.0, image=image_at(Rect((412, 291), (16, 16)), colorkey=-1), callback=self.set_closed),
				dict(duration=0.1, image=image_at(Rect((372, 291), (16, 16)), colorkey=-1), callback=self.set_open),
				dict(duration=0.1, image=image_at(Rect((332, 291), (16, 16)), colorkey=-1)),
				dict(duration=3.5, image=image_at(Rect((295, 291), (16, 16)), colorkey=-1), callback=self.start_shooting),
				dict(duration=0.1, image=image_at(Rect((332, 291), (16, 16)), colorkey=-1)),
				dict(duration=0.1, image=image_at(Rect((372, 291), (16, 16)), colorkey=-1)),
				dict(duration=0.5, image=image_at(Rect((412, 291), (16, 16)), colorkey=-1), callback=self.close_and_deactivate),
			]),
			shoot_right=Animation([
				dict(duration=1.5, image=image_at(Rect((412, 291), (16, 16)), colorkey=-1, flip=True), callback=self.set_closed),
				dict(duration=0.25, image=image_at(Rect((372, 291), (16, 16)), colorkey=-1, flip=True), callback=self.set_open),
				dict(duration=0.25, image=image_at(Rect((332, 291), (16, 16)), colorkey=-1, flip=True)),
				dict(duration=3.5, image=image_at(Rect((295, 291), (16, 16)), colorkey=-1, flip=True), callback=self.start_shooting),
				dict(duration=0.25, image=image_at(Rect((332, 291), (16, 16)), colorkey=-1, flip=True)),
				dict(duration=0.25, image=image_at(Rect((372, 291), (16, 16)), colorkey=-1, flip=True)),
				dict(duration=0.5, image=image_at(Rect((412, 291), (16, 16)), colorkey=-1, flip=True), callback=self.close_and_deactivate),
			]),
			still_left=Animation([
				dict(duration=1.0, image=image_at(Rect((412, 291), (16, 16)), colorkey=-1)),
			]),
			still_right=Animation([
				dict(duration=1.0, image=image_at(Rect((412, 291), (16, 16)), colorkey=-1, flip=True)),
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
				dict(duration=1.0, image=image_at(Rect((412, 251), (16, 16)), colorkey=-1), callback=self.set_closed),
				dict(duration=0.1, image=image_at(Rect((372, 251), (16, 16)), colorkey=-1), callback=self.set_open),
				dict(duration=0.1, image=image_at(Rect((332, 251), (16, 16)), colorkey=-1)),
				dict(duration=3.5, image=image_at(Rect((295, 251), (16, 16)), colorkey=-1), callback=self.start_shooting),
				dict(duration=0.1, image=image_at(Rect((332	,251), (16, 16)), colorkey=-1)),
				dict(duration=0.1, image=image_at(Rect((372, 251), (16, 16)), colorkey=-1)),
				dict(duration=0.5, image=image_at(Rect((412, 251), (16, 16)), colorkey=-1), callback=self.close_and_deactivate),
			]),
			shoot_right=Animation([
				dict(duration=1.5, image=image_at(Rect((412, 251), (16, 16)), colorkey=-1, flip=True), callback=self.set_closed),
				dict(duration=0.25, image=image_at(Rect((372, 251), (16, 16)), colorkey=-1, flip=True), callback=self.set_open),
				dict(duration=0.25, image=image_at(Rect((332, 251), (16, 16)), colorkey=-1, flip=True)),
				dict(duration=3.5, image=image_at(Rect((295, 251), (16, 16)), colorkey=-1, flip=True), callback=self.start_shooting),
				dict(duration=0.25, image=image_at(Rect((332, 251), (16, 16)), colorkey=-1, flip=True)),
				dict(duration=0.25, image=image_at(Rect((372, 251), (16, 16)), colorkey=-1, flip=True)),
				dict(duration=0.5, image=image_at(Rect((412, 251), (16, 16)), colorkey=-1, flip=True), callback=self.close_and_deactivate),
			]),
			still_left=Animation([
				dict(duration=1.0, image=image_at(Rect((412, 251), (16, 16)), colorkey=-1)),
			]),
			still_right=Animation([
				dict(duration=1.0, image=image_at(Rect((412, 251), (16, 16)), colorkey=-1, flip=True)),
			])
		)

		self.pellet_image = image_at(Rect((281, 256), (6, 6)), -1)

		start_frame = self.animations['still_right'].current() if self.direction == 1 else self.animations['still_left'].current()
		self.image = start_frame['image']
		self.rect = self.image.get_rect()

class Snapper(Enemy):
	def __init__(self, name, spritesheet, stage, sounds, enemies, player, *position, **attributes):
		attributes['direction'] = 0 if position[0] > player.get_position().x else 1
		super().__init__(name, spritesheet, stage,sounds, enemies, player, position[0], position[1], **attributes)

		if self.direction:
			self.angle = 45
		else:
			self.angle = -45

		self.jumping = False
		self.move_time = 0

		self.load_sprites()

	def get_default_move_x_speed(self):
		return 5

	def get_default_move_y_speed(self):
		return 5

	def get_default_hit_points(self):
		return 3

	def get_default_damage(self):
		return 8

	def load_sprites(self):
		image_at = self.spritesheet.image_at

		self.animations = dict(
			move_left=Animation([
				dict(duration=0.1, image=image_at(Rect((216, 9), (16, 20)), colorkey=-1)),
				dict(duration=0.1, image=image_at(Rect((176, 12), (16, 20)), colorkey=-1)),
			]),
			move_right=Animation([
				dict(duration=0.1, image=image_at(Rect((216, 9), (16, 20)), colorkey=-1, flip=True)),
				dict(duration=0.1, image=image_at(Rect((176, 12), (16, 20)), colorkey=-1, flip=True)),
			])
		)

		start_frame = self.animations['move_right'].current() if self.direction == 1 else  self.animations['move_left'].current()
		self.image = start_frame['image']
		self.rect = self.image.get_rect()

	def jump(self, angle, target, delta):
		print('JUMP angle=%d delta=%f'%(angle, delta))
		self.jumping = True
		self.angle = angle
		self.jump_start_time = delta
		self.jump_time = 0
		self.jump_velocity = 15

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
			# gravity = -9.8
			time_diff = (self.jump_time - self.jump_start_time) * 7
			print('time_diff=%f'%time_diff)
			if time_diff > 0:
				half_gravity_time_squared = GRAVITY * (time_diff * time_diff) * 0.5
				displacement_x = self.jump_velocity * math.sin(self.angle) * time_diff
				displacement_y = self.jump_velocity * math.cos(self.angle) * time_diff - half_gravity_time_squared

				start_x, start_y = self.start_position.x, self.start_position.y

				self.position.x = start_x + int(displacement_x)
				self.position.y = start_y - int(displacement_y)
				# print('new pos=%d,%d'%(self.position.x, self.position.y))


	# import math
	# from processing import *

	# X = 30
	# Y = 30
	# gravity=9.81
	# angle=70
	# velocity=80
	# vx=velocity * math.cos(math.radians(angle))
	# vy=velocity * math.sin(math.radians(angle))
	# t=0

	# def setup():
	# 	strokeWeight(10)
	# 	frameRate(100)
	# 	size(400,400)

	# def throwBall():
	# 	global X, Y, radius, gravity, t,vx,vy
	# 	background(100)
	# 	fill(0,121,184)
	# 	stroke(255)
	# 	fc = environment.frameCount
	# 	t +=0.02
	# 	X = vx*t
	# 	Y = 400 -(vy*t - (gravity/2)*t*t)

	# 	ellipse(X,Y,30,30)


	# draw = throwBall
	# run()

	def update(self, delta):
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

			offset = self.view.get_offset()
			self.rect.center = int(self.position.x - offset.x), int(self.position.y - offset.y)
