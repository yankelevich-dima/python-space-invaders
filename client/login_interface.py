import json
import pygame_sdl2 as pygame

MOUSE_BUTTON_LEFT = 1


class Button(pygame.sprite.Sprite):

    def __init__(self, size, offset, text, border=1, border_color='#FFFFFF', color='#111111'):
        super().__init__()

        self.text = text
        self.font = pygame.font.Font('./fonts/space_invaders.ttf', 24)
        self.text_label = self.font.render(self.text, 1, (255, 255, 255))

        self.border = border
        self.bottom_image = pygame.Surface(size)
        self.bottom_image.fill(pygame.Color(border_color))

        width, height = size
        self.top_image = pygame.Surface((width - 2 * border, height - 2 * border))
        self.top_image.fill(pygame.Color(color))

        self.rect = pygame.Rect(*offset, *size)

    def draw(self, screen):
        screen.blit(self.bottom_image, (self.rect.x, self.rect.y))
        screen.blit(self.top_image, (self.rect.x + self.border, self.rect.y + self.border))
        screen.blit(
            self.text_label,
            (self.rect.x + 10, self.rect.y + (self.rect.height - self.text_label.get_height()) // 2)
        )


class TextArea(pygame.sprite.Sprite):

    def __init__(self, size, offset, border=1, border_color='#FFFFFF', color='#111111', protected=False):
        super().__init__()
        self.protected = protected
        self.is_active = False

        self.text = ''
        self.font = pygame.font.Font('./fonts/space_invaders.ttf', 24)
        self.text_label = self.font.render(self.text, 1, (255, 255, 255))

        self.border = border
        self.bottom_image = pygame.Surface(size)
        self.bottom_image.fill(pygame.Color(border_color))

        width, height = size
        self.top_image = pygame.Surface((width - 2 * border, height - 2 * border))
        self.top_image.fill(pygame.Color(color))

        self.rect = pygame.Rect(*offset, *size)

    def activate(self):
        self.is_active = True

    def deactivate(self):
        self.is_active = False

    def update_text(self, key, pressed_keys):
        if key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        elif key < 127:
            if pressed_keys[pygame.K_RSHIFT] or pressed_keys[pygame.K_LSHIFT]:
                letter = chr(key).upper()
            else:
                letter = chr(key).lower()
            if letter.isalnum():
                self.text = self.text + letter

        if self.protected:
            self.text_label = self.font.render('*' * len(self.text), 1, (255, 255, 255))
        else:
            self.text_label = self.font.render(self.text, 1, (255, 255, 255))

    def draw(self, screen):
        screen.blit(self.bottom_image, (self.rect.x, self.rect.y))
        screen.blit(self.top_image, (self.rect.x + self.border, self.rect.y + self.border))
        screen.blit(
            self.text_label,
            (self.rect.x + 10, self.rect.y + (self.rect.height - self.text_label.get_height()) // 2)
        )


class RequestInterface(object):

    def __init__(self, websocket):

        self.websocket = websocket

        pygame.init()
        pygame.font.init()

        self.screen = pygame.display.set_mode((600, 480))
        self.background = pygame.Surface((600, 480))
        self.background.fill(pygame.Color('#111111'))
        pygame.display.set_caption('Authorization')

        self.create_objects()

    def create_objects(self):
        self.font = pygame.font.Font('./fonts/space_invaders.ttf', 24)

        self.logo = pygame.sprite.Sprite()
        self.logo.image = pygame.image.load('./images/logo.gif')

        # Why antialias make font white?
        self.username_label = self.font.render('Username', 0, (255, 255, 255))
        self.password_label = self.font.render('Password', 0, (255, 255, 255))

        self.username_area = TextArea((250, 40), (280, 240), 2, '#FFFFFF')
        self.password_area = TextArea((250, 40), (280, 310), 2, '#FFFFFF', '#111111', True)

        self.login_button = Button((110, 40), (120, 400), 'Login')
        self.register_button = Button((150, 40), (340, 400), 'Sign up')

    def draw_objects(self):
        self.screen.blit(self.background, (0, 0))

        self.register_button.draw(self.screen)
        self.login_button.draw(self.screen)
        self.username_area.draw(self.screen)
        self.password_area.draw(self.screen)

        self.screen.blit(self.username_label, (70, 250))
        self.screen.blit(self.password_label, (70, 320))
        self.screen.blit(self.logo.image, (95, 20))

        pygame.display.flip()

    def run(self):
        while True:
            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    raise KeyboardInterrupt

                elif event.type == pygame.KEYDOWN:
                    pressed_keys = pygame.key.get_pressed()
                    if self.username_area.is_active:
                        self.username_area.update_text(event.key, pressed_keys)
                    elif self.password_area.is_active:
                        self.password_area.update_text(event.key, pressed_keys)

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == MOUSE_BUTTON_LEFT:
                    pos = pygame.mouse.get_pos()
                    if self.username_area.rect.collidepoint(pos):
                        self.username_area.activate()
                        self.password_area.deactivate()
                    elif self.password_area.rect.collidepoint(pos):
                        self.password_area.activate()
                        self.username_area.deactivate()
                    elif self.login_button.rect.collidepoint(pos):
                        self.websocket.sendMessage(json.dumps({
                            'type': 'login',
                            'username': self.username_area.text,
                            'password': self.password_area.text
                        }).encode('utf8'))
                        return
                    elif self.register_button.rect.collidepoint(pos):
                        self.websocket.sendMessage(json.dumps({
                            'type': 'registration',
                            'username': self.username_area.text,
                            'password': self.password_area.text
                        }).encode('utf8'))
                        return

            self.draw_objects()
