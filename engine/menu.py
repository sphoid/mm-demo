import pygame
from pygame import display
from pygame.sprite import Rect
from .constants import *

class Menu:
	def __init__(self, logger, loader, screen, buffer, sounds, music_player, game, **opts):
		self.logger = logger
		self.screen = screen
		self.buffer = buffer
		self.loader = loader
		self.game = game
		self.sounds = sounds
		self.music_player = music_player
		self.title_font = self.loader.load_font('megaman_2.ttf', TITLE_FONT_SIZE)
		self.prompt_font = self.loader.load_font('megaman_2.ttf', PROMPT_FONT_SIZE)
		self.title = 'Game Demo'
		self.menu_time = 0
		self.prompt_blinking = False
		self.area = Rect(0, 0, int(SCREEN_W / 2), int(SCREEN_H / 2))

	def update(self, delta):
		self.menu_time += delta

	def render(self):
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

		display.flip()

	def handle_event(self, event):
		if event.type in (pygame.KEYDOWN, pygame.KEYUP):
			if event.key == pygame.K_RETURN:
				self.sounds.play_sound('start', True)
				self.game.set_mode(MODE_GAME)
			elif event.key == pygame.K_ESCAPE:
				self.game.quit()