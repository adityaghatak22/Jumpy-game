# --------------------------------------------
#                   JUMPY
#   Doodle Jump Style Game using Pygame
#   Author: Aditya Ghatak - 316
# --------------------------------------------

import pygame
import random

# --------------------------------------------
#   INITIALIZATION
# --------------------------------------------
pygame.init()
pygame.mixer.init()  # Initialize sound mixer

# --------------------------------------------
#   GAME WINDOW SETUP
# --------------------------------------------
BASE_WIDTH, BASE_HEIGHT = 500, 750
info = pygame.display.Info()
screen_width, screen_height = info.current_w, info.current_h

scale_factor = min(screen_width / BASE_WIDTH, screen_height / BASE_HEIGHT)
new_width = int(BASE_WIDTH * scale_factor)
new_height = int(BASE_HEIGHT * scale_factor)

screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
game_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))

# --------------------------------------------
#   GAME VARIABLES
# --------------------------------------------
BASE_GRAVITY = 0.6
MAX_GRAVITY = 1.0
current_gravity = BASE_GRAVITY

MAX_PLATFORMS = 14
SCROLL_THRESH = 250

scroll = 0
score = 0
high_score = 0
highest_y = BASE_HEIGHT
game_over = False

# Bird spawn control
last_bird_spawn_time = 0
BIRD_SPAWN_DELAY = 5000  # 5 seconds

# --------------------------------------------
#   LOAD IMAGES & ASSETS
# --------------------------------------------
bg_image = pygame.image.load('assets/bg2.png').convert_alpha()
jumpy_image = pygame.image.load('assets/jump.png').convert_alpha()
platform_image = pygame.image.load('assets/wood.png').convert_alpha()
bird_image = pygame.image.load('assets/bird.png').convert_alpha()
spring_image = pygame.image.load('assets/spring.png').convert_alpha()

bg_image_scaled = pygame.transform.scale(bg_image, (BASE_WIDTH, BASE_HEIGHT))

# --------------------------------------------
#   LOAD SOUNDS
# --------------------------------------------
pygame.mixer.music.load('assets/bgmusic.mp3')  
pygame.mixer.music.set_volume(0.4)

spring_sound = pygame.mixer.Sound('assets/spring.wav')
spring_sound.set_volume(0.7)

jump_sound = pygame.mixer.Sound('assets/jump.wav')
jump_sound.set_volume(0.6)

death_sound = pygame.mixer.Sound('assets/death.wav')
death_sound.set_volume(0.7)

# Start background music loop
pygame.mixer.music.play(-1)

# --------------------------------------------
#   FONTS
# --------------------------------------------
font = pygame.font.SysFont('arial', 50, bold=True)

# --------------------------------------------
#   LOAD HIGH SCORE
# --------------------------------------------
try:
    with open("highscore.txt", "r") as f:
        high_score = int(f.read().strip())
except:
    high_score = 0


# --------------------------------------------
#   PLAYER CLASS
# --------------------------------------------
class Player():
    def __init__(self, x, y):
        self.image = pygame.transform.scale(jumpy_image, (50, 50))
        self.width = 30
        self.height = 45
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = (x, y)
        self.vel_y = 0
        self.flip = False
        self.last_platform = None

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

        global current_gravity
        self.vel_y += current_gravity
        dy += self.vel_y

        # boundary checks
        if self.rect.left + dx < 0:
            dx = -self.rect.left
        if self.rect.right + dx > BASE_WIDTH:
            dx = BASE_WIDTH - self.rect.right

        global score
        platform_bounced = False

        for platform in platform_group:
            if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                if self.rect.bottom < platform.rect.centery and self.vel_y > 0:
                    self.rect.bottom = platform.rect.top
                    dy = 0
                    self.vel_y = -20
                    platform_bounced = True
                    if self.last_platform != platform:
                        score += 10
                        self.last_platform = platform
                        jump_sound.play()

        # Spring collision (+50 points)
        for spring in spring_group:
            if spring.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                if self.rect.bottom < spring.rect.centery and self.vel_y > 0:
                    self.rect.bottom = spring.rect.top + 5
                    dy = 0
                    self.vel_y = -30
                    score += 50
                    spring_sound.play()

        if self.rect.top <= SCROLL_THRESH and self.vel_y < 0:
            scroll = -dy

        self.rect.x += dx
        self.rect.y += dy + scroll
        return scroll

    def draw(self, surface):
        surface.blit(
            pygame.transform.flip(self.image, self.flip, False),
            (self.rect.x - 12, self.rect.y - 5)
        )


