import json
import asyncio
import random
import logging
import time
import ntplib

import pygame

from config import ENEMY_CONFIG, GAME_CONFIG, PLATFORM_CONFIG, PLAYER_CONFIG

DIRECTION_STAY = 0
DIRECTION_RIGHT = 1
DIRECTION_LEFT = 2
DIRECTION_TOP = 3
DIRECTION_BOTTOM = 4


class ContextFilter(logging.Filter):

    def __init__(self, game_id):
        self.game_id = game_id

    def filter(self, record):
        record.game_id = self.game_id
        return True


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
        self.rect = pygame.Rect(*offset, *size)

    @property
    def coordinates(self):
        return self.rect

    @property
    def is_dead(self):
        return self.health <= 0

    def hit(self, strength):
        self.health -= strength


class Platform(GameObject):
    '''
    Platform - static gameobject with hit animations
    Parent: GameObject
    '''
    def __init__(self, size, offset):
        super().__init__(size, offset)
        self.health = PLATFORM_CONFIG['HEALTH']

    def to_dict(self):
        return {
            'type': 'Platform',
            'id': id(self),
            'health': self.health,
            'coordinates': [self.coordinates.x, self.coordinates.y]
        }


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

    def to_dict(self):
        return {
            'type': 'Bullet',
            'id': id(self),
            'speed': self.speed,
            'direction': self.direction,
            'coordinates': [self.coordinates.x, self.coordinates.y]
        }

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
        self.speed = PLAYER_CONFIG['SPEED']
        self.health = PLAYER_CONFIG['HEALTH']
        self.lives = PLAYER_CONFIG['LIVES']
        self.is_cannon_locked = False
        self.score = 0

    def to_dict(self):
        return {
            'type': 'Player',
            'id': id(self),
            'lives': self.lives,
            'health': self.health,
            'score': self.score,
            'coordinates': [self.coordinates.x, self.coordinates.y]
        }

    def update(self, direction):
        if direction == DIRECTION_LEFT:
            self.coordinates.x -= self.speed
        elif direction == DIRECTION_RIGHT:
            self.coordinates.x += self.speed

    def hit(self, strength):
        self.health -= strength
        if self.is_dead:
            self.lives -= 1

    def rebirth(self):
        self.health = PLAYER_CONFIG['HEALTH']

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
        self.type = enemy_type
        self.health = ENEMY_CONFIG['HEALTH']
        self.points = ENEMY_CONFIG['ENEMIES'][enemy_type]['POINTS']

    def to_dict(self):
        return {
            'type': 'Enemy',
            'id': id(self),
            'health': self.health,
            'type': self.type,
            'coordinates': [self.coordinates.x, self.coordinates.y]
        }

    def update(self, direction, jump_next_line=False):
        if jump_next_line:
            self.coordinates.y += ENEMY_CONFIG['STEP_Y']
        elif direction == DIRECTION_RIGHT:
            self.coordinates.x += ENEMY_CONFIG['STEP_X']
        else:
            self.coordinates.x -= ENEMY_CONFIG['STEP_X']

    def hit(self, strength):
        self.health -= strength
        if self.is_dead:
            current_center = self.coordinates.center
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
        self.points = ENEMY_CONFIG['ENEMIES']['UFO']['POINTS']
        self.base_offset = offset
        self.health = 0

    def to_dict(self):
        return {
            'type': 'UFO',
            'id': id(self),
            'coordinates': [self.coordinates.x, self.coordinates.y],
            'health': self.health
        }

    def create(self):
        if self.is_dead:
            self.coordinates.x, self.coordinates.y = self.base_offset
            self.health = ENEMY_CONFIG['HEALTH']

    def update(self):
        if not self.is_dead:
            self.coordinates.x += ENEMY_CONFIG['UFO_SPEED']

    def hide(self):
        self.coordinates.x, self.coordinates.y = self.base_offset

    def hit(self, strength):
        self.health -= strength


class EnemyGroup(pygame.sprite.Group):
    '''
    Enemy Group
    Parent: pygame.sprite.Group
    Updates enemies and loads them from date
    '''

    def __init__(self):
        super().__init__()
        self.moving = True

    def to_dict(self):
        return {
            'type': 'EnemyGroup',
            'id': id(self),
            'objects': [enemy.to_dict() for enemy in self]
        }

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

            # Form coordinates offset for transfer

            offset_y = 0
            offset_x = 0
            if jump_next_line:
                offset_y = ENEMY_CONFIG['STEP_Y']
            elif self.enemy_direction == DIRECTION_RIGHT:
                offset_x = ENEMY_CONFIG['STEP_X']
            else:
                offset_x = -ENEMY_CONFIG['STEP_X']

            return {
                'type': 'EnemyGroup',
                'id': id(self),
                'coordinates': [offset_x, offset_y]
            }


