from pygame.math import Vector2
import math

def hex_to_rgb(value):
	value = value.lstrip('#')
	if len(value) == 8:
		value = value[2:]

	lv = len(value)

	return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

def calculate_velocity(speed, angle):
	radians = math.radians(angle)
	vx = speed * math.cos(radians)
	vy = speed * math.sin(radians)

	return Vector2(vx, vy)