# --------------------------------------------
#   PLATFORM CLASSES
# --------------------------------------------
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


# --------------------------------------------
#   SPRING CLASS
# --------------------------------------------
class Spring(pygame.sprite.Sprite):
    def __init__(self, platform):
        super().__init__()
        self.image = pygame.transform.scale(spring_image, (30, 25))
        self.rect = self.image.get_rect()
        self.rect.centerx = platform.rect.centerx
        self.rect.bottom = platform.rect.top + 5
        self.platform = platform

    def update(self, scroll):
        self.rect.y += scroll
        if self.platform.alive():
            self.rect.bottom = self.platform.rect.top + 5
        else:
            self.kill()


# --------------------------------------------
#   BIRD CLASS
# --------------------------------------------
class Bird(pygame.sprite.Sprite):
    def __init__(self, y):
        super().__init__()
        size = random.randint(45, 60)
        self.image = pygame.transform.scale(bird_image, (size, size))
        self.rect = self.image.get_rect()
        self.rect.y = y
        self.rect.x = random.choice([-size, BASE_WIDTH + size])
        self.speed = random.choice([4, 5]) * (1 if self.rect.x < 0 else -1)

    def update(self, scroll):
        self.rect.x += self.speed
        self.rect.y += scroll
        if self.rect.right < -50 or self.rect.left > BASE_WIDTH + 50:
            self.kill()


