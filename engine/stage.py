from pygame import sprite
from pygame.sprite import Rect
from .constants import *
from .util import *
from .object import *
from .tile import *
from .enemy import *

class Stage:
	def __init__(self, loader, spritesheet_loader, sounds, **opts):
		self.tile_height = 32
		self.tile_width = 32
		self.loader = loader
		self.spritesheet_loader = spritesheet_loader
		self.player = None
		self.map = None
		self.tiles = {}
		self.ladders = {}
		self.platforms = {}
		self.tile_sprite_group = sprite.Group()
		self.enemy_sprite_group = sprite.Group()
		self.scroll_offset = 0
		self.area = Rect(0, 0, round(SCREEN_W / 2), round(SCREEN_H / 2))
		self.center = self.area.width / 2
		self.map_size = None
		self.sounds = sounds

		if hasattr(opts, 'map_debug'):
			self.map_debug = map_debug
		else:
			self.map_debug = False

	def load_map(self):
		self.map = self.loader.load_map('level-1.tmx')

		if not self.map_debug:
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

		if self.map_debug:
			for platform in self.platforms.values():
				pygame.draw.rect(surface, (0, 0, 255), platform.rect)

			for ladder in self.ladders.values():
				pygame.draw.rect(surface, (255,0,0), ladder.rect)
