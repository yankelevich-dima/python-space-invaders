import json
import asyncio
import random

import pygame

from config import ENEMY_CONFIG, GAME_CONFIG, PLATFORM_CONFIG, PLAYER_CONFIG, LOGGER

DIRECTION_STAY = 0
DIRECTION_RIGHT = 1
DIRECTION_LEFT = 2
DIRECTION_TOP = 3
DIRECTION_BOTTOM = 4


# class Button(pygame.sprite.Sprite):
#
#     def __init__(self, x, y, text):
#         self.x = x
#         self.y = y
#
#         super().__init__()
#         self.img_selected = pygame.image.load('images/menu_selected.png').convert()
#         self.img_unselecled = pygame.image.load('images/menu_unselected.png').convert()
#         self.textSprite = pygame.TextSprite(self.x, self.y, text)
#         self.changeState(0)
#
#     def changeState(self, state):
#         if state == 0:
#             self.image = self.img_unsel
#             self.textSprite.setColor((255, 165, 149))
#         elif state == 1:
#             self.image = self.img_sel
#             self.textSprite.setColor((243, 227, 200))
#         self.image.set_colorkey(self.image.get_at((0, 0)), pygame.RLEACCEL)
#
#         self.rect = self.image.get_rect()
#         self.rect.center = (self.x, self.y)


class GameObject(pygame.sprite.Sprite):
    '''
    Base gameobject, implements draw method of pygame.sprite.Sprite class
    And creates coordinates property - link to rect property
    '''

    def __str__(self):
        return '<{} 0x{}>'.format(self.__class__.__name__, id(self))

    def __init__(self, size, offset, color=None):
        super().__init__()
        self.health = None

        # If color exists - create Surface
        if color is not None:
            self.image = pygame.Surface(size)
            self.image.fill(pygame.Color(color))
        else:
            self.image = None

        self.rect = pygame.Rect(*offset, *size)

    @property
    def coordinates(self):
        return self.rect

    @property
    def is_dead(self):
        return self.health <= 0

    def hit(self, strength):
        self.health -= strength

    def draw(self, screen):
        screen.blit(self.image, (self.coordinates.x, self.coordinates.y))


class Platform(GameObject):
    '''
    Platform - static gameobject with hit animations
    Parent: GameObject
    '''
    def __init__(self, size, offset):
        super().__init__(size, offset)
        self.animations = [pygame.image.load(image) for image in PLATFORM_CONFIG['ANIMATIONS']]
        self.image = self.animations[0]
        # Loading animations
        self.health = PLATFORM_CONFIG['HEALTH']


class Bullet(GameObject):
    '''
    Bullet
    Parent: GameObject
    '''

    def __init__(self, parent, speed, strength, direction):
        # TODO: params to config
        super().__init__((3, 20), parent.coordinates.center, color='#FFFF00')
        if direction == DIRECTION_TOP:
            self.coordinates.bottom = parent.coordinates.top
        elif direction == DIRECTION_BOTTOM:
            self.coordinates.top = parent.coordinates.bottom
        self.coordinates.centerx = parent.coordinates.centerx
        self.parent = parent
        self.speed = speed
        self.strength = strength
        self.direction = direction

    def update(self):
        if self.direction == DIRECTION_TOP:
            self.coordinates.y -= self.speed
        elif self.direction == DIRECTION_BOTTOM:
            self.coordinates.y += self.speed


