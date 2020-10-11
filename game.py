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
TILE_HALF_WIDTH = TILE_WIDTH / 2
TILE_HEIGHT = 16
TILE_HALF_HEIGHT = TILE_HEIGHT / 2

PLAYER_WIDTH = 24
PLAYER_HALF_WIDTH = PLAYER_WIDTH / 2
PLAYER_HEIGHT = 24
PLAYER_HALF_HEIGHT = PLAYER_HEIGHT / 2

TERMINAL_VELOCITY = 20

SCALE2X = False

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
			buster=load_sound('buster.wav', self.mixer)
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
		return TILE_WIDTH

	def get_height(self):
		return TILE_HEIGHT

	def get_grid_position(self):
		return self.grid_position

	def get_position(self):
		return self.position

	def get_bottom(self):
		return self.position.y + TILE_HEIGHT

	def get_top(self):
		return self.position.y

	def get_left(self):
		return self.position.x

	def get_right(self):
		return self.position.x + TILE_WIDTH

	def update(self, delta):
		p = self.position
		self.rect.topleft = p.x + self.stage.get_scroll_offset(), p.y

class Stage:
	def __init__(self, loader):
		self.tile_height = 32
		self.tile_width = 32
		self.loader = loader
		self.player = None
		self.map = None
		self.platforms = {}
		self.ladders = {}
		self.platform_sprite_group = pygame.sprite.Group()
		self.ladder_sprite_group = pygame.sprite.Group()
		self.scroll_offset = 0
		self.area = Rect(0, 0, round(SCREEN_W / 2), round(SCREEN_H / 2))
		self.center = self.area.width / 2
		self.map_size = None
		self.sounds = {}

	def load_map_objects(self, type, map):
		objects = map.get_layer_by_name(type)
		if type == 'platforms':
			obj_dict = self.platforms
			sprite_group = self.platform_sprite_group
		elif type == 'ladders':
			obj_dict = self.ladders
			sprite_group = self.ladder_sprite_group
		else:
			raise SystemExist('Invalid map object type %d'%type)

		for obj in objects:
			tile = Tile(obj.image, self, obj.x, obj.y)
			obj_dict[obj.x, obj.y] = tile
			sprite_group.add(tile)
			print('Tile type=%s %d,%d'%(type, obj.x, obj.y))

	def load_map(self):
		self.map = self.loader.load_map('level-1.tmx')

		for object_type in ['platforms', 'ladders']:
			self.load_map_objects(object_type, self.map)

		self.map_size = self.map.width * TILE_WIDTH, self.map.height * TILE_HEIGHT

		print('Loaded map grid_size=%dx%d size=%dx%d' % (self.map.width, self.map.height, self.map_size[0], self.map_size[1]))

	def load(self):
		self.load_map()

	def tiles_at_y(self, tile_dict, x1, x2, y):
		gridx1 = math.floor(x1 / TILE_WIDTH) * TILE_WIDTH
		gridx2 = math.floor(x2 / TILE_WIDTH) * TILE_WIDTH
		gridy = math.floor(y / TILE_HEIGHT) * TILE_HEIGHT
		tiles = list()

		for gridx in range(gridx1, gridx2):
			if (gridx, gridy) in tile_dict:
				tile = tile_dict[gridx, gridy]
				if tile.get_right() > x1 or tile.get_left() < x2:
					tiles.append(tile)

		return tiles

	def tiles_at_x(self, tile_dict, x, y1, y2):
		gridx = math.floor(x / TILE_WIDTH) * TILE_WIDTH
		gridy1 = math.floor(y1 / TILE_HEIGHT) * TILE_HEIGHT
		gridy2 = math.floor(y2 / TILE_HEIGHT) * TILE_HEIGHT
		tiles = list()

		for gridy in range(gridy1, gridy2):
			if (gridx, gridy) in tile_dict:
				tile = tile_dict[gridx, gridy]
				if tile.get_top() > y1 or tile.get_bottom() < y2:
					tiles.append(tile)

		return tiles

	def platforms_at_y(self, x1, x2, y):
		return self.tiles_at_y(self.platforms, x1, x2, y)

	def platforms_at_x(self, x, y1, y2):
		return self.tiles_at_x(self.platforms, x, y1, y2)

	def ladders_at_x(self, x, y1, y2):
		return self.tiles_at_x(self.ladders, x, y1, y2)

	def ladders_at_y(self, x1, x2, y):
		return self.tiles_at_y(self.ladders, x1, x2, y)

	# def ladders_above(self, x1, x2, y):
	# 	tile_dict = self.ladders
	# 	gridx1 = math.floor(x1 / TILE_WIDTH) * TILE_WIDTH
	# 	gridx2 = math.floor(x2 / TILE_WIDTH) * TILE_WIDTH
	# 	gridy = math.floor(y / TILE_HEIGHT) * TILE_HEIGHT + TILE_HEIGHT
	# 	tiles = list()

	# 	for gridx in range(gridx1, gridx2):
	# 		if (gridx, gridy) in tile_dict:
	# 			tile = tile_dict[gridx, gridy]
	# 			if tile.get_right() > x1 or tile.get_left() < x2:
	# 				tiles.append(tile)

	# 	return tiles

	# def ladders_above(self, x, y1, y2):
	# 	return self.tiles_above(self.ladders, x, y1, y2)

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
		w, h = self.get_map_size()
		right_scroll_threshold = a.width / 2
		left_scroll_threshold = w - right_scroll_threshold

		if player_position.x > right_scroll_threshold and player_position.x < left_scroll_threshold:
			self.scroll_offset = -(player_position.x - right_scroll_threshold)
		elif player_position.x >= left_scroll_threshold:
			self.scroll_offset = -(w - a.width)
		elif player_position.x <= right_scroll_threshold:
			self.scroll_offset = 0

		# print('area_width=%d map_width=%d scroll_offset=%d'%(a.width, w, self.scroll_offset))

	def update(self, delta):
		self.platform_sprite_group.update(delta)
		self.ladder_sprite_group.update(delta)

	def draw(self, surface):
		self.platform_sprite_group.draw(surface)
		self.ladder_sprite_group.draw(surface)

