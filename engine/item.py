from pygame import sprite
from .object import *
from .animation import *
from .entity import *

class Item(Entity):
	def __init__(self, spritesheet, view, sounds, *position):
		super().__init__()
		self.spritesheet = spritesheet
		self.sounds = sounds
		self.position = Vector2(position[0], position[1])
		self.view = view
		self.current_time = 0
		self.animation = None

		self.gravity = True

		self.reset_animation = False

		self.load_sprites()

	def load_sprites(self):
		pass

	def use(self, player):
		pass

	def update(self, delta):
		self.update_position(delta)

		self.current_time += delta
		if self.current_time >= self.animation.next_time:
			prev_center = self.rect.center
			self.image = self.animation.next(0)['image']
			self.rect.width = self.image.get_rect().width
			self.rect.center = prev_center
			self.current_time = 0

		p = self.position
		view = self.view
		offset = view.get_offset()
		self.rect.topleft = int(p.x - offset.x), int(p.y - offset.y)

class BigHealth(Item):
	def load_sprites(self):
		image_at = self.spritesheet.image_at

		self.animations = dict(
			default=Animation([
				dict(duration=2, image=image_at(Rect((51, 5), (16, 16)), alpha=True)),
				dict(duration=0.25, image=image_at(Rect((33, 5), (16, 16)), alpha=True))
			])
		)

		self.animation = self.animations['default']
		start_frame = self.animations['default'].current()
		self.image = start_frame['image']
		self.rect = self.image.get_rect()

	def use(self, player):
		player.heal(14)
		self.kill()

class SmallHealth(Item):
	def load_sprites(self):
		image_at = self.spritesheet.image_at

		self.animations = dict(
			default=Animation([
				dict(duration=2, image=image_at(Rect((2, 5), (16, 16)), alpha=True)),
			])
		)

		self.animation = self.animations['default']
		start_frame = self.animations['default'].current()
		self.image = start_frame['image']
		self.rect = self.image.get_rect()

	def use(self, player):
		player.heal(6)
		self.kill()

class BonusPoint(Item):
	def use(self, player):
		player.add_bonus_points(1)
		self.kill()

class RedBonusPoint(BonusPoint):
	def load_sprites(self):
		image_at = self.spritesheet.image_at

		self.animations = dict(
			default=Animation([
				dict(duration=2, image=image_at(Rect((5, 35), (8, 8)), alpha=True)),
			])
		)

		self.animation = self.animations['default']
		start_frame = self.animations['default'].current()
		self.image = start_frame['image']
		self.rect = self.image.get_rect()


class BlueBonusPoint(BonusPoint):
	def load_sprites(self):
		image_at = self.spritesheet.image_at

		self.animations = dict(
			default=Animation([
				dict(duration=2, image=image_at(Rect((17, 35), (8, 8)), alpha=True)),
			])
		)

		self.animation = self.animations['default']
		start_frame = self.animations['default'].current()
		self.image = start_frame['image']
		self.rect = self.image.get_rect()

class GreenBonusPoint(BonusPoint):
	def load_sprites(self):
		image_at = self.spritesheet.image_at

		self.animations = dict(
			default=Animation([
				dict(duration=2, image=image_at(Rect((29, 35), (8, 8)), alpha=True)),
			])
		)

		self.animation = self.animations['default']
		start_frame = self.animations['default'].current()
		self.image = start_frame['image']
		self.rect = self.image.get_rect()

class OrangeBonusPoint(BonusPoint):
	def load_sprites(self):
		image_at = self.spritesheet.image_at

		self.animations = dict(
			default=Animation([
				dict(duration=2, image=image_at(Rect((41, 35), (8, 8)), alpha=True)),
			])
		)

		self.animation = self.animations['default']
		start_frame = self.animations['default'].current()
		self.image = start_frame['image']
		self.rect = self.image.get_rect()


class ExtraLife(Item):
	def load_sprites(self):
		image_at = self.spritesheet.image_at

		self.animations = dict(
			default=Animation([
				dict(duration=2, image=image_at(Rect((193, 26), (16, 16)), alpha=True)),
			])
		)

		self.animation = self.animations['default']
		start_frame = self.animations['default'].current()
		self.image = start_frame['image']
		self.rect = self.image.get_rect()

	def use(self, player):
		player.add_life()
		self.kill()

ITEM_CLASS=dict(
	bighealth = BigHealth,
	smallhealth = SmallHealth,
	redbonus = RedBonusPoint,
	bluebonus = BlueBonusPoint,
	greenbonus = GreenBonusPoint,
	orangebonus = OrangeBonusPoint,
	extralife = ExtraLife,
)

class Items:
	def __init__(self, spritesheet_loader, sounds, view):
		self.spritesheet = spritesheet_loader.load(self.get_spritesheet_filename())
		self.view = view
		self.sounds = sounds
		self.items = dict()
		self.item_sprite_group = sprite.Group()

	def get_spritesheet_filename(self):
		return 'items.png'

	def get_items(self):
		return self.item_sprite_group

	def load(self, type, *position):
		if type in ITEM_CLASS:
			item_class = ITEM_CLASS[type]
		else:
			print('ERROR: Unknown item type %s'%type)
			return None

		x, y = position
		item = item_class(self.spritesheet, self.view, self.sounds, x, y)
		self.items[x, y] = item
		self.item_sprite_group.add(item)

	def update(self, delta):
		self.item_sprite_group.update(delta)

	def draw(self, surface):
		self.item_sprite_group.draw(surface)