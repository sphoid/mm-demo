from pygame import sprite, math
from pygame.sprite import Rect
from .constants import *

class BusterPellet(sprite.Sprite):
	def __init__(self, image, view, direction, *position):
		super().__init__()
		self.image = image
		self.rect = image.get_rect()
		self.position = math.Vector2(position[0], position[1])
		self.direction = direction
		self.speed = 10
		self.damage = 1
		self.view = view

	def get_rect(self):
		return Rect((self.get_left(), self.get_top()), (self.get_width(), self.get_height()))

	def get_width(self):
		return self.rect.width

	def get_height(self):
		return self.rect.height

	def get_position(self):
		return self.position

	def get_bottom(self):
		return int(self.position.y + int(self.rect.height / 2))

	def get_top(self):
		return int(self.position.y - int(self.rect.height / 2))

	def get_left(self):
		return int(self.position.x - int(self.rect.width / 2))

	def get_right(self):
		return int(self.position.x + int(self.rect.width / 2))

	def get_damage(self):
		return self.damage

	def update_position(self):
		if self.direction == 1:
			self.position.x += self.speed
		else:
			self.position.x -= self.speed

	def update(self, delta):
		offset = self.view.get_offset()
		self.rect.center = int(self.position.x - offset.x), int(self.position.y - offset.y)

class Weapon:
	def __init__(self, spritesheet_loader, sounds, player):
		super().__init__()
		self.spritesheet_loader = spritesheet_loader
		self.pew_sprite_group = sprite.Group()
		self.area = Rect(0, 0, int(SCREEN_W / 2), int(SCREEN_H / 2))
		self.sounds = sounds
		self.player = player

		self.load_sprites()

	def load_sprites(self):
		self.spritesheet = self.spritesheet_loader.load(self.get_spritesheet_filename())
		image_at = self.spritesheet.image_at

		self.pellet_image = image_at(Rect((0, 0), (14, 10)), -1)

	def get_spritesheet_filename(self):
		return 'weapon-sprites.png'

	def shoot(self):
		player = self.player
		view = player.get_view()
		start_pos_x = player.get_right() if player.get_direction() else player.get_left()
		start_pos_y = player.get_top() + int(player.get_height() / 3)
		pellet = BusterPellet(self.pellet_image, view, player.get_direction(), start_pos_x, start_pos_y)
		self.pew_sprite_group.add(pellet)

		self.sounds.play_sound('buster')

		return pellet

	def check_hits(self, enemy_sprite_group):
		if len(self.pew_sprite_group) > 0:
			for pew in self.pew_sprite_group:
				for enemy in enemy_sprite_group:
					hit = enemy.collides_with(pew.get_rect())
					if hit:
						enemy.hit(pew)
						pew.kill()

	def update(self, delta):
		for pew in self.pew_sprite_group:
			pew.update_position()
			p = pew.get_position()
			view = self.player.get_view()
			offset = view.get_offset()

			if p.x - offset.x > view.get_width() or p.x < offset.x:
				pew.kill()

		self.pew_sprite_group.update(delta)
