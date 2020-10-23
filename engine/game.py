import pygame
from pygame import sprite, transform, display, draw
from pygame.math import Vector2
from .constants import *
from .sprite import *
from .player import *
from .stage import *
from .hud import *
from .view import *

class Game:
	def __init__(self, config, logger, loader, screen, sounds, music_player, game):
		self.logger = logger
		self.config = config
		self.screen = screen
		self.buffer = pygame.Surface((int(SCREEN_W / SCALE_FACTOR), int(SCREEN_H / SCALE_FACTOR)))
		self.loader = loader
		self.sounds = sounds
		self.music_player = music_player
		self.game = game
		self.spritesheet_loader = SpriteSheetLoader(self.loader)
		self.sprites = sprite.Group()
		self.view = View(int(SCREEN_W / SCALE_FACTOR), int(SCREEN_H / SCALE_FACTOR))

		self.transition_speed = 8
		self.transitioning = False
		self.transition_from_zone = None
		self.transition_to_zone = None
		self.transition_axis = None
		self.zoned = False

		self.debug = self.config.get_debug()

		self.init_stage()
		self.init_player()
		self.init_hud()

	def init_stage(self):
		self.stage = Stage(self.config, self.loader, self.spritesheet_loader, self.sounds)
		self.stage.load()
		self.stage.set_view(self.view)
		self.music_player.play(self.stage.get_music_track())

	def init_player(self):
		self.player = Player(self.spritesheet_loader, self.sounds)
		self.sprites.add(self.player)
		self.player.set_view(self.view)

		if self.debug and self.debug['start_position']:
			pos = self.debug['start_position']
			self.player.set_position(pos[0], pos[1])
		else:
			self.player.warp(self.stage.get_warp_start_position())

	def init_hud(self):
		self.life_meter = LifeMeter(self.spritesheet_loader, self.sounds, self.player)
		self.hud = HudGroup([self.life_meter])

	def check_off_screen(self):
		stage = self.stage
		player = self.player
		zone = stage.get_zone()
		mh = stage.get_map_height()

		if player.get_top() > mh + player.get_height():
			player.die()

	def check_collision(self):
		stage = self.stage
		player = self.player

		if player.is_arriving():
			return

		if player.is_warping():
			lp = stage.get_warp_land_position()
			if player.get_bottom() >= lp.y:
				player.arrive(lp.y)
			return

		colliding_hazards = list(filter((lambda hazard: hazard.collides_with(player.get_rect())), stage.get_hazards()))
		if len(colliding_hazards) > 0:
			p = player.get_position()
			hazard = colliding_hazards[0]
			player.damage(hazard.get_damage())

		colliding_platforms = list(filter((lambda platform: platform.collides_with(player.get_rect())), stage.get_platforms()))
		colliding_ladders = list(filter((lambda ladder: ladder.collides_with(player.get_rect())), stage.get_ladders()))
		v = player.get_velocity()
		if len(colliding_platforms) > 0:
			p = player.get_position()
			for platform in colliding_platforms:
				pleft, pright, ptop, pbottom, pwidth, pheight = platform.get_left(), platform.get_right(), platform.get_top(), platform.get_bottom(), platform.get_width(), platform.get_height()
				left, right, top, bottom = player.get_left(), player.get_right(), player.get_top(), player.get_bottom()

				if v.y > 0 and v.x == 0 and ptop < bottom :
					# print('collide bottom platform')
					player.collide_bottom(ptop)
					# print('new bottom=%d'%player.get_bottom())
				elif v.y < 0 and v.x == 0 and pbottom > top:
					# print('collide top platform')
					player.collide_top(pbottom)
				elif v.x > 0 and v.y == 0 and pleft < right and bottom > ptop:
					# print('collide right platform')
					# if self.debug['map_debug']:
						# platform.flag()
					# print('bottom=%d ptop=%d'%(player.get_bottom(), platform.get_top()))
					player.collide_right(pleft)
				elif v.x < 0 and v.y == 0 and pright > left and bottom > ptop:
					# print('collide left platform')
					player.collide_left(pright)

				elif v.x > 0 and v.y > 0:
					if p.x >= pleft and p.x <= pright and ptop < bottom:
						# print('collide bottom platform while falling right')
						player.collide_bottom(ptop)
						# print('new bottom=%d'%player.get_bottom())
					elif left < pright and p.x > pright:
						# print('collide left platform while falling right')
						player.collide_left(pright)
					elif right > pleft and right < pright:
						# print('collide right platform while falling right')
						player.collide_right(pleft)

				elif v.x > 0 and v.y < 0:
					if p.x >= pleft and p.x <= pright and pbottom > top:
						# print('collide top platform while jumping right')
						player.collide_top(pbottom)
					elif right > pleft and right < pright:
						# print('collide right platform while jumping right')
						player.collide_right(pleft)

				elif v.x < 0 and v.y > 0:
					if p.x >= pleft and p.x <= pright and ptop < bottom:
						# print('collide bottom platform while falling left')
						player.collide_bottom(ptop)
					elif right > pleft and p.x < pleft:
						# print('collide right platform while falling left')
						player.collide_right(pleft)
					elif left < pright and left > pleft:
						# print('collide left platform while falling left')
						player.collide_left(pright)

				elif v.x < 0 and v.y < 0:
					if right >= pleft and left <= pright and pbottom > top:
						# print('collide top platform while jumping left')
						player.collide_top(pbottom)
					elif left < pright and left > pleft:
						# print('collide left platform while jumping left')
						player.collide_left(pright)

		elif not player.is_climbing() and len(colliding_ladders) > 0:
			p = player.get_position()
			for ladder in colliding_ladders:
				if v.y > 0 and ladder.get_top() < player.get_bottom() and (player.get_bottom() - ladder.get_top()) < PLAYER_HALF_HEIGHT:
					player.collide_bottom(ladder.get_top())
		else:
			zone = self.stage.get_zone()
			zpos = zone.get_position()
			zw = zone.get_width()
			view = self.view
			offset = view.get_offset()
			# print('view offset=%d,%d'%(offset.x, offset.y))

			if player.get_left() < zpos.x:
				print('collide zone left boundary')
				player.collide_left(zpos.x)
			elif player.get_right() > (offset.x + zw):
				print('collide zone right boundary px=%d offsetx=%d vw=%d'%(player.get_right(), offset.x, view.get_width()))
				player.collide_right(offset.x + zw)

		if not player.is_damaged():
			colliding_enemies = list(filter((lambda enemy: enemy.collides_with(player.get_rect())), stage.get_enemies().get_enemies()))
			if len(colliding_enemies) > 0:
				enemy = colliding_enemies[0]
				print('enemy hit epos=%d,%d ppos=%d, %d'%(enemy.get_position().x, enemy.get_position().y, player.get_position().x, player.get_position().y))
				player.damage(enemy.get_damage())

		weapon = player.get_weapon()
		enemies = stage.get_enemies().get_enemies()
		weapon.check_hits(enemies)

	def check_climb(self):
		player = self.player

		if not player.is_climbing():
			return

		stage = self.stage
		ladder = stage.ladder_behind(player.get_rect())

		if ladder is None:
			player.fall()
			return

		p = player.get_position()
		if not player.is_climbing_over():
			if player.get_top() <= ladder.get_top() and p.y >= ladder.get_top():
				player.climb_over()
			elif p.y > ladder.get_bottom():
				player.climb_off(ladder.get_bottom() + player.get_height())
			elif p.y < ladder.get_top():
				player.climb_off(ladder.get_top())
		else:
			if p.y < ladder.get_top():
				player.climb_off(ladder.get_top())
			elif player.get_top() > ladder.get_top():
				player.stop_climbing_over()

	def apply_gravity(self):
		player = self.player

		if player.is_climbing():
			return

		if player.is_falling() or player.is_warping():
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

	def transition_zones(self, from_zone, to_zone):
		if not self.transitioning:
			self.transitioning = True
			self.transition_from_zone = from_zone
			self.transition_to_zone = to_zone

			from_p = from_zone.get_position()
			to_p = to_zone.get_position()

			if to_p.y != from_p.y:
				self.transition_axis = 'y'
			else:
				self.transition_axis = 'x'

			print('transition to zone %s axis=%s'%(to_zone.get_name(), self.transition_axis))

	def stop_transition_zones(self):
		self.stage.set_zone(self.transition_to_zone.get_name())
		self.transitioning = False
		self.transition_from_zone = None
		self.transition_to_zone = None
		self.transition_axis = None
		self.zoned = True

	def update_zone(self):
		player = self.player

		if player.is_climbing() or (player.is_falling()):
			zone = self.stage.get_zone()
			in_zone = self.stage.in_zone(self.player)

			if not in_zone or not zone:
				return

			if player.is_falling() and in_zone.get_position().y < zone.get_position().y:
				return

			if zone.get_name() != in_zone.get_name():
				self.transition_zones(zone, in_zone)

	def update_scrolling(self):
		view = self.view
		if self.transitioning:
			s_from = self.transition_from_zone
			from_p = s_from.get_position()
			s_to = self.transition_to_zone
			to_p = s_to.get_position()
			offset = view.get_offset()

			if self.transition_axis == 'y':
				if to_p.y < from_p.y and offset.y > to_p.y:
					view.set_offset(Vector2(offset.x, offset.y - self.transition_speed))
				elif to_p.y > from_p.y and offset.y < to_p.y:
					view.set_offset(Vector2(offset.x, offset.y + self.transition_speed))
				else:
					print('arrived at zone %s'% s_to.get_name())
					print('setting view offset %d,%d'%(offset.x, to_p.y))
					view.set_offset(Vector2(offset.x, to_p.y))
					self.stop_transition_zones()
			elif self.transition_axis == 'x':
				if to_p.x > from_p.x and offset.x < to_p.x:
					view.set_offset(Vector2(offset.x + self.transition_speed, offset.y))
				elif to_p.x < from_p.x and offset.x > to_p.x:
					view.set_offset(Vector2(offset.x - self.transition_speed, offset.y))
				else:
					print('arrived at zone %s'% s_to.get_name())
					print('setting view offset %d,%d'%(to_p.x, offset.y))
					view.set_offset(Vector2(to_p.x, offset.y))
					self.stop_transition_zones()
		else:
			stage, player = self.stage, self.player
			vw, vh = view.get_size()
			zone = stage.get_zone()
			zw, zh = zone.get_size()
			zpos = zone.get_position()

			if vw == zw:
				return

			p = player.get_position()
			right_scroll_threshold = zpos.x + int(vw / 2)
			left_scroll_threshold = (zpos.x + zw) - int(vw / 2)

			if p.x > right_scroll_threshold and p.x < left_scroll_threshold:
				offset_x = zpos.x + p.x - right_scroll_threshold
			elif p.x >= left_scroll_threshold:
				offset_x = zone.get_position().x + zw - vw
			elif p.x <= right_scroll_threshold:
				offset_x = zpos.x

			self.view.set_offset(Vector2(offset_x, view.get_offset().y))

	def update_enemies(self, delta):
		stage, player = self.stage, self.player
		enemies = stage.get_enemies()
		enemies.check_hits(player)
		enemies.spawn_nearby(player, stage.get_zone(), self.zoned)
		self.zoned = False

		enemies.update(delta)

	def update(self, delta):
		player = self.player

		self.check_climb()
		self.apply_gravity()

		buffer = self.buffer
		sprites = self.sprites
		hud = self.hud
		stage = self.stage
		view = self.view

		player.update_position()
		self.update_zone()
		self.update_scrolling()
		self.check_collision()
		self.check_off_screen()

		self.update_enemies(delta)

		player.update_status(delta)

		view.update()

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
		enemies = self.stage.get_enemies()
		hud = self.hud
		view = self.view

		background_color = stage.get_background_color()

		buffer.fill(background_color)

		stage.draw(buffer)
		enemies.draw(buffer)

		if self.debug['player_debug']:
			player = self.player
			prect = player.get_rect()
			offset = view.get_offset()
			pvrect = Rect((prect.left - offset.x, prect.top - offset.y), (player.get_width(), player.get_height()))
			draw.rect(buffer, (0, 255, 0), pvrect)
		else:
			sprites.draw(buffer)

		hud.draw(buffer)

		if SCALE_FACTOR > 1:
			screen.blit(transform.smoothscale(buffer, (SCREEN_W, SCREEN_W)), (0, 0))
		else:
			screen.blit(buffer, (0, 0))

		display.flip()

	def handle_event(self, event):
		player = self.player
		debug = self.logger.debug
		if event.type in (pygame.KEYDOWN, pygame.KEYUP):
			if event.key == pygame.K_RIGHT:
				if event.type == pygame.KEYDOWN:
					# debug('R Down')
					if not player.is_climbing() and not player.is_warping():
						player.move_right()
					elif player.is_climbing():
						player.set_direction(1)
				elif event.type == pygame.KEYUP:
					# debug('R Up')
					if player.get_velocity().x > 0:
						player.stop_x()
			elif event.key == pygame.K_LEFT:
				if event.type == pygame.KEYDOWN:
					# debug('L Down')
					if not player.is_climbing() and not player.is_warping():
						player.move_left()
					elif player.is_climbing():
						player.set_direction(0)
				elif event.type == pygame.KEYUP:
					# debug('L Up')
					if player.get_velocity().x < 0:
						player.stop_x()
			elif event.key == pygame.K_UP:
				if event.type == pygame.KEYDOWN:
					# debug('U Down')
					if not player.is_climbing():
						grabbed = self.grab_ladder_behind(player)
						if grabbed:
							player.climb_up()
					else:
						player.climb_up()
				elif event.type == pygame.KEYUP:
					# debug('U Up')
					if player.is_climbing():
						player.stop_climbing()
			elif event.key == pygame.K_DOWN:
				if event.type == pygame.KEYDOWN:
					# debug('D Down')
					if not player.is_climbing():
						grabbed = self.grab_ladder_below(player)
						if grabbed:
							player.climb_down()
					else:
						player.climb_down()
				elif event.type == pygame.KEYUP:
					# debug('D Up')
					if player.is_climbing():
						player.stop_climbing()
			elif event.key == pygame.K_SPACE and event.type == pygame.KEYDOWN:
				# debug('Space')
				if not player.is_falling():
					player.jump()
			elif event.key == pygame.K_f:
				if event.type == pygame.KEYDOWN:
					# debug('Pew')
					pew = player.shoot()
					self.sprites.add(pew)
				elif event.type == pygame.KEYUP:
					player.stop_shooting()
			elif event.key == pygame.K_ESCAPE:
				self.game.quit()