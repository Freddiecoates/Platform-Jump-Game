import pygame
import sys
import random
import math

# Initialize Pygame and Mixer
pygame.init()
pygame.mixer.init()

# Constants
WIDTH, HEIGHT = 1000, 600
FPS = 60
GRAVITY = 0.8
PLAYER_SPEED = 6
JUMP_POWER = -18
ENEMY_SPEED = 2
SCROLL_THRESH = 300
GROUND_HEIGHT = 60
BULLET_SPEED = 10
ENEMY_FIRE_RATE = 2000
PLAYER_FIRE_RATE = 500

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)


# Asset Loading Function
def load_image(path, scale=1, size=None):
    image = pygame.image.load(path).convert_alpha()
    if size:
        image = pygame.transform.scale(image, size)
    elif scale != 1:
        new_size = (int(image.get_width() * scale), int(image.get_height() * scale))
        image = pygame.transform.scale(image, new_size)
    return image


# Projectile Class
class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y, is_player_shot=True):
        super().__init__()
        self.image = pygame.Surface((8, 8))
        self.image.fill((255, 255, 0) if is_player_shot else (255, 0, 0))
        self.rect = self.image.get_rect(center=(x, y))
        self.is_player_shot = is_player_shot

        dx = target_x - x
        dy = target_y - y
        distance = math.hypot(dx, dy)
        if distance == 0:
            self.dx = 0
            self.dy = 0
        else:
            self.dx = dx / distance
            self.dy = dy / distance

    def update(self, *args, **kwargs):
        self.rect.x += self.dx * BULLET_SPEED
        self.rect.y += self.dy * BULLET_SPEED
        if not pygame.Rect(-100, -100, WIDTH + 200, HEIGHT + 200).colliderect(self.rect):
            self.kill()


# Player Class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.load_animations()
        self.frame_index = 0
        self.image = self.animations['idle'][self.frame_index]
        self.rect = self.image.get_rect(midbottom=(100, HEIGHT - GROUND_HEIGHT))
        self.direction = 1
        self.velocity_y = 0
        self.on_ground = True
        self.invincible = False
        self.health = 100
        self.score = 0
        self.animation_speed = 0.15
        self.status = 'idle'
        self.last_shot = 0

    def load_animations(self):
        self.animations = {
            'idle': [load_image('assets/player/idle.png', scale=1.0)],
            'run': [
                load_image('assets/player/run1.png', scale=1.0),
                load_image('assets/player/run2.png', scale=1.0)
            ],
            'jump': [load_image('assets/player/jump.png', scale=1.0)]
        }

    def animate(self):
        animation = self.animations[self.status]
        self.frame_index += self.animation_speed
        if self.frame_index >= len(animation):
            self.frame_index = 0
        self.image = animation[int(self.frame_index)]
        self.image = pygame.transform.flip(self.image, self.direction < 0, False)

    def move(self):
        keys = pygame.key.get_pressed()
        dx = 0

        if keys[pygame.K_LEFT]:
            dx = -PLAYER_SPEED
            self.direction = -1
            self.status = 'run' if self.on_ground else 'jump'
        elif keys[pygame.K_RIGHT]:
            dx = PLAYER_SPEED
            self.direction = 1
            self.status = 'run' if self.on_ground else 'jump'
        else:
            self.status = 'idle' if self.on_ground else 'jump'

        if keys[pygame.K_SPACE] and self.on_ground:
            self.jump()

        self.rect.x += dx
        self.rect.y += self.velocity_y
        self.velocity_y += GRAVITY

    def jump(self):
        self.velocity_y = JUMP_POWER
        self.on_ground = False
        self.status = 'jump'
        jump_sound.play()

    def take_damage(self, damage=20):
        if not self.invincible:
            self.health -= damage
            self.invincible = True
            pygame.time.set_timer(pygame.USEREVENT, 2000)

    def handle_shooting(self, game):
        now = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()

        if keys[pygame.K_DOWN] and now - self.last_shot > PLAYER_FIRE_RATE:
            bullet_x = self.rect.centerx + (20 * self.direction)
            bullet_y = self.rect.centery
            target_x = bullet_x + (1000 * self.direction)
            target_y = bullet_y
            bullet = Projectile(bullet_x, bullet_y, target_x, target_y)
            game.player_bullets.add(bullet)
            game.all_sprites.add(bullet)
            shoot_sound.play()
            self.last_shot = now

    def update(self, game):
        self.move()
        self.animate()
        self.check_boundaries()
        self.handle_shooting(game)

    def check_boundaries(self):
        if self.rect.bottom > HEIGHT - GROUND_HEIGHT:
            self.rect.bottom = HEIGHT - GROUND_HEIGHT
            self.on_ground = True
            self.velocity_y = 0