class Player(GameObject):
    '''
    Player
    Parent: GameObject
    '''
    def __init__(self, offset):
        super().__init__(PLAYER_CONFIG['SIZE'], offset)
        self.image = pygame.image.load(PLAYER_CONFIG['ANIMATIONS'])
        self.speed = PLAYER_CONFIG['SPEED']
        self.health = PLAYER_CONFIG['HEALTH']
        self.lives = PLAYER_CONFIG['LIVES']
        self.is_cannon_locked = False
        self.score = 0

    def update(self, direction):
        if direction == DIRECTION_LEFT:
            self.coordinates.x -= self.speed
        elif direction == DIRECTION_RIGHT:
            self.coordinates.x += self.speed

    def hit(self, strength):
        self.health -= strength
        if self.is_dead:
            self.lives -= 1
            self.image = pygame.image.load(PLAYER_CONFIG['ANIMATIONS_DEATH'])

    def rebirth(self):
        self.health = PLAYER_CONFIG['HEALTH']
        self.image = pygame.image.load(PLAYER_CONFIG['ANIMATIONS'])

    def lock_cannon(self, timeout):
        self.is_cannon_locked = True
        loop = asyncio.get_event_loop()
        loop.call_later(timeout, self.unlock_cannon)

    def unlock_cannon(self):
        self.is_cannon_locked = False


class Enemy(GameObject):
    '''
    Enemy
    Parent: GameObject
    '''

    def __init__(self, offset, enemy_type):
        super().__init__(ENEMY_CONFIG['ENEMIES'][enemy_type]['SIZE'], offset)
        self.animations = [
            pygame.image.load(image)
            for image in ENEMY_CONFIG['ENEMIES'][enemy_type]['ANIMATIONS']
        ]
        self.image = self.animations[0]
        self.health = ENEMY_CONFIG['HEALTH']
        self.points = ENEMY_CONFIG['ENEMIES'][enemy_type]['POINTS']
        self.dead_animation = pygame.image.load(ENEMY_CONFIG['ENEMIES']['DEAD']['ANIMATIONS'])

    def update(self, direction, jump_next_line=False):
        if jump_next_line:
            self.coordinates.y += ENEMY_CONFIG['STEP_Y']
        elif direction == DIRECTION_RIGHT:
            self.coordinates.x += ENEMY_CONFIG['STEP_X']
        else:
            self.coordinates.x -= ENEMY_CONFIG['STEP_X']

        if not self.is_dead:
            if self.image == self.animations[0]:
                self.image = self.animations[1]
            else:
                self.image = self.animations[0]

    def hit(self, strength):
        self.health -= strength
        if self.is_dead:
            current_center = self.coordinates.center
            self.image = self.dead_animation
            # Change animation to DEAD
            self.rect = pygame.Rect((self.coordinates.x, self.coordinates.y), ENEMY_CONFIG['ENEMIES']['DEAD']['SIZE'])
            # Center image
            self.coordinates.center = current_center
            # Delete enemy from physical map
            self.rect = pygame.Rect((self.coordinates.x, self.coordinates.y), (0, 0))


class UFO(GameObject):
    '''
    UFO Enemy
    Parent: GameObject
    '''

    def __init__(self, offset):
        super().__init__(ENEMY_CONFIG['ENEMIES']['UFO']['SIZE'], offset)
        self.image = pygame.image.load(ENEMY_CONFIG['ENEMIES']['UFO']['ANIMATIONS'])
        self.points = ENEMY_CONFIG['ENEMIES']['UFO']['POINTS']
        self.base_offset = offset
        self.health = 0

    def create(self):
        if self.is_dead:
            self.coordinates.x, self.coordinates.y = self.base_offset
            self.health = ENEMY_CONFIG['HEALTH']
            self.image = pygame.image.load(ENEMY_CONFIG['ENEMIES']['UFO']['ANIMATIONS'])

    def update(self):
        if not self.is_dead:
            self.coordinates.x += ENEMY_CONFIG['UFO_SPEED']

    def hide(self):
        self.coordinates.x, self.coordinates.y = self.base_offset

    def hit(self, strength):
        self.health -= strength
        self.image = pygame.image.load(ENEMY_CONFIG['ENEMIES']['DEAD']['ANIMATIONS'])


