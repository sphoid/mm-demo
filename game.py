import os, sys, math, pygame, pytmx
from pygame import Rect
from functools import reduce
# from pytmx.util_pygame import load_pygame

DEBUG = 0
INFO = 2
WARN = 4
ERROR = 8
FATAL = 16

TYPE_INTEGER = 'integer'
TYPE_FLOAT = 'float'
TYPE_STRING = 'string'
TYPE_OBJECT = 'object'

MODE_MENU = 'menu'
MODE_GAME = 'game'
MODE_PAUSE = 'pause'

SPRITE_CHARACTER = 'character'

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

	def get_data_path(self):
		return "data"

	def get_images_path(self):
		return self.get_data_path() + '/images'

	def get_background_color(self):
		return 0, 0, 0

	def get_animation_speed(self):
		return [1, 1]

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

	def load_audio(self, filename):
		class NoneSound:
			def play(self): pass

		if not pygame.mixer:
			return NoneSound()

		filepath = os.path.join('data', 'audio', filename)

		try:
			sound = pygame.mixer.Sound(filepath)
		except pygame.error as message:
			self.logger.error('Cannot load audio: %s' %(filepath))
			raise SystemExit(message)

		return sound

class Animation:
	def __init__(self, frames):
		self.frames = frames
		self.index = 0
		self.next_time = frames[self.index]['duration']

	def reset(self):
		self.index = len(self.frames) - 1
		self.next_time = 0

	def current(self):
		return self.frames[self.index]

	def next(self, last_time):
		if self.index == len(self.frames) - 1:
			self.index = 0
		else:
			self.index += 1

		next_frame = self.frames[self.index]
		self.next_time = next_frame['duration'] + last_time

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


class TileSprite(pygame.sprite.Sprite):
	def __init__(self, image, *position):
		super().__init__()
		self.image = image
		self.rect = image.get_rect()
		self.rect.topleft = position

class Tiles:
	def __init__(self, map_rect):
		self.tiles = {}
		self.tile_sprite_group = pygame.sprite.Group()
		self.map_rect = map_rect

	def add(self, image, x, y):
		print('Registering tile %d, %d'%(x, y))
		position = ((x * TILE_WIDTH) + self.map_rect.left), ((y * TILE_HEIGHT) + self.map_rect.top)
		sprite = TileSprite(image, position)
		self.tiles[x, y] = sprite
		self.tile_sprite_group.add(sprite)
		
		return sprite

	def tile_at(self, *position):
		xpos, ypos = position
		x = math.ceil(xpos / TILE_WIDTH)
		y = math.ceil(ypos / TILE_HEIGHT)

		# print('tile_at=%d,%d'%(x, y))

		if (x, y) in self.tiles:
			return self.tiles[x, y]
		return None

	def get_position(self, x, y):
		return (x * TILE_WIDTH) + (TILE_HALF_WIDTH), (y * TILE_HEIGHT) + (TILE_HALF_HEIGHT)

	def get_left(self, x, y):
		position = self.get_position(x, y)
		return position[0] - TILE_HALF_WIDTHself.stage

	def get_right(self, x, y):
		position = self.get_position(x, y)
		return position[0] + TILE_HALF_WIDTH

	def get_bottom(self, x, y):
		position = self.get_position(x, y)
		return position[1] + TILE_HALF_HEIGHT

	def get_top(self, x, y):
		position = self.get_position(x, y)
		return position[1] - TILE_HALF_HEIGHT

	def spritecollide(self, sprite):
		return pygame.sprite.spritecollide(sprite, self.tile_sprite_group, False)

	def update(self, delta):
		for pos in self.tiles.keys():
			x, y = pos
			sprite = self.tiles[pos]
			sprite.rect.topleft = ((x * TILE_WIDTH) + self.map_rect.left), ((y * TILE_HEIGHT) + self.map_rect.top)

		self.tile_sprite_group.update(delta)

	def draw(self, surface):
		self.tile_sprite_group.draw(surface)

class PlayerSprite(pygame.sprite.Sprite):
	def __init__(self, image):
		super().__init__()
		self.image = image
		self.rect = image.get_rect()