class Player(pygame.sprite.Sprite):
	def __init__(self, spritesheet_loader, sounds):
		super().__init__()
		self.spritesheet_loader = spritesheet_loader
		self.sounds = sounds
		self.move_speed = 5
		self.jump_speed = 10

		self.max_height = 48
		self.max_width = 48

		self.velocity = pygame.math.Vector2(0, 0)
		self.position = pygame.math.Vector2(PLAYER_HALF_WIDTH, PLAYER_HALF_HEIGHT)

		self.current_time = 0
		self.direction = 1
		self.falling = True
		self.teleporting = True
		self.arriving = False
		self.climbing = False
		self.climbing_over = False
		self.climb_hand_side = 1
		self.dead = False
		self.shooting = False

		self.reset_animation = False

		self.area = Rect(0, 0, round(SCREEN_W / 2), round(SCREEN_H / 2))
		self.map_size = None

		self.load_sprites()

	def toggle_climb_hand_side(self, index):
		self.climb_hand_side = int(not self.climb_hand_side)

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
			walk_left=Animation([
				dict(duration=0.05, image=image_at(Rect((80, 8), (24, 24)), -1)),
				dict(duration=0.05, image=image_at(Rect((108, 8), (24, 24)), -1)),
				dict(duration=0.05, image=image_at(Rect((133, 8), (24, 24)), -1))
			]),
			walk_right=Animation([
				dict(duration=0.05, image=image_at(Rect((80, 8), (24, 24)), -1, flip=True)),
				dict(duration=0.05, image=image_at(Rect((108, 8), (24, 24)), -1, flip=True)),
				dict(duration=0.05, image=image_at(Rect((133, 8), (24, 24)), -1, flip=True))
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
			jump_right=Animation([
				dict(duration=0, image=image_at(Rect((194, 0), (26, 30)), -1, flip=True))
			]),
			teleport=Animation([
				dict(duration=0, image=image_at(Rect((670, 0), (8, 32)), -1))
			]),
			teleport_arrive=Animation([
				dict(duration=0.1, image=image_at(Rect((680, 0), (24, 32)), -1)),
				dict(duration=0.1, image=image_at(Rect((705, 0), (24, 32)), -1))
			]),
			still_shoot_left=Animation([
				dict(duration=0, image=image_at(Rect((291, 8), (32, 24)), -1))
			]),
			still_shoot_right=Animation([
				dict(duration=0, image=image_at(Rect((291, 8), (32, 24)), -1, flip=True))
			])
		)

		start_frame = self.animations['still_right'].current() if self.direction == 1 else  self.animations['still_left'].current()
		self.image = start_frame['image']
		self.rect = self.image.get_rect()

	def set_map_size(self, map_size):
		self.map_size = map_size

	def get_spritesheet_filename(self):
		return 'megaman-sprites.png'

	def is_dead(self):
		return self.dead

	def get_width(self):
		return PLAYER_WIDTH

	def get_height(self):
		return PLAYER_HEIGHT

	def get_position(self):
		return self.position

	def set_position(self, *position):
		self.position.x = position[0]
		self.position.y = position[1]

	def get_bottom(self):
		return self.position.y + PLAYER_HALF_HEIGHT

	def get_top(self):
		return self.position.y - PLAYER_HALF_HEIGHT

	def get_left(self):
		return self.position.x - PLAYER_HALF_WIDTH

	def get_right(self):
		return self.position.x + PLAYER_HALF_WIDTH

	def collide_bottom(self, y):
		print('Resetting player_y=%d'%y)
		self.velocity.y = 0
		self.position.y = y - PLAYER_HALF_HEIGHT

		if self.teleporting:
			self.teleporting = False
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
		self.position.y = y + PLAYER_HALF_HEIGHT
		self.falling = True

		print('collide_top new pos=%d,%d'%(self.position.x, self.position.y))

	def collide_right(self, x):
		self.velocity.x = 0
		self.position.x = x - PLAYER_HALF_WIDTH
		self.reset_animation = True

		print('collide_right new pos=%d,%d'%(self.position.x, self.position.y))

	def collide_left(self, x):
		self.velocity.x = 0
		self.position.x = x + PLAYER_HALF_WIDTH
		# self.stopping = True
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

	def grab_ladder(self, x, going_down=False):
		self.velocity.x = 0
		self.position.x = x + PLAYER_HALF_WIDTH
		if going_down:
			self.position.y += PLAYER_HALF_HEIGHT
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
			self.position.y = y - PLAYER_HALF_HEIGHT
			print('climb_off: Resetting player_y=%d'%self.position.y)
		self.climbing = False
		self.climbing_over = False
		self.reset_animation = True


	def climb_up(self):
		self.accelerate(0, -self.move_speed)

	def climb_down(self):
		self.accelerate(0, self.move_speed)

	def stop_climbing(self):
		self.velocity.y = 0
		self.reset_animation = True

	def fall(self):
		self.falling = True

	def is_falling(self):
		return self.falling

	def jump(self):
		if not self.falling:
			self.accelerate(0, -self.jump_speed)

	def shoot(self):
		self.shooting = True
		self.sounds.play_sound('buster')
		self.reset_animation = True

	def die(self):
		self.dead = True

	def stop_shooting(self):
		self.shooting = False
		self.reset_animation = True

	def update_position(self):
		v = self.get_velocity()
		self.position.x += v.x
		self.position.y += v.y

	def update_status(self):
		p = self.get_position()
		a = self.area
		if p.y > a.height:
			self.die()

	def update(self, delta):
		if self.teleporting:
			animation = self.animations['teleport']
		elif self.arriving:
			animation = self.animations['teleport_arrive']
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
				animation = self.animations['jump_right'] if self.direction == 1 else self.animations['jump_left']
			elif v.x != 0:
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
			self.image = animation.next(0)['image']
			self.current_time = 0

		a = self.area
		mw, mh = self.map_size
		right_scroll_threshold = a.width / 2
		left_scroll_threshold = mw - right_scroll_threshold
		p = self.position
		if p.x > right_scroll_threshold and p.x < left_scroll_threshold:
			self.rect.center = right_scroll_threshold, p.y
		elif p.x >= left_scroll_threshold:
			diff = p.x - left_scroll_threshold
			self.rect.center = (right_scroll_threshold + diff), p.y
		elif p.x <= right_scroll_threshold:
			self.rect.center = self.position

class Game:
	def __init__(self, game_config, logger, loader):
		self.config = game_config
		self.logger = logger
		self.loader = loader
		self.spritesheet_loader = SpriteSheetLoader(self.loader)
		self.mode = MODE_MENU
		self.clock = pygame.time.Clock()
		self.area = Rect(0, 0, round(SCREEN_W / 2), round(SCREEN_H / 2))
		self.sprites = pygame.sprite.Group()

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

	def init_stage(self):
		self.stage = Stage(self.loader)
		self.stage.load()

		self.player.set_map_size(self.stage.get_map_size())

		self.music_player.play('bombman-stage')

	def check_climb(self):
		player = self.player

		if not player.is_climbing():
			return

		stage = self.stage
		ladder_tiles = stage.ladders_at_x(player.get_position().x, player.get_top() - TILE_HEIGHT, player.get_bottom() + TILE_HEIGHT)
		top_tile = reduce((lambda top_tile, tile: tile if (top_tile is None or tile.get_top() < top_tile.get_top()) else top_tile), ladder_tiles, None)

		if not player.is_climbing_over():
			if player.get_top() <= top_tile.get_top() and player.get_position().y >= top_tile.get_top():
				player.climb_over()
			elif player.get_position().y < top_tile.get_top():
				player.climb_off(top_tile.get_top())
		else:
			if player.get_position().y < top_tile.get_top():
				player.climb_off(top_tile.get_top())
			elif player.get_top() > top_tile.get_top():
				player.stop_climbing_over()

	def apply_gravity(self):
		player = self.player

		if player.is_climbing():
			return

		x1 = player.get_left()
		x2 = player.get_right()
		v = player.get_velocity()
		stage = self.stage
		platforms_below = stage.platforms_at_y(x1, x2, player.get_bottom())
		ladders_below = stage.ladders_at_y(x1, x2, player.get_bottom())

		if len(platforms_below) == 0 and len(ladders_below) == 0:
			player.fall()

		if player.is_falling():
			if v.y == 0:
				player.accelerate(0, 1)
			elif v.y < TERMINAL_VELOCITY:
				player.accelerate(0, 1)
			else:
				player.set_velocity_y(TERMINAL_VELOCITY)

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
		title_rect = title_text.get_rect(center=(SCREEN_W/2, SCREEN_H/2))

		prompt_text = prompt_font.render('Press Enter to start', 0, prompt_font_color)
		prompt_rect = prompt_text.get_rect(center=(SCREEN_W/2, (SCREEN_H/2) + 50))

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

	def check_tile_collision(self, player):
		stage = self.stage
		platform_collide_list = pygame.sprite.spritecollide(player, stage.platform_sprite_group, False)
		ladder_collide_list = pygame.sprite.spritecollide(player, stage.ladder_sprite_group, False)
		v = player.get_velocity()
		if len(platform_collide_list) > 0:
			p = player.get_position()
			for tile in platform_collide_list:
				if v.y > 0 and tile.get_top() < player.get_bottom():
					print('collision BOTTOM tile_y=%d bottom=%d pos=%d,%d'%(tile.get_top(), player.get_bottom(), p.x, p.y))
					player.collide_bottom(tile.get_top())
				elif v.y < 0 and tile.get_bottom() > player.get_top():
					print('collision TOP tile_y=%d top=%d pos=%d,%d'%(tile.get_top(), player.get_top(), p.x, p.y))
					player.collide_top(tile.get_bottom())

				if v.x > 0 and tile.get_left() < player.get_right() and tile.get_top() < player.get_bottom():
					print('collision RIGHT tile_left=%d right=%d pos=%d,%d'%(tile.get_left(), player.get_right(), p.x, p.y))
					player.collide_right(tile.get_left())
				elif v.x < 0 and tile.get_right() > player.get_left() and tile.get_top() < player.get_bottom():
					print('collision LEFT tile_right=%d left=%d pos=%d,%d'%(tile.get_right(), player.get_left(), p.x, p.y))
					player.collide_left(tile.get_right())
		elif not player.is_climbing() and len(ladder_collide_list) > 0 and v.y > 0:
			for tile in ladder_collide_list:
				if tile.get_top() < player.get_bottom():
					print('ladder collision tile_top=%d bottom=%d'%(tile.get_top(), player.get_bottom()))
					player.collide_bottom(tile.get_top())
		else:
			mw, mh = stage.get_map_size()

			if player.get_left() < 0:
				player.collide_left(0)
			elif player.get_right() > mw:
				player.collide_right(mw)

	def grab_near_ladder(self, player):
		stage = self.stage
		tile_collide_list = pygame.sprite.spritecollide(player, stage.ladder_sprite_group, False)
		if len(tile_collide_list) > 0:
			tile = tile_collide_list[0]
			print('Grabbing ladder behind')
			player.grab_ladder(tile.get_left())
			return True
		else:
			tiles_below = stage.ladders_at_y(player.get_left(), player.get_right(), player.get_bottom())
			if len(tiles_below) > 0:
				tile = tiles_below[0]
				print('Grabbing ladder below')
				player.grab_ladder(tile.get_left(), True)
				return True

			return False

	def render_game(self):
		delta = self.clock.tick(FPS) / 1000
		player = self.player

		self.check_climb()
		self.apply_gravity()

		buffer = self.buffer
		sprites = self.sprites
		stage = self.stage
		area = self.area
		screen = self.screen
		mw, mh = stage.get_map_size()

		player.update_position()
		stage.update_scroll_offset(player.get_position())
		self.check_tile_collision(player)

		player.update_status()

		sprites.update(delta)
		stage.update(delta)

		background_color = stage.get_background_color()

		buffer.fill(background_color)

		stage.draw(buffer)
		sprites.draw(buffer)

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
		if event.type in (pygame.KEYDOWN, pygame.KEYUP):
			if event.key == pygame.K_RIGHT:
				if event.type == pygame.KEYDOWN:
					self.logger.debug('R Down')
					self.player.move_right()
				elif event.type == pygame.KEYUP:
					self.logger.debug('R Up')
					self.player.stop_x()
			elif event.key == pygame.K_LEFT:
				if event.type == pygame.KEYDOWN:
					self.logger.debug('L Down')
					self.player.move_left()
				elif event.type == pygame.KEYUP:
					self.logger.debug('L Up')
					self.player.stop_x()
			elif event.key == pygame.K_UP:
				if event.type == pygame.KEYDOWN:
					self.logger.debug('U Down')
					if not self.player.is_climbing():
						grabbed = self.grab_near_ladder(self.player)
						if grabbed:
							self.player.climb_up()
					else:
						self.player.climb_up()
				elif event.type == pygame.KEYUP:
					self.logger.debug('U Up')
					if self.player.is_climbing():
						self.player.stop_climbing()
			elif event.key == pygame.K_DOWN:
				if event.type == pygame.KEYDOWN:
					self.logger.debug('D Down')
					if not self.player.is_climbing():
						grabbed = self.grab_near_ladder(self.player)
						if grabbed:
							self.player.climb_down()
					else:
						self.player.climb_down()
				elif event.type == pygame.KEYUP:
					self.logger.debug('D Up')
					if self.player.is_climbing():
						self.player.stop_climbing()
			elif event.key == pygame.K_SPACE and event.type == pygame.KEYUP:
				self.logger.debug('Space')
				self.player.jump()
			elif event.key == pygame.K_f:
				if event.type == pygame.KEYDOWN:
					self.logger.debug('Pew')
					self.player.shoot()
				elif event.type == pygame.KEYUP:
					self.player.stop_shooting()
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