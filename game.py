#import libraries
import pygame
import random

#initializing pygame
pygame.init()

#game window
BASE_WIDTH, BASE_HEIGHT = 400, 600
info = pygame.display.Info()
#fetches the monitor resolution
screen_width, screen_height = info.current_w, info.current_h     

scale_factor = min(screen_width / BASE_WIDTH, screen_height / BASE_HEIGHT)
new_width = int(BASE_WIDTH * scale_factor)
new_height = int(BASE_HEIGHT * scale_factor)

#creates a background fullscreen and the actual game window surface in 2:3
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
game_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))                                    

#game variables
GRAVITY = 1
MAX_PLATFORMS = 10

# Load images
bg_image = pygame.image.load('assets/bg2.png').convert_alpha()
jumpy_image = pygame.image.load('assets/jump.png').convert_alpha()
platform_image = pygame.image.load('assets/wood.png').convert_alpha()

# Scale background to game surface
bg_image_scaled = pygame.transform.smoothscale(bg_image, (BASE_WIDTH, BASE_HEIGHT))

# Player class
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
		#reset variables
		dx = 0
		dy = 0

		#process keypresses
		key = pygame.key.get_pressed()
		if key[pygame.K_a]:
			dx = -10
			self.flip = True
		if key[pygame.K_d]:
			dx = 10
			self.flip = False

		#gravity
		self.vel_y += GRAVITY
		dy += self.vel_y

		#ensure player doesn't go off the edge of the screen
		if self.rect.left + dx < 0:
			dx = -self.rect.left
		if self.rect.right + dx > BASE_WIDTH:
			dx = BASE_WIDTH - self.rect.right

		#check collision with platforms
		for platform in platform_group:
			if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
				if self.rect.bottom < platform.rect.centery and self.vel_y > 0:
					self.rect.bottom = platform.rect.top
					dy = 0
					self.vel_y = -20  # automatic jump

		#check collision with ground
		if self.rect.bottom + dy > BASE_HEIGHT:
			dy = 0
			self.vel_y = -20  # automatic jump

		#update rectangle position
		self.rect.x += dx
		self.rect.y += dy

	def draw(self, surface):
		surface.blit(pygame.transform.flip(self.image, self.flip, False), (self.rect.x - 12, self.rect.y - 5))
		# Optional rectangle for debugging
		# pygame.draw.rect(surface, (255, 255, 255), self.rect, 2)

# Platform class
class Platform(pygame.sprite.Sprite):
	def __init__(self, x, y, width):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.transform.scale(platform_image, (width, 10))
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y

# Initialize player at center-bottom
jumpy = Player(BASE_WIDTH // 2, BASE_HEIGHT - 150)

# Create sprite group
platform_group = pygame.sprite.Group()

# Create temporary platforms
for p in range(MAX_PLATFORMS):
	p_w = random.randint(40, 60)
	p_x = random.randint(0, BASE_WIDTH - p_w)
	p_y = p * random.randint(80, 120)
	platform = Platform(p_x, p_y, p_w)
	platform_group.add(platform)

# Game loop
running = True
clock = pygame.time.Clock()
FPS = 60

while running:
	clock.tick(FPS)

	# Move player
	jumpy.move()

	# Draw background onto game surface
	game_surface.blit(bg_image_scaled, (0, 0))

	# Draw platforms on game surface
	platform_group.draw(game_surface)

	# Draw the player on game surface
	jumpy.draw(game_surface)

	# Scale and center the game surface for fullscreen
	scaled_surface = pygame.transform.scale(game_surface, (new_width, new_height))
	screen.blit(scaled_surface, ((screen_width - new_width) // 2, (screen_height - new_height) // 2))

	# Update display
	pygame.display.flip()

	# Event handler
	for event in pygame.event.get():
		if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
			running = False  # Exit on pressing ESC key

pygame.quit()
