from .constants import *

class Logger:
	def __init__(self, log_level):
		self.log_level = log_level

	def log_message(self, message, level):
		print('%s: %s' % (level, message))

	def debug(self, message):
		if self.log_level == DEBUG:
			self.log_message(message, 'DEBUG')

	def info(self, message):
		if self.log_level <= INFO:
			self.log_message(message, 'INFO')

	def warn(self, message):
		if self.log_level <= WARN:
			self.log_message(message, 'WARN')

	def error(self, message):
		if self.log_level <= ERROR:
			self.log_message(message, 'ERROR')

	def info(self, message):
		if self.log_level <= FATAL:
			self.log_message(message, 'FATAL')
