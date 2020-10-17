import os, sys, math, pygame, pytmx

class ResourceLoader:
	def __init__(self, config, logger):
		self.config = config
		self.logger = logger

	def load_font(self, filename, size):
		filepath = os.path.join('data', 'fonts', filename)

		try:
			return pygame.font.Font(filepath, size)
		except pygame.error as message:
			self.logger.error('Cannot load font: %s' %(filename))
			raise SystemExit(message)

	def load_map(self, filename):
		filepath = os.path.join('maps', filename)
		return pytmx.util_pygame.load_pygame(filepath)

	def load_image(self, filename, colorkey=None):
		filepath = os.path.join('data', 'images', filename)

		try:
			image = pygame.image.load(filepath)
		except pygame.error as message:
			self.logger.error('Cannot load image: %s' %(filename))
			raise SystemExit(message)

		image = image.convert()

		if colorkey is not None:
			if colorkey == -1:
				colorkey = image.get_at((0, 0))

			image.set_colorkey(colorkey, RLEACCEL)

		return image, image.get_rect()

	def load_sound(self, filename, mixer=None):
		class NoneSound:
			def play(self): pass

		if not pygame.mixer:
			return NoneSound()

		filepath = os.path.join('data', 'sounds', filename)

		try:
			sound = mixer.Sound(filepath) if mixer else pygame.mixer.Sound(filepath)
		except pygame.error as message:
			self.logger.error('Cannot load sound: %s' %(filepath))
			raise SystemExit(message)

		return sound

	def load_song(self, filename):
		filepath = os.path.join('data', 'music', filename)

		try:
			pygame.mixer.music.load(filepath)
		except pygame.error as message:
			self.logger.error('Cannot load song: %s' %(filepath))
			raise SystemExit(message)