class EnemyGroup(pygame.sprite.Group):
    '''
    Enemy Group
    Parent: pygame.sprite.Group
    Updates enemies and loads them from date
    '''

    def __init__(self):
        super().__init__()
        self.moving = True

    def grant_moving(self):
        self.moving = True

    def load(self, data):
        self.enemy_direction = DIRECTION_RIGHT
        for enemy_data in data:
            enemy_width, enemy_height = ENEMY_CONFIG['ENEMIES'][enemy_data['type']]['SIZE']
            base_x, base_y = enemy_data['base_offset']
            for i in range(enemy_data['count']):
                offset = (base_x + i * (enemy_width + enemy_data['distance']), base_y)
                enemy = Enemy(offset, enemy_data['type'])
                self.add(enemy)

    def update(self):
        if self.moving:
            self.moving = False

            right = max(self.sprites(), key=lambda x: x.coordinates.right).coordinates.right
            left = min(self.sprites(), key=lambda x: x.coordinates.left).coordinates.left
            bottom = max(self.sprites(), key=lambda x: x.coordinates.bottom).coordinates.bottom

            jump_next_line = False

            if self.enemy_direction == DIRECTION_RIGHT:
                right += ENEMY_CONFIG['STEP_X']
                left += ENEMY_CONFIG['STEP_X']
            else:
                right -= ENEMY_CONFIG['STEP_X']
                left -= ENEMY_CONFIG['STEP_X']

            if left < 0 or right > GAME_CONFIG['DISPLAY_SIZE'][0]:
                if self.enemy_direction == DIRECTION_RIGHT:
                    self.enemy_direction = DIRECTION_LEFT
                else:
                    self.enemy_direction = DIRECTION_RIGHT

                if bottom < ENEMY_CONFIG['MAX_Y']:
                    jump_next_line = True

            for enemy in self.sprites():
                enemy.update(self.enemy_direction, jump_next_line)


class PlatformGroup(pygame.sprite.Group):

    def load(self, data):
        # All space without platforms
        all_distance = GAME_CONFIG['DISPLAY_SIZE'][0] - data['count'] * PLATFORM_CONFIG['SIZE'][0]
        # Distance between platforms
        distance = all_distance // (data['count'] + 1)
        for i in range(data['count']):
            offset_x = distance + i * (distance + PLATFORM_CONFIG['SIZE'][0])
            platform = Platform(
                PLATFORM_CONFIG['SIZE'],
                (offset_x, PLATFORM_CONFIG['Y_POSITION'])
            )
            self.add(platform)


