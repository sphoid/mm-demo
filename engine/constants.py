from enum import Enum
import pygame

class Direction(Enum):
	N='N'
	NW='NW'
	W='W'
	SW='SW'
	S='S'
	SE='SE'
	E='E'
	NE='NE'

DEBUG = 0
INFO = 2
WARN = 4
ERROR = 8
FATAL = 16

MODE_MENU = 'menu'
MODE_GAME = 'game'
MODE_PAUSE = 'pause'
MODE_GAME_OVER = 'game_over'

TITLE_FONT_SIZE = 16
PROMPT_FONT_SIZE = 12
FPS = 60
BASE_SCREEN_SIZE = 256
SCALE_FACTOR = 3
SCREEN_W = BASE_SCREEN_SIZE * SCALE_FACTOR
SCREEN_H = BASE_SCREEN_SIZE * SCALE_FACTOR
TILE_WIDTH = 16
TILE_HALF_WIDTH = int(TILE_WIDTH / 2)
TILE_HEIGHT = 16
TILE_HALF_HEIGHT = int(TILE_HEIGHT / 2)

PLAYER_WIDTH = 24
PLAYER_HALF_WIDTH = int(PLAYER_WIDTH / 2)
PLAYER_HEIGHT = 24
PLAYER_HALF_HEIGHT = int(PLAYER_HEIGHT / 2)

TERMINAL_VELOCITY = 20
GRAVITY = 9.8

PLAYER_DEFEATED = pygame.USEREVENT + 1