class Player:
	def __init__(self, spritesheet_loader):
		self.spritesheet_loader = spritesheet_loader
		self.speed = 5
		self.jump_speed = 10
		self.direction = 1
		self.velocity = pygame.math.Vector2(0, 0)
		self.position = PLAYER_HALF_WIDTH, PLAYER_HALF_HEIGHT

		self.max_height = 48
		self.max_width = 48

		self.current_time = 0
		self.stopping = False
		self.falling = True

		self.area = Rect(0, 0, round(SCREEN_W / 2), round(SCREEN_H / 2))
		self.map_rect = None

		self.player_sprite_group = pygame.sprite.Group()

		self.load_sprites()

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
			jump_left=Animation([
				dict(duration=0, image=image_at(Rect((194, 0), (26, 30)), -1))
			]),
			jump_right=Animation([
				dict(duration=0, image=image_at(Rect((194, 0), (26, 30)), -1, flip=True))
			])
		)

		start_frame = self.animations['still_right'].current() if self.direction == 1 else  self.animations['still_left'].current()
		self.sprite = PlayerSprite(start_frame['image'])
		self.rect = self.sprite.rect
		self.player_sprite_group.add(self.sprite)

	def set_map_rect(self, map_rect):
		self.map_rect = map_rect

	def get_spritesheet_filename(self):
		return 'megaman-sprites.png'

	def get_width(self):
		return PLAYER_WIDTH

	def get_height(self):
		return PLAYER_HEIGHT

	def get_position(self):
		return self.position

	def set_position(self, *position):
		self.position = position

	def get_bottom(self):
		return self.position[1] + PLAYER_HALF_HEIGHT

	def get_top(self):
		return self.position[1] - PLAYER_HALF_HEIGHT

	def get_left(self):
		return self.position[0] - PLAYER_HALF_WIDTH

	def get_right(self):
		return self.position[0] + PLAYER_HALF_WIDTH

	def collide_bottom(self, y):
		self.velocity.y = 0
		self.position = self.position[0], y - PLAYER_HALF_HEIGHT
		self.falling = False
		self.stopping = True

		print('collide_bottom pos=%d,%d'%self.position)

	def collide_top(self, y):
		self.velocity.y = 0
		self.position = self.position[0], y + PLAYER_HALF_HEIGHT
		self.falling = True

		print('collide_top pos=%d,%d'%self.position)

	def collide_right(self, x):
		self.velocity.x = 0
		self.position = x - PLAYER_HALF_WIDTH, self.position[1]
		self.stopping = True

	def collide_left(self, x):
		self.velocity.x = 0
		self.position = x + PLAYER_HALF_WIDTH, self.position[1]
		self.stopping = True

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
		self.accelerate(self.speed, 0)

	def move_left(self):
		self.direction = 0
		self.accelerate(-self.speed, 0)

	def stop_x(self):
		self.set_velocity_x(0)
		self.stopping = True

	def jump(self):
		if not self.falling:
			self.accelerate(0, -self.jump_speed)

	def update_position(self):
		v = self.get_velocity()
		self.position = self.position[0] + v.x, self.position[1] + v.y

	def check_collision(self, tiles, max_x):
		tile_collide_list = tiles.spritecollide(self.sprite)
		if len(tile_collide_list) > 0:
			v = self.velocity
			if v.y > 0:
				y = min(list(map((lambda tile: tile.rect.top), tile_collide_list)))
				if y < self.get_bottom():
					print('collision tile_y=%d bottom=%d'%(y, self.get_bottom()))
					self.collide_bottom(y)
			elif v.y < 0:
				y = max(list(map((lambda tile: tile.rect.bottom), tile_collide_list)))
				if y > self.get_top():
					self.collide_top(y)
			elif v.x > 0:
				x = min(map((lambda tile: tile.rect.left), tile_collide_list))
				if x < self.get_right():
					print('collision tile_x=%d right=%d'%(x, self.get_right()))
					self.collide_right(x)
			elif v.x < 0:
				x = max(map((lambda tile: tile.rect.right), tile_collide_list))
				if x > self.get_left():
					self.collide_left(x)
		else:
			if self.get_left() < 0:
				self.collide_left(0)
			elif self.get_right() > max_x:
				self.collide_right(max_x)

	def update(self, delta):
		v = self.velocity

		if v.y != 0:
			animation = self.animations['jump_right'] if self.direction == 1 else self.animations['jump_left']
		elif v.x != 0:
			animation = self.animations['walk_right'] if self.direction == 1 else self.animations['walk_left']
		else:
			animation = self.animations['still_right'] if self.direction == 1 else self.animations['still_left']

			if self.stopping:
				animation.reset()
				self.stopping = False

		self.current_time += delta
		if self.current_time >= animation.next_time:
			self.sprite.image = animation.next(0)['image']
			self.current_time = 0

		a = self.area
		right_scroll_threshold = a.width / 2
		left_scroll_threshold = self.map_rect.width - right_scroll_threshold
		px, py = self.position
		if px > right_scroll_threshold and px < left_scroll_threshold:
			self.sprite.rect.center = right_scroll_threshold, py
		elif px >= left_scroll_threshold:
			diff = px - left_scroll_threshold
			self.sprite.rect.center = (right_scroll_threshold + diff), py
		elif px <= right_scroll_threshold:
			self.sprite.rect.center = self.position

	def draw(self, surface):
		self.player_sprite_group.draw(surface)

