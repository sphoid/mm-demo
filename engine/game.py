import pygame
from pygame import sprite, transform, display, draw
from .constants import *
from .sprite import *
from .player import *
from .stage import *
from .hud import *

class Game:
	def __init__(self, logger, loader, screen, buffer, sounds, music_player, game, **opts):
		self.logger = logger
		self.screen = screen
		# self.buffer = buffer
		self.buffer = pygame.Surface((int(SCREEN_W/2), int(SCREEN_H/2)))
		self.loader = loader
		self.sounds = sounds
		self.music_player = music_player
		self.game = game
		self.spritesheet_loader = SpriteSheetLoader(self.loader)
		self.sprites = sprite.Group()
		self.area = Rect(0, 0, int(SCREEN_W / 2), int(SCREEN_H / 2))

		if hasattr(opts, 'player_debug'):
			self.player_debug = opts['player_debug']
		else:
			self.player_debug = False

		if hasattr(opts, 'map_debug'):
			self.map_debug = opts['map_debug']
		else:
			self.map_debug = False

		self.init_player()
		self.init_stage()
		self.init_hud()

	def init_player(self):
		self.player = Player(self.spritesheet_loader, self.sounds)
		self.sprites.add(self.player)

	def init_stage(self):
		self.stage = Stage(self.loader, self.spritesheet_loader, self.sounds, map_debug=self.map_debug)
		self.stage.load()

		self.player.set_stage(self.stage)

		self.music_player.play('bombman-stage')

	def init_hud(self):
		self.life_meter = LifeMeter(self.spritesheet_loader, self.sounds, self.player)
		self.hud = HudGroup([self.life_meter])

	def check_collision(self, player):
		stage = self.stage
		colliding_platforms = list(filter((lambda platform: platform.collides_with(player.get_rect())), stage.platforms.values()))
		colliding_ladders = list(filter((lambda ladder: ladder.collides_with(player.get_rect())), stage.ladders.values()))
		v = player.get_velocity()
		if len(colliding_platforms) > 0:
			p = player.get_position()
			for platform in colliding_platforms:
				pleft, pright, ptop, pbottom, pwidth, pheight = platform.get_left(), platform.get_right(), platform.get_top(), platform.get_bottom(), platform.get_width(), platform.get_height()
				left, right, top, bottom = player.get_left(), player.get_right(), player.get_top(), player.get_bottom()

				if v.x > 0 and v.y == 0 and pleft < right:
					player.collide_right(pleft)
				elif v.x < 0 and v.y == 0 and pright > left:
					player.collide_left(pright)
				elif v.y > 0 and v.x == 0 and ptop < bottom :
					player.collide_bottom(ptop)
				elif v.y < 0 and v.x == 0 and pbottom > top:
					player.collide_top(pbottom)
				elif v.x > 0 and v.y > 0:
					if p.x >= pleft and p.x <= pright and ptop < bottom:
						player.collide_bottom(ptop)
					elif right > pleft and right < pright:
						player.collide_right(pleft)
				elif v.x > 0 and v.y < 0:
					if p.x >= pleft and p.x <= pright and pbottom > top:
						player.collide_top(pbottom)
					elif right > pleft and right < pright:
						player.collide_right(pleft)
				elif v.x < 0 and v.y > 0:
					if p.x >= pleft and p.x <= pright and ptop < bottom:
						player.collide_bottom(ptop)
					elif left < pright and left > pleft:
						player.collide_left(pright)
				elif v.x < 0 and v.y < 0:
					if p.x >= pleft and p.x <= pright and pbottom > top:
						player.collide_top(pbottom)
					elif left < pright and left > pleft:
						player.collide_left(pright)
		elif not player.is_climbing() and len(colliding_ladders) > 0:
			p = player.get_position()
			for ladder in colliding_ladders:
				if v.y > 0 and ladder.get_top() < player.get_bottom() and (player.get_bottom() - ladder.get_top()) < PLAYER_HALF_HEIGHT:
					player.collide_bottom(ladder.get_top())
		else:
			mw, mh = stage.get_map_size()

			if player.get_left() < 0:
				player.collide_left(0)
			elif player.get_right() > mw:
				player.collide_right(mw)

		if not player.is_damaged():
			colliding_enemies = list(filter((lambda enemy: enemy.collides_with(player.get_rect())), stage.enemy_sprite_group))
			if len(colliding_enemies) > 0:
				enemy = colliding_enemies[0]
				print('enemy hit epos=%d,%d ppos=%d, %d'%(enemy.get_position().x, enemy.get_position().y, player.get_position().x, player.get_position().y))
				player.damage(enemy.get_damage())

		weapon = player.get_weapon()
		weapon.check_hits(stage.enemy_sprite_group)

	def check_climb(self):
		player = self.player

		if not player.is_climbing():
			return

		stage = self.stage
		ladder = stage.ladder_behind(player.get_rect())

		if not player.is_climbing_over():
			if player.get_top() <= ladder.get_top() and player.get_position().y >= ladder.get_top():
				player.climb_over()
			elif player.get_position().y < ladder.get_top():
				player.climb_off(ladder.get_top())
		else:
			if player.get_position().y < ladder.get_top():
				player.climb_off(ladder.get_top())
			elif player.get_top() > ladder.get_top():
				player.stop_climbing_over()

	def apply_gravity(self):
		player = self.player

		if player.is_climbing():
			return

		if player.is_falling():
			v = player.get_velocity()
			if v.y == 0:
				player.accelerate(0, 1)
			elif v.y < TERMINAL_VELOCITY:
				player.accelerate(0, 0.5)
			else:
				player.set_velocity_y(TERMINAL_VELOCITY)
		else:
			stage = self.stage
			prect = player.get_rect()
			platform_below = stage.platform_below(prect)
			ladder_behind = stage.ladder_behind(prect)
			ladder_below = stage.ladder_below(prect)

			if not platform_below and not ladder_below and not ladder_behind:
				player.fall()

	def grab_ladder_behind(self, player):
		stage = self.stage
		prect = player.get_rect()
		ladder = stage.ladder_behind(prect)
		if ladder:
			print('Grabbing ladder behind')
			player.grab_ladder(ladder)
			return True

		return False

	def grab_ladder_below(self, player):
		stage = self.stage
		prect = player.get_rect()
		ladder = stage.ladder_below(prect)
		if ladder:
			print('Grabbing ladder below')
			player.grab_ladder(ladder, True)
			return True

		return False

	def update(self, delta):
		player = self.player

		self.check_climb()
		self.apply_gravity()

		buffer = self.buffer
		sprites = self.sprites
		hud = self.hud
		stage = self.stage
		area = self.area

		player.update_position()
		stage.update_scroll_offset(player.get_position())
		self.check_collision(player)
		stage.update_enemies(player)

		player.update_status(delta)

		sprites.update(delta)
		stage.update(delta)
		hud.update(delta)

		if self.player.is_dead():
			self.music_player.stop()
			self.sounds.play_sound('defeat', True)
			self.game.set_mode(MODE_GAME_OVER)

	def render(self):
		buffer = self.buffer
		sprites = self.sprites
		screen = self.screen
		stage = self.stage
		hud = self.hud

		background_color = stage.get_background_color()

		buffer.fill(background_color)

		stage.draw(buffer)
		sprites.draw(buffer)
		hud.draw(buffer)

		if self.player_debug:
			draw.rect(buffer, (0, 255, 0), player.rect)

		screen.blit(transform.scale2x(buffer), (0, 0))

		display.flip()

	def handle_event(self, event):
		player = self.player
		debug = self.logger.debug
		if event.type in (pygame.KEYDOWN, pygame.KEYUP):
			if event.key == pygame.K_RIGHT:
				if event.type == pygame.KEYDOWN:
					debug('R Down')
					if not player.is_climbing() and not player.is_warping():
						player.move_right()
					elif player.is_climbing():
						player.set_direction(1)
				elif event.type == pygame.KEYUP:
					debug('R Up')
					player.stop_x()
			elif event.key == pygame.K_LEFT:
				if event.type == pygame.KEYDOWN:
					debug('L Down')
					if not player.is_climbing() and not player.is_warping():
						player.move_left()
					elif player.is_climbing():
						player.set_direction(0)
				elif event.type == pygame.KEYUP:
					debug('L Up')
					player.stop_x()
			elif event.key == pygame.K_UP:
				if event.type == pygame.KEYDOWN:
					debug('U Down')
					if not player.is_climbing():
						grabbed = self.grab_ladder_behind(player)
						if grabbed:
							player.climb_up()
					else:
						player.climb_up()
				elif event.type == pygame.KEYUP:
					debug('U Up')
					if player.is_climbing():
						player.stop_climbing()
			elif event.key == pygame.K_DOWN:
				if event.type == pygame.KEYDOWN:
					debug('D Down')
					if not player.is_climbing():
						grabbed = self.grab_ladder_below(player)
						if grabbed:
							player.climb_down()
					else:
						player.climb_down()
				elif event.type == pygame.KEYUP:
					debug('D Up')
					if player.is_climbing():
						player.stop_climbing()
			elif event.key == pygame.K_SPACE and event.type == pygame.KEYDOWN:
				debug('Space')
				if not player.is_falling():
					player.jump()
			elif event.key == pygame.K_f:
				if event.type == pygame.KEYDOWN:
					debug('Pew')
					pew = player.shoot()
					self.sprites.add(pew)
				elif event.type == pygame.KEYUP:
					player.stop_shooting()
			elif event.key == pygame.K_ESCAPE:
				self.game.quit()