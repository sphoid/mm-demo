import os, sys, math, pygame, pytmx
from pygame import Rect
from functools import reduce
# from pytmx.util_pygame import load_pygame

DEBUG = 0
INFO = 2
WARN = 4
ERROR = 8
FATAL = 16

MODE_MENU = 'menu'
MODE_GAME = 'game'
MODE_PAUSE = 'pause'
MODE_GAME_OVER = 'game_over'

TITLE_FONT_SIZE = 16
PROMPT_FONT_SIZE = 12
FPS = 60
SCREEN_W = 800
SCREEN_H = 800
TILE_WIDTH = 16
TILE_HALF_WIDTH = int(TILE_WIDTH / 2)
TILE_HEIGHT = 16
TILE_HALF_HEIGHT = int(TILE_HEIGHT / 2)

PLAYER_WIDTH = 24
PLAYER_HALF_WIDTH = int(PLAYER_WIDTH / 2)
PLAYER_HEIGHT = 24
PLAYER_HALF_HEIGHT = int(PLAYER_HEIGHT / 2)

TERMINAL_VELOCITY = 20

SCALE2X = False

MAP_DEBUG = False
PLAYER_DEBUG = False

def hex_to_rgb(value):
	value = value.lstrip('#')
	lv = len(value)
	return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

# def partial_dict_key(key, d):
# 	for k, v in d.iteritems():
# 		if all(k1 == k2 or k2 is None  for k1, k2 in zip(k, key)):
# 			yield v


class GameConfig:
	def get_screen_resolution(self):
		return SCREEN_W, SCREEN_H

class Logger:
	def __init__(self, log_level):
		self.log_level = log_level

	def log_message(self, message, level):
		print('%s: %s' % (level, message))

	def debug(self, message):
		if self.log_level == DEBUG:
			self.log_message(message, 'DEBUG')

	def info(self, message):
		if self.log_level <= INFO:
			self.log_message(message, 'INFO')

	def warn(self, message):
		if self.log_level <= WARN:
			self.log_message(message, 'WARN')

	def error(self, message):
		if self.log_level <= ERROR:
			self.log_message(message, 'ERROR')

	def info(self, message):
		if self.log_level <= FATAL:
			self.log_message(message, 'FATAL')

class ResourceLoader:
	def __init__(self, config, logger):
		self.config = config
		self.logger = logger

	def load_font(self, filename, size):
		filepath = os.path.join('data', 'fonts', filename)

		try:
			return pygame.font.Font(filepath, size)
		except pygame.error as message:
			self.logger.error('Cannot load font: %s' %(filename))
			raise SystemExit(message)

	def load_map(self, filename):
		filepath = os.path.join('maps', filename)
		return pytmx.util_pygame.load_pygame(filepath)

	def load_image(self, filename, colorkey=None):
		filepath = os.path.join('data', 'images', filename)

		try:
			image = pygame.image.load(filepath)
		except pygame.error as message:
			self.logger.error('Cannot load image: %s' %(filename))
			raise SystemExit(message)

		image = image.convert()

		if colorkey is not None:
			if colorkey == -1:
				colorkey = image.get_at((0, 0))

			image.set_colorkey(colorkey, RLEACCEL)

		return image, image.get_rect()

	def load_sound(self, filename, mixer=None):
		class NoneSound:
			def play(self): pass

		if not pygame.mixer:
			return NoneSound()

		filepath = os.path.join('data', 'sounds', filename)

		try:
			sound = mixer.Sound(filepath) if mixer else pygame.mixer.Sound(filepath)
		except pygame.error as message:
			self.logger.error('Cannot load sound: %s' %(filepath))
			raise SystemExit(message)

		return sound

	def load_song(self, filename):
		filepath = os.path.join('data', 'songs', filename)

		try:
			pygame.mixer.music.load(filepath)
		except pygame.error as message:
			self.logger.error('Cannot load song: %s' %(filepath))
			raise SystemExit(message)

class Animation:
	def __init__(self, frames, callback=None):
		self.frames = frames
		self.index = 0
		self.next_time = frames[self.index]['duration']
		self.callback = callback

	def reset(self):
		self.index = len(self.frames) - 1
		self.next_time = 0

		if self.callback is not None:
			self.callback(self.index)

	def current(self):
		return self.frames[self.index]

	def next(self, last_time):
		if self.index == len(self.frames) - 1:
			self.index = 0
		else:
			self.index += 1

		next_frame = self.frames[self.index]
		self.next_time = next_frame['duration'] + last_time

		if self.callback is not None:
			self.callback(self.index)

		return next_frame

