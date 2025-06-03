from settings import *
from player import Player
from sprites import *
from pytmx.util_pygame import load_pygame
from groups import AllSprites
from random import choice
import pygame
import time
import sys  # Добавляем sys для завершения программы

class Menu:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.Font(None, 74)
        self.small_font = pygame.font.Font(None, 50)
        self.input_box = pygame.Rect(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 - 25, 200, 50)
        self.color_inactive = pygame.Color('lightskyblue3')
        self.color_active = pygame.Color('dodgerblue2')
        self.color = self.color_inactive
        self.active = False
        self.text = ''
        self.done = False
        self.show_intro = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.input_box.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = self.color_active if self.active else self.color_inactive
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    self.done = True
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode

    def draw_input_screen(self):
        self.game.display_surface.fill((30, 30, 30))
        txt_surface = self.font.render("Введите ваше имя:", True, (255, 255, 255))
        self.game.display_surface.blit(txt_surface, (WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2 - 100))
        pygame.draw.rect(self.game.display_surface, self.color, self.input_box, 2)
        txt_surface = self.font.render(self.text, True, (255, 255, 255))
        self.game.display_surface.blit(txt_surface, (self.input_box.x + 5, self.input_box.y + 5))
        pygame.display.flip()

    def draw_intro_screen(self):
        self.game.display_surface.fill((30, 30, 30))
        txt_surface = self.font.render("The Last Hope", True, (255, 0, 0))
        self.game.display_surface.blit(txt_surface, (WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2 - 200))

        intro_text = [
            "Добро пожаловать в игру The Last Hope!",
            "Ваша задача - выживать как можно дольше,",
            "уничтожая врагов и избегая их атак.",
            "Удачи!"
        ]
        for i, line in enumerate(intro_text):
            txt_surface = self.small_font.render(line, True, (255, 255, 255))
            self.game.display_surface.blit(txt_surface, (WINDOW_WIDTH // 2 - 250, WINDOW_HEIGHT // 2 - 100 + i * 40))

        play_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 + 100, 200, 50)
        pygame.draw.rect(self.game.display_surface, (0, 255, 0), play_button)
        txt_surface = self.small_font.render("Играть", True, (0, 0, 0))
        self.game.display_surface.blit(txt_surface, (WINDOW_WIDTH // 2 - 50, WINDOW_HEIGHT // 2 + 115))
        pygame.display.flip()

        return play_button

    def run(self):
        while not self.done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()  # Завершаем программу полностью
                self.handle_event(event)
            self.draw_input_screen()

        self.show_intro = True
        while self.show_intro:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()  # Завершаем программу полностью
                if event.type == pygame.MOUSEBUTTONDOWN:
                    play_button = self.draw_intro_screen()
                    if play_button.collidepoint(event.pos):
                        self.show_intro = False
            self.draw_intro_screen()

class Game:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('The Last Hope')
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_over = False
        self.show_leaderboard_flag = False

        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()

        self.can_shoot = True
        self.shoot_time = 0
        self.gun_cooldown = 100

        self.enemy_event = pygame.event.custom_type()
        pygame.time.set_timer(self.enemy_event, 300)
        self.spawn_positions = []

        # Звуки
        self.shoot_sound = pygame.mixer.Sound(BASE_DIR / 'audio' / 'shoot.wav')
        self.shoot_sound.set_volume(0.2)
        self.impact_sound = pygame.mixer.Sound(BASE_DIR / 'audio' / 'impact.ogg')
        self.music = pygame.mixer.Sound(BASE_DIR / 'audio' / 'music.wav')
        self.music.set_volume(0.5)
        self.hurt_sound = pygame.mixer.Sound(BASE_DIR / 'audio' / 'hurt.wav')
        self.death_sound = pygame.mixer.Sound(BASE_DIR / 'audio' / 'death.wav')

        self.killed_enemies = 0
        self.start_time = time.time()

        self.load_images()
        self.setup()

        # Меню
        self.menu = Menu(self)
        self.player_name = ''
        self.menu.run()

    def load_images(self):
        self.bullet_surf = pygame.image.load(BASE_DIR / 'images' / 'gun' / 'bullet.png').convert_alpha()
        folders = list((BASE_DIR / 'images' / 'enemies').iterdir())
        self.enemy_frames = {}
        for folder in folders:
            if folder.is_dir():
                self.enemy_frames[folder.name] = []
                for file_path in sorted(folder.iterdir(), key=lambda p: int(p.stem)):
                    surf = pygame.image.load(file_path).convert_alpha()
                    self.enemy_frames[folder.name].append(surf)

    def setup(self):
        map = load_pygame(BASE_DIR / 'data' / 'maps' / 'world.tmx')
        for x, y, image in map.get_layer_by_name('Ground').tiles():
            Sprite((x * TILE_SIZE, y * TILE_SIZE), image, self.all_sprites)
        for obj in map.get_layer_by_name('Objects'):
            CollisionSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))
        for obj in map.get_layer_by_name('Collisions'):
            CollisionSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), self.collision_sprites)
        for obj in map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player((obj.x, obj.y), self.all_sprites, self.collision_sprites, self.hurt_sound)
                self.gun = Gun(self.player, self.all_sprites)
            else:
                self.spawn_positions.append((obj.x, obj.y))

    def gun_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.shoot_time >= self.gun_cooldown:
                self.can_shoot = True

    def input(self):
        if pygame.mouse.get_pressed()[0] and self.can_shoot:
            self.shoot_sound.play()
            pos = self.gun.rect.center + self.gun.player_direction * 50
            Bullet(self.bullet_surf, pos, self.gun.player_direction, (self.all_sprites, self.bullet_sprites))
            self.can_shoot = False
            self.shoot_time = pygame.time.get_ticks()

    def bullet_collision(self):
        for bullet in self.bullet_sprites:
            collision_sprites = pygame.sprite.spritecollide(bullet, self.enemy_sprites, False, pygame.sprite.collide_mask)
            if collision_sprites:
                self.impact_sound.play()
                for sprite in collision_sprites:
                    sprite.destroy()
                    self.killed_enemies += 1
                bullet.kill()

    def player_collision(self):
        if pygame.sprite.spritecollide(self.player, self.enemy_sprites, False, pygame.sprite.collide_mask):
            self.player.take_damage()
            if self.player.health <= 0:
                self.death_sound.play()
                self.game_over = True

    def save_result(self):
        player_name = self.menu.text
        time_survived = int(time.time() - self.start_time)
        kills = self.killed_enemies
        try:
            with open("leaderboard.txt", "r") as file:
                lines = file.readlines()
        except FileNotFoundError:
            lines = []
        updated_lines = []
        player_found = False
        for line in lines:
            name, old_time, old_kills = line.strip().split(", ")
            if name == player_name:
                if kills > int(old_kills):
                    updated_lines.append(f"{player_name}, {time_survived}, {kills}\n")
                else:
                    updated_lines.append(line)
                player_found = True
            else:
                updated_lines.append(line)
        if not player_found:
            updated_lines.append(f"{player_name}, {time_survived}, {kills}\n")
        with open("leaderboard.txt", "w") as file:
            file.writelines(updated_lines)

    def show_game_over_screen(self):
        self.display_surface.fill('black')
        font = pygame.font.Font(None, 74)
        text = font.render('Game Over', True, (255, 0, 0))
        text_rect = text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 50))
        self.display_surface.blit(text, text_rect)
        font = pygame.font.Font(None, 50)
        restart_text = font.render('Press R to Restart', True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 50))
        self.display_surface.blit(restart_text, restart_rect)
        leaderboard_text = font.render('Press L for Leaderboard', True, (255, 255, 255))
        leaderboard_rect = leaderboard_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 120))
        self.display_surface.blit(leaderboard_text, leaderboard_rect)
        pygame.display.update()

    def show_leaderboard(self):
        self.display_surface.fill('black')
        font = pygame.font.Font(None, 50)
        title_text = font.render("Leaderboard", True, (255, 255, 255))
        self.display_surface.blit(title_text, (WINDOW_WIDTH // 2 - 100, 50))
        try:
            with open("leaderboard.txt", "r") as file:
                results = file.readlines()
                results = [line.strip().split(", ") for line in results]
                results.sort(key=lambda x: int(x[2]), reverse=True)
                for i, result in enumerate(results[:10]):
                    name, time_survived, kills = result
                    result_text = f"{i + 1}. {name}: {time_survived}s, {kills} kills"
                    text_surface = font.render(result_text, True, (255, 255, 255))
                    self.display_surface.blit(text_surface, (50, 150 + i * 50))
        except FileNotFoundError:
            text_surface = font.render("No results yet!", True, (255, 255, 255))
            self.display_surface.blit(text_surface, (WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2))
        back_text = font.render("Press B to go back", True, (255, 255, 255))
        self.display_surface.blit(back_text, (WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT - 100))
        pygame.display.update()

    def restart_game(self):
        self.all_sprites.empty()
        self.collision_sprites.empty()
        self.bullet_sprites.empty()
        self.enemy_sprites.empty()
        self.killed_enemies = 0
        self.start_time = time.time()
        self.setup()
        self.game_over = False
        self.running = True

    def draw_health(self):
        font = pygame.font.Font(None, 36)
        health_text = f"Health: {self.player.health}"
        text_surface = font.render(health_text, True, (255, 255, 255))
        self.display_surface.blit(text_surface, (10, 10))

    def draw_killed_enemies(self):
        font = pygame.font.Font(None, 36)
        enemies_text = f"Killed: {self.killed_enemies}"
        text_surface = font.render(enemies_text, True, (255, 255, 255))
        self.display_surface.blit(text_surface, (WINDOW_WIDTH - 150, 10))

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == self.enemy_event:
                    Enemy(choice(self.spawn_positions), choice(list(self.enemy_frames.values())),
                          (self.all_sprites, self.enemy_sprites), self.player, self.collision_sprites)
            if not self.game_over and not self.show_leaderboard_flag:
                self.gun_timer()
                self.input()
                self.all_sprites.update(dt)
                self.bullet_collision()
                self.player_collision()
                self.display_surface.fill('black')
                self.all_sprites.draw(self.player.rect.center)
                self.draw_health()
                self.draw_killed_enemies()
            elif self.game_over:
                self.show_game_over_screen()
                keys = pygame.key.get_pressed()
                if keys[pygame.K_r]:
                    self.restart_game()
                if keys[pygame.K_l]:
                    self.save_result()
                    self.show_leaderboard_flag = True
                    self.game_over = False
            elif self.show_leaderboard_flag:
                self.show_leaderboard()
                keys = pygame.key.get_pressed()
                if keys[pygame.K_b]:
                    self.show_leaderboard_flag = False
                    self.running = False
                    self.__init__()
            pygame.display.update()
        pygame.quit()
        sys.exit()  # Завершаем программу после выхода из игрового цикла

if __name__ == '__main__':
    game = Game()
    game.run()