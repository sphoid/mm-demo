from pygame import sprite
from pygame.sprite import Rect
from pygame.math import Vector2
from .object import *
from .entity import *

class GateSprite(Entity):
	def __init__(self, image, view, gate, *position):
		super().__init__(view)
		self.image = image
		self.rect = image.get_rect()
		self.gate = gate
		self.position = Vector2(position[0], position[1])

	def update(self, delta):
		p = self.position

		if p.y >= self.gate.get_bottom():
			self.kill()

		view = self.view
		offset = view.get_offset()
		self.rect.topleft = int(p.x - offset.x), int(p.y - offset.y)

class Gate(GameObject):
	def __init__(self, spritesheet, view, x, y, width, height):
		self.spritesheet = spritesheet

		self.locked = False
		self.opening = False
		self.closing = False

		self.animation_time = 0

		self.view = view
		self.position = Vector2(x, y)
		self.rect = Rect((x, y), (width, height))
		self.max_height = self.rect.height

		self.gate_sprite_group = sprite.Group()

		self.load_sprites()

		super().__init__(self.rect)

	def load_sprites(self):
		image_at = self.spritesheet.image_at

		self.image = image_at(Rect((85, 0), (16, 16)))

		self.fill_sprites()

	def fill_sprites(self):
		xtiles = int(self.rect.width / 16)
		ytiles = int(self.rect.height / 16)
		p = self.position

		for col in range(0, xtiles):
			for row in range(0, ytiles):
				xpos, ypos = p.x + (col * 16), p.y + (row * 16)
				self.gate_sprite_group.add(GateSprite(self.image, self.view, self, xpos, ypos))


	def is_locked(self):
		return self.locked

	def lock(self):
		self.locked = True

	def is_open(self):
		return self.get_height() == 0

	def open(self):
		if not self.opening:
			self.opening = True
			self.animation_time = 0

	def close(self):
		if not self.closing:
			self.closing = True
			self.animation_time = 0

	def update(self, delta):
		if self.opening:
			if self.get_height() == 0:
				self.opening = False
			else:
				self.animation_time += delta
				if self.animation_time > 0.1:
					self.rect.height -= 16
					self.animation_time = 0

		elif self.closing:
			if self.get_height() == self.max_height:
				self.closing = False
			else:
				self.animation_time += delta
				if self.animation_time > 0.1:
					self.rect.height += 16
					self.fill_sprites()
					self.animation_time = 0

		self.gate_sprite_group.update(delta)

	def draw(self, surface):
		self.gate_sprite_group.draw(surface)

class Gates:
	def __init__(self, spritesheet_loader, sounds, view):
		self.spritesheet = spritesheet_loader.load(self.get_spritesheet_filename())
		self.view = view
		self.sounds = sounds
		self.gates = dict()

	def get_spritesheet_filename(self):
		return 'cutman-tiles.png'

	def get_gates(self):
		return self.gates.values()

	def load(self, x, y, width, height):
		gate = Gate(self.spritesheet, self.view, x, y, width, height)
		self.gates[x, y] = gate

	def update(self, delta):
		for gate in self.gates.values():
			gate.update(delta)

	def draw(self, surface):
		for gate in self.gates.values():
			gate.draw(surface)