class SpriteSheet:
	def __init__(self, image, rect):
		self.image = image
		self.rect = rect

	def image_at(self, rect, colorkey=None, scale2x=False, flip=False):
		image = pygame.Surface(rect.size).convert()
		image.blit(self.image, (0, 0), rect)
		if colorkey is not None:
			if colorkey == -1:
				colorkey = image.get_at((0,0))
			image.set_colorkey(colorkey, pygame.RLEACCEL)

		if flip:
			image = pygame.transform.flip(image, True, False)

		if scale2x:
			image = pygame.transform.scale2x(image)

		return image

	def images_at(self, rects, colorkey=None, scale2x=False, flip=False):
		return [self.image_at(rect, colorkey, scale2x, flip) for rect in rects]


class SpriteSheetLoader:
	def __init__(self, loader):
		self.loader = loader

	def load(self, filename):
		image, rect = self.loader.load_image(filename)
		return SpriteSheet(image, rect)

class SoundLibrary:
	def __init__(self, loader, mixer):
		self.loader = loader
		self.sounds = {}
		self.mixer = mixer

	def load(self):
		load_sound = self.loader.load_sound
		self.sounds = dict(
			start=load_sound('start.wav', self.mixer),
			defeat=load_sound('defeat.wav', self.mixer),
			land=load_sound('land.wav', self.mixer),
			pause=load_sound('pause.wav', self.mixer),
			warp=load_sound('warp.wav', self.mixer),
			buster=load_sound('buster.wav', self.mixer),
			damage=load_sound('damage.wav', self.mixer),
			edamage=load_sound('edamage.wav', self.mixer),
		)

	def play_sound(self, sound, blocking=False):
		if blocking:
			channel = self.sounds[sound].play()
			while channel.get_busy():
				pygame.time.wait(100)
		else:
			self.sounds[sound].play()

class MusicPlayer:
	def __init__(self, loader):
		self.loader = loader
		self.songs = {}

	def play(self, song):
		songfile = '%s.mp3'%song
		self.loader.load_song(songfile)
		pygame.mixer.music.play(-1)

	def stop(self):
		pygame.mixer.music.stop()


class Tile(pygame.sprite.Sprite):
	def __init__(self, image, stage, *grid_position):
		super().__init__()
		self.image = image
		self.rect = image.get_rect()
		self.position = pygame.math.Vector2(grid_position[0], grid_position[1])
		self.stage = stage

	def get_width(self):
		return self.rect.width

	def get_height(self):
		return self.rect.height

	def get_grid_position(self):
		return self.grid_position

	def get_position(self):
		return self.position

	def get_bottom(self):
		return self.position.y + self.rect.height

	def get_top(self):
		return self.position.y

	def get_left(self):
		return self.position.x

	def get_right(self):
		return self.position.x + self.rect.width

	def update(self, delta):
		p = self.position
		self.rect.topleft = int(p.x + self.stage.get_scroll_offset()), int(p.y)

class GameObject:
	def __init__(self, rect):
		self.rect = rect

	def get_rect(self):
		return Rect((self.get_left(), self.get_top()), (self.get_width(), self.get_height()))

	def get_bottom(self):
		return self.rect.bottom

	def get_top(self):
		return self.rect.top

	def get_left(self):
		return self.rect.left

	def get_right(self):
		return self.rect.right

	def get_width(self):
		return self.rect.width

	def get_height(self):
		return self.rect.height

	def collides_with(self, rect):
		return self.get_rect().colliderect(rect)

class Enemy(pygame.sprite.Sprite):
	def __init__(self, spritesheet_loader, stage, sounds, *position):
		super().__init__()
		self.spritesheet_loader = spritesheet_loader

		self.direction = 0
		self.move_speed = 5
		self.velocity = pygame.math.Vector2(0, 0)
		self.position = pygame.math.Vector2(position[0], position[1])
		self.stage = stage
		self.sounds = sounds

		self.area = Rect(0, 0, round(SCREEN_W / 2), round(SCREEN_H / 2))

		self.reset_animation = False
		self.current_time = 0

		self.hit_points = 1
		self.damage = 4
		self.dead = False

		self.load_sprites()

	def load_sprites(self):
		self.spritesheet = self.spritesheet_loader.load(self.get_spritesheet_filename())
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

	def get_spritesheet_filename(self):
		return 'enemies.png'

	def get_rect(self):
		return Rect((self.get_left(), self.get_top()), (self.get_width(), self.get_height()))

	def get_width(self):
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
		self.accelerate(self.move_speed, 0)

	def move_left(self):
		self.direction = 0
		self.accelerate(-self.move_speed, 0)

	def stop_x(self):
		self.set_velocity_x(0)

	def move_down(self):
		self.accelerate(0, self.move_speed)

	def move_up(self):
		self.accelerate(0, -self.move_speed)

	def damage(self, pew):
		damage = pew.get_damage()
		self.hit_points -= damage

		self.sounds.play_sound('edamage')

	def get_damage(self):
		return self.damage

	def die(self):
		self.dead = True

	def collides_with(self, rect):
		return self.get_rect().colliderect(rect)

	def react(self, player):
		v = self.get_velocity()
		if player.get_right() > self.get_left() - 200 and v.x == 0 and v.y == 0:
			self.move_left()
		elif player.get_right() > self.get_left() - 50 and v.y == 0:
			self.stop_x()
			self.move_down()

	def update_position(self):
		v = self.get_velocity()
		self.position.x += v.x
		self.position.y += v.y

	def update_status(self):
		if self.hit_points <= 0:
			self.die()

	def update(self, delta):
		if self.dead:
			self.kill()
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

