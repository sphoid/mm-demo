from pygame import sprite, draw
from pygame.sprite import Rect
from pygame.math import Vector2
from functools import reduce
from .constants import *
from .util import *
from .object import *
from .tile import *
from .enemy import *
from .item import *
from .hazards import Hazards
from .gate import Gates

class Stage:
	def __init__(self, config, loader, spritesheet_loader, view, sounds, explosions):
		self.config = config
		self.tile_height = 32
		self.tile_width = 32
		self.loader = loader
		self.spritesheet_loader = spritesheet_loader
		self.player = None
		self.map = None
		self.zone = None
		self.tiles = {}
		self.zones = {}
		self.ladders = {}
		self.platforms = {}
		self.hazards = {}
		self.items = {}
		self.gates = {}
		self.tile_sprite_group = sprite.Group()
		self.enemies = None
		self.items = None
		self.explosions = explosions
		self.enemy_sprite_group = sprite.Group()
		self.scroll_offset_x = 0
		self.scroll_offset_y = 0
		self.area = Rect(0, 0, round(SCREEN_W / 2), round(SCREEN_H / 2))
		self.center = self.area.width / 2
		self.map_size = None
		self.sounds = sounds
		self.music_track = None
		self.start_zone = None
		self.view = view

		self.warp_start_position = Vector2(0, 0)
		self.warp_land_position = Vector2(0, 0)

		self.debug = self.config.get_debug()

		self.load_map()

	def load_map(self):
		self.map = self.loader.load_map('cutman.tmx')
		self.music_track = self.map.properties['Music Track']
		self.start_zone = self.map.properties['Start Zone']
		self.map_size = self.map.width * TILE_WIDTH, self.map.height * TILE_HEIGHT

		map_debug = self.debug['map_debug']

		if not map_debug:
			for x, y, image in self.map.get_layer_by_name('tiles').tiles():
				rect = image.get_rect()
				width, height = rect.width, rect.height
				position = x * width, y * height
				tile = Tile(image, self, position[0], position[1])
				self.tiles[x, y] = tile
				self.tile_sprite_group.add(tile)
				# print('LOAD: Tile %d,%d %dx%d'%(position[0], position[1], width, height))

		for obj in self.map.get_layer_by_name('zones'):
			x, y, width, height = int(obj.x), int(obj.y), int(obj.width), int(obj.height)
			self.zones[obj.name] = GameObject(Rect((x, y), (width, height)), name=obj.name)
			print('LOAD: Zone %d,%d %dx%d'%(x, y, width, height))

		if self.debug['start_zone'] is not None:
			zone_name = self.debug['start_zone']
		else:
			zone_name = self.start_zone

		self.zone = self.zones[zone_name]
		self.view.set_offset(self.zone.get_position())

		for obj in self.map.get_layer_by_name('platforms'):
			x, y, width, height = int(obj.x), int(obj.y), int(obj.width), int(obj.height)
			self.platforms[x, y] = GameObject(Rect((x, y), (width, height)))

		for obj in self.map.get_layer_by_name('ladders'):
			x, y, width, height = int(obj.x), int(obj.y), int(obj.width), int(obj.height)
			self.ladders[x, y] = GameObject(Rect((x, y), (width, height)))

		for obj in self.map.get_layer_by_name('hazards'):
			x, y, width, height = int(obj.x), int(obj.y), int(obj.width), int(obj.height)
			self.hazards[x, y] = Hazards.load(obj.type, Rect((x, y), (width, height)))

		self.gates = Gates(self.spritesheet_loader, self.sounds, self.view)
		for obj in self.map.get_layer_by_name('gates'):
			x, y, width, height = int(obj.x), int(obj.y), int(obj.width), int(obj.height)
			self.gates.load(x, y, width, height)
			# self.gates[x, y] = Gate(self.spritesheet_loader, self.sounds, self.view, Rect((x, y), (width, height)))

		self.enemies = Enemies(self.spritesheet_loader, self.sounds, self.view, self, self.explosions)
		for obj in self.map.get_layer_by_name('enemies'):
			x, y = int(obj.x), int(obj.y)
			self.enemies.load(obj.name, obj.type, x, y, **obj.properties)
			print('LOAD: Enemy type=%s name=%s %d,%d'%(obj.type, obj.name, x, y))

		for obj in self.map.get_layer_by_name('player'):
			x, y = int(obj.x), int(obj.y)
			if obj.type == 'start':
				self.warp_start_position = Vector2(x, y)
			elif obj.type == 'land':
				self.warp_land_position = Vector2(x, y)

		self.items = Items(self.spritesheet_loader, self.sounds, self.view)
		for obj in self.map.get_layer_by_name('items'):
			x, y = int(obj.x), int(obj.y)
			self.items.load(obj.type, x, y)
			print("loaded item %s %d,%d"%(obj.type, x, y))

		print('Loaded map grid_size=%dx%d size=%dx%d' % (self.map.width, self.map.height, self.map_size[0], self.map_size[1]))

	def get_platforms(self):
		return self.platforms.values()

	def get_ladders(self):
		return self.ladders.values()

	def get_hazards(self):
		return self.hazards.values()

	def get_music_track(self):
		return self.music_track

	def get_zone(self):
		return self.zone

	def set_zone(self, zone_name):
		self.zone = self.zones[zone_name]

	def in_zone(self, player):
		prect = player.get_rect()
		colliding_zones = list(filter((lambda zone: prect.colliderect(zone.rect)), self.zones.values()))

		if len(colliding_zones) == 0:
			return None

		if len(colliding_zones) == 1:
			return colliding_zones[0]
		elif len(colliding_zones) > 1:
			next_zone = list(filter((lambda zone: zone.get_name() != self.zone.get_name()), colliding_zones))[0]
			return next_zone

	def platform_left_adjacent(self, rect):
		test_rect = Rect((rect.left - 1, rect.top), (rect.width, rect.height))
		colliding_platforms = list(filter((lambda platform: test_rect.colliderect(platform.rect)), self.platforms.values()))

		return colliding_platforms[0] if len(colliding_platforms) > 0 else None

	def platform_right_adjacent(self, rect):
		test_rect = Rect((rect.right + 1, rect.top), (rect.width, rect.height))
		colliding_platforms = list(filter((lambda platform: test_rect.colliderect(platform.rect)), self.platforms.values()))

		return colliding_platforms[0] if len(colliding_platforms) > 0 else None

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

	def get_warp_start_position(self):
		return self.warp_start_position

	def get_warp_land_position(self):
		return self.warp_land_position

	def get_zone_size(self):
		return self.zone.get_size()

	def get_map_size(self):
		return self.map_size

	def get_map_width(self):
		return self.map_size[0]

	def get_map_height(self):
		return self.map_size[1]

	def get_view(self):
		return self.view

	def get_enemies(self):
		return self.enemies

	def get_items(self):
		return self.items

	def get_gates(self):
		return self.gates

	def update(self, delta):
		self.tile_sprite_group.update(delta)

	def draw(self, surface):
		self.tile_sprite_group.draw(surface)

		if self.debug['map_debug']:
			view = self.view
			offset = view.get_offset()

			for platform in self.platforms.values():
				prect = platform.get_rect()
				pvrect = Rect((prect.left - offset.x, prect.top - offset.y), (platform.get_width(), platform.get_height()))
				if platform.is_flagged():
					color = (255, 255, 0)
				else:
					color = (0, 0, 255)
				draw.rect(surface, color, pvrect)

			for ladder in self.ladders.values():
				lrect = ladder.get_rect()
				lvrect = Rect((lrect.left - offset.x, lrect.top - offset.y), (ladder.get_width(), ladder.get_height()))
				draw.rect(surface, (255,0,0), lvrect)
