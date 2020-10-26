import os, sys, math, pygame, pytmx
from pygame import Rect
from pygame.time import Clock
from functools import reduce
from engine import *
from config import *

class GameConfig:
	def get_screen_resolution(self):
		return SCREEN_W, SCREEN_H

	def get_map(self):
		return MAP

	def get_debug(self):
		return dict(
			map_debug = MAP_DEBUG,
			player_debug = PLAYER_DEBUG,
			start_zone = DEBUG_START_ZONE,
			start_position = DEBUG_START_POSITION,
			player_invincible = PLAYER_INVINCIBLE,
		)

class GameLoop:
	def __init__(self, game_config, logger, loader):
		self.config = game_config
		self.logger = logger
		self.loader = loader
		self.mode = None
		self.clock = Clock()
		self.debug = dict(map_debug=MAP_DEBUG, player_debug=PLAYER_DEBUG, start_zone=DEBUG_START_ZONE, start_position=DEBUG_START_POSITION)

	def init_screen(self):
		self.resolution = width, height = self.config.get_screen_resolution()
		self.logger.debug('resolution: %dx%d' % (width, height))
		self.screen = pygame.display.set_mode(self.resolution, pygame.HWSURFACE|pygame.DOUBLEBUF)
		self.buffer = pygame.Surface((int(SCREEN_W), int(SCREEN_H)))

	def init_audio(self):
		self.mixer = pygame.mixer.init()
		self.sounds = SoundLibrary(self.loader, self.mixer)
		self.sounds.load()
		self.music_player = MusicPlayer(self.loader)

	def quit(self):
		self.running = False

	def loop(self):
		self.running = True
		while self.running:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					sys.exit()
				else:
					self.mode.handle_event(event)

			if self.running:
				delta = self.clock.tick(FPS) / 1000
				self.mode.update(delta)
				self.mode.render()

				# print('fps=%d'%(self.clock.get_fps()))


	def set_mode(self, mode_id):
		if mode_id == MODE_MENU:
			self.mode = Menu(self.logger, self.loader, self.screen, self.sounds, self.music_player, self)
		elif mode_id == MODE_GAME:
			self.mode = Game(self.config, self.logger, self.loader, self.screen, self.sounds, self.music_player, self)
		elif mode_id == MODE_GAME_OVER:
			self.mode = GameOver(self.logger, self.loader, self.screen, self.sounds, self.music_player, self)

	def start(self):
		self.init_screen()
		self.init_audio()

		if self.mode is None:
			self.set_mode(MODE_MENU)

		self.loop()

def main():
	if not pygame.font: print('Warning, fonts disabled')
	if not pygame.mixer: print('Warning, sound disabled')

	game_config = GameConfig()
	logger = Logger(DEBUG)
	loader = ResourceLoader(game_config, logger)
	game = GameLoop(game_config, logger, loader)
	pygame.init()
	game.start()
	pygame.quit()

main()