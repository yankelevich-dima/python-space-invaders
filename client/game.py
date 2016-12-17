import json
import time
import asyncio
import logging

try:
    import pygame_sdl2 as pygame
    USING_SDL2 = True
except ImportError:
    import pygame
    USING_SDL2 = False

from config import ENEMY_CONFIG, GAME_CONFIG, PLATFORM_CONFIG, PLAYER_CONFIG

DIRECTION_STAY = 0
DIRECTION_RIGHT = 1
DIRECTION_LEFT = 2
DIRECTION_TOP = 3
DIRECTION_BOTTOM = 4


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

    def draw(self, screen):
        screen.blit(self.image, (self.coordinates.x, self.coordinates.y))


class Platform(GameObject):
    '''
    Platform - static gameobject with hit animations
    Parent: GameObject
    '''
    def __init__(self, offset, platform_id):
        super().__init__(PLATFORM_CONFIG['SIZE'], offset)
        self.id = platform_id
        self.animations = [pygame.image.load(image) for image in PLATFORM_CONFIG['ANIMATIONS']]
        self.image = self.animations[0]


class Bullet(GameObject):
    '''
    Bullet
    Parent: GameObject
    '''

    def __init__(self, speed, direction, coordinates, bullet_id):
        # TODO: params to config
        super().__init__((3, 20), coordinates, color='#FFFF00')
        self.id = bullet_id
        self.speed = speed
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

    def draw(self, screen):
        if self.is_dead:
            image = pygame.image.load(PLAYER_CONFIG['ANIMATIONS_DEATH'])
        else:
            image = pygame.image.load(PLAYER_CONFIG['ANIMATIONS'])
        screen.blit(image, (self.coordinates.x, self.coordinates.y))


class Enemy(GameObject):
    '''
    Enemy
    Parent: GameObject
    '''

    def __init__(self, offset, enemy_type, enemy_id):
        super().__init__(ENEMY_CONFIG['ENEMIES'][enemy_type]['SIZE'], offset)
        self.animations = [
            pygame.image.load(image)
            for image in ENEMY_CONFIG['ENEMIES'][enemy_type]['ANIMATIONS']
        ]
        self.state = 0
        self.id = enemy_id
        self.dead_animation = pygame.image.load(ENEMY_CONFIG['ENEMIES']['DEAD']['ANIMATIONS'])

    def draw(self, screen):
        if not self.is_dead:
            screen.blit(self.animations[self.state], (self.coordinates.x, self.coordinates.y))
        else:
            screen.blit(
                pygame.image.load(
                    ENEMY_CONFIG['ENEMIES']['DEAD']['ANIMATIONS']
                ),
                (self.coordinates.x, self.coordinates.y)
            )

    def kill(self):
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
        self.health = 0

    def draw(self, screen):
        if not self.is_dead:
            screen.blit(
                pygame.image.load(ENEMY_CONFIG['ENEMIES']['UFO']['ANIMATIONS']),
                (self.coordinates.x, self.coordinates.y)
            )
        else:
            screen.blit(
                pygame.image.load(ENEMY_CONFIG['ENEMIES']['DEAD']['ANIMATIONS']),
                (self.coordinates.x, self.coordinates.y)
            )


class EnemyGroup(pygame.sprite.Group):
    '''
    Enemy Group
    Parent: pygame.sprite.Group
    Updates enemies and loads them from date
    '''

    def __init__(self):
        super().__init__()

    # As we use default draw method in Enemy class, override default draw
    # method in sprite.Group
    def draw(self, screen):
        [enemy.draw(screen) for enemy in self.sprites()]