class Game(object):
    '''
    Game
    Main class with all game logic, such as
        - world update
        - objects loading
        - collisions handle
    '''

    def __init__(self, debug=False):
        self.enemy_direction = DIRECTION_RIGHT
        self.enemy_speed = ENEMY_CONFIG['BASE_SPEED']
        self.enemies = EnemyGroup()
        self.platforms = PlatformGroup()
        self.bullets = pygame.sprite.Group()
        self.current_wave = 1
        self.debug = debug
        self.player = None
        self.UFO = None
        self.game_over = False

    def load_map(self, path_to_file='objects.json'):
        with open(path_to_file, 'r') as map_file:
            return json.load(map_file)

    def create_world(self, data):
        self.player = Player(data['Player']['offset'])
        self.enemies.load(data['Enemies'])
        self.UFO = UFO(data['Ufo']['offset'])
        self.platforms.load(data['Platforms'])
        # Save enemies count for further speed increase
        self.base_enemies_count = len(self.enemies)

    def find_collisions(self):

        # TODO: log collisions

        # If UFO out of screen
        if self.UFO.coordinates.left > GAME_CONFIG['DISPLAY_SIZE'][0]:
            # Kill UFO
            self.UFO.health = 0
            self.UFO.hide()
            LOGGER.debug('UFO out of screen')

        # If Player out of screen
        if self.player.coordinates.left > GAME_CONFIG['DISPLAY_SIZE'][0]:
            self.player.coordinates.right = 0
        elif self.player.coordinates.right < 0:
            self.player.coordinates.left = GAME_CONFIG['DISPLAY_SIZE'][0]

        # Bullets collide handlement
        for bullet in self.bullets.sprites():

            # If bullet out of screen
            if bullet.coordinates.top > GAME_CONFIG['DISPLAY_SIZE'][1] or bullet.coordinates.bottom < 0:
                self.bullets.remove(bullet)
                LOGGER.debug('Bullet {} out of screen'.format(bullet))
                continue

            # If bullet collide with Surface
            for platform in self.platforms.sprites():
                if pygame.sprite.collide_rect(platform, bullet):
                    platform.hit(bullet.strength)
                    self.bullets.remove(bullet)
                    LOGGER.debug('Platform {} hitted by {} {}'.format(
                        platform,
                        bullet.parent.__class__.__name__,
                        bullet.parent
                    ))
                    if platform.is_dead:
                        self.platforms.remove(platform)

            # If bullet collide with UFO
            if pygame.sprite.collide_rect(bullet, self.UFO) and isinstance(bullet.parent, Player):
                self.UFO.hit(bullet.strength)
                loop = asyncio.get_event_loop()
                # TODO: magic number to config
                loop.call_later(0.5, self.UFO.hide)
                self.bullets.remove(bullet)
                LOGGER.debug('UFO hitted')
                self.player.score += self.UFO.points

            # If bullet collide with enemy
            for enemy in self.enemies.sprites():
                if pygame.sprite.collide_rect(enemy, bullet) and isinstance(bullet.parent, Player):
                    enemy.hit(bullet.strength)
                    LOGGER.debug('Enemy {} hitted'.format(enemy))
                    self.player.score += enemy.points
                    self.bullets.remove(bullet)
                    enemy.draw(self.screen)
                    loop = asyncio.get_event_loop()
                    # TODO: magic number to config
                    loop.call_later(0.5, self.enemies.remove, enemy)
                    # Change enemy speed
                    speed_coef = (self.base_enemies_count - len(self.enemies)) / self.base_enemies_count
                    max_speed = ENEMY_CONFIG['MAX_SPEED'] * self.current_wave
                    speed_delta = max_speed - ENEMY_CONFIG['BASE_SPEED']
                    self.enemy_speed = ENEMY_CONFIG['BASE_SPEED'] + (speed_coef ** 2) * speed_delta

            # If bullet collide with player
            if pygame.sprite.collide_rect(self.player, bullet) and isinstance(bullet.parent, Enemy):
                self.player.hit(bullet.strength)
                LOGGER.debug('Player hitted by Enemy {}'.format(bullet.parent))
                self.bullets.remove(bullet)
                loop = asyncio.get_event_loop()
                if self.player.lives:
                    # Rebirth after 1 second
                    LOGGER.info('Player dead, rebithing after 1 second')
                    loop.call_later(1, self.player.rebirth)
                else:
                    # Game end after 1 second
                    LOGGER.info('Player out of lives')
                    self.game_over = True
                    loop.call_later(1, self.end_game('All cannons were destroyed'))

    def draw_objects(self):
        self.screen.blit(self.background, (0, 0))
        self.player.draw(self.screen)
        self.platforms.draw(self.screen)
        self.enemies.draw(self.screen)
        self.bullets.draw(self.screen)
        self.UFO.draw(self.screen)
        pygame.display.update()

    def end_game(self, message):
        # TODO: create window with message
        LOGGER.info(message)
        raise KeyboardInterrupt

    def enemy_game_tick(self):
        self.enemies.grant_moving()
        loop = asyncio.get_event_loop()
        loop.call_later(1 / self.enemy_speed, self.enemy_game_tick)

    def game_tick(self):

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise KeyboardInterrupt

        # Stop animations if game is over
        if self.game_over:
            return

        # Stop animations and end game if all enemies are DEAD
        if not len(self.enemies):
            if self.current_wave < GAME_CONFIG['MAX_WAVE']:
                data = self.load_map()
                self.enemies = EnemyGroup()
                self.enemies.load(data['Enemies'])
                self.enemy_speed = ENEMY_CONFIG['BASE_SPEED']
                self.platforms = PlatformGroup()
                self.platforms.load(data['Platforms'])
                self.bullets = pygame.sprite.Group()
                LOGGER.info('WAVE {} PASSED'.format(self.current_wave))
                self.current_wave += 1
            else:
                self.end_game('Space invaders were destroyed')
                return

        # Skip all animations if player is dead
        if self.player.is_dead:
            loop = asyncio.get_event_loop()
            loop.call_later(1 / GAME_CONFIG['TICK_RATE'], self.game_tick)
            return

        keys = pygame.key.get_pressed()
        player_direction = DIRECTION_STAY
        if keys[pygame.K_LEFT]:
            player_direction = DIRECTION_LEFT
        elif keys[pygame.K_RIGHT]:
            player_direction = DIRECTION_RIGHT

        # Only for debugging under MacOS (no input)
        if self.debug:
            player_direction = DIRECTION_LEFT
            if random.random() < 0.25 and not self.player.is_cannon_locked:
                bullet = Bullet(
                    parent=self.player,
                    speed=PLAYER_CONFIG['BULLET_SPEED'],
                    strength=PLAYER_CONFIG['BULLET_STRENGTH'],
                    direction=DIRECTION_TOP,
                )
                self.bullets.add(bullet)
                self.player.lock_cannon(PLAYER_CONFIG['SHOOT_DELAY'])

        # Player shoot if cannon is released
        if keys[pygame.K_SPACE] and not self.player.is_cannon_locked:
            bullet = Bullet(
                parent=self.player,
                speed=PLAYER_CONFIG['BULLET_SPEED'],
                strength=PLAYER_CONFIG['BULLET_STRENGTH'],
                direction=DIRECTION_TOP,
            )
            self.bullets.add(bullet)
            self.player.lock_cannon(PLAYER_CONFIG['SHOOT_DELAY'])

        # Enemy shoot with some constant probability
        if len(self.enemies):
            if random.random() < ENEMY_CONFIG['SHOOT_PROBABILITY']:
                enemy_to_shoot = random.choice(self.enemies.sprites())
                LOGGER.debug('Enemy {} shoot'.format(enemy_to_shoot))
                bullet = Bullet(
                    parent=enemy_to_shoot,
                    speed=ENEMY_CONFIG['BULLET_SPEED'],
                    strength=ENEMY_CONFIG['BULLET_STRENGTH'],
                    direction=DIRECTION_BOTTOM,
                )
                self.bullets.add(bullet)

        self.player.update(player_direction)
        self.bullets.update()
        self.enemies.update()
        self.UFO.update()
        self.find_collisions()
        self.draw_objects()

        # Create UFO with some constant probability
        if random.random() < ENEMY_CONFIG['UFO_PROBABILITY'] and self.UFO.is_dead:
            self.UFO.create()
            LOGGER.debug('UFO created')

        loop = asyncio.get_event_loop()
        loop.call_later(1 / GAME_CONFIG['TICK_RATE'], self.game_tick)

    def run(self):
        pygame.init()
        pygame.display.set_caption('Space Invaders')
        self.screen = pygame.display.set_mode(GAME_CONFIG['DISPLAY_SIZE'])
        self.background = pygame.Surface(GAME_CONFIG['DISPLAY_SIZE'])
        self.background.fill(pygame.Color(GAME_CONFIG['BACKGROUND_COLOR']))

        data = self.load_map()
        self.create_world(data)

        loop = asyncio.get_event_loop()
        # Game ticks init with enemy steps
        loop.call_soon(self.game_tick)
        # Base game ticks init
        loop.call_soon(self.enemy_game_tick)

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass

        return self.player.score
