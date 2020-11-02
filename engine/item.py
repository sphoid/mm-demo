from pygame import sprite
from .object import *
from .animation import *
from .entity import *

class Item(Entity):
	def __init__(self, spritesheet, view, sounds, *position):
		self.sounds = sounds

		super().__init__(spritesheet=spritesheet, view=view, position=(position[0], position[1]), gravity=True)

	def use(self, player):
		pass

class BigHealth(Item):
	def get_animation_states(self):
		return dict(
			states=dict(
				default = [
					dict(at=(51, 5), size=(16, 16), duration=2, alpha=True),
					dict(at=(33, 5), size=(16, 16), duration=0.25, alpha=True),
				],
			),
			default = 'default'
		)

	def use(self, player):
		player.heal(14)
		self.kill()

class SmallHealth(Item):
	def get_animation_states(self):
		return dict(
			states=dict(
				default = [
					dict(at=(2, 5), size=(16, 16), duration=2, alpha=True),
				],
			),
			default = 'default'
		)

	def use(self, player):
		player.heal(6)
		self.kill()

class BonusPoint(Item):
	def use(self, player):
		player.add_bonus_points(1)
		self.kill()

class RedBonusPoint(BonusPoint):
	def get_animation_states(self):
		return dict(
			states=dict(
				default = [
					dict(at=(5, 35), size=(8, 8), duration=2, alpha=True),
				],
			),
			default = 'default'
		)

class BlueBonusPoint(BonusPoint):
	def get_animation_states(self):
		return dict(
			states=dict(
				default = [
					dict(at=(17, 35), size=(8, 8), duration=2, alpha=True),
				],
			),
			default = 'default'
		)

class GreenBonusPoint(BonusPoint):
	def get_animation_states(self):
		return dict(
			states=dict(
				default = [
					dict(at=(29, 35), size=(8, 8), duration=2, alpha=True),
				],
			),
			default = 'default'
		)

class OrangeBonusPoint(BonusPoint):
	def get_animation_states(self):
		return dict(
			states=dict(
				default = [
					dict(at=(41, 35), size=(8, 8), duration=2, alpha=True),
				],
			),
			default = 'default'
		)

class ExtraLife(Item):
	def get_animation_states(self):
		return dict(
			states=dict(
				default = [
					dict(at=(193, 26), size=(16, 16), duration=2, alpha=True),
				],
			),
			default = 'default'
		)

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