import os, sys, pygame, pytmx
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

SCALE2X = False

def hex_to_rgb(value):
	value = value.lstrip('#')
	lv = len(value)
	return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

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

class Player(pygame.sprite.Sprite):
	def __init__(self, spritesheet_loader):
		super().__init__()
		self.spritesheet_loader = spritesheet_loader
		self.speed = 5
		self.jump_speed = 10
		self.direction = 1
		self.velocity = pygame.math.Vector2(0, 0)
		self.position = [0, 0]

		self.max_height = 48
		self.max_width = 48

		self.current_time = 0
		self.moving = False
		self.stopping = False
		self.falling = True

		self.stage = None

		self.area = pygame.Rect(0, 0, SCREEN_W / 2, SCREEN_H / 2)

		self.load_sprites()

	def load_sprites(self):
		self.spritesheet = self.spritesheet_loader.load(self.get_spritesheet_filename())
		image_at = self.spritesheet.image_at

		self.animations = dict(
			still_left=Animation([
				dict(duration=1, image=image_at(Rect((0, 8), (24, 24)), -1)),
				dict(duration=0.1, image=image_at(Rect((25, 8), (24, 24)), -1))
			]),
			still_right=Animation([
				dict(duration=1, image=image_at(Rect((0, 8), (24, 24)), -1, flip=True)),
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
		self.image = start_frame['image']
		self.rect = self.image.get_rect()

	def get_spritesheet_filename(self):
		return 'megaman-sprites.png'

	def get_width(self):
		return self.rect.width

	def get_height(self):
		return self.rect.height

	def accelerate(self, x, y):
		self.velocity.x += x
		self.velocity.y += y

	def deccelerate(self, x, y):
		self.velocity.x -= x
		self.velocity.y -= y

	def set_velocity(self, x, y):
		self.velocity.x = x
		self.velocity.y = y

	def set_velocity_x(self, velocity):
		self.velocity.x = velocity

	def set_velocity_y(self, velocity):
		self.velocity.y = velocity

	def move(self, x, y):
		self.position = [x, y]

	def move_right(self):
		self.direction = 1
		self.moving = True
		self.accelerate(self.speed, 0)

	def move_left(self):
		self.direction = 0
		self.moving = True
		self.accelerate(-self.speed, 0)

	def stop_x(self):
		self.set_velocity_x(0)
		self.stopping = True
	def stop_y(self):
		self.set_velocity_y(0)
		self.stopping = True

	def jump(self):
		if not self.falling:
			self.accelerate(0, -self.jump_speed)

	def set_stage(self, stage):
		self.stage = stage
		start_position = self.stage.get_start_position()
		self.move(start_position[0], start_position[1] - self.get_height())

	def check_collision(self):
		tile_collide_list = pygame.sprite.spritecollide(self, self.stage.tile_sprite_group, False)
		if len(tile_collide_list) > 0:
			if self.velocity.y > 0:
				y = reduce((lambda y, tile: tile.rect.top if tile.rect.top < y else y), tile_collide_list, self.area.height)
				if y < self.rect.bottom:
					self.stop_y()
					self.position[1] = y - self.rect.height
					self.falling = False
					self.stopping = True
			elif self.velocity.y < 0:
				y = reduce((lambda y, tile: tile.rect.bottom if tile.rect.bottom > y else y), tile_collide_list, 0)
				if y > self.rect.top:
					self.stop_y()
					self.position[1] = y
			elif self.velocity.x > 0:
				x = min(map((lambda tile: tile.rect.left), tile_collide_list))
				if x < self.position[0] + self.rect.width:
					self.stop_x()
					self.position[0] = x - self.rect.width
			elif self.velocity.x < 0:
				x = max(map((lambda tile: tile.rect.right), tile_collide_list))
				if x > self.position[0]:
					self.stop_x()
					self.position[0] = x
		else:
			if self.position[0] < 0:
				self.position[0] = 0
			elif self.position[0] + self.rect.width > self.area.width:
				self.position[0] = self.area.width - self.rect.width

	def apply_gravity(self):
		tiles_below = list(filter((lambda tile: tile.rect.left >= self.position[0] and tile.rect.left <= (self.position[0] + self.rect.width)), self.stage.tile_sprite_group))
		nearest_tile_distance = min(map((lambda tile: tile.rect.top - self.rect.bottom), tiles_below))

		if nearest_tile_distance > 0:
			self.falling = True

		if self.falling:
			if self.velocity.y == 0:
				self.accelerate(0, 1)
			else:
				self.accelerate(0, 0.8)

	def update(self, delta):
		self.check_collision()
		self.apply_gravity()

		if self.velocity.y != 0:
			animation = self.animations['jump_right'] if self.direction == 1 else self.animations['jump_left']
		elif self.velocity.x != 0:
			animation = self.animations['walk_right'] if self.direction == 1 else self.animations['walk_left']
		else:
			animation = self.animations['still_right'] if self.direction == 1 else self.animations['still_left']

			if self.stopping:
				animation.reset()

		self.current_time += delta
		if self.current_time >= animation.next_time:
			self.image = animation.next(0)['image']
			self.current_time = 0

		self.position = [self.position[0] + self.velocity.x, self.position[1] + self.velocity.y]
		self.rect.topleft = self.position

		# print('frame=%d/%d atime=%.2f velocity=%.2f,%.2f bound=%dx%d pos=%dx%d' % (self.sprite_index, len(self.images), animation_time, self.velocity.x, self.velocity.y, self.rect.width, self.rect.height, self.position[0], self.position[1]))

class Tile(pygame.sprite.Sprite):
	def __init__(self, image, x, y):
		super().__init__()
		self.image = image
		self.rect = image.get_rect()
		self.rect.topleft = x * 16, y * 16

class Stage:
	def __init__(self, loader):
		self.tile_height = 32
		self.tile_width = 32
		self.loader = loader
		self.map = None

		self.tile_sprite_group = pygame.sprite.Group()

		self.area = pygame.Rect(0, 0, SCREEN_W / 2, SCREEN_H / 2)

	def load_map(self):
		self.map = self.loader.load_map('test.tmx')

		layer = self.map.layers[0]
		for x, y, image in layer.tiles():
			self.tile_sprite_group.add(Tile(image, x, y))

	def get_background_color(self):
		return hex_to_rgb(self.map.background_color)

	def get_start_position(self):
		return (10, self.area.height - (self.tile_height * 5))

	def load(self):
		self.load_map()

		# start_position = self.get_start_position()
		# self.player.move(start_position[0], start_position[1] - self.player.get_sprite_height())

	def update(self, delta):
		self.tile_sprite_group.update(delta)

	def draw(self, screen):
		self.tile_sprite_group.draw(screen)

class Game:
	def __init__(self, game_config, logger, loader):
		self.config = game_config
		self.logger = logger
		self.loader = loader
		self.spritesheet_loader = SpriteSheetLoader(self.loader)
		self.mode = MODE_GAME
		self.clock = pygame.time.Clock()

	def init_screen(self):
		self.resolution = width, height = self.config.get_screen_resolution()
		self.logger.debug('resolution: %dx%d' % (width, height))
		self.screen = pygame.display.set_mode(self.resolution, pygame.HWSURFACE|pygame.DOUBLEBUF)
		self.buffer = pygame.Surface((SCREEN_W/2, SCREEN_H/2))

	def init_stage(self):
		self.stage = Stage(self.loader)
		self.stage.load()

	def init_player(self):
		self.player = Player(self.spritesheet_loader)
		self.sprites = pygame.sprite.Group((self.player))
		self.player.set_stage(self.stage)

	def render_game(self):
		delta = self.clock.tick(FPS) / 1000

		self.sprites.update(delta)
		self.stage.update(delta)

		background_color = self.config.get_background_color()
		background_color = self.stage.get_background_color()

		self.buffer.fill(background_color)
		self.sprites.draw(self.buffer)
		self.stage.draw(self.buffer)

		self.screen.blit(pygame.transform.scale2x(self.buffer), (0, 0))

		# self.screen.fill(background_color)
		# self.sprites.draw(self.screen)
		# self.stage.draw(self.screen)
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
		self.init_stage()
		self.init_player()

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