from pygame import Surface, transform, RLEACCEL, SRCALPHA, sprite

class SpriteSheet:
	def __init__(self, image, rect):
		self.image = image
		self.rect = rect

	def image_at(self, rect, colorkey=None, scale2x=False, flip=False, alpha=False):
		if alpha:
			image = Surface(rect.size, SRCALPHA)
			image.blit(self.image, (0, 0), rect)
		else:
			image = Surface(rect.size).convert()
			image.blit(self.image, (0, 0), rect)
			if colorkey is not None:
				if colorkey == -1:
					colorkey = image.get_at((0,0))
				image.set_colorkey(colorkey, RLEACCEL)

		if flip == 'x':
			image = transform.flip(image, True, False)
		elif flip == 'y':
			image = transform.flip(image, False, True)

		if scale2x:
			image = transform.scale2x(image)

		return image

	def images_at(self, rects, colorkey=None, scale2x=False, flip=False, alpha=False):
		return [self.image_at(rect, colorkey=colorkey, scale2x=scale2x, flip=flip, alpha=alpha) for rect in rects]


class SpriteSheetLoader:
	def __init__(self, loader):
		self.loader = loader

	def load(self, filename):
		image, rect = self.loader.load_image(filename)
		return SpriteSheet(image, rect)

# class Sprite(sprite.Sprite):
# 	def get_spritesheet_filename(self):
# 		pass

# 	def load_sprites(self):
# 		pass