class PlatformGroup(pygame.sprite.Group):

    def to_dict(self):
        return {
            'type': 'PlatformGroup',
            'id': id(self),
            'objects': [platform.to_dict() for platform in self.sprites()]
        }

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

    def __str__(self):
        return '<Game 0x{}>'.format(id(self))

    def __init__(self, websocket, debug=False):
        self.enemy_direction = DIRECTION_RIGHT
        self.enemy_speed = ENEMY_CONFIG['BASE_SPEED']
        self.enemies = EnemyGroup()
        self.platforms = PlatformGroup()
        self.bullets = pygame.sprite.Group()
        self.websocket = websocket
        self.current_wave = 1
        self.debug = debug
        self.player = None
        self.UFO = None
        self.game_over = False
        self.player_shoot = False
        self.player_direction = DIRECTION_STAY
        self.logger = self.create_logger()
        self.loop = asyncio.get_event_loop()

    def create_logger(self):
        logger = logging.getLogger(str(self))
        formatter = logging.Formatter('[%(asctime)s] - %(levelname)s - [%(game_id)s] - %(message)s')

        logger_filter = ContextFilter(str(self))
        logger.addFilter(logger_filter)

        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        sh.setLevel(logging.DEBUG)

        logger.addHandler(sh)
        if self.debug:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        return logger

    def handle_event(self, data):
        self.player_shoot = data['player_shoot']
        self.player_direction = data['player_direction']

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

        data_to_send = {'Create': []}
        data_to_send['Create'].append(self.player.to_dict())
        data_to_send['Create'].append(self.enemies.to_dict())
        data_to_send['Create'].append(self.UFO.to_dict())
        data_to_send['Create'].append(self.platforms.to_dict())
        self.send_objects(data_to_send)

    def find_collisions(self):

        data = {}
        data['Delete'] = []
        data['Update'] = []

        # If UFO out of screen
        if self.UFO.coordinates.left > GAME_CONFIG['DISPLAY_SIZE'][0]:
            # Kill UFO
            self.UFO.health = 0
            self.UFO.hide()
            data['Update'].append({
                'type': 'UFO',
                'health': self.UFO.health,
                'coordinates': [self.UFO.coordinates.x, self.UFO.coordinates.y]
            })
            self.logger.debug('UFO out of screen')

        # If Player out of screen
        if self.player.coordinates.left > GAME_CONFIG['DISPLAY_SIZE'][0]:
            self.player.coordinates.right = 0
        elif self.player.coordinates.right < 0:
            self.player.coordinates.left = GAME_CONFIG['DISPLAY_SIZE'][0]

        # Bullets collide handlement
        for bullet in self.bullets:

            # If bullet out of screen
            if bullet.coordinates.top > GAME_CONFIG['DISPLAY_SIZE'][1] or bullet.coordinates.bottom < 0:
                self.bullets.remove(bullet)
                self.logger.debug('Bullet {} out of screen'.format(bullet))
                data['Delete'].append({
                    'type': 'Bullet',
                    'id': id(bullet)
                })
                continue

            # If bullet collide with Surface
            for platform in self.platforms:
                if pygame.sprite.collide_rect(platform, bullet):
                    platform.hit(bullet.strength)
                    data['Update'].append({
                        'type': 'Platform',
                        'id': id(platform),
                        'health': platform.health
                    })
                    self.bullets.remove(bullet)
                    data['Delete'].append({
                        'type': 'Bullet',
                        'id': id(bullet)
                    })
                    self.logger.debug('Platform {} hitted by {} {}'.format(
                        platform,
                        bullet.parent.__class__.__name__,
                        bullet.parent
                    ))
                    if platform.is_dead:
                        self.platforms.remove(platform)
                        data['Delete'].append({
                            'type': 'Platform',
                            'id': id(platform)
                        })

            # If bullet collide with UFO
            if pygame.sprite.collide_rect(bullet, self.UFO) and isinstance(bullet.parent, Player):
                self.UFO.hit(bullet.strength)
                # TODO: magic number to config
                self.loop.call_later(0.5, self.UFO.hide)
                self.bullets.remove(bullet)
                data['Delete'].append({
                    'type': 'Bullet',
                    'id': id(bullet)
                })
                self.logger.debug('UFO hitted')
                self.player.score += self.UFO.points

            # If bullet collide with enemy
            for enemy in self.enemies:
                if pygame.sprite.collide_rect(enemy, bullet) and isinstance(bullet.parent, Player):
                    if not enemy.is_dead:
                        enemy.hit(bullet.strength)
                        data['Update'].append({
                            'type': 'Enemy',
                            'health': enemy.health,
                            'id': id(enemy)
                        })
                        self.logger.debug('Enemy {} hitted'.format(enemy))
                        self.player.score += enemy.points
                        self.bullets.remove(bullet)
                        data['Delete'].append({
                            'type': 'Bullet',
                            'id': id(bullet)
                        })
                        # TODO: magic number to config
                        self.loop.call_later(0.5, self.enemies.remove, enemy)
                        # Change enemy speed
                        speed_coef = (self.base_enemies_count - len(self.enemies)) / self.base_enemies_count
                        max_speed = ENEMY_CONFIG['MAX_SPEED'] * self.current_wave
                        speed_delta = max_speed - ENEMY_CONFIG['BASE_SPEED']
                        self.enemy_speed = ENEMY_CONFIG['BASE_SPEED'] + (speed_coef ** 2) * speed_delta

            # If bullet collide with player
            if pygame.sprite.collide_rect(self.player, bullet) and isinstance(bullet.parent, Enemy):
                self.player.hit(bullet.strength)
                self.logger.debug('Player hitted by Enemy {}'.format(bullet.parent))
                self.bullets.remove(bullet)
                data['Delete'].append({
                    'type': 'Bullet',
                    'id': id(bullet)
                })
                if self.player.lives:
                    # Rebirth after 1 second
                    self.logger.info('Player dead, rebithing after 1 second')
                    self.loop.call_later(1, self.player.rebirth)
                else:
                    # Game end after 1 second
                    self.logger.info('Player out of lives')
                    self.loop.call_later(1, self.end_game, 'All cannons were destroyed')

        return data

    def end_game(self, message):
        # TODO: create window with message
        self.logger.info(message)
        self.websocket.sendMessage(
            json.dumps({
                'type': 'game_over',
                'message': {
                    'player_score': self.player.score,
                    'reason': message
                }
            }).encode('utf8')
        )
        self.websocket.sendClose()
        self.game_over = True

    def enemy_game_tick(self):
        self.enemies.grant_moving()
        # Stop animations if game is over
        if self.game_over:
            return

        self.loop.call_later(1 / self.enemy_speed, self.enemy_game_tick)

    def send_objects(self, data):
        self.websocket.sendMessage(
            json.dumps({
                'type': 'game_action',
                'message': data
            }).encode('utf8')
        )

    def game_tick(self):

        if self.game_over:
            return

        self.loop.call_later(1 / GAME_CONFIG['TICK_RATE'], self.game_tick)

        # Skip all animations if player is dead
        if self.player.is_dead:
            return

        # Update world if all enemies are dead
        if not self.enemies:
            data = self.load_map()
            data_to_send = {'Create': [], 'Delete': []}
            data_to_send['Delete'] = [{
                'type': 'Bullet',
                'id': id(bullet)
            } for bullet in self.bullets]

            self.enemies = EnemyGroup()
            self.enemies.load(data['Enemies'])
            self.enemy_speed = ENEMY_CONFIG['BASE_SPEED']
            self.platforms = PlatformGroup()
            self.platforms.load(data['Platforms'])
            self.bullets = pygame.sprite.Group()
            self.logger.info('WAVE {} PASSED'.format(self.current_wave))
            self.current_wave += 1

            data_to_send['Create'].append(self.enemies.to_dict())
            data_to_send['Create'].append(self.platforms.to_dict())
            self.send_objects(data_to_send)

            return

        data = {}
        data['Create'] = []

        # Player shoot if cannon is released
        if self.player_shoot and not self.player.is_cannon_locked:
            self.player_shoot = False
            bullet = Bullet(
                parent=self.player,
                speed=PLAYER_CONFIG['BULLET_SPEED'],
                strength=PLAYER_CONFIG['BULLET_STRENGTH'],
                direction=DIRECTION_TOP,
            )
            self.bullets.add(bullet)
            data['Create'].append(bullet.to_dict())
            self.player.lock_cannon(PLAYER_CONFIG['SHOOT_DELAY'])

        # Enemy shoot with some constant probability
        if self.enemies:
            if random.random() < ENEMY_CONFIG['SHOOT_PROBABILITY']:
                enemy_to_shoot = random.choice(self.enemies.sprites())
                self.logger.debug('Enemy {} shoot'.format(enemy_to_shoot))
                bullet = Bullet(
                    parent=enemy_to_shoot,
                    speed=ENEMY_CONFIG['BULLET_SPEED'],
                    strength=ENEMY_CONFIG['BULLET_STRENGTH'],
                    direction=DIRECTION_BOTTOM,
                )
                self.bullets.add(bullet)
                data['Create'].append(bullet.to_dict())

        self.player.update(self.player_direction)
        self.player_direction = DIRECTION_STAY
        self.bullets.update()
        enemy_step = self.enemies.update()
        self.UFO.update()

        data.update(self.find_collisions())
        data['Update'].append({'type': 'BulletGroup'})
        data['Update'].append(self.player.to_dict())
        if enemy_step:
            data['Update'].append(enemy_step)
        data['Update'].append(self.UFO.to_dict())

        # Create UFO with some constant probability
        if random.random() < ENEMY_CONFIG['UFO_PROBABILITY'] and self.UFO.is_dead:
            self.UFO.create()
            data['Update'].append({
                'type': 'UFO',
                'health': self.UFO.health,
                'coordinates': [self.UFO.coordinates.x, self.UFO.coordinates.y]
            })
            self.logger.debug('UFO created')

        self.send_objects(data)

    def run(self):
        pygame.init()

        data = self.load_map()
        self.create_world(data)

        # Game ticks init with enemy steps
        self.loop.call_later(1, self.game_tick)
        # Base game ticks init
        self.loop.call_later(1 / self.enemy_speed, self.enemy_game_tick)
