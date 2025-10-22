# import libraries
import pygame
import random
import math

# initializing pygame
pygame.init()

# game window setup
BASE_WIDTH, BASE_HEIGHT = 400, 600
info = pygame.display.Info()
screen_width, screen_height = info.current_w, info.current_h

scale_factor = min(screen_width / BASE_WIDTH, screen_height / BASE_HEIGHT)
new_width = int(BASE_WIDTH * scale_factor)
new_height = int(BASE_HEIGHT * scale_factor)

screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
game_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))

# game variables
GRAVITY = 1
MAX_PLATFORMS = 12
SCROLL_THRESH = 200
scroll = 0
highest_y = BASE_HEIGHT  # track height

# load images
bg_image = pygame.image.load('assets/bg2.png').convert_alpha()
jumpy_image = pygame.image.load('assets/jump.png').convert_alpha()
platform_image = pygame.image.load('assets/wood.png').convert_alpha()

bg_image_scaled = pygame.transform.smoothscale(bg_image, (BASE_WIDTH, BASE_HEIGHT))

# player class
class Player():
    def __init__(self, x, y):
        self.image = pygame.transform.scale(jumpy_image, (45, 45))
        self.width = 25
        self.height = 40
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = (x, y)
        self.vel_y = 0
        self.flip = False

    def move(self):
        scroll = 0
        dx = 0
        dy = 0

        key = pygame.key.get_pressed()
        if key[pygame.K_a]:
            dx = -10
            self.flip = True
        if key[pygame.K_d]:
            dx = 10
            self.flip = False

        self.vel_y += GRAVITY
        dy += self.vel_y

        # boundary checks
        if self.rect.left + dx < 0:
            dx = -self.rect.left
        if self.rect.right + dx > BASE_WIDTH:
            dx = BASE_WIDTH - self.rect.right

        # platform collisions
        for platform in platform_group:
            if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                if self.rect.bottom < platform.rect.centery and self.vel_y > 0:
                    self.rect.bottom = platform.rect.top
                    dy = 0
                    self.vel_y = -20

        # bottom bounce (like trampoline)
        if self.rect.bottom + dy > BASE_HEIGHT:
            dy = 0
            self.vel_y = -20

        # upward scroll trigger
        if self.rect.top <= SCROLL_THRESH and self.vel_y < 0:
            scroll = -dy

        self.rect.x += dx
        self.rect.y += dy + scroll

        return scroll

    def draw(self, surface):
        surface.blit(pygame.transform.flip(self.image, self.flip, False), (self.rect.x - 12, self.rect.y - 5))


# platform base class
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width):
        super().__init__()
        self.image = pygame.transform.scale(platform_image, (width, 10))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self, scroll):
        self.rect.y += scroll
        if self.rect.top > BASE_HEIGHT:
            self.kill()


# moving platform subclass
class MovingPlatform(Platform):
    def __init__(self, x, y, width):
        super().__init__(x, y, width)
        self.speed = random.choice([1, 2])
        self.direction = random.choice([-1, 1])
        self.range = random.randint(60, 120)
        self.start_x = x
        self.move_offset = 0

    def update(self, scroll):
        super().update(scroll)
        self.move_offset += self.direction * self.speed
        if abs(self.move_offset) > self.range:
            self.direction *= -1
        self.rect.x = self.start_x + self.move_offset


# initialize player and platform group
jumpy = Player(BASE_WIDTH // 2, BASE_HEIGHT - 150)
platform_group = pygame.sprite.Group()

# create base platforms
for i in range(MAX_PLATFORMS):
    p_w = random.randint(50, 100)
    p_x = random.randint(0, BASE_WIDTH - p_w)
    p_y = BASE_HEIGHT - i * 80
    platform = Platform(p_x, p_y, p_w)
    platform_group.add(platform)

# game loop
running = True
clock = pygame.time.Clock()
FPS = 60

while running:
    clock.tick(FPS)
    scroll = jumpy.move()

    # draw background
    game_surface.blit(bg_image_scaled, (0, 0))

    # update and draw platforms
    platform_group.update(scroll)
    platform_group.draw(game_surface)

    # track player's upward progress
    if scroll > 0:
        highest_y -= scroll

    # smoother difficulty scaling
    height_progress = max(0, -highest_y // 100)
    difficulty_factor = math.log(height_progress + 1, 1.5)  # gentle logarithmic growth
    min_width = max(45, 90 - int(5 * difficulty_factor))
    max_width = max(70, 130 - int(6 * difficulty_factor))
    move_chance = min(0.12 + 0.02 * difficulty_factor, 0.35)

    # generate new platforms
    if scroll > 0:
        highest_platform_y = min([p.rect.y for p in platform_group])
        last_was_moving = False
        while len(platform_group) < MAX_PLATFORMS:
            p_w = random.randint(min_width, max_width)
            p_x = random.randint(0, BASE_WIDTH - p_w)
            p_y = highest_platform_y - random.randint(80, 120)

            # avoid consecutive moving platforms
            make_moving = random.random() < move_chance and not last_was_moving
            if make_moving:
                new_platform = MovingPlatform(p_x, p_y, p_w)
                last_was_moving = True
            else:
                new_platform = Platform(p_x, p_y, p_w)
                last_was_moving = False

            platform_group.add(new_platform)
            highest_platform_y = p_y

    # draw player
    jumpy.draw(game_surface)

    # scale and center
    scaled_surface = pygame.transform.scale(game_surface, (new_width, new_height))
    screen.blit(scaled_surface, ((screen_width - new_width) // 2, (screen_height - new_height) // 2))
    pygame.display.flip()

    # event handler
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

pygame.quit()
