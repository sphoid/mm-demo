import pygame
from pygame import display, Surface
from pygame.sprite import Rect
from .constants import *

class GameOver:
	def __init__(self, logger, input, loader, screen, sounds, music_player, game, **opts):
		self.logger = logger
		self.screen = screen
		self.input = input
		self.buffer = Surface((int(SCREEN_W), int(SCREEN_H)))
		self.loader = loader
		self.game = game
		self.sounds = sounds
		self.music_player = music_player
		self.game_over_font = self.loader.load_font('megaman_2.ttf', TITLE_FONT_SIZE)
		self.game_over_time = 0

		self.area = Rect(0, 0, int(SCREEN_W / 2), int(SCREEN_H / 2))

	def update(self, delta):
		self.game_over_time += delta

		if self.game_over_time >= 5:
			self.game.set_mode(MODE_MENU)

	def render(self):
		buffer = self.buffer
		screen = self.screen
		game_over_font = self.game_over_font

		background_color = 0, 0, 0
		default_font_color = 255, 255, 255
		buffer.fill(background_color)

		game_over_text = game_over_font.render('Game Over', 0, default_font_color)
		game_over_rect = game_over_text.get_rect(center=(SCREEN_W/2, SCREEN_H/2))

		buffer.blit(game_over_text, game_over_rect)

		screen.blit(buffer, buffer.get_rect())
		# screen.blit(game_over_text, game_over_rect)

		display.flip()

	def handle_event(self, event):
		pass