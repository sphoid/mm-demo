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
TILE_WIDTH = 16
TILE_HEIGHT = 16

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


class TileSprite(pygame.sprite.Sprite):
	def __init__(self, image, x, y, map_rect):
		super().__init__()
		self.image = image
		self.rect = image.get_rect()
		self.x = x
		self.y = y
		self.map_rect = map_rect

	def update(self, delta):
		self.rect.topleft = ((self.x * TILE_WIDTH) + self.map_rect.left), ((self.y * TILE_HEIGHT) + self.map_rect.top)

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
		self.position = [0, 0]

		self.max_height = 48
		self.max_width = 48

		self.current_time = 0
		self.stopping = False
		self.falling = True

		self.stage = None

		self.area = Rect(0, 0, round(SCREEN_W / 2), round(SCREEN_H / 2))

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
		self.player_sprite_group.add(self.sprite)

	def get_spritesheet_filename(self):
		return 'megaman-sprites.png'

	def get_width(self):
		return self.sprite.rect.width

	def get_height(self):
		return self.sprite.rect.height

	def get_map_x(self):
		return self.position[0]

	def set_map_x(self, x):
		self.position[0] = round(x)

	def set_map_y(self, y):
		self.position[1] = round(y)

	def get_map_y(self):
		return self.position[1]

	def set_map_position(self, x, y):
		self.position = round(x), round(y)

	def get_screen_x(self):
		return self.sprite.rect.left

	def set_screen_x(self, x):
		self.sprite.rect.left = round(x)

	def set_screen_position(self, x, y):
		self.sprite.rect.topleft = round(x), round(y)

	def get_screen_y(self):
		return self.sprite.rect.top

	def set_screen_y(self, y):
		self.sprite.rect.top = round(y)

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
		self.accelerate(self.speed, 0)

	def move_left(self):
		self.direction = 0
		self.accelerate(-self.speed, 0)

	def stop_x(self):
		self.set_velocity_x(0)
		self.stopping = True

	def stop_y(self):
		self.set_velocity_y(0)

	def jump(self):
		if not self.falling:
			self.accelerate(0, -self.jump_speed)

	def set_stage(self, stage):
		stage.set_player(self)

		self.stage = stage
		start_position = self.stage.get_start_position()
		self.move(start_position[0], start_position[1] - self.get_height())

	def check_collision(self):
		tile_collide_list = pygame.sprite.spritecollide(self.sprite, self.stage.tile_sprite_group, False)
		if len(tile_collide_list) > 0:
			if self.velocity.y > 0:
				y = reduce((lambda y, tile: tile.rect.top if tile.rect.top < y else y), tile_collide_list, self.area.height)
				if y < self.get_map_y() + self.get_height():
					self.stop_y()
					self.set_map_y(y - self.get_height())
					self.falling = False
					self.stopping = True
			elif self.velocity.y < 0:
				y = reduce((lambda y, tile: tile.rect.bottom if tile.rect.bottom > y else y), tile_collide_list, 0)
				if y > self.get_map_y():
					self.stop_y()
					self.set_map_y(y)
					self.falling = True
			elif self.velocity.x > 0:
				x = min(map((lambda tile: tile.rect.left), tile_collide_list))
				if x < self.get_map_x() + self.get_width():
					self.stop_x()
					self.set_map_x(x - self.get_width())
			elif self.velocity.x < 0:
				x = max(map((lambda tile: tile.rect.right), tile_collide_list))
				if x > self.get_map_x():
					self.stop_x()
					self.set_map_x(x)
		else:
			if self.get_map_x() < 0:
				self.set_map_x(0)
			elif self.get_map_x() + self.get_width() > self.area.width:
				self.set_map_x(self.area.width - self.get_width())

	def apply_gravity(self):
		tiles_below = list(filter((lambda tile: tile.rect.left >= self.get_screen_x() and tile.rect.left <= (self.get_screen_x() + self.get_width())), self.stage.tile_sprite_group))

		if len(tiles_below) > 0:
			nearest_tile_distance = min(map((lambda tile: tile.rect.top - (self.get_screen_y() + self.get_height())), tiles_below))

			if nearest_tile_distance > 0:
				self.falling = True
		else:
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
				self.stopping = False

		self.current_time += delta
		if self.current_time >= animation.next_time:
			self.sprite.image = animation.next(0)['image']
			self.current_time = 0

		self.position = [self.get_map_x() + self.velocity.x, self.get_map_y() + self.velocity.y]

	def draw(self, screen):
		self.player_sprite_group.draw(screen)

