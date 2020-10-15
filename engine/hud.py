from pygame import sprite, draw
from pygame.sprite import Rect

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

class LifeMeter(sprite.Sprite):
	def __init__(self, spritesheet_loader, sounds, player):
		super().__init__()
		self.spritesheet_loader = spritesheet_loader
		self.player = player
		self.sounds = sounds

		self.load_sprites()

	def get_spritesheet_filename(self):
		return 'energy-sprites.png'

	def load_sprites(self):
		self.spritesheet = self.spritesheet_loader.load(self.get_spritesheet_filename())
		image_at = self.spritesheet.image_at

		self.image = image_at(Rect((0, 8), (8, 56)), None, True)
		self.rect = self.image.get_rect(left=10, top=10)
		self.damage_mask_rect = Rect((self.rect.left + 1, self.rect.top), (self.rect.width - 2, 0))

	def draw_damage_mask(self, surface):
		diff = self.player.get_max_hit_points() - self.player.get_hit_points()
		damage_mask_rect = Rect((self.rect.left + 1, self.rect.top), (self.rect.width - 2, diff * 4))

		draw.rect(surface, (0, 0, 0), damage_mask_rect)