class Stage:
	def __init__(self, loader, spritesheet_loader):
		self.tile_height = 32
		self.tile_width = 32
		self.loader = loader
		self.spritesheet_loader = spritesheet_loader
		self.player = None
		self.map = None
		self.tiles = {}
		self.ladders = {}
		self.platforms = {}
		self.tile_sprite_group = pygame.sprite.Group()
		self.enemy_sprite_group = pygame.sprite.Group()
		self.scroll_offset = 0
		self.area = Rect(0, 0, round(SCREEN_W / 2), round(SCREEN_H / 2))
		self.center = self.area.width / 2
		self.map_size = None
		self.sounds = {}

	def load_map(self):
		self.map = self.loader.load_map('level-1.tmx')

		if not MAP_DEBUG:
			for obj in self.map.get_layer_by_name('tiles'):
				x, y = int(obj.x), int(obj.y)
				tile = Tile(obj.image, self, x, y)
				self.tiles[x, y] = tile
				self.tile_sprite_group.add(tile)

		for obj in self.map.get_layer_by_name('platforms'):
			x, y, width, height = int(obj.x), int(obj.y), int(obj.width), int(obj.height)
			self.platforms[x, y] = GameObject(Rect((x, y), (width, height)))
			print('LOAD: Platform %d,%d %dx%d'%(x, y, width, height))

		for obj in self.map.get_layer_by_name('ladders'):
			x, y, width, height = int(obj.x), int(obj.y), int(obj.width), int(obj.height)
			self.ladders[x, y] = GameObject(Rect((x, y), (width, height)))
			print('LOAD: Ladder %d,%d %dx%d'%(x, y, width, height))

		for obj in self.map.get_layer_by_name('enemies'):
			x, y, width, height = int(obj.x), int(obj.y), int(obj.width), int(obj.height)
			enemy = Enemy(self.spritesheet_loader, self, self.sounds, x, y)
			self.enemy_sprite_group.add(enemy)
			# self.enemies.append(enemy)
			print('LOAD: Enemy %d,%d %dx%d'%(x, y, width, height))

		self.map_size = self.map.width * TILE_WIDTH, self.map.height * TILE_HEIGHT

		print('Loaded map grid_size=%dx%d size=%dx%d' % (self.map.width, self.map.height, self.map_size[0], self.map_size[1]))

	def load(self):
		self.load_map()

	def platform_below(self, rect):
		test_rect = Rect((rect.left, rect.top + 1), (rect.width, rect.height))
		colliding_platforms = list(filter((lambda platform: test_rect.colliderect(platform.rect)), self.platforms.values()))

		return colliding_platforms[0] if len(colliding_platforms) > 0 else None

	def ladder_below(self, rect):
		test_rect = Rect((rect.left, rect.top + 1), (rect.width, rect.height))
		colliding_ladders = list(filter((lambda ladder: test_rect.colliderect(ladder.rect)), self.ladders.values()))

		return colliding_ladders[0] if len(colliding_ladders) > 0 else None

	def ladder_behind(self, rect):
		colliding_ladders = list(filter((lambda ladder: rect.colliderect(ladder.rect)), self.ladders.values()))

		return colliding_ladders[0] if len(colliding_ladders) > 0 else None

	def get_background_color(self):
		return hex_to_rgb(self.map.background_color)

	def get_map_size(self):
		return self.map_size

	def get_map_width(self):
		return self.map_size[0]

	def get_map_height(self):
		return self.map_size[1]

	def get_scroll_offset(self):
		return self.scroll_offset

	def update_scroll_offset(self, player_position):
		a = self.area
		w, h = self.map_size
		right_scroll_threshold = a.width / 2
		left_scroll_threshold = w - right_scroll_threshold

		if player_position.x > right_scroll_threshold and player_position.x < left_scroll_threshold:
			self.scroll_offset = -(player_position.x - right_scroll_threshold)
		elif player_position.x >= left_scroll_threshold:
			self.scroll_offset = -(w - a.width)
		elif player_position.x <= right_scroll_threshold:
			self.scroll_offset = 0

		# print('area_width=%d map_width=%d scroll_offset=%d'%(a.width, w, self.scroll_offset))

	def update_enemies(self, player):
		for enemy in self.enemy_sprite_group:
			enemy.react(player)

	def update(self, delta):
		for enemy in self.enemy_sprite_group:
			enemy.update_position()
			enemy.update_status()

		self.tile_sprite_group.update(delta)
		self.enemy_sprite_group.update(delta)

	def draw(self, surface):
		self.tile_sprite_group.draw(surface)
		self.enemy_sprite_group.draw(surface)

		if MAP_DEBUG:
			for platform in self.platforms.values():
				pygame.draw.rect(surface, (0, 0, 255), platform.rect)

			for ladder in self.ladders.values():
				pygame.draw.rect(surface, (255,0,0), ladder.rect)