class PlatformGroup(pygame.sprite.Group):
    pass


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
        pygame.font.init()

        self.enemies = EnemyGroup()
        self.platforms = PlatformGroup()
        self.bullets = pygame.sprite.Group()
        self.websocket = websocket
        self.player = None
        self.debug = debug
        self.UFO = None
        self.wave = 0
        self.loop = asyncio.get_event_loop()
        self.logger = self.create_logger()
        self.last_frames = []
        self.font = pygame.font.Font('./fonts/space_invaders.ttf', 15)
        self.last = 0

    def draw_labels(self):
        current_time = time.time()
        self.last_frames = [
            frame for frame in self.last_frames
            if frame['client_time'] > (current_time - 1)
        ]
        total_bytes = sum([frame['size'] for frame in self.last_frames])

        # TODO: colors and offsets to config
        wave_label = self.font.render('Current wave: {}'.format(self.wave), 1, (127, 242, 25))
        latency_label = self.font.render('Latency: {} ms'.format(self.websocket.latency), 1, (127, 242, 25))
        speed_label = self.font.render('Speed: {} KB/s'.format(total_bytes // 1024), 1, (127, 242, 25))
        fps_label = self.font.render('FPS: {}'.format(len(self.last_frames)), 1, (127, 242, 25))
        lives_label = self.font.render('Lives: {}'.format(self.player.lives), 1, (127, 242, 25))
        score_label = self.font.render('Score: {}'.format(self.player.score), 1, (127, 242, 25))
        self.screen.blit(fps_label, (10, 465))
        self.screen.blit(lives_label, (250, 465))
        self.screen.blit(score_label, (460, 465))
        self.screen.blit(latency_label, (10, 10))
        self.screen.blit(speed_label, (230, 10))
        self.screen.blit(wave_label, (430, 10))

    def draw_objects(self):
        self.screen.blit(self.background, (0, 0))
        if self.player:
            self.player.draw(self.screen)
        if self.enemies:
            self.enemies.draw(self.screen)
        if self.UFO:
            self.UFO.draw(self.screen)
        if self.platforms:
            self.platforms.draw(self.screen)
        if self.bullets:
            self.bullets.draw(self.screen)
        self.draw_labels()
        pygame.display.update()

    def delete_objects(self, elements):
        for element in elements:
            if element['type'] == 'Bullet':
                bullet = [bullet for bullet in self.bullets if bullet.id == element['id']]
                self.bullets.remove(bullet)

    def create_objects(self, elements):
        for element in elements:
            if element['type'] == 'Player':
                # TODO: create update method
                self.player = Player(element['coordinates'])
                self.player.health = element['health']
                self.player.score = element['score']
                self.player.lives = element['lives']
            if element['type'] == 'UFO':
                self.UFO = UFO(element['coordinates'])
            if element['type'] == 'EnemyGroup':
                self.wave += 1
                for subelement in element['objects']:
                    enemy = Enemy(subelement['coordinates'], subelement['type'], subelement['id'])
                    enemy.health = subelement['health']
                    self.enemies.add(enemy)
            if element['type'] == 'PlatformGroup':
                for subelement in element['objects']:
                    platform = Platform(subelement['coordinates'], subelement['id'])
                    self.platforms.add(platform)
            if element['type'] == 'Bullet':
                bullet = Bullet(element['speed'], element['direction'], element['coordinates'], element['id'])
                self.bullets.add(bullet)

    def update_objects(self, elements):
        for element in elements:
            if element['type'] == 'BulletGroup':
                self.bullets.update()
            if element['type'] == 'EnemyGroup':
                coordinates = element['coordinates']
                for subelement in self.enemies:
                    # Change state for drawing
                    subelement.state = 1 - subelement.state
                    subelement.coordinates.x += coordinates[0]
                    subelement.coordinates.y += coordinates[1]
            if element['type'] == 'Enemy':
                enemy = [enemy for enemy in self.enemies if enemy.id == element['id']][0]
                enemy.health = element['health']
                enemy.kill()
                self.loop.call_later(0.5, self.enemies.remove, enemy)
            if element['type'] == 'UFO':
                self.UFO.health = element['health']
                self.UFO.coordinates.x, self.UFO.coordinates.y = element['coordinates']
            if element['type'] == 'Player':
                # TODO: create update method
                self.player.health = element['health']
                self.player.lives = element['lives']
                self.player.score = element['score']
                self.player.coordinates.x, self.player.coordinates.y = element['coordinates']
            if element['type'] == 'Platform':
                platform = [platform for platform in self.platforms if platform.id == element['id']][0]
                platform.health = element['health']
                if platform.is_dead:
                    self.platforms.remove(platform)

    def handle_event(self, data):
        if data.get('Delete', None):
            self.delete_objects(data['Delete'])
        if data.get('Create', None):
            self.create_objects(data['Create'])
        if data.get('Update', None):
            self.update_objects(data['Update'])

        self.draw_objects()
        self.send_user_events()

    def game_over(self, data):
        font = pygame.font.Font('./fonts/space_invaders.ttf', 36)
        small_font = pygame.font.Font('./fonts/space_invaders.ttf', 20)
        label_game_over = font.render('GAME OVER', 1, (127, 242, 25))
        label_reason = small_font.render(data['reason'], 1, (127, 242, 25))
        label_player_score = small_font.render('Your score: {}'.format(data['player_score']), 1, (127, 242, 25))
        self.screen.blit(self.background, (0, 0))
        self.screen.blit(label_game_over, ((self.background.get_width() - label_game_over.get_width()) // 2, 170))
        self.screen.blit(label_reason, ((self.background.get_width() - label_reason.get_width()) // 2, 250))
        self.screen.blit(label_player_score, ((self.background.get_width() - label_player_score.get_width()) // 2, 300))
        pygame.display.update()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise KeyboardInterrupt

    def send_user_events(self):

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise KeyboardInterrupt

        # Handle user events and send them to server

        keys = pygame.key.get_pressed()
        player_direction = DIRECTION_STAY
        player_shoot = False

        if keys[pygame.K_SPACE]:
            player_shoot = True

        if keys[pygame.K_LEFT] and not keys[pygame.K_RIGHT]:
            player_direction = DIRECTION_LEFT
        elif keys[pygame.K_RIGHT] and not keys[pygame.K_LEFT]:
            player_direction = DIRECTION_RIGHT

        if player_direction or player_shoot:
            self.websocket.sendMessage(json.dumps({
                'type': 'player_event',
                'message': {
                    'player_shoot': player_shoot,
                    'player_direction': player_direction
                }
            }).encode('utf8'))

    def create_logger(self):
        logger = logging.getLogger(str(self))
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        sh.setLevel(logging.DEBUG)

        logger.addHandler(sh)

        if self.debug:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        return logger

    def run(self):
        pygame.init()
        pygame.display.set_caption('Space Invaders')
        self.screen = pygame.display.set_mode(GAME_CONFIG['DISPLAY_SIZE'], pygame.DOUBLEBUF, 32)
        flags = pygame.SRCALPHA if USING_SDL2 else 0
        self.background = pygame.Surface(GAME_CONFIG['DISPLAY_SIZE'], flags)
        self.background.fill(pygame.Color(GAME_CONFIG['BACKGROUND_COLOR']))