class Stage:
	def __init__(self, loader):
		self.tile_height = 32
		self.tile_width = 32
		self.loader = loader
		self.player = None
		self.map = None
		self.layer = None
		self.tiles = []

		self.tile_sprite_group = pygame.sprite.Group()

		self.area = Rect(0, 0, round(SCREEN_W / 2), round(SCREEN_H / 2))
		self.center = self.area.width / 2
		self.rect = Rect(0, 0, round(SCREEN_W / 2), round(SCREEN_H / 2))

	def set_player(self, player):
		self.player = player

	def load_map(self):
		self.map = self.loader.load_map('test.tmx')
		self.rect = Rect(0, 0, self.get_map_width(), self.get_map_height())
		self.layer = self.map.layers[0]

		for x, y, image in self.layer.tiles():
			self.tile_sprite_group.add(TileSprite(image, x, y, self.rect))

	def get_background_color(self):
		return hex_to_rgb(self.map.background_color)

	def get_map_width(self):
		return self.map.width * self.map.tilewidth

	def get_map_height(self):
		return self.map.height * self.map.tileheight

	def get_map_screen_x(self):
		return self.rect.left

	def get_map_screen_y(self):
		return self.rect.top

	def scroll(self, velocity):
		vx = round(velocity[0])
		vy = round(velocity[1])

		self.rect.left -= vx
		self.rect.top -= vy

	def get_start_position(self):
		return (10, self.area.height - self.tile_height)

	def load(self):
		self.load_map()

	def update(self, delta):
		player_x = self.player.get_map_x()
		player_y = self.player.get_map_y()

		if self.get_map_width() > self.area.width:
			right_scroll_threshold = self.center
			left_scroll_threshold = self.get_map_width() - self.center

			if self.player.velocity.x != 0 and player_x >= right_scroll_threshold and player_x <= left_scroll_threshold:
				velocity = [self.player.velocity.x, 0]
				self.scroll(velocity)
				self.player.set_screen_position(self.player.get_screen_x(), player_y)
			elif player_x > left_scroll_threshold:
				self.player.set_screen_position(left_scroll_threshold + (self.get_map_width() - player_x), player_y)
			elif player_x < right_scroll_threshold:
				self.player.set_screen_position(player_x, player_y)
		else:
			self.player.set_screen_position(player_x, player_y)

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
		self.area = Rect(0, 0, round(SCREEN_W / 2), round(SCREEN_H / 2))

	def init_screen(self):
		self.resolution = width, height = self.config.get_screen_resolution()
		self.logger.debug('resolution: %dx%d' % (width, height))
		self.screen = pygame.display.set_mode(self.resolution, pygame.HWSURFACE|pygame.DOUBLEBUF)
		self.buffer = pygame.Surface((round(SCREEN_W/2), round(SCREEN_H/2)))

	def init_stage(self):
		self.stage = Stage(self.loader)
		self.stage.load()

	def init_player(self):
		self.player = Player(self.spritesheet_loader)
		self.player.set_stage(self.stage)

	def render_game(self):
		delta = self.clock.tick(FPS) / 1000

		self.player.update(delta)
		self.stage.update(delta)

		print('player mpos=%d,%d spos=%d,%d map=%d, %d' % (self.player.get_map_x(), self.player.get_map_y(), self.player.get_screen_x(), self.player.get_screen_y(), self.stage.get_map_screen_x(), self.stage.get_map_screen_y()))

		background_color = self.config.get_background_color()
		background_color = self.stage.get_background_color()

		self.buffer.fill(background_color)
		self.player.draw(self.buffer)
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