class BusterPellet(pygame.sprite.Sprite):
	def __init__(self, image, direction, *position):
		super().__init__()
		self.image = image
		self.rect = image.get_rect()
		self.position = pygame.math.Vector2(position[0], position[1])
		self.direction = direction
		self.speed = 20
		self.damage = 1

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

	def get_damage(self):
		return self.damage

	def update_position(self):
		if self.direction == 1:
			self.position.x += self.speed
		else:
			self.position.x -= self.speed

	def update(self, delta):
		self.rect.center = int(self.position.x), int(self.position.y)

class Weapon:
	def __init__(self, spritesheet_loader, sounds):
		super().__init__()
		self.spritesheet_loader = spritesheet_loader
		self.pew_sprite_group = pygame.sprite.Group()
		self.area = Rect(0, 0, int(SCREEN_W / 2), int(SCREEN_H / 2))
		self.sounds = sounds

		self.load_sprites()

	def load_sprites(self):
		self.spritesheet = self.spritesheet_loader.load(self.get_spritesheet_filename())
		image_at = self.spritesheet.image_at

		self.pellet_image = image_at(Rect((0, 0), (14, 10)), -1)

	def get_spritesheet_filename(self):
		return 'weapon-sprites.png'

	def shoot(self, player):
		pellet = BusterPellet(self.pellet_image, player.get_direction(), player.rect.right, (player.rect.top + int(player.get_height() / 3)))
		self.pew_sprite_group.add(pellet)

		self.sounds.play_sound('buster')

		return pellet

	def check_hits(self, enemy_sprite_group):
		if len(self.pew_sprite_group) > 0:
			print('checking enemy hits')
			for pew in self.pew_sprite_group:
				for enemy in enemy_sprite_group:
					hit = enemy.collides_with(pew.get_rect())
					if hit:
						print('hit enemy')
						enemy.damage(pew)

	def update(self, delta):
		for pew in self.pew_sprite_group:
			pew.update_position()
			p = pew.get_position()
			if p.x > self.area.width or p.x < 0:
				pew.kill()

		self.pew_sprite_group.update(delta)

class HudGroup(pygame.sprite.Group):
	def add(self, *sprites):
		for sprite in sprites:
			if sprite.__class__.__name__ == 'LifeMeter':
				self.life_meter = sprite
			super().add(sprite)

	def draw(self, surface):
		super().draw(surface)
		if hasattr(self, 'life_meter'):
			self.life_meter.draw_damage_mask(surface)

class LifeMeter(pygame.sprite.Sprite):
	def __init__(self, spritesheet_loader, sounds, player):
		super().__init__()
		self.spritesheet_loader = spritesheet_loader
		self.player = player
		self.sounds = sounds

		self.load_sprites()

	def get_spritesheet_filename(self):
		return 'energy-sprites.png'

	def load_sprites(self):
		self.spritesheet = self.spritesheet_loader.load(self.get_spritesheet_filename())
		image_at = self.spritesheet.image_at

		self.image = image_at(Rect((0, 8), (8, 56)), None, True)
		self.rect = self.image.get_rect(left=10, top=10)
		self.damage_mask_rect = Rect((self.rect.left + 1, self.rect.top), (self.rect.width - 2, 0))

	def draw_damage_mask(self, surface):
		diff = self.player.get_max_hit_points() - self.player.get_hit_points()
		damage_mask_rect = Rect((self.rect.left + 1, self.rect.top), (self.rect.width - 2, diff * 4))

		pygame.draw.rect(surface, (0, 0, 0), damage_mask_rect)

