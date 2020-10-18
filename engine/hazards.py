from .object import *

class Hazards:
	@classmethod
	def load(self, type, rect):
		if type == 'spike':
			return Spike(rect)
		else:
			raise SystemExit('Invalid hazard type %d'%type)

class Hazard(GameObject):
	def __init__(self, rect, damage):
		super().__init__(rect)
		self.damage = damage

	def get_damage(self):
		return self.damage

class Spike(Hazard):
	def __init__(self, rect):
		super().__init__(rect, 999)