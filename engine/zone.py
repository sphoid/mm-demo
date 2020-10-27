from .object import *
from .util import *

class Zone(GameObject):
	def __init__(self, rect, name, **attributes):
		if 'background' in attributes:
			attributes['background'] = hex_to_rgb(attributes['background'])

		super().__init__(rect, name=name, attributes=attributes)

		print('zone attributes %r'%self.attributes)


	def get_background_color(self):
		return self.attributes['background'] if 'background' in self.attributes else None