class Player(pygame.sprite.Sprite):
	def __init__(self, spritesheet_loader, sounds):
		super().__init__()
		self.spritesheet_loader = spritesheet_loader
		self.sounds = sounds
		self.move_speed = 5
		self.climb_speed = 3
		self.jump_speed = 10
		self.max_hit_points = 28
		self.hit_points = self.max_hit_points

		self.damage_time = 0

		self.max_height = 48
		self.max_width = 48

		self.velocity = pygame.math.Vector2(0, 0)
		self.position = pygame.math.Vector2(PLAYER_HALF_WIDTH, PLAYER_HALF_HEIGHT)

		self.current_time = 0
		self.direction = 1
		self.falling = True
		self.warping = True
		self.arriving = False
		self.climbing = False
		self.climbing_over = False
		self.climb_hand_side = 1
		self.dead = False
		self.shooting = False
		self.damaged = False

		self.weapon = Weapon(self.spritesheet_loader, self.sounds)

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
				dict(duration=0.1, image=image_at(Rect((291, 8), (32, 24)), -1))
			]),
			still_shoot_right=Animation([
				dict(duration=0.1, image=image_at(Rect((291, 8), (32, 24)), -1, flip=True))
			]),
			walk_left=Animation([
				dict(duration=0.05, image=image_at(Rect((80, 8), (24, 24)), -1)),
				dict(duration=0.05, image=image_at(Rect((108, 8), (24, 24)), -1)),
				dict(duration=0.05, image=image_at(Rect((133, 8), (24, 24)), -1))
			]),
			walk_left_shoot=Animation([
				dict(duration=0.05, image=image_at(Rect((324, 8), (32, 24)), -1)),
				dict(duration=0.05, image=image_at(Rect((357, 8), (32, 24)), -1)),
				dict(duration=0.05, image=image_at(Rect((390, 8), (32, 24)), -1)),
			]),
			walk_right=Animation([
				dict(duration=0.05, image=image_at(Rect((80, 8), (24, 24)), -1, flip=True)),
				dict(duration=0.05, image=image_at(Rect((108, 8), (24, 24)), -1, flip=True)),
				dict(duration=0.05, image=image_at(Rect((133, 8), (24, 24)), -1, flip=True))
			]),
			walk_right_shoot=Animation([
				dict(duration=0.05, image=image_at(Rect((324, 8), (32, 24)), -1, flip=True)),
				dict(duration=0.05, image=image_at(Rect((357, 8), (32, 24)), -1, flip=True)),
				dict(duration=0.05, image=image_at(Rect((390, 8), (32, 24)), -1, flip=True)),
			]),
			climb_still_right=Animation([
				dict(duration=0, image=image_at(Rect((224, 0), (16, 32)), -1)),
			]),
			climb_still_left=Animation([
				dict(duration=0, image=image_at(Rect((224, 0), (16, 32)), -1, flip=True)),
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
				dict(duration=0.1, image=image_at(Rect((680, 0), (24, 32)), -1)),
				dict(duration=0.1, image=image_at(Rect((705, 0), (24, 32)), -1))
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

	def set_map_size(self, map_size):
		self.map_size = map_size

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
		if self.climbing:
			return 16

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
		return int(self.position.x - int(self.rect.width / 2))

	def get_right(self):
		return int(self.position.x + int(self.rect.width / 2))

	def get_direction(self):
		return self.direction

	def collide_bottom(self, y):
		print('Resetting player_y=%d'%y)
		self.velocity.y = 0
		self.position.y = int(y - int(self.rect.height / 2))

		if self.warping:
			self.warping = False
			self.arriving = True
			self.reset_animation = True
		elif self.arriving:
			self.arriving = False
			self.reset_animation = True
			self.sounds.play_sound('warp')
		elif self.climbing:
			self.climbing = False
			self.climbing_over = False
			self.reset_animation = True
			self.sounds.play_sound('land')
		else:
			self.falling = False
			self.reset_animation = True
			self.sounds.play_sound('land')

		print('collide_bottom new pos=%d,%d'%(self.position.x, self.position.y))

	def collide_top(self, y):
		self.velocity.y = 0
		self.position.y = int(y + int(self.rect.height / 2))
		self.falling = True

		print('collide_top new pos=%d,%d'%(self.position.x, self.position.y))

	def collide_right(self, x):
		self.velocity.x = 0
		self.position.x = int(x - int(self.rect.width / 2))
		self.reset_animation = True

		print('collide_right new pos=%d,%d'%(self.position.x, self.position.y))

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
			self.position.y += int(self.rect.height / 2)
		self.climbing = True
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

	def fall(self):
		self.falling = True

	def is_falling(self):
		return self.falling

	def is_warping(self):
		return self.warping

	def jump(self):
		if not self.falling and not self.climbing:
			self.accelerate(0, -self.jump_speed)
			self.falling = True

	def shoot(self):
		self.shooting = True
		self.reset_animation = True

		return self.weapon.shoot(self)

	def damage(self, damage, force=2):
		self.hit_points -= damage

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

	def update_position(self):
		v = self.get_velocity()
		self.position.x += v.x
		self.position.y += v.y

	def update_status(self, delta):
		p = self.get_position()
		a = self.area
		if p.y > a.height:
			self.die()

		if self.damaged:
			self.damage_time += delta
			if self.damage_time >= 0.2:
				self.damaged = False
				self.stop_x()
				self.animation_reset = True

		if self.hit_points <= 0:
			self.die()

	def update(self, delta):
		if self.warping:
			animation = self.animations['warp']
		elif self.arriving:
			animation = self.animations['warp_arrive']
		elif self.damaged:
			animation = self.animations['damaged_right'] if self.direction == 1 else self.animations['damaged_left']
		elif self.climbing:
			if self.climbing_over:
				animation = self.animations['climb_over']
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

		a = self.area
		mw, mh = self.map_size
		right_scroll_threshold = round(a.width / 2)
		left_scroll_threshold = mw - right_scroll_threshold
		p = self.position
		if p.x > right_scroll_threshold and p.x < left_scroll_threshold:
			self.rect.center = right_scroll_threshold, p.y
		elif p.x >= left_scroll_threshold:
			diff = p.x - left_scroll_threshold
			self.rect.center = (right_scroll_threshold + diff), p.y
		elif p.x <= right_scroll_threshold:
			self.rect.center = int(self.position.x), int(self.position.y)

class Game:
	def __init__(self, game_config, logger, loader):
		self.config = game_config
		self.logger = logger
		self.loader = loader
		self.spritesheet_loader = SpriteSheetLoader(self.loader)
		self.mode = MODE_MENU
		self.clock = pygame.time.Clock()
		self.area = Rect(0, 0, int(SCREEN_W / 2), int(SCREEN_H / 2))
		self.sprites = pygame.sprite.Group()
		self.hud = HudGroup()

	def init_screen(self):
		self.resolution = width, height = self.config.get_screen_resolution()
		self.logger.debug('resolution: %dx%d' % (width, height))
		self.screen = pygame.display.set_mode(self.resolution, pygame.HWSURFACE|pygame.DOUBLEBUF)
		self.buffer = pygame.Surface((round(SCREEN_W/2), round(SCREEN_H/2)))

	def init_audio(self):
		self.mixer = pygame.mixer.init()
		self.sounds = SoundLibrary(self.loader, self.mixer)
		self.sounds.load()
		self.music_player = MusicPlayer(self.loader)

	def init_menu(self):
		self.title_font = self.loader.load_font('megaman_2.ttf', TITLE_FONT_SIZE)
		self.prompt_font = self.loader.load_font('megaman_2.ttf', PROMPT_FONT_SIZE)
		self.title = 'Game Demo'
		self.menu_time = 0
		self.prompt_blinking = False

	def init_game_over(self):
		self.game_over_font = self.loader.load_font('megaman_2.ttf', TITLE_FONT_SIZE)
		self.game_over_time = 0

	def init_player(self):
		self.player = Player(self.spritesheet_loader, self.sounds)
		self.sprites.add(self.player)

	def init_hud(self):
		self.life_meter = LifeMeter(self.spritesheet_loader, self.sounds, self.player)
		self.hud.add(self.life_meter)

	def init_stage(self):
		self.stage = Stage(self.loader, self.spritesheet_loader)
		self.stage.load()

		self.player.set_map_size(self.stage.get_map_size())

		self.music_player.play('bombman-stage')

	def render_menu(self):
		delta = self.clock.tick(FPS) / 1000
		self.menu_time += delta

		buffer = self.buffer
		screen = self.screen
		title_font = self.title_font
		prompt_font = self.prompt_font
		title = self.title

		background_color = 0, 0, 0
		default_font_color = 255, 255, 255
		buffer.fill(background_color)

		if self.prompt_blinking and self.menu_time >= 0.25:
			self.menu_time = 0
			self.prompt_blinking = False
		elif not self.prompt_blinking and self.menu_time >= 0.5:
			self.menu_time = 0
			self.prompt_blinking = True

		if self.prompt_blinking:
			prompt_font_color = background_color
		else:
			prompt_font_color = default_font_color

		title_text = title_font.render(self.title, 0, default_font_color)
		title_rect = title_text.get_rect(center=(round(SCREEN_W/2), round(SCREEN_H/2)))

		prompt_text = prompt_font.render('Press Enter to start', 0, prompt_font_color)
		prompt_rect = prompt_text.get_rect(center=(round(SCREEN_W/2), round(SCREEN_H/2) + 50))

		screen.blit(title_text, title_rect)
		screen.blit(prompt_text, prompt_rect)

		pygame.display.flip()

	def render_game_over(self):
		delta = self.clock.tick(FPS) / 1000
		self.game_over_time += delta

		buffer = self.buffer
		screen = self.screen
		game_over_font = self.game_over_font

		background_color = 0, 0, 0
		default_font_color = 255, 255, 255
		buffer.fill(background_color)

		game_over_text = game_over_font.render('Game Over', 0, default_font_color)
		game_over_rect = game_over_text.get_rect(center=(SCREEN_W/2, SCREEN_H/2))

		screen.blit(game_over_text, game_over_rect)

		pygame.display.flip()

	def check_collision(self, player):
		stage = self.stage
		colliding_platforms = list(filter((lambda platform: platform.collides_with(player.get_rect())), stage.platforms.values()))
		colliding_ladders = list(filter((lambda ladder: ladder.collides_with(player.get_rect())), stage.ladders.values()))
		v = player.get_velocity()
		if len(colliding_platforms) > 0:
			p = player.get_position()
			for platform in colliding_platforms:
				if v.y > 0 and platform.get_top() < player.get_bottom():
					print('collision BOTTOM platform_top=%d bottom=%d pos=%d,%d'%(platform.get_top(), player.get_bottom(), p.x, p.y))
					player.collide_bottom(platform.get_top())
				elif v.y < 0 and platform.get_bottom() > player.get_top():
					print('collision TOP platform_bottom=%d top=%d pos=%d,%d'%(platform.get_bottom(), player.get_top(), p.x, p.y))
					player.collide_top(platform.get_bottom())

				if v.x > 0 and platform.get_left() < player.get_right() and platform.get_top() < player.get_bottom():
					print('collision RIGHT platform_left=%d right=%d pos=%d,%d'%(platform.get_left(), player.get_right(), p.x, p.y))
					player.collide_right(platform.get_left())
				elif v.x < 0 and platform.get_right() > player.get_left() and platform.get_top() < player.get_bottom():
					print('collision LEFT platform_right=%d left=%d pos=%d,%d'%(platform.get_right(), player.get_left(), p.x, p.y))
					player.collide_left(platform.get_right())
		elif not player.is_climbing() and len(colliding_ladders) > 0:
			p = player.get_position()
			for ladder in colliding_ladders:
				if v.y > 0 and ladder.get_top() < player.get_bottom() and (player.get_bottom() - ladder.get_top()) < PLAYER_HALF_HEIGHT:
					print('collision BOTTOM ladder_top=%d bottom=%d pos=%d,%d'%(ladder.get_top(), player.get_bottom(), p.x, p.y))
					player.collide_bottom(ladder.get_top())
		else:
			mw, mh = stage.get_map_size()

			if player.get_left() < 0:
				player.collide_left(0)
			elif player.get_right() > mw:
				player.collide_right(mw)

		if not player.is_damaged():
			colliding_enemies = list(filter((lambda enemy: enemy.collides_with(player.get_rect())), stage.enemy_sprite_group))
			if len(colliding_enemies) > 0:
				enemy = colliding_enemies[0]
				print('enemy hit epos=%d,%d ppos=%d, %d'%(enemy.get_position().x, enemy.get_position().y, player.get_position().x, player.get_position().y))
				player.damage(enemy.get_damage())

		weapon = player.get_weapon()
		weapon.check_hits(stage.enemy_sprite_group)

	def check_climb(self):
		player = self.player

		if not player.is_climbing():
			return

		stage = self.stage
		ladder = stage.ladder_behind(player.get_rect())

		if not player.is_climbing_over():
			if player.get_top() <= ladder.get_top() and player.get_position().y >= ladder.get_top():
				player.climb_over()
			elif player.get_position().y < ladder.get_top():
				player.climb_off(ladder.get_top())
		else:
			if player.get_position().y < ladder.get_top():
				player.climb_off(ladder.get_top())
			elif player.get_top() > ladder.get_top():
				player.stop_climbing_over()

	def apply_gravity(self):
		player = self.player

		if player.is_climbing():
			return

		if player.is_falling():
			v = player.get_velocity()
			if v.y == 0:
				player.accelerate(0, 1)
			elif v.y < TERMINAL_VELOCITY:
				player.accelerate(0, 1)
			else:
				player.set_velocity_y(TERMINAL_VELOCITY)
		else:
			stage = self.stage
			prect = player.get_rect()
			platform_below = stage.platform_below(prect)
			ladder_behind = stage.ladder_behind(prect)
			ladder_below = stage.ladder_below(prect)

			if not platform_below and not ladder_below and not ladder_behind:
				player.fall()

	def grab_ladder_behind(self, player):
		stage = self.stage
		prect = player.get_rect()
		ladder = stage.ladder_behind(prect)
		if ladder:
			print('Grabbing ladder behind')
			player.grab_ladder(ladder)
			return True

		return False

	def grab_ladder_below(self, player):
		stage = self.stage
		prect = player.get_rect()
		ladder = stage.ladder_below(prect)
		if ladder:
			print('Grabbing ladder below')
			player.grab_ladder(ladder, True)
			return True

		return False

	def render_game(self):
		delta = self.clock.tick(FPS) / 1000
		player = self.player

		self.check_climb()
		self.apply_gravity()

		buffer = self.buffer
		sprites = self.sprites
		hud = self.hud
		stage = self.stage
		area = self.area
		screen = self.screen
		mw, mh = stage.get_map_size()

		player.update_position()
		stage.update_scroll_offset(player.get_position())
		self.check_collision(player)
		stage.update_enemies(player)

		player.update_status(delta)

		sprites.update(delta)
		stage.update(delta)
		hud.update(delta)

		background_color = stage.get_background_color()

		buffer.fill(background_color)

		stage.draw(buffer)
		sprites.draw(buffer)
		hud.draw(buffer)

		if PLAYER_DEBUG:
			pygame.draw.rect(buffer, (0, 255, 0), player.rect)

		screen.blit(pygame.transform.scale2x(buffer), (0, 0))

		pygame.display.flip()

	def render(self):
		if self.mode == MODE_GAME:
			self.render_game()
		elif self.mode == MODE_MENU:
			self.render_menu()
		elif self.mode == MODE_PAUSE:
			self.render_pause()
		elif self.mode == MODE_GAME_OVER:
			self.render_game_over()

	def handle_game_event(self, event):
		player = self.player
		debug = self.logger.debug
		if event.type in (pygame.KEYDOWN, pygame.KEYUP):
			if event.key == pygame.K_RIGHT:
				if event.type == pygame.KEYDOWN:
					debug('R Down')
					if not player.is_climbing() and not player.is_warping():
						player.move_right()
				elif event.type == pygame.KEYUP:
					debug('R Up')
					player.stop_x()
			elif event.key == pygame.K_LEFT:
				if event.type == pygame.KEYDOWN:
					debug('L Down')
					if not player.is_climbing() and not player.is_warping():
						player.move_left()
				elif event.type == pygame.KEYUP:
					debug('L Up')
					player.stop_x()
			elif event.key == pygame.K_UP:
				if event.type == pygame.KEYDOWN:
					debug('U Down')
					if not player.is_climbing():
						grabbed = self.grab_ladder_behind(player)
						if grabbed:
							player.climb_up()
					else:
						player.climb_up()
				elif event.type == pygame.KEYUP:
					debug('U Up')
					if player.is_climbing():
						player.stop_climbing()
			elif event.key == pygame.K_DOWN:
				if event.type == pygame.KEYDOWN:
					debug('D Down')
					if not player.is_climbing():
						grabbed = self.grab_ladder_below(player)
						if grabbed:
							player.climb_down()
					else:
						player.climb_down()
				elif event.type == pygame.KEYUP:
					debug('D Up')
					if player.is_climbing():
						player.stop_climbing()
			elif event.key == pygame.K_SPACE and event.type == pygame.KEYDOWN:
				debug('Space')
				if not player.is_climbing() and not player.is_falling():
					player.jump()
			elif event.key == pygame.K_f:
				if event.type == pygame.KEYDOWN:
					debug('Pew')
					pew = player.shoot()
					self.sprites.add(pew)
				elif event.type == pygame.KEYUP:
					player.stop_shooting()
			elif event.key == pygame.K_ESCAPE:
				self.running = False

	def handle_menu_event(self, event):
		if event.type in (pygame.KEYDOWN, pygame.KEYUP):
			if event.key == pygame.K_RETURN:
				self.sounds.play_sound('start', True)
				self.start(MODE_GAME)
			elif event.key == pygame.K_ESCAPE:
				self.running = False

	def handle_event(self, event):
		if self.mode == MODE_GAME:
			self.handle_game_event(event)
		elif self.mode == MODE_MENU:
			self.handle_menu_event(event)
		elif self.mode == MODE_PAUSE:
			self.handle_pause_event(event)

	def loop(self):
		self.running = True
		while self.running:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					sys.exit()
				else:
					self.handle_event(event)

			if self.running:
				self.clock.tick(60)
				self.render()

			if self.mode == MODE_GAME_OVER and self.game_over_time >= 3:
				self.start(MODE_MENU)
			elif self.mode == MODE_GAME and self.player.is_dead():
				self.music_player.stop()
				self.sounds.play_sound('defeat', True)
				self.start(MODE_GAME_OVER)

	def start(self, mode):
		self.mode = mode
		self.init_screen()
		self.init_audio()

		if self.mode == MODE_GAME:
			self.init_player()
			self.init_stage()
			self.init_hud()
		elif self.mode == MODE_MENU:
			self.init_menu()
		elif self.mode == MODE_GAME_OVER:
			self.init_game_over()

		self.loop()

def main():
	if not pygame.font: print('Warning, fonts disabled')
	if not pygame.mixer: print('Warning, sound disabled')

	game_config = GameConfig()
	logger = Logger(DEBUG)
	loader = ResourceLoader(game_config, logger)
	game = Game(game_config, logger, loader)
	pygame.init()
	game.start(MODE_MENU)
	pygame.quit()

main()