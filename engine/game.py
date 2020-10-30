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
	def __init__(self, config, logger, input, loader, screen, sounds, music_player, game):
		self.logger = logger
		self.config = config
		self.screen = screen
		self.input = input
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
		self.player_dead = False
		self.entering_gate = None

		self.player = None
		self.ladders = None
		self.items = None
		self.platforms = None
		self.hazards = None
		self.gates = None
		self.enemies = None
		self.warp_start_position = None
		self.warp_land_position = None
		self.explosions = Explosions(self.spritesheet_loader)

		self.debug = self.config.get_debug()

		self.init_stage()
		self.init_player()
		self.init_hud()

	def init_stage(self):
		self.stage = Stage(self.config, self.loader, self.spritesheet_loader, self.view, self.sounds, self.explosions)

		self.platforms = self.stage.get_platforms()
		self.ladders = self.stage.get_ladders()
		self.hazards = self.stage.get_hazards()
		self.items = self.stage.get_items()
		self.gates = self.stage.get_gates()
		self.enemies = self.stage.get_enemies()
		self.warp_start_position = self.stage.get_warp_start_position()
		self.warp_land_position = self.stage.get_warp_land_position()

		self.music_player.play(self.stage.get_music_track())

	def init_player(self):
		self.player = Player(self.spritesheet_loader, self.view, self.sounds, self.explosions, self.debug)
		self.score = Score(self.loader, self.player)
		self.sprites.add(self.player)

		if self.debug and self.debug['start_position']:
			pos = self.debug['start_position']
			self.player.set_position(pos[0], pos[1])
		else:
			self.player.warp(self.warp_start_position)

	def init_hud(self):
		self.life_meter = LifeMeter(self.spritesheet_loader, self.sounds, self.player)
		self.score = Score(self.loader, self.player)
		self.hud = HudGroup([self.life_meter])

	def check_collision(self, entity, recursion=False):
		collided = False
		colliding_platforms = list(filter((lambda platform: platform.collides_with(entity.get_rect())), self.platforms))
		colliding_ladders = list(filter((lambda ladder: ladder.collides_with(entity.get_rect())), self.ladders))

		v = entity.get_velocity()
		p = entity.get_position()
		if len(colliding_platforms) > 0:
			for platform in colliding_platforms:
				pleft, pright, ptop, pbottom, pwidth, pheight = platform.get_left(), platform.get_right(), platform.get_top(), platform.get_bottom(), platform.get_width(), platform.get_height()
				left, right, top, bottom = entity.get_left(), entity.get_right(), entity.get_top(), entity.get_bottom()

				if p.y < ptop and bottom > ptop and ptop - bottom < TILE_HEIGHT:
					entity.collide_bottom(ptop)
					platform.flag()
					if not recursion:
						self.check_collision(entity, True)
					collided = True
				elif p.y > pbottom and top < pbottom and pbottom - top < TILE_HEIGHT:
					entity.collide_top(pbottom)
					platform.flag()
					if not recursion:
						self.check_collision(entity, True)
					collided = True
				elif left < pright and pright - left < TILE_WIDTH:
					entity.collide_left(pright)
					platform.flag()
					if not recursion:
						self.check_collision(entity, True)
					collided = True
				elif right > pleft and right - pleft < TILE_WIDTH:
					entity.collide_right(pleft)
					platform.flag()
					if not recursion:
						self.check_collision(entity, True)
					collided = True
		elif entity.is_gravity_enabled() and len(colliding_ladders) > 0:
			for ladder in colliding_ladders:
				if v.y > 0 and ladder.get_top() < entity.get_bottom() and (entity.get_bottom() - ladder.get_top()) < PLAYER_HALF_HEIGHT:
					entity.collide_bottom(ladder.get_top())
					collided = True

		return collided

	def check_player_collision(self):
		player = self.player
		stage = self.stage

		if player.is_arriving():
			return

		if player.is_warping():
			lp = self.warp_land_position
			if player.get_bottom() >= lp.y:
				player.arrive(lp.y)
			return

		colliding_hazards = list(filter((lambda hazard: hazard.collides_with(player.get_rect())), self.hazards))
		if len(colliding_hazards) > 0:
			p = player.get_position()
			hazard = colliding_hazards[0]
			player.damage(hazard.get_damage())

		colliding_gates = list(filter((lambda gate: gate.collides_with(player.get_rect())), self.gates.get_gates()))
		if len(colliding_gates) > 0:
			gate = colliding_gates[0]
			if not gate.is_locked():
				print("Opening gate")
				player.immobilize()
				self.entering_gate = gate
				gate.open()
			else:
				p = player.get_position()
				gp = gate.get_position()
				if p.x < gp.x:
					player.collide_right(gate.get_left())
				elif p.x > gp.x:
					player.collide_left(gate.get_right())
			collided = True

		collided = self.check_collision(player)

		if not collided:
			zone = self.stage.get_zone()
			zpos = zone.get_position()
			zw = zone.get_width()
			view = self.view
			offset = view.get_offset()

			if player.get_left() < zpos.x:
				player.collide_left(zpos.x)
			elif player.get_right() > (offset.x + zw):
				player.collide_right(offset.x + zw)

		if not player.is_damaged() and not player.is_invincible():
			colliding_enemies = list(filter((lambda enemy: enemy.collides_with(player.get_rect())), self.enemies.get_enemies()))
			if len(colliding_enemies) > 0:
				enemy = colliding_enemies[0]
				player.damage(enemy.get_damage())

		collided_items = list(filter((lambda item: item.collides_with(player.get_rect())), self.items.get_items()))
		for item in collided_items:
			item.use(player)

	def check_player_off_map(self):
		stage = self.stage
		player = self.player
		zone = stage.get_zone()
		mh = stage.get_map_height()

		if player.get_top() > mh + player.get_height():
			player.die()

	def check_player_climb(self):
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

	def check_weapon_hits(self):
		weapon = self.player.get_weapon()
		enemies = self.enemies.get_enemies()
		weapon.check_hits(enemies)

	def apply_gravity(self, entity):
		if not entity.is_gravity_enabled():
			return

		if entity.is_falling():
			v = entity.get_velocity()
			if v.y == 0:
				entity.accelerate(0, 1)
			elif v.y < TERMINAL_VELOCITY:
				entity.accelerate(0, 0.5)
			else:
				entity.set_velocity_y(TERMINAL_VELOCITY)
		else:
			stage = self.stage
			prect = entity.get_rect()
			platform_below = stage.platform_below(prect)
			ladder_behind = stage.ladder_behind(prect)
			ladder_below = stage.ladder_below(prect)

			if not platform_below and not ladder_below and not ladder_behind:
				entity.fall()

	def grab_ladder_behind(self, player):
		stage = self.stage
		prect = player.get_rect()
		ladder = stage.ladder_behind(prect)
		if ladder:
			player.grab_ladder(ladder)
			return True

		return False

	def grab_ladder_below(self, player):
		stage = self.stage
		prect = player.get_rect()
		ladder = stage.ladder_below(prect)
		if ladder:
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

	def stop_transition_zones(self):
		self.stage.set_zone(self.transition_to_zone.get_name())
		self.transitioning = False
		self.transition_from_zone = None
		self.transition_to_zone = None
		self.transition_axis = None
		self.zoned = True

	def update_zone(self):
		player = self.player
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
					view.set_offset(Vector2(offset.x, to_p.y))
					self.stop_transition_zones()
			elif self.transition_axis == 'x':
				if to_p.x > from_p.x and offset.x < to_p.x:
					view.set_offset(Vector2(offset.x + self.transition_speed, offset.y))
				elif to_p.x < from_p.x and offset.x > to_p.x:
					view.set_offset(Vector2(offset.x - self.transition_speed, offset.y))
				else:
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
		enemies = self.enemies

		for enemy in enemies.get_enemies():
			self.apply_gravity(enemy)
			if not enemy.is_clip_enabled():
				self.check_collision(enemy)

		enemies.check_hits(player)
		enemies.spawn_nearby(player, stage.get_zone(), self.zoned)
		self.zoned = False

		enemies.update(delta)

	def update_items(self, delta):
		for item in self.items.get_items():
			self.apply_gravity(item)
			if not item.is_clip_enabled():
				self.check_collision(item)

		self.items.update(delta)

	def update_gates(self, delta):
		self.gates.update(delta)

	def update_player(self, delta):
		player = self.player

		if self.entering_gate is not None:
			gate = self.entering_gate
			if gate.is_open():
				p = player.get_position()
				v = player.get_velocity()
				if p.x < gate.get_right() and v.x == 0:
					player.set_velocity(1, 0)
				elif player.get_left() > gate.get_right() + (player.get_width() / 2):
					print('Releasing player and locking gate')
					self.entering_gate = None
					player.stop_x()
					player.mobilize()
					gate.close()
					gate.lock()

		else:
			self.check_player_climb()
			self.apply_gravity(player)
			self.check_player_collision()
			self.check_player_off_map()

	def update(self, delta):
		player = self.player
		view = self.view
		buffer = self.buffer
		sprites = self.sprites
		hud = self.hud
		stage = self.stage
		explosions = self.explosions

		if player.is_dead():
			if not self.player_dead:
				self.player_dead = True
				self.explosions.big_explode(view, player.get_position())
				self.music_player.stop()
				self.sounds.play_sound('defeat', False, PLAYER_DEFEATED)
		else:
			self.update_player(delta)
			self.update_enemies(delta)
			self.update_items(delta)
			self.update_gates(delta)
			self.check_weapon_hits()

			self.update_zone()
			self.update_scrolling()

			view.update()

		sprites.update(delta)
		stage.update(delta)
		hud.update(delta)
		explosions.update(delta)

	def render(self):
		buffer = self.buffer
		sprites = self.sprites
		screen = self.screen
		stage = self.stage
		zone = stage.get_zone()
		hud = self.hud
		view = self.view

		background_color = zone.get_background_color()
		if background_color is None:
			background_color = stage.get_background_color()

		buffer.fill(background_color)

		stage.draw(buffer)
		self.enemies.draw(buffer)
		self.items.draw(buffer)
		self.gates.draw(buffer)

		if self.debug['player_debug']:
			player = self.player
			prect = player.get_rect()
			offset = view.get_offset()
			pvrect = Rect((prect.left - offset.x, prect.top - offset.y), (player.get_width(), player.get_height()))
			draw.rect(buffer, (0, 255, 0), pvrect)
		else:
			sprites.draw(buffer)

		self.score.draw(buffer)
		hud.draw(buffer)

		self.explosions.draw(buffer)

		if SCALE_FACTOR > 1:
			screen.blit(transform.smoothscale(buffer, (SCREEN_W, SCREEN_W)), (0, 0))
		else:
			screen.blit(buffer, (0, 0))

		display.flip()

	# Player Events

	def player_start_right(self):
		player = self.player
		if not player.is_climbing() and player.is_moveable():
			player.move_right()
		elif player.is_climbing():
			player.set_direction_right()

	def player_stop_right(self):
		player = self.player
		if player.get_velocity().x > 0:
			player.stop_x()

	def player_start_left(self):
		player = self.player
		if not player.is_climbing() and player.is_moveable():
			player.move_left()
		elif player.is_climbing():
			player.set_direction(0)

	def player_stop_left(self):
		player = self.player
		if player.get_velocity().x < 0:
			player.stop_x()

	def player_start_up(self):
		player = self.player
		if not player.is_climbing():
			grabbed = self.grab_ladder_behind(player)
			if grabbed:
				player.climb_up()
		else:
			player.climb_up()

	def player_stop_up(self):
		player = self.player
		if player.is_climbing():
			player.stop_climbing()

	def player_start_down(self):
		player = self.player
		if not player.is_climbing():
			grabbed = self.grab_ladder_below(player)
			if grabbed:
				player.climb_down()
		else:
			player.climb_down()

	def player_stop_down(self):
		player = self.player
		if player.is_climbing():
			player.stop_climbing()

	def player_jump(self):
		player = self.player
		if not player.is_falling():
			player.jump()

	def player_start_shoot(self):
		pew = self.player.shoot()
		self.sprites.add(pew)

	def player_stop_shoot(self):
		self.player.stop_shooting()

	def game_pause_unpause(self):
		if not self.game.is_paused():
			self.music_player.pause()
			self.game.pause()
		else:
			self.music_player.unpause()
			self.game.unpause()

	def is_game_paused(self):
		return self.game.is_paused()

	def game_over(self):
		self.game.game_over()

	def game_quit(self):
		self.game.quit()

	def handle_event(self, event):
		input = self.input

		if input.is_pressed(event) or input.is_released(event):
			if self.player.is_dead():
				return

			# Pause
			if input.is_pause(event) and input.is_released(event):
				self.game_pause_unpause()

			# Quit
			elif input.is_cancel(event):
				self.game_quit()

			else:
				if self.is_game_paused():
					return

				# Right
				if input.is_right(event) and input.is_pressed(event):
					self.player_start_right()
				elif input.is_right(event) and input.is_released(event):
					self.player_stop_right()

				# Left
				elif input.is_left(event) and input.is_pressed(event):
					self.player_start_left()
				elif input.is_left(event) and input.is_released(event):
					self.player_stop_left()

				# Up
				elif input.is_up(event) and input.is_pressed(event):
					self.player_start_up()
				elif input.is_up(event) and input.is_released(event):
					self.player_stop_up()

				# Down
				elif input.is_down(event) and input.is_pressed(event):
					self.player_start_down()
				elif input.is_down(event) and input.is_released(event):
					self.player_stop_down()

				# Jump
				elif input.is_jump(event) and input.is_pressed(event):
					self.player_jump()

				# Shoot
				elif input.is_shoot(event) and input.is_pressed(event):
					self.player_start_shoot()
				elif input.is_shoot(event) and input.is_released(event):
					self.player_stop_shoot()

		elif event.type == PLAYER_DEFEATED:
			self.game_over()