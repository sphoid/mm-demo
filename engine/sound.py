from pygame import time, mixer

class SoundLibrary:
	def __init__(self, loader, mixer):
		self.loader = loader
		self.sounds = {}
		self.mixer = mixer

	def load(self):
		load_sound = self.loader.load_sound
		self.sounds = dict(
			start=load_sound('start.wav', self.mixer),
			defeat=load_sound('defeat.wav', self.mixer),
			land=load_sound('land.wav', self.mixer),
			pause=load_sound('pause.wav', self.mixer),
			warp=load_sound('warp.wav', self.mixer),
			buster=load_sound('buster.wav', self.mixer),
			damage=load_sound('damage.wav', self.mixer),
			edamage=load_sound('edamage.wav', self.mixer),
			eshoot=load_sound('eshoot.wav', self.mixer),
			dink=load_sound('dink.wav', self.mixer),
			energy=load_sound('energyfill.wav', self.mixer),
			bonus=load_sound('bonusball.wav', self.mixer),
			extralife=load_sound('1up.wav', self.mixer),
		)

	def play_sound(self, sound, blocking=False, end_event=None):
		# print('Playing sound %s'%sound)
		if blocking:
			channel = self.sounds[sound].play()
			while channel.get_busy():
				time.wait(100)
		else:
			channel = self.sounds[sound].play()

		# print(channel)

		if end_event is not None:
			channel.set_endevent(end_event)
			# self.sounds[sound].play()

class MusicPlayer:
	def __init__(self, loader):
		self.loader = loader
		self.songs = {}

	def play(self, song):
		songfile = '%s.mp3'%song
		self.loader.load_song(songfile)
		mixer.music.play(-1)

	def stop(self):
		mixer.music.stop()

	def pause(self):
		mixer.music.pause()

	def unpause(self):
		mixer.music.unpause()
