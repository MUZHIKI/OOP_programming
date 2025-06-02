from settings import *
import pygame
from pathlib import Path

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, collision_sprites, hurt_sound):
        super().__init__(groups)
        self.load_images()
        self.state, self.frame_index = 'right', 0
        self.image = pygame.image.load(BASE_DIR / 'images' / 'player' / 'down' / '0.png').convert_alpha()
        self.rect = self.image.get_rect(center=pos)
        self.hitbox_rect = self.rect.inflate(-60, -90)

        self.direction = pygame.Vector2()
        self.speed = 500
        self.collision_sprites = collision_sprites

        # Добавляем жизни
        self.health = 3  # Начальное количество жизней
        self.max_health = 3
        self.last_hit_time = 0  # Время последнего удара

        # Звук при потере сердца
        self.hurt_sound = hurt_sound

    def take_damage(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_hit_time > 3000:  # Урон раз в 3 секунды
            self.health -= 1
            self.last_hit_time = current_time
            self.hurt_sound.play()  # Воспроизводим звук при потере сердца
            if self.health <= 0:
                self.kill()  # Уничтожаем персонажа, если жизни закончились

    def load_images(self):
        self.frames = {'left': [], 'right': [], 'up': [], 'down': []}

        for state in self.frames.keys():
            folder_path = BASE_DIR / 'images' / 'player' / state
            if folder_path.exists():
                for file_path in sorted(folder_path.iterdir(), key=lambda p: int(p.stem)):
                    surf = pygame.image.load(file_path).convert_alpha()
                    self.frames[state].append(surf)

    def input(self):
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
        self.direction.y = int(keys[pygame.K_DOWN] or keys[pygame.K_s]) - int(keys[pygame.K_UP] or keys[pygame.K_w])
        self.direction = self.direction.normalize() if self.direction else self.direction

    def move(self, dt):
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.collision('horizontal')
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self.collision('vertical')
        self.rect.center = self.hitbox_rect.center

    def collision(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox_rect):
                if direction == 'horizontal':
                    if self.direction.x > 0: self.hitbox_rect.right = sprite.rect.left
                    if self.direction.x < 0: self.hitbox_rect.left = sprite.rect.right
                else:
                    if self.direction.y < 0: self.hitbox_rect.top = sprite.rect.bottom
                    if self.direction.y > 0: self.hitbox_rect.bottom = sprite.rect.top

    def animate(self, dt):
        if self.direction.x != 0:
            self.state = 'right' if self.direction.x > 0 else 'left'
        if self.direction.y != 0:
            self.state = 'down' if self.direction.y > 0 else 'up'

        self.frame_index = self.frame_index + 5 * dt if self.direction else 0
        self.image = self.frames[self.state][int(self.frame_index) % len(self.frames[self.state])]

    def update(self, dt):
        self.input()
        self.move(dt)
        self.animate(dt)