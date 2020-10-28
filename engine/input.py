import pygame

class InputMethod:
	def is_right(self, event):
		return False

	def is_left(self, event):
		return False

	def is_up(self, event):
		return False

	def is_down(self, event):
		return False

	def is_jump(self, event):
		return False

	def is_shoot(self, event):
		return False

	def is_start(self, event):
		return False

	def is_cancel(self, event):
		return False

	def is_pause(self, event):
		return False

	def is_pressed(self, event):
		return False

class KeyboardInput(InputMethod):
	def is_right(self, event):
		return event.key == pygame.K_RIGHT

	def is_left(self, event):
		return event.key == pygame.K_LEFT

	def is_up(self, event):
		return event.key == pygame.K_UP

	def is_down(self, event):
		return event.key == pygame.K_DOWN

	def is_jump(self, event):
		return event.key == pygame.K_SPACE

	def is_shoot(self, event):
		return event.key == pygame.K_f

	def is_start(self, event):
		return event.key == pygame.K_RETURN

	def is_pause(self, event):
		return event.key == pygame.K_RETURN

	def is_cancel(self, event):
		return event.key == pygame.K_ESCAPE

	def is_pressed(self, event):
		return event.type == pygame.KEYDOWN

	def is_released(self, event):
		return event.type == pygame.KEYUP
