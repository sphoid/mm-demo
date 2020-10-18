class Animation:
	def __init__(self, frames):
		self.frames = frames
		self.index = 0
		self.next_time = frames[self.index]['duration']

	def reset(self):
		self.index = len(self.frames) - 1
		self.next_time = 0

	def current(self):
		return self.frames[self.index]

	def next(self, last_time):
		if self.index == len(self.frames) - 1:
			self.index = 0
		else:
			self.index += 1

		next_frame = self.frames[self.index]
		self.next_time = next_frame['duration'] + last_time

		if 'callback' in next_frame:
			next_frame['callback']()

		return next_frame