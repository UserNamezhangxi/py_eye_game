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
        self.player_size = 80
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

        self.tile_size = 40  # 每个小方块的像素大小，可根据需要调整
        self.bg_pattern = self.create_checkerboard_bg()
        self.bg_offset_x = 0  # 水平方向偏移量
        self.bg_offset_y = 0  # 垂直方向偏移量
        self.bg_speed_x = 2  # 水平滚动速度，正数向左滚，负数向右滚
        self.bg_speed_y = 2  # 垂直滚动速度，正数向上滚，负数向下滚

        # --- 新增：游戏流程控制状态 ---
        self.game_state = 'input'  # 初始状态为输入时间
        self.input_buffer = ""  # 存储用户输入的分钟数字符串
        self.target_duration_sec = 0  # 目标游戏时长（秒）
        self.start_game_time = 0  # 游戏正式开始的毫秒时间戳

        try:
            self.font_cn = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 40)
            self.font_small = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 24)
        except:
            self.font_cn = pygame.font.SysFont('arial', 40)
            self.font_small = pygame.font.SysFont('arial', 24)

        # --- 新增：吃掉海鲜的音效加载 ---
        try:
            self.eat_sound = pygame.mixer.Sound("eat.MP3")  # 替换成你自己的音效文件名
            self.eat_sound.set_volume(0.7)  # 调整音量到合适大小，避免太吵

            self.bg_music = pygame.mixer.Sound("bg_music.MP3")  # 替换成你自己的音效文件名
            self.bg_music.set_volume(0.7)  # 调整音量到合适大小，避免太吵

        except FileNotFoundError:
            print("提示：未找到音效文件，将跳过音效播放")
            self.eat_sound = None

    def handle_input_phase(self, event):
        """处理输入阶段的事件"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                # 确认输入
                if self.input_buffer.isdigit() and int(self.input_buffer) > 0:
                    self.target_duration_sec = int(self.input_buffer) * 60
                    self.game_state = 'playing'
                    self.start_game_time = pygame.time.get_ticks()
                    print(f"游戏开始！时长设定为: {self.input_buffer} 分钟")
                    self.bg_music.play(-1)  # 播放背景音乐，循环播放
                else:
                    self.input_buffer = ""  # 输入无效清空
            elif event.key == pygame.K_BACKSPACE:
                self.input_buffer = self.input_buffer[:-1]
            elif event.unicode.isdigit():
                # 限制最多输入2位数字，避免过大
                if len(self.input_buffer) < 2:
                    self.input_buffer += event.unicode

    def create_checkerboard_bg(self):
        """生成一个全屏的黑白棋盘格背景 Surface"""
        bg_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        # 遍历屏幕上的每一个格子位置
        for y in range(0, SCREEN_HEIGHT, self.tile_size):
            for x in range(0, SCREEN_WIDTH, self.tile_size):
                # 判断当前格子应该是黑色还是白色
                # 逻辑：如果行号+列号是偶数则白色，奇数则黑色（或者反过来）
                row_index = y // self.tile_size
                col_index = x // self.tile_size

                if (row_index + col_index) % 2 == 0:
                    color = WHITE
                else:
                    color = BLACK

                # 绘制矩形填充颜色
                pygame.draw.rect(bg_surface, color, (x, y, self.tile_size, self.tile_size))

        return bg_surface

    def draw_background(self):
        """绘制可滚动的棋盘格背景"""
        # 更新偏移量
        self.bg_offset_x -= self.bg_speed_x
        self.bg_offset_y -= self.bg_speed_y

        # 获取背景图的宽高
        bg_w, bg_h = self.bg_pattern.get_width(), self.bg_pattern.get_height()

        # 使用取余运算确保偏移量在合理范围内，实现无缝循环
        # 注意：这里假设 bg_pattern 足够大或者我们采用双图拼接法
        # 更简单的无缝滚动方法是：绘制两张图，一张在当前偏移位置，一张在互补位置

        current_x = self.bg_offset_x % bg_w
        current_y = self.bg_offset_y % bg_h

        # 为了覆盖整个屏幕并实现无缝，通常需要绘制 4 份背景图（左上、右上、左下、右下）
        # 或者至少 2 份（如果只向一个方向滚）。这里提供全方向无缝滚动的通用写法：

        # 绘制第一张（主图）
        self.screen.blit(self.bg_pattern, (current_x - bg_w, current_y - bg_h))
        self.screen.blit(self.bg_pattern, (current_x, current_y - bg_h))
        self.screen.blit(self.bg_pattern, (current_x - bg_w, current_y))
        self.screen.blit(self.bg_pattern, (current_x, current_y))

    def get_formatted_time(self, elapsed_sec):
        """获取当前游戏运行时间，格式为 MM:SS"""
        # get_ticks() 返回自 pygame.init() 以来的毫秒数
        total_seconds = elapsed_sec
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        # 格式化为两位数字，例如 01:05
        return f"时间: {minutes:02d}:{seconds:02d}"

    def generate_cartoon_fish(self):
        fish_surf = pygame.image.load("c.jpeg").convert_alpha()
        fish_surf = pygame.transform.scale(fish_surf, (self.player_size, self.player_size))
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

            # 根据当前状态分发事件
            if self.game_state == 'input':
                self.handle_input_phase(event)
            elif self.game_state == 'ended':
                # 结束后按 R 键重启，或 Q 键退出
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.__init__()  # 重置游戏
                    elif event.key == pygame.K_q:
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
                if enemy in self.enemies:
                    self.enemies.remove(enemy)
                    # 碰撞触发，播放吃掉音效
                    if self.eat_sound is not None:
                        self.eat_sound.play()

    def update_background_state(self):
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.start_time
        time_in_cycle = elapsed % 90000
        if time_in_cycle < 30000:
            self.current_phase = 'grating'
            self.bg_color = WHITE
        elif time_in_cycle < 60000:
            self.current_phase = 'black_white'
        else:
            flash_time = time_in_cycle - 30000
            if (flash_time // 1000) % 2 == 0:
                self.current_phase = 'red'
                self.bg_color = RED
            else:
                self.current_phase = 'blue'
                self.bg_color = BLUE
        self.grating_offset += 2

        if self.current_phase == 'grating':
            self.draw_grating()
        elif self.current_phase == 'black_white':
            self.draw_background()
        else:
            self.screen.fill(self.bg_color)

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

    def draw_time(self, elapsed_sec):
        text_color = BLACK if self.current_phase == 'grating' else WHITE
        bg_box_color = WHITE if self.current_phase == 'grating' else BLACK
        time_text = self.get_formatted_time(elapsed_sec)
        text = self.font_cn.render(time_text, True, text_color)
        text_rect = text.get_rect(topleft=(10, 10))
        pygame.draw.rect(self.screen, bg_box_color, text_rect.inflate(10, 10))
        self.screen.blit(text, (15, 15))

    def draw_input_screen(self):
        """绘制输入界面"""
        title_surf = self.font_cn.render("请输入训练时长(分钟):", True, BLACK)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(title_surf, title_rect)

        # 显示当前输入的数字
        input_surf = self.font_cn.render(self.input_buffer + "_", True, BLUE)  # 加个下划线模拟光标
        input_rect = input_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(input_surf, input_rect)

        hint_surf = self.font_small.render("输入数字后按 Enter 确认", True, (100, 100, 100))
        hint_rect = hint_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
        self.screen.blit(hint_surf, hint_rect)

    def draw_end_screen(self):
        """绘制结束提示界面"""
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        msg1 = self.font_cn.render("时间到！", True, WHITE)
        msg2 = self.font_cn.render("请休息后再次游戏吧", True, WHITE)
        msg3 = self.font_small.render("按 R 重新开始 | 按 Q 退出", True, (200, 200, 200))

        rect1 = msg1.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
        rect2 = msg2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        rect3 = msg3.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))

        self.screen.blit(msg1, rect1)
        self.screen.blit(msg2, rect2)
        self.screen.blit(msg3, rect3)

        self.bg_music.stop()

    def check_tim_over(self):
        current_time = pygame.time.get_ticks()
        elapsed_sec = (current_time - self.start_game_time) // 1000

        if elapsed_sec >= self.target_duration_sec:
            self.game_state = 'ended'
        return elapsed_sec

    def run(self):
        while self.running:
            # --- 事件处理 ---
            self.handle_events()

            # --- 绘制阶段 ---
            self.screen.fill(WHITE)  # 先清屏

            if self.game_state == 'input':
                self.draw_input_screen()
            elif self.game_state == 'playing':
                self.draw_playing()
            elif self.game_state == 'ended':
                self.draw_end_screen()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

    def draw_playing(self):
        self.handle_input()
        self.update_enemies()
        self.check_collisions()
        self.update_background_state()
        self.draw_enemies()
        self.draw_player()
        elapsed_sec = self.check_tim_over()
        self.draw_time(elapsed_sec)


if __name__ == "__main__":
    game = Game()
    game.run()