class Stage:
	def __init__(self, loader):
		self.tile_height = 32
		self.tile_width = 32
		self.loader = loader
		self.player = None
		self.map = None
		self.layer = None
		self.tiles = None

		self.area = Rect(0, 0, round(SCREEN_W / 2), round(SCREEN_H / 2))
		self.center = self.area.width / 2
		self.rect = Rect(0, 0, round(SCREEN_W / 2), round(SCREEN_H / 2))

	def load_map(self):
		self.map = self.loader.load_map('test.tmx')
		self.rect = Rect(0, 0, self.map.width * TILE_WIDTH, self.map.height * TILE_HEIGHT)
		self.tiles = Tiles(self.rect)
		self.layer = self.map.layers[0]

		for x, y, image in self.layer.tiles():
			sprite = self.tiles.add(image, x, y)
			# print ('Load tile grid=%d,%d pos=%d,%d'%(x, y, sprite.rect.left, sprite.rect.top))

		print('Loaded map size=%dx%d' % (self.map.width, self.map.height))

	def get_background_color(self):
		return hex_to_rgb(self.map.background_color)

	def get_map_size(self):
		return self.map.width * TILE_WIDTH, self.map.height * TILE_HEIGHT

	def load(self, player):
		self.load_map()

		player.set_map_rect(self.rect)
		self.player = player

	def update(self, delta):
		a = self.area
		right_scroll_threshold = a.width / 2
		left_scroll_threshold = self.rect.width - right_scroll_threshold
		px, py = self.player.position

		print('px=%d/%d/%d'%(px, right_scroll_threshold, left_scroll_threshold))

		if px > right_scroll_threshold and px < left_scroll_threshold:
			diff = px - right_scroll_threshold
			self.rect.left = -diff
		elif px >= left_scroll_threshold:
			self.rect.right = a.right
		elif px <= right_scroll_threshold:
			self.rect.left = 0

		self.tiles.update(delta)

	def draw(self, surface):
		self.tiles.draw(surface)

class Game:
	def __init__(self, game_config, logger, loader):
		self.config = game_config
		self.logger = logger
		self.loader = loader
		self.spritesheet_loader = SpriteSheetLoader(self.loader)
		self.mode = MODE_GAME
		self.clock = pygame.time.Clock()
		self.area = Rect(0, 0, round(SCREEN_W / 2), round(SCREEN_H / 2))
		self.player_position = 0, 0

	def init_screen(self):
		self.resolution = width, height = self.config.get_screen_resolution()
		self.logger.debug('resolution: %dx%d' % (width, height))
		self.screen = pygame.display.set_mode(self.resolution, pygame.HWSURFACE|pygame.DOUBLEBUF)
		self.buffer = pygame.Surface((round(SCREEN_W/2), round(SCREEN_H/2)))

	def init_player(self):
		self.player = Player(self.spritesheet_loader)

	def init_stage(self):
		self.stage = Stage(self.loader)
		self.stage.load(self.player)

	def get_player_lower_bound(self):
		x, y = self.player_position
		return y + PLAYER_HALF_HEIGHT

	def get_player_upper_bound(self):
		x, y = self.player_position
		return y - PLAYER_HALF_HEIGHT

	def apply_gravity(self):
		p = self.player
		v = p.get_velocity()
		tiles = self.stage.tiles
		tile_below = tiles.tile_at(p.get_left(), p.get_bottom())

		if tile_below is None:
			p.falling = True

		if p.falling:
			if v.y == 0:
				p.accelerate(0, 1)
			elif v.y < TERMINAL_VELOCITY:
				p.accelerate(0, 0.8)
			else:
				p.set_velocity_y(TERMINAL_VELOCITY)

	def render_game(self):
		delta = self.clock.tick(FPS) / 1000

		self.apply_gravity()

		p = self.player
		s = self.stage
		a = self.area

		p.update_position()

		mw, mh = s.get_map_size()

		p.check_collision(s.tiles, mw)

		p.update(delta)
		s.update(delta)

		background_color = self.config.get_background_color()
		background_color = self.stage.get_background_color()

		self.buffer.fill(background_color)
		self.player.draw(self.buffer)
		self.stage.draw(self.buffer)

		self.screen.blit(pygame.transform.scale2x(self.buffer), (0, 0))

		pygame.display.flip()

	def render(self):
		if self.mode == MODE_GAME:
			self.render_game()
		elif self.mode == MODE_PAUSE:
			self.render_pause()

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
			elif event.key == pygame.K_SPACE and event.type == pygame.KEYUP:
				self.logger.debug('Space')
				self.player.jump()
			elif event.key == pygame.K_ESCAPE:
				self.running = False


	def handle_event(self, event):
		if self.mode == MODE_GAME:
			self.handle_game_event(event)
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

	def start(self):
		pygame.init()
		self.init_screen()
		self.init_player()
		self.init_stage()

		self.loop()

		pygame.quit()

def main():
	if not pygame.font: print('Warning, fonts disabled')
	if not pygame.mixer: print('Warning, sound disabled')

	game_config = GameConfig()
	logger = Logger(DEBUG)
	loader = ResourceLoader(game_config, logger)
	game = Game(game_config, logger, loader)
	game.start()

main()