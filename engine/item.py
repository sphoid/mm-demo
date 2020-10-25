from pygame import sprite
from .object import *

class Item(sprite.Sprite):
	def __init__(self, spritesheet_loader, sounds, stage):
		super().__init__()
		self.spritesheet_loader = spritesheet_loader
		self.sounds = sounds
		self.position = Vector2(0, 0)
		self.stage = stage

		self.reset_animation = False