# Enemy Class
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, player):
        super().__init__()
        self.frames = [
            load_image('assets/enemy/walk1.png', scale=1.0),
            load_image('assets/enemy/walk2.png', scale=1.0)
        ]
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.direction = 1
        self.animation_speed = 0.1
        self.player = player
        self.last_shot = random.randint(0, ENEMY_FIRE_RATE)

    def update(self, game):
        self.animate()
        if self.rect.x < self.player.rect.x:
            self.direction = 1
        else:
            self.direction = -1
        self.rect.x += ENEMY_SPEED * self.direction
        self.handle_shooting(game)

    def animate(self):
        self.frame_index += self.animation_speed
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        self.image = self.frames[int(self.frame_index)]
        self.image = pygame.transform.flip(self.image, self.direction > 0, False)

    def handle_shooting(self, game):
        now = pygame.time.get_ticks()
        if now - self.last_shot > ENEMY_FIRE_RATE:
            bullet = Projectile(self.rect.centerx, self.rect.centery,
                                *self.player.rect.center, is_player_shot=False)
            game.enemy_bullets.add(bullet)
            game.all_sprites.add(bullet)
            shoot_sound.play()
            self.last_shot = now


# Coin Class
class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.frames = [
            load_image('assets/coin/spin1.png', scale=0.3),
            load_image('assets/coin/spin2.png', scale=0.3),
            load_image('assets/coin/spin3.png', scale=0.3)
        ]
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.animation_speed = 0.2

    def animate(self):
        self.frame_index += self.animation_speed
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        self.image = self.frames[int(self.frame_index)]

    def update(self, *args, **kwargs):
        self.animate()


# Platform Class
class Platform(pygame.sprite.Sprite):
    def __init__(self, image, rect):
        super().__init__()
        self.image = image
        self.rect = rect

    def update(self, *args, **kwargs):
        pass


# FinishLine Class
class FinishLine(pygame.sprite.Sprite):
    def __init__(self, x):
        super().__init__()
        self.image = pygame.Surface((20, HEIGHT - GROUND_HEIGHT))
        self.image.fill((255, 215, 0))
        self.rect = self.image.get_rect(bottomleft=(x, HEIGHT - GROUND_HEIGHT))

    def update(self, *args, **kwargs):
        pass


