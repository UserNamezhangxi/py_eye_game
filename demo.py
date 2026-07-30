import pygame
import sys
import math
import random

# 初始化 Pygame
pygame.init()

# 常量定义
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
FPS = 60

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("弱视训练：SVG风格海鲜大作战")
        self.clock = pygame.time.Clock()
        self.running = True

        # 新增玩家朝向标记，默认初始面朝左
        self.player_facing_right = False

        # --- 玩家属性 ---
        self.player_size = 60
        self.player_x = SCREEN_WIDTH // 2
        self.player_y = SCREEN_HEIGHT // 2
        self.player_speed = 4
        self.base_player_img = self.generate_cartoon_fish()
        self.player_img = self.base_player_img
        self.fish_anim_timer = 0

        # --- 敌人属性 ---
        self.enemies = []
        self.enemy_spawn_timer = 0
        self.enemy_spawn_interval = 50
        # 预生成 SVG 风格海鲜图案
        self.seafood_assets = self.generate_custom_seafood()

        # --- 背景状态控制 ---
        self.start_time = pygame.time.get_ticks()
        self.bg_color = WHITE
        self.grating_offset = 0
        self.current_phase = 'grating'

        # --- 字体 ---
        self.font = pygame.font.SysFont('arial', 24)

    def generate_cartoon_fish(self):
        fish_surf = pygame.image.load("c.jpeg").convert_alpha()
        fish_surf = pygame.transform.scale(fish_surf, (60, 60))
        return fish_surf

    def generate_custom_seafood(self):
        """加载你自己的JPG/PNG海鲜图案，替换原来的自动生成逻辑"""
        assets = {}

        # 加载自定义螃蟹图，缩放到60*60尺寸
        assets['crab'] = pygame.image.load("b.jpeg").convert_alpha()
        assets['crab'] = pygame.transform.scale(assets['crab'], (60, 60))

        # 加载自定义虾图
        assets['shrimp'] = pygame.image.load("a.jpeg").convert_alpha()
        assets['shrimp'] = pygame.transform.scale(assets['shrimp'], (60, 60))

        # 加载自定义贝壳图
        assets['shell'] = pygame.image.load("d.jpeg").convert_alpha()
        assets['shell'] = pygame.transform.scale(assets['shell'], (60, 60))
        return assets

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def handle_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player_x -= self.player_speed
            self.player_facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player_x += self.player_speed
            self.player_facing_right = True
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.player_y -= self.player_speed
        # 修正下方向逻辑：Y坐标增大才是往屏幕下方移动
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.player_y += self.player_speed
        # 保留边界限制，避免鱼移出屏幕外
        self.player_x = max(self.player_size, min(SCREEN_WIDTH - self.player_size, self.player_x))
        self.player_y = max(self.player_size, min(SCREEN_HEIGHT - self.player_size, self.player_y))

    def spawn_enemy(self):
        size = random.randint(25, 30)
        speed = random.uniform(1, 2)
        enemy_type_name = random.choice(['crab', 'shrimp', 'shell'])
        side = random.choice([1, 2, 3])  # 右, 下, 左
        dx = dy = x = y = 0

        if side == 1:  # 右
            x = SCREEN_WIDTH + size
            y = random.randint(size, SCREEN_HEIGHT - size)
            angle = random.uniform(3 * math.pi / 4, 5 * math.pi / 4)
        elif side == 2:  # 下
            x = random.randint(size, SCREEN_WIDTH - size)
            y = SCREEN_HEIGHT + size
            angle = random.uniform(5 * math.pi / 4, 7 * math.pi / 4)
        else:  # 左
            x = -size
            y = random.randint(size, SCREEN_HEIGHT - size)
            angle = random.uniform(-math.pi / 4, math.pi / 4)

        dx = math.cos(angle) * speed
        dy = math.sin(angle) * speed
        self.enemies.append({'x': x, 'y': y, 'size': size, 'dx': dx, 'dy': dy, 'type_name': enemy_type_name})

    def update_enemies(self):
        self.enemy_spawn_timer += 1
        if self.enemy_spawn_timer >= self.enemy_spawn_interval:
            self.enemy_spawn_timer = 0
            self.spawn_enemy()
        for enemy in self.enemies[:]:
            enemy['x'] += enemy['dx']
            enemy['y'] += enemy['dy']
            margin = enemy['size'] + 50
            if (enemy['x'] < -margin or enemy['x'] > SCREEN_WIDTH + margin or
                    enemy['y'] < -margin or enemy['y'] > SCREEN_HEIGHT + margin):
                if enemy in self.enemies:
                    self.enemies.remove(enemy)

    def check_collisions(self):
        for enemy in self.enemies[:]:
            dist = math.hypot(self.player_x - enemy['x'], self.player_y - enemy['y'])
            if dist < self.player_size + enemy['size']:
                if enemy in self.enemies: self.enemies.remove(enemy)

    def update_background_state(self):
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.start_time
        time_in_cycle = elapsed % 60000
        if time_in_cycle < 30000:
            self.current_phase = 'grating'
            self.bg_color = WHITE
        else:
            flash_time = time_in_cycle - 30000
            if (flash_time // 1000) % 2 == 0:
                self.current_phase = 'red'
                self.bg_color = RED
            else:
                self.current_phase = 'blue'
                self.bg_color = BLUE
        self.grating_offset += 2

    def draw_grating(self):
        if self.current_phase != 'grating':
            return
        self.screen.fill(WHITE)
        grating_width = 20
        for x in range(-grating_width * 2, SCREEN_WIDTH + grating_width * 2, grating_width * 2):
            draw_x = x + (self.grating_offset % (grating_width * 2))
            pygame.draw.rect(self.screen, BLACK, (draw_x, 0, grating_width, SCREEN_HEIGHT))

    def draw_player(self):
        self.fish_anim_timer += 1
        current_anim_img = self.base_player_img
        if self.fish_anim_timer % 30 == 0:
            rotate_angle = 5 if (self.fish_anim_timer // 30) % 2 == 0 else -5
            current_anim_img = pygame.transform.rotate(self.base_player_img, rotate_angle)

        # 核心镜像逻辑：面朝右时水平翻转图片
        if self.player_facing_right:
            current_anim_img = pygame.transform.flip(current_anim_img, True, False)

        self.player_img = current_anim_img
        img_rect = self.player_img.get_rect(center=(int(self.player_x), int(self.player_y)))
        self.screen.blit(self.player_img, img_rect)

    def draw_enemies(self):
        # 遍历所有敌人，给每个敌人维护独立的动画计时
        for enemy in self.enemies:
            base_img = self.seafood_assets.get(enemy['type_name'])
            if base_img:
                # 初始化敌人专属动画计时器，避免所有海鲜同步摆动
                if 'anim_timer' not in enemy:
                    enemy['anim_timer'] = random.randint(0, 30)
                enemy['anim_timer'] += 1

                # 每30帧切换一次旋转角度，和玩家鱼的摆动节奏完全对齐
                if enemy['anim_timer'] % 35 == 0:
                    rotate_angle = 5 if (enemy['anim_timer'] // 35) % 2 == 0 else -5
                    # 基于原始素材旋转，避免多次旋转导致画面变形糊掉
                    enemy['current_anim_img'] = pygame.transform.rotate(base_img, rotate_angle)

                # 取当前帧的动画图，没有生成过就用原始图兜底
                anim_img = enemy.get('current_anim_img', base_img)
                target_size = int(enemy['size'] * 2)
                scaled_img = pygame.transform.smoothscale(anim_img, (target_size, target_size))
                rect = scaled_img.get_rect(center=(int(enemy['x']), int(enemy['y'])))
                self.screen.blit(scaled_img, rect)

    def draw_ui(self):
        text_color = BLACK if self.current_phase == 'grating' else WHITE
        bg_box_color = WHITE if self.current_phase == 'grating' else BLACK
        text = self.font.render("Arrows to Move | Eat Seafood", True, text_color)
        text_rect = text.get_rect(topleft=(10, 10))
        pygame.draw.rect(self.screen, bg_box_color, text_rect.inflate(10, 10))
        self.screen.blit(text, (15, 15))

    def run(self):
        while self.running:
            self.handle_events()
            self.handle_input()
            self.update_enemies()
            self.check_collisions()
            self.update_background_state()
            if self.current_phase == 'grating':
                self.draw_grating()
            else:
                self.screen.fill(self.bg_color)
            self.draw_enemies()
            self.draw_player()
            self.draw_ui()
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
