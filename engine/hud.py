from pygame import sprite, draw
from pygame.sprite import Rect
from .constants import *

class HudGroup(sprite.Group):
	def add(self, *sprites):
		for sprite in sprites:
			if sprite.__class__.__name__ == 'LifeMeter':
				self.life_meter = sprite
			super().add(sprite)

	def draw(self, surface):
		super().draw(surface)
		if hasattr(self, 'life_meter'):
			self.life_meter.draw_damage_mask(surface)

class Score:
	def __init__(self, loader, player):
		self.font = loader.load_font('megaman_2.ttf', SCORE_FONT_SIZE)
		self.player = player
		self.text_color = 255, 255, 255
		self.shadow_color = 0, 0, 0
		self.dshadow_offset = 1 + (SCORE_FONT_SIZE // 15)

	def update(self, delta):
		pass

	def draw(self, surface):
		score = "%07d" % self.player.get_score()
		position = round(BASE_SCREEN_SIZE/2), 10
		dshadow_position = round(BASE_SCREEN_SIZE/2) + self.dshadow_offset, 10 + self.dshadow_offset
		score_text = self.font.render(score, False, self.text_color)
		score_shadow_text = self.font.render(score, False, self.shadow_color)
		score_shadow_rect = score_shadow_text.get_rect(center=dshadow_position)
		score_rect = score_text.get_rect(center=position)

		surface.blit(score_shadow_text, score_shadow_rect)
		surface.blit(score_text, score_rect)

class LifeMeter(sprite.Sprite):
	def __init__(self, spritesheet_loader, sounds, player):
		super().__init__()
		self.spritesheet_loader = spritesheet_loader
		self.player = player
		self.sounds = sounds

		self.load_sprites()

	def get_spritesheet_filename(self):
		return 'energy-sprites-1.5x.png'

	def load_sprites(self):
		self.spritesheet = self.spritesheet_loader.load(self.get_spritesheet_filename())
		image_at = self.spritesheet.image_at

		self.image = image_at(Rect((0, 12), (11, 83)), None, False)
		self.rect = self.image.get_rect(left=10, top=10)
		self.damage_mask_rect = Rect((self.rect.left + 1, self.rect.top), (self.rect.width - 2, 0))

	def draw_damage_mask(self, surface):
		diff = self.player.get_max_hit_points() - self.player.get_hit_points()
		if diff == 0:
			return

		damage_mask_rect = Rect((self.rect.left + 1, self.rect.top), (self.rect.width - 2, diff * 3))

		if damage_mask_rect.height > self.rect.height:
			damage_mask_rect.height = self.rect.height

		draw.rect(surface, (0, 0, 0), damage_mask_rect)