# Game Class
class Game:
    current_level_width = 3000

    def __init__(self, level_config):
        self.ground_tile = load_image('assets/ground.png')
        self.level_width = level_config['level_width']
        Game.current_level_width = self.level_width
        self.elevated_platform_data = level_config['elevated_platforms']
        self.enemy_count = level_config['enemy_count']

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Platformer Game")
        self.clock = pygame.time.Clock()
        self.bg_image = load_image('assets/background.png', size=(WIDTH, HEIGHT))

        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.elevated_platforms = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.finish_line_group = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()

        self.player = Player()
        self.all_sprites.add(self.player)
        self.generate_level()

        self.scroll = 0
        self.max_scroll = self.level_width - WIDTH

    def create_tiled_platform(self, width, height):
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        tile_width = self.ground_tile.get_width()
        tile_height = self.ground_tile.get_height()
        for x in range(0, width, tile_width):
            for y in range(0, height, tile_height):
                surface.blit(self.ground_tile, (x, y))
        return surface

    def generate_level(self):
        ground_tile_width = 100
        for x in range(0, self.level_width, ground_tile_width):
            platform_image = self.create_tiled_platform(ground_tile_width, GROUND_HEIGHT)
            rect = platform_image.get_rect(topleft=(x, HEIGHT - GROUND_HEIGHT))
            platform = Platform(platform_image, rect)
            self.platforms.add(platform)
            self.all_sprites.add(platform)

        for data in self.elevated_platform_data:
            x, y, width, height = data
            platform_image = self.create_tiled_platform(width, height)
            rect = platform_image.get_rect(topleft=(x, y))
            platform = Platform(platform_image, rect)
            self.elevated_platforms.add(platform)
            self.all_sprites.add(platform)

        for _ in range(self.enemy_count):
            enemy_x = random.randint(500, self.level_width - 500)
            enemy = Enemy(enemy_x, HEIGHT - GROUND_HEIGHT, self.player)
            self.enemies.add(enemy)
            self.all_sprites.add(enemy)

        for platform in self.elevated_platforms:
            coin_x = platform.rect.x + random.randint(20, max(20, platform.rect.width - 20))
            coin_y = platform.rect.y
            coin = Coin(coin_x, coin_y)
            self.coins.add(coin)
            self.all_sprites.add(coin)

        finish_line_x = self.level_width - 50
        finish_line = FinishLine(finish_line_x)
        self.finish_line_group.add(finish_line)
        self.all_sprites.add(finish_line)

    def scroll_screen(self):
        if self.player.rect.right > WIDTH - SCROLL_THRESH:
            self.scroll = min(self.player.rect.right - (WIDTH - SCROLL_THRESH), self.max_scroll)
        elif self.player.rect.left < SCROLL_THRESH:
            self.scroll = max(self.player.rect.left - SCROLL_THRESH, 0)

    def draw_hud(self):
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {self.player.score}", True, WHITE)
        self.screen.blit(score_text, (20, 60))

        bar_position = (20, 20)
        bar_size = (200, 20)
        pygame.draw.rect(self.screen, WHITE, (*bar_position, *bar_size), 2)
        health_width = (self.player.health / 100) * (bar_size[0] - 4)
        pygame.draw.rect(self.screen, RED, (bar_position[0] + 2, bar_position[1] + 2, health_width, bar_size[1] - 4))

    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.USEREVENT:
                    self.player.invincible = False

            self.all_sprites.update(self)
            self.scroll_screen()

            platform_hits = pygame.sprite.spritecollide(self.player, self.elevated_platforms, False)
            if platform_hits:
                if self.player.velocity_y > 0 and self.player.rect.bottom <= platform_hits[0].rect.bottom:
                    self.player.rect.bottom = platform_hits[0].rect.top
                    self.player.velocity_y = 0
                    self.player.on_ground = True

            coin_hits = pygame.sprite.spritecollide(self.player, self.coins, True)
            if coin_hits:
                coin_sound.play()
                self.player.score += 10 * len(coin_hits)

            enemy_hits = pygame.sprite.spritecollide(self.player, self.enemies, False)
            if enemy_hits:
                self.player.take_damage()

            for bullet in self.player_bullets:
                enemy_hits = pygame.sprite.spritecollide(bullet, self.enemies, True)
                if enemy_hits:
                    hit_sound.play()
                    self.player.score += 50
                    bullet.kill()

            for bullet in self.enemy_bullets:
                if pygame.sprite.collide_rect(bullet, self.player):
                    self.player.take_damage(10)
                    hit_sound.play()
                    bullet.kill()

            if pygame.sprite.spritecollide(self.player, self.finish_line_group, False):
                self.level_complete()
                return

            self.screen.blit(self.bg_image, (0, 0))

            for platform in self.platforms:
                if platform.rect.right - self.scroll > 0 and platform.rect.left - self.scroll < WIDTH:
                    self.screen.blit(platform.image, (platform.rect.x - self.scroll, platform.rect.y))

            for platform in self.elevated_platforms:
                if platform.rect.right - self.scroll > 0 and platform.rect.left - self.scroll < WIDTH:
                    self.screen.blit(platform.image, (platform.rect.x - self.scroll, platform.rect.y))

            for sprite in self.enemies:
                self.screen.blit(sprite.image, (sprite.rect.x - self.scroll, sprite.rect.y))
            for sprite in self.coins:
                self.screen.blit(sprite.image, (sprite.rect.x - self.scroll, sprite.rect.y))
            for bullet in self.player_bullets:
                self.screen.blit(bullet.image, (bullet.rect.x - self.scroll, bullet.rect.y))
            for bullet in self.enemy_bullets:
                self.screen.blit(bullet.image, (bullet.rect.x - self.scroll, bullet.rect.y))
            for sprite in self.finish_line_group:
                self.screen.blit(sprite.image, (sprite.rect.x - self.scroll, sprite.rect.y))

            self.screen.blit(self.player.image, (self.player.rect.x - self.scroll, self.player.rect.y))
            self.draw_hud()
            pygame.display.update()

            if self.player.health <= 0:
                self.game_over()
                return

    def level_complete(self):
        font = pygame.font.Font(None, 74)
        text = font.render("LEVEL COMPLETE!", True, WHITE)
        self.screen.blit(text, (WIDTH // 2 - 200, HEIGHT // 2 - 50))
        pygame.display.flip()
        pygame.time.wait(3000)

    def game_over(self):
        game_over_sound.play()
        font = pygame.font.Font(None, 74)
        text = font.render("GAME OVER", True, WHITE)
        self.screen.blit(text, (WIDTH // 2 - 140, HEIGHT // 2))
        pygame.display.flip()
        pygame.time.wait(3000)


# Main Menu
def main_menu():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Platformer Game - Main Menu")
    clock = pygame.time.Clock()

    try:
        bg_image = load_image('assets/background.png', size=(WIDTH, HEIGHT))
    except Exception:
        bg_image = pygame.Surface((WIDTH, HEIGHT))
        bg_image.fill(BLACK)

    font_large = pygame.font.Font(None, 74)
    font_small = pygame.font.Font(None, 36)

    button_width = 200
    button_height = 50
    level1_button = pygame.Rect(WIDTH // 2 - button_width - 20, HEIGHT // 2, button_width, button_height)
    level2_button = pygame.Rect(WIDTH // 2 + 20, HEIGHT // 2, button_width, button_height)

    menu_running = True
    level_choice = None

    while menu_running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                if level1_button.collidepoint(mouse_pos):
                    level_choice = 1
                    menu_running = False
                elif level2_button.collidepoint(mouse_pos):
                    level_choice = 2
                    menu_running = False

        screen.blit(bg_image, (0, 0))
        title = font_large.render("Platformer Game", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 3 - 50))

        pygame.draw.rect(screen, GREEN, level1_button)
        pygame.draw.rect(screen, GREEN, level2_button)

        level1_text = font_small.render("Level 1", True, BLACK)
        level2_text = font_small.render("Level 2", True, BLACK)
        screen.blit(level1_text, (level1_button.centerx - level1_text.get_width() // 2,
                                  level1_button.centery - level1_text.get_height() // 2))
        screen.blit(level2_text, (level2_button.centerx - level2_text.get_width() // 2,
                                  level2_button.centery - level2_text.get_height() // 2))

        pygame.display.update()

    return level_choice


# Sound Loading
jump_sound = pygame.mixer.Sound('assets/sounds/jump.wav')
coin_sound = pygame.mixer.Sound('assets/sounds/coin.wav')
game_over_sound = pygame.mixer.Sound('assets/sounds/game_over.wav')
shoot_sound = pygame.mixer.Sound('assets/sounds/shoot.wav')
hit_sound = pygame.mixer.Sound('assets/sounds/hit.wav')

# Level Configurations
level_configs = {
    1: {
        'level_width': 3000,
        'elevated_platforms': [
            (500, HEIGHT - 200, 200, 20),
            (750, HEIGHT - 250, 150, 20),
            (950, HEIGHT - 300, 200, 20),
            (1200, HEIGHT - 250, 150, 20)
        ],
        'enemy_count': 5
    },
    2: {
        'level_width': 4000,
        'elevated_platforms': [
            (600, HEIGHT - 250, 180, 20),
            (850, HEIGHT - 300, 150, 20),
            (1050, HEIGHT - 350, 200, 20),
            (1300, HEIGHT - 300, 150, 20)
        ],
        'enemy_count': 10
    }
}

# Main Program
if __name__ == "__main__":
    while True:
        level_choice = main_menu()
        if level_choice is None:
            break
        config = level_configs.get(level_choice, level_configs[1])
        game = Game(config)
        game.run()