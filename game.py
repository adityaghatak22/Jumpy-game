# --import libraries--
import pygame
import random

# --initialize pygame--
pygame.init()

# --game window setup--
BASE_WIDTH, BASE_HEIGHT = 500, 750
info = pygame.display.Info()
screen_width, screen_height = info.current_w, info.current_h

scale_factor = min(screen_width / BASE_WIDTH, screen_height / BASE_HEIGHT)
new_width = int(BASE_WIDTH * scale_factor)
new_height = int(BASE_HEIGHT * scale_factor)

screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
game_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))

# --game variables--
GRAVITY = 1
MAX_PLATFORMS = 14
SCROLL_THRESH = 250
game_over = False
scroll = 0
score = 0
high_score = 0
highest_y = BASE_HEIGHT

# --load images--
bg_image = pygame.image.load('assets/bg2.png').convert_alpha()
jumpy_image = pygame.image.load('assets/jump.png').convert_alpha()
platform_image = pygame.image.load('assets/wood.png').convert_alpha()
bg_image_scaled = pygame.transform.scale(bg_image, (BASE_WIDTH, BASE_HEIGHT))

# --fonts--
font = pygame.font.SysFont('arial', 28, bold=True)

# --load high score--
try:
    with open("highscore.txt", "r") as f:
        high_score = int(f.read().strip())
except:
    high_score = 0


# --player class--
class Player():
    def __init__(self, x, y):
        self.image = pygame.transform.scale(jumpy_image, (50, 50))
        self.width = 30
        self.height = 45
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = (x, y)
        self.vel_y = 0
        self.flip = False
        self.last_platform = None  # track last landed platform

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

        # gravity
        self.vel_y += GRAVITY
        dy += self.vel_y

        # boundary checks
        if self.rect.left + dx < 0:
            dx = -self.rect.left
        if self.rect.right + dx > BASE_WIDTH:
            dx = BASE_WIDTH - self.rect.right

        # platform collisions
        global score
        for platform in platform_group:
            if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                if self.rect.bottom < platform.rect.centery and self.vel_y > 0:
                    self.rect.bottom = platform.rect.top
                    dy = 0
                    self.vel_y = -20

                    # add score when landing on a *new* platform
                    if self.last_platform != platform:
                        score += 10
                        self.last_platform = platform

        # upward scroll
        if self.rect.top <= SCROLL_THRESH and self.vel_y < 0:
            scroll = -dy

        self.rect.x += dx
        self.rect.y += dy + scroll

        return scroll

    def draw(self, surface):
        surface.blit(pygame.transform.flip(self.image, self.flip, False),
                     (self.rect.x - 12, self.rect.y - 5))


# --platform classes--
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width):
        super().__init__()
        self.image = pygame.transform.scale(platform_image, (width, 12))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self, scroll):
        self.rect.y += scroll
        if self.rect.top > BASE_HEIGHT:
            self.kill()


class MovingPlatform(Platform):
    def __init__(self, x, y, width):
        super().__init__(x, y, width)
        self.speed = random.choice([1, 2])
        self.direction = random.choice([-1, 1])
        max_left = self.rect.x
        max_right = BASE_WIDTH - self.rect.width
        self.min_x = max(0, max_left - random.randint(40, 80))
        self.max_x = min(max_right, max_left + random.randint(40, 80))

    def update(self, scroll):
        super().update(scroll)
        self.rect.x += self.direction * self.speed
        if self.rect.x <= self.min_x or self.rect.x >= self.max_x:
            self.direction *= -1


# --functions--
def reset_game():
    global platform_group, jumpy, scroll, score, highest_y, game_over
    platform_group.empty()
    score = 0
    highest_y = BASE_HEIGHT
    scroll = 0
    game_over = False

    jumpy.rect.center = (BASE_WIDTH // 2, BASE_HEIGHT - 200)
    jumpy.vel_y = 0
    jumpy.last_platform = None

    start_width = 100
    start_x = (BASE_WIDTH - start_width) // 2
    start_y = BASE_HEIGHT - 40
    starting_platform = Platform(start_x, start_y, start_width)
    platform_group.add(starting_platform)

    for i in range(1, MAX_PLATFORMS):
        p_w = random.randint(60, 110)
        margin = 40
        p_x = random.randint(margin, BASE_WIDTH - p_w - margin)
        p_y = start_y - i * 85
        platform = Platform(p_x, p_y, p_w)
        platform_group.add(platform)


# --initialize player and platform group--
jumpy = Player(BASE_WIDTH // 2, BASE_HEIGHT - 200)
platform_group = pygame.sprite.Group()
reset_game()

# --game loop--
running = True
clock = pygame.time.Clock()
FPS = 60
last_was_moving = False

while running:
    clock.tick(FPS)

    if not game_over:
        scroll = jumpy.move()
        game_surface.blit(bg_image_scaled, (0, 0))
        platform_group.update(scroll)
        platform_group.draw(game_surface)

        # generate new platforms when scrolling upward
        if scroll > 0:
            highest_y -= scroll
            highest_platform_y = min([p.rect.y for p in platform_group], default=BASE_HEIGHT)
            while len(platform_group) < MAX_PLATFORMS:
                p_w = random.randint(60, 110)
                margin = 40
                p_x = random.randint(margin, BASE_WIDTH - p_w - margin)
                p_y = highest_platform_y - random.randint(90, 130)
                make_moving = random.random() < 0.1 and not last_was_moving
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

        # draw scores
        score_text = font.render(f"Score: {score}", True, (255, 255, 255))
        high_text = font.render(f"High Score: {high_score}", True, (255, 215, 0))
        game_surface.blit(score_text, (20, 20))
        game_surface.blit(high_text, (BASE_WIDTH - high_text.get_width() - 20, 20))

        # check for game over
        if jumpy.rect.top > BASE_HEIGHT:
            game_over = True

            # update high score if beaten
            if score > high_score:
                high_score = score
                with open("highscore.txt", "w") as f:
                    f.write(str(high_score))

    else:
        game_surface.blit(bg_image_scaled, (0, 0))
        game_over_text = font.render("GAME OVER", True, (255, 80, 80))
        score_text = font.render(f"Score: {score}", True, (255, 255, 255))
        high_text = font.render(f"High Score: {high_score}", True, (255, 215, 0))
        restart_text = font.render("Press SPACE to Restart", True, (255, 255, 255))

        game_surface.blit(game_over_text, (BASE_WIDTH // 2 - game_over_text.get_width() // 2, BASE_HEIGHT // 2 - 80))
        game_surface.blit(score_text, (BASE_WIDTH // 2 - score_text.get_width() // 2, BASE_HEIGHT // 2 - 20))
        game_surface.blit(high_text, (BASE_WIDTH // 2 - high_text.get_width() // 2, BASE_HEIGHT // 2 + 20))
        game_surface.blit(restart_text, (BASE_WIDTH // 2 - restart_text.get_width() // 2, BASE_HEIGHT // 2 + 80))

        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            reset_game()

    # draw final surface
    scaled_surface = pygame.transform.scale(game_surface, (new_width, new_height))
    screen.blit(scaled_surface, ((screen_width - new_width) // 2, (screen_height - new_height) // 2))
    pygame.display.flip()

    # event handling
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
        if event.type == pygame.QUIT:
            running = False

pygame.quit()