# --------------------------------------------
#   FUNCTIONS
# --------------------------------------------
def reset_game():
    global platform_group, bird_group, spring_group, jumpy, scroll, score, highest_y, current_gravity, game_over, last_bird_spawn_time

    platform_group.empty()
    bird_group.empty()
    spring_group.empty()
    score = 0
    highest_y = BASE_HEIGHT
    scroll = 0
    current_gravity = BASE_GRAVITY
    game_over = False
    last_bird_spawn_time = pygame.time.get_ticks()

    jumpy.rect.center = (BASE_WIDTH // 2, BASE_HEIGHT - 200)
    jumpy.vel_y = 0
    jumpy.last_platform = None

    # Restart background music
    pygame.mixer.music.play(-1)

    # starting platform
    start_width = 100
    start_x = (BASE_WIDTH - start_width) // 2
    start_y = BASE_HEIGHT - 40
    starting_platform = Platform(start_x, start_y, start_width)
    platform_group.add(starting_platform)

    # generate initial platforms
    for i in range(1, MAX_PLATFORMS):
        p_w = random.randint(60, 110)
        margin = 40
        p_x = random.randint(margin, BASE_WIDTH - p_w - margin)
        p_y = start_y - i * 85
        platform = Platform(p_x, p_y, p_w)
        platform_group.add(platform)

        #  spring spawn chance
        if random.random() < 0.1:
            spring = Spring(platform)
            spring_group.add(spring)


# --------------------------------------------
#   INITIALIZE OBJECTS
# --------------------------------------------
jumpy = Player(BASE_WIDTH // 2, BASE_HEIGHT - 200)
platform_group = pygame.sprite.Group()
bird_group = pygame.sprite.Group()
spring_group = pygame.sprite.Group()
reset_game()

# --------------------------------------------
#   MAIN GAME LOOP
# --------------------------------------------
running = True
clock = pygame.time.Clock()
FPS = 60
last_was_moving = False

while running:
    clock.tick(FPS)

    if not game_over:
        # --- Player Movement ---
        scroll = jumpy.move()

        # --- Gravity Progression ---
        progress = min(score / 1000, 1.0)
        current_gravity = BASE_GRAVITY + (MAX_GRAVITY - BASE_GRAVITY) * progress

        # --- Draw Background ---
        game_surface.blit(bg_image_scaled, (0, 0))

        # --- Platforms ---
        platform_group.update(scroll)
        platform_group.draw(game_surface)

        # --- Springs ---
        spring_group.update(scroll)
        spring_group.draw(game_surface)

        # --- Bird Spawn ---
        current_time = pygame.time.get_ticks()
        if score > 200 and len(bird_group) < 2 and current_time - last_bird_spawn_time > BIRD_SPAWN_DELAY:
            y = random.randint(50, 150)
            bird = Bird(y)
            bird_group.add(bird)
            last_bird_spawn_time = current_time

        # --- Birds ---
        bird_group.update(scroll)
        bird_group.draw(game_surface)

        # --- Platform Generation ---
        if scroll > 0:
            highest_y -= scroll
            highest_platform_y = min([p.rect.y for p in platform_group], default=BASE_HEIGHT)

            while len(platform_group) < MAX_PLATFORMS:
                min_width = 110 - int(50 * progress)
                p_w = random.randint(min_width, 110)
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

                #  10% spring spawn chance
                if random.random() < 0.1:
                    spring = Spring(new_platform)
                    spring_group.add(spring)

        # --- Player ---
        jumpy.draw(game_surface)

        # --- Collision Check with Bird ---
        if pygame.sprite.spritecollide(jumpy, bird_group, False):
            game_over = True
            pygame.mixer.music.stop()
            death_sound.play()  

        # --- Draw Everything on Screen ---
        scaled_surface = pygame.transform.scale(game_surface, (new_width, new_height))
        screen.blit(scaled_surface, ((screen_width - new_width) // 2, (screen_height - new_height) // 2))

        side_padding = (screen_width - new_width) // 2
        pygame.draw.rect(screen, (0, 0, 0), (screen_width - side_padding, 0, side_padding, screen_height))

        # --- Score Display ---
        score_text = font.render(f"Score: {score}", True, (255, 255, 255))
        high_text = font.render(f"High Score: {high_score}", True, (255, 215, 0))

        right_bar_x = screen_width - side_padding + 40
        score_y = 80
        high_y = score_y + score_text.get_height() + 15

        screen.blit(score_text, (right_bar_x, score_y))
        screen.blit(high_text, (right_bar_x, high_y))

        # --- Game Over Condition ---
        if jumpy.rect.top > BASE_HEIGHT:
            game_over = True
            pygame.mixer.music.stop()
            death_sound.play()  
            if score > high_score:
                high_score = score
                with open("highscore.txt", "w") as f:
                    f.write(str(high_score))

    else:
        # --- Game Over Screen ---
        game_surface.blit(bg_image_scaled, (0, 0))
        over_text = font.render("GAME OVER", True, (255, 0, 0))
        restart_text = font.render("Press SPACE to Restart", True, (255, 255, 255))

        game_surface.blit(over_text, (BASE_WIDTH // 2 - over_text.get_width() // 2, 300))
        game_surface.blit(restart_text, (BASE_WIDTH // 2 - restart_text.get_width() // 2, 400))

        scaled_surface = pygame.transform.scale(game_surface, (new_width, new_height))
        screen.blit(scaled_surface, ((screen_width - new_width) // 2, (screen_height - new_height) // 2))

    pygame.display.flip()

    # ----------------------------------------
    #   EVENT HANDLING
    # ----------------------------------------
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_SPACE and game_over:
                reset_game()
        if event.type == pygame.QUIT:
            running = False

# --------------------------------------------
#   QUIT GAME
# --------------------------------------------
pygame.quit()
