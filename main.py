import pygame
import asyncio
import random

pygame.init()

WIDTH, HEIGHT = 480, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
GREEN = (0, 180, 0)
GRAY = (100, 100, 100)
YELLOW = (255, 255, 0)
PURPLE = (180, 0, 255)

font_small = pygame.font.SysFont(None, 28)

cp_levels = [
    {"shoot_rate": 80, "speed": 2},
    {"shoot_rate": 60, "speed": 3},
    {"shoot_rate": 50, "speed": 4},
    {"shoot_rate": 40, "speed": 5},
    {"shoot_rate": 30, "speed": 6},
    {"shoot_rate": 20, "speed": 7},
    {"shoot_rate": 15, "speed": 8},
    {"shoot_rate": 10, "speed": 9},
    {"shoot_rate": 6, "speed": 10},
    {"shoot_rate": 3, "speed": 12},
]

best_scores = [0] * 20


class Button:
    def __init__(self, rect, color, text):
        self.rect = pygame.Rect(rect)
        self.color = color
        self.text = text

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        t = font_small.render(self.text, True, WHITE)
        screen.blit(t, t.get_rect(center=self.rect.center))


# =========================
# 弾除けゲーム
# =========================
async def dodge_game(level):
    player = pygame.Rect(WIDTH // 2 - 25, HEIGHT - 120, 50, 50)
    bullets = []
    speed = 5 + level

    left_btn = pygame.Rect(30, HEIGHT - 120, 80, 80)
    right_btn = pygame.Rect(130, HEIGHT - 120, 80, 80)

    active_touches = {}

    start_time = pygame.time.get_ticks()

    while True:
        clock.tick(60)
        screen.fill(BLACK)

        # 弾生成
        if random.randint(0, 20) == 0:
            bullets.append(pygame.Rect(random.randint(0, WIDTH - 10), -10, 10, 10))

        moving_left = False
        moving_right = False

        # 入力
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "QUIT", 0, 0
            if e.type in (pygame.FINGERDOWN, pygame.FINGERMOTION):
                active_touches[e.finger_id] = (e.x, e.y)
            if e.type == pygame.FINGERUP:
                active_touches.pop(e.finger_id, None)

        # タッチ判定
        for tx, ty in active_touches.values():
            x, y = tx * WIDTH, ty * HEIGHT
            if left_btn.collidepoint((x, y)):
                moving_left = True
            if right_btn.collidepoint((x, y)):
                moving_right = True

        # 移動
        if moving_left:
            player.x -= 6
        if moving_right:
            player.x += 6

        player.x = max(0, min(WIDTH - player.width, player.x))

        # 弾処理
        for b in bullets[:]:
            b.y += speed
            if player.colliderect(b):
                time_sec = (pygame.time.get_ticks() - start_time) / 1000
                return "LOSE", 0, time_sec
            if b.y > HEIGHT:
                bullets.remove(b)

        # 描画
        pygame.draw.rect(screen, BLUE, player)
        for b in bullets:
            pygame.draw.rect(screen, RED, b)

        pygame.draw.rect(screen, GREEN, left_btn)
        pygame.draw.rect(screen, GREEN, right_btn)

        screen.blit(font_small.render("L", True, WHITE),
                    font_small.render("L", True, WHITE).get_rect(center=left_btn.center))
        screen.blit(font_small.render("R", True, WHITE),
                    font_small.render("R", True, WHITE).get_rect(center=right_btn.center))

        # 時間表示
        time_sec = (pygame.time.get_ticks() - start_time) / 1000
        screen.blit(font_small.render(f"{time_sec:.2f}s", True, WHITE), (10, 10))

        pygame.display.flip()
        await asyncio.sleep(0)
# =========================
# ノーマルゲーム（前半：バフ基盤）
# =========================
async def normal_game(cp_level, max_player_hp):
    cp = min(cp_level, 9)

    player = pygame.Rect(WIDTH // 2 - 25, HEIGHT - 260, 50, 50)
    enemy = pygame.Rect(WIDTH // 2 - 25, 50, 50, 50)

    player_bullets = []
    enemy_bullets = []
    explosions = []

    # ===== 難易度調整（ここ変更）=====
    player_hp = max_player_hp

    # 元：enemy_hp = 5 + (cp_level + 1) ** 2 * 2
    enemy_hp = int(10 + (cp_level + 1) ** 1.7 * 3)
    max_enemy_hp = enemy_hp

    start_time = pygame.time.get_ticks()

    # ===== ボタン =====
    left_btn = pygame.Rect(30, HEIGHT - 160, 80, 80)
    right_btn = pygame.Rect(130, HEIGHT - 160, 80, 80)
    shoot_btn = pygame.Rect(WIDTH - 110, HEIGHT - 160, 80, 80)
    special_btn = pygame.Rect(WIDTH - 110, HEIGHT - 250, 80, 60)

    # ===== バフボタン =====
    buff_c_btn = pygame.Rect(230, HEIGHT - 160, 40, 40)
    buff_s_btn = pygame.Rect(275, HEIGHT - 160, 40, 40)
    buff_h_btn = pygame.Rect(320, HEIGHT - 160, 40, 40)

    shoot_cooldown = 0
    cooldown_time = 30

    special_gauge = 0
    special_timer = 0

    buff_gauge = 0
    buff_timer = 0

    cooldown_reduction = 0.0
    attack_power = 0.0

    combo = 0
    combo_timer = 0

    shake_timer = 0
    blink_timer = 0

    active_touches = {}

    running = True
    result = None

    while running:
        clock.tick(60)
        screen.fill(BLACK)
        blink_timer += 1

        offset = random.randint(-3, 3) if shake_timer > 0 else 0
        if shake_timer > 0:
            shake_timer -= 1

        moving_left = False
        moving_right = False
        shooting = False
        special = False
        buff_c = False
        buff_s = False
        buff_h = False

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "QUIT", 0, 0
            if e.type in (pygame.FINGERDOWN, pygame.FINGERMOTION):
                active_touches[e.finger_id] = (e.x, e.y)
            if e.type == pygame.FINGERUP:
                active_touches.pop(e.finger_id, None)

        for tx, ty in active_touches.values():
            x, y = tx * WIDTH, ty * HEIGHT

            if left_btn.collidepoint((x, y)):
                moving_left = True
            if right_btn.collidepoint((x, y)):
                moving_right = True
            if shoot_btn.collidepoint((x, y)):
                shooting = True
            if special_btn.collidepoint((x, y)):
                special = True

            if buff_c_btn.collidepoint((x, y)):
                buff_c = True
            if buff_s_btn.collidepoint((x, y)):
                buff_s = True
            if buff_h_btn.collidepoint((x, y)):
                buff_h = True

        if shoot_cooldown > 0:
            shoot_cooldown -= 1

        special_timer += 1
        if special_timer >= 60:
            special_timer = 0
            special_gauge = min(20, special_gauge + 1)

        # ===== バフ速度変更（10秒でMAX）=====
        buff_timer += 1
        if buff_timer >= 30:
            buff_timer = 0
            buff_gauge = min(20, buff_gauge + 1)

        if buff_gauge >= 20:
            if buff_c:
                cooldown_reduction += 0.1
                buff_gauge = 0
            elif buff_s:
                attack_power += 0.3
                buff_gauge = 0
            elif buff_h:
                max_player_hp += 2
                player_hp = min(max_player_hp, player_hp + 2)
                buff_gauge = 0

        if moving_left:
            player.x -= 5
        if moving_right:
            player.x += 5

        player.x = max(0, min(WIDTH - player.width, player.x))

        # ===== 射撃 =====
        if shooting and shoot_cooldown == 0:
            player_bullets.append({
                "rect": pygame.Rect(player.centerx - 5, player.y, 10, 10),
                "power": 1 + combo + attack_power
            })
            shoot_cooldown = max(1, int(cooldown_time - cooldown_reduction * 60))

        # ===== スペシャル =====
        if special and special_gauge >= 20:
            player_bullets.append({
                "rect": pygame.Rect(player.centerx - 15, player.y, 30, 30),
                "power": 3 + attack_power,
                "pierce": True,
                "hit_enemy": False
            })
            special_gauge = 0

        # ===== 敵移動（調整＋ランダム追加）=====
        dx = player.centerx - enemy.centerx
        direction = dx / abs(dx) if dx != 0 else 0

        # 元：+ cp_level * 0.3
        enemy_speed = cp_levels[cp]["speed"] + cp_level * 0.2

        # 変更後（ヌルヌル）
        enemy.x += direction * enemy_speed

        # ===== 敵弾（調整）=====
        # 元：- cp_level * 2
        shoot_rate = max(5, int(cp_levels[cp]["shoot_rate"] - cp_level * 1.5))

        if random.randint(0, shoot_rate) == 0:
            enemy_bullets.append(
                pygame.Rect(enemy.centerx - 5, enemy.bottom, 10, 10)
            )

        # ===== 弾移動 =====
        for b in player_bullets:
            b["rect"].y -= 7
        for b in enemy_bullets:
            b.y += 7

        # ===== 弾相殺 =====
        for pb in player_bullets[:]:
            for eb in enemy_bullets[:]:
                if pb["rect"].colliderect(eb):
                    if not pb.get("pierce"):
                        player_bullets.remove(pb)
                    enemy_bullets.remove(eb)
                    break

        # ===== 敵ヒット =====
        for b in player_bullets[:]:
            if enemy.colliderect(b["rect"]):

                if b.get("pierce") and b.get("hit_enemy"):
                    continue

                if b.get("pierce"):
                    b["hit_enemy"] = True

                enemy_hp -= b["power"]
                shake_timer = 3
                explosions.append([enemy.centerx, enemy.centery, 5])

                if not b.get("pierce"):
                    player_bullets.remove(b)

                combo += 1
                combo_timer = 180

                buff_gauge = min(20, buff_gauge + 1)

        # ===== プレイヤー被弾 =====
        for b in enemy_bullets[:]:
            if player.colliderect(b):
                enemy_bullets.remove(b)
                player_hp -= 1
                shake_timer = 5
                explosions.append([player.centerx, player.centery, 5])

        # ===== コンボ減少 =====
        if combo_timer > 0:
            combo_timer -= 1
        else:
            combo = 0

        # ===== 勝敗判定 =====
        if player_hp <= 0:
            result = "LOSE"
            running = False
        if enemy_hp <= 0:
            result = "WIN"
            running = False

        # ===== 描画 =====
        pygame.draw.rect(screen, BLUE, player.move(offset, 0))
        pygame.draw.rect(screen, RED, enemy.move(offset, 0))

        for b in player_bullets:
            color = PURPLE if b.get("pierce") else WHITE
            pygame.draw.rect(screen, color, b["rect"].move(offset, 0))

        for b in enemy_bullets:
            pygame.draw.rect(screen, WHITE, b.move(offset, 0))

        # ===== 爆発 =====
        for exp in explosions[:]:
            pygame.draw.circle(screen, (255, 200, 0), (exp[0] + offset, exp[1]), exp[2])
            pygame.draw.circle(screen, (255, 100, 0), (exp[0] + offset, exp[1]), exp[2] // 2)
            exp[2] += 2
            if exp[2] > 20:
                explosions.remove(exp)

        # ===== HPバー =====
        x = (WIDTH - 200) // 2
        pygame.draw.rect(screen, WHITE, (x, 10, 200, 20), 2)
        pygame.draw.rect(screen, RED, (x, 10, 200 * (enemy_hp / max_enemy_hp), 20))

        pygame.draw.rect(screen, WHITE, (x, HEIGHT - 40, 200, 20), 2)
        pygame.draw.rect(screen, BLUE, (x, HEIGHT - 40, 200 * (player_hp / max_player_hp), 20))

        # ===== スペシャルゲージ =====
        pygame.draw.rect(screen, WHITE, (WIDTH - 110, HEIGHT - 300, 80, 10), 2)
        pygame.draw.rect(screen, YELLOW,
                         (WIDTH - 110, HEIGHT - 300, 80 * (special_gauge / 20), 10))

        # ===== ボタン =====
        pygame.draw.rect(screen, GREEN, left_btn)
        pygame.draw.rect(screen, GREEN, right_btn)

        shoot_color = GRAY if shoot_cooldown > 0 else RED
        pygame.draw.rect(screen, shoot_color, shoot_btn)

        pygame.draw.rect(screen, YELLOW if special_gauge >= 20 else GRAY, special_btn)

        # ===== バフボタン =====
        buff_ready = buff_gauge >= 20

        pygame.draw.rect(screen, YELLOW if buff_ready else GRAY, buff_c_btn)
        pygame.draw.rect(screen, YELLOW if buff_ready else GRAY, buff_s_btn)
        pygame.draw.rect(screen, YELLOW if buff_ready else GRAY, buff_h_btn)

        # ===== テキスト =====
        screen.blit(font_small.render("L", True, WHITE),
                    font_small.render("L", True, WHITE).get_rect(center=left_btn.center))
        screen.blit(font_small.render("R", True, WHITE),
                    font_small.render("R", True, WHITE).get_rect(center=right_btn.center))
        screen.blit(font_small.render("SHOOT", True, WHITE),
                    font_small.render("SHOOT", True, WHITE).get_rect(center=shoot_btn.center))
        screen.blit(font_small.render("SP", True, WHITE),
                    font_small.render("SP", True, WHITE).get_rect(center=special_btn.center))

        screen.blit(font_small.render("C", True, WHITE),
                    font_small.render("C", True, WHITE).get_rect(center=buff_c_btn.center))
        screen.blit(font_small.render("S", True, WHITE),
                    font_small.render("S", True, WHITE).get_rect(center=buff_s_btn.center))
        screen.blit(font_small.render("H", True, WHITE),
                    font_small.render("H", True, WHITE).get_rect(center=buff_h_btn.center))

        # ===== バフゲージ =====
        pygame.draw.rect(screen, WHITE, (240, HEIGHT - 110, 100, 6), 1)
        pygame.draw.rect(screen, YELLOW,
                         (240, HEIGHT - 110, 100 * (buff_gauge / 20), 6))

        # ===== 時間 =====
        time_sec = (pygame.time.get_ticks() - start_time) / 1000
        screen.blit(font_small.render(f"{time_sec:.2f}s", True, WHITE), (10, 10))

        if combo > 0:
            screen.blit(font_small.render(f"{combo} COMBO", True, YELLOW),
                        (WIDTH // 2 - 50, 100))

        pygame.display.flip()
        await asyncio.sleep(0)

    # ===== 終了処理 =====
    time_sec = (pygame.time.get_ticks() - start_time) / 1000
    score = int(time_sec * (10 if result == "WIN" else 5) * (1 + cp_level * 0.1))
    return result, score, time_sec

# =========================
# ボス戦（完全版＋強化）
# =========================
async def boss_battle(level):
    player = pygame.Rect(WIDTH // 2 - 25, HEIGHT - 200, 50, 50)
    boss = pygame.Rect(WIDTH // 2 - 40, 50, 80, 80)

    player_hp = 10
    max_player_hp = 10
    cp_directions = [1, -1, 1]
    # ===== ボスHPスケール調整 =====
    boss_hp = int(80 + (level + 1) ** 1.8 * 10)
    max_boss_hp = boss_hp

    bullets = []
    player_bullets = []
    explosions = []

    # ===== 追加要素 =====
    shake_timer = 0

    combo = 0
    combo_timer = 0

    respawn_timer = 0
    player_dead = False

    # ===== 味方CP（弱体＋レベルで強化）=====
    cp_allies = [
        pygame.Rect(WIDTH // 2 - 120, HEIGHT - 200, 40, 40),
        pygame.Rect(WIDTH // 2, HEIGHT - 230, 40, 40),  # ← 追加（中央）
        pygame.Rect(WIDTH // 2 + 80, HEIGHT - 200, 40, 40)
    ]
    cp_pos = [
        float(cp_allies[0].x),
        float(cp_allies[1].x),
        float(cp_allies[2].x)
    ]

    # 元：5固定 → 弱体＆スケール
    ally_hp = [3 + level // 5, 3 + level // 5, 3 + level // 5]
    ally_respawn = [0, 0, 0]

    # ===== ボタン =====
    left_btn = pygame.Rect(30, HEIGHT - 160, 80, 80)
    right_btn = pygame.Rect(130, HEIGHT - 160, 80, 80)
    shoot_btn = pygame.Rect(WIDTH - 110, HEIGHT - 160, 80, 80)
    special_btn = pygame.Rect(WIDTH - 110, HEIGHT - 250, 80, 60)

    # ===== バフボタン =====
    buff_c_btn = pygame.Rect(230, HEIGHT - 160, 40, 40)
    buff_s_btn = pygame.Rect(275, HEIGHT - 160, 40, 40)
    buff_h_btn = pygame.Rect(320, HEIGHT - 160, 40, 40)

    # ===== ゲージ =====
    special_gauge = 0
    special_timer = 0

    buff_gauge = 0
    buff_timer = 0

    cooldown_reduction = 0
    attack_power = 0

    shoot_cooldown = 0

    active_touches = {}
    start_time = pygame.time.get_ticks()

    boss_direction = 1

    while True:
        clock.tick(60)
        screen.fill(BLACK)

        # ===== 揺れ =====
        offset = random.randint(-4, 4) if shake_timer > 0 else 0
        if shake_timer > 0:
            shake_timer -= 1

        # ===== 入力 =====
        moving_left = moving_right = shooting = special = False
        buff_c = buff_s = buff_h = False

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "QUIT", 0, 0
            if e.type in (pygame.FINGERDOWN, pygame.FINGERMOTION):
                active_touches[e.finger_id] = (e.x, e.y)
            if e.type == pygame.FINGERUP:
                active_touches.pop(e.finger_id, None)

        for tx, ty in active_touches.values():
            x, y = tx * WIDTH, ty * HEIGHT

            if left_btn.collidepoint((x, y)): moving_left = True
            if right_btn.collidepoint((x, y)): moving_right = True
            if shoot_btn.collidepoint((x, y)): shooting = True
            if special_btn.collidepoint((x, y)): special = True

            if buff_c_btn.collidepoint((x, y)): buff_c = True
            if buff_s_btn.collidepoint((x, y)): buff_s = True
            if buff_h_btn.collidepoint((x, y)): buff_h = True

        # ===== ゲージ =====
        special_timer += 1
        if special_timer >= 60:
            special_timer = 0
            special_gauge = min(10, special_gauge + 1)

        # 🔥 バフ10秒でMAX
        buff_timer += 1
        if buff_timer >= 30:
            buff_timer = 0
            buff_gauge = min(20, buff_gauge + 1)

        # ===== バフ発動 =====
        if buff_gauge >= 20:
            if buff_c:
                cooldown_reduction += 0.1
                buff_gauge = 0
            elif buff_s:
                attack_power += 0.3
                buff_gauge = 0
            elif buff_h:
                player_hp = min(max_player_hp, player_hp + 2)
                buff_gauge = 0

        # ===== プレイヤー復活処理 =====
        if player_dead:
            respawn_timer += 1

            if respawn_timer >= 300:
                player_hp = max_player_hp
                player_dead = False
                respawn_timer = 0
                player.centerx = WIDTH // 2

        else:
            # ===== プレイヤー操作 =====
            if moving_left: player.x -= 6
            if moving_right: player.x += 6

            if shoot_cooldown > 0:
                shoot_cooldown -= 1

            if shooting and shoot_cooldown == 0:
                player_bullets.append({
                    "rect": pygame.Rect(player.centerx - 5, player.y, 6, 12),
                    "power": 1 + combo + attack_power
                })
                shoot_cooldown = max(1, int(20 - cooldown_reduction * 60))

            # ===== スペシャル =====
            if special and special_gauge >= 10:
                player_bullets.append({
                    "rect": pygame.Rect(player.centerx - 15, player.y, 30, 30),
                    "power": 3 + attack_power,
                    "pierce": True,
                    "hit_enemy": False,
                    "color": PURPLE
                })
                special_gauge = 0

            player.x = max(0, min(WIDTH - player.width, player.x))

        # ===== ボス移動（ランダム追加）=====
        boss.x += boss_direction * (3 + level * 0.3)
        if boss.left <= 0 or boss.right >= WIDTH:
            boss_direction *= -1

        # ===== 味方CP（完成版）=====
        for i, cp in enumerate(cp_allies):

            if ally_hp[i] > 0:

                target_x = boss.centerx

                # 移動
                if i == 0:
                    cp_pos[i] += (target_x - cp_pos[i]) * 0.08
                    cp.x = int(cp_pos[i])

                elif i == 1:
                    cp.x += (target_x - cp.centerx) * 0.05

                elif i == 2:
                    cp.x += cp_directions[i] * 3
                    if cp.left <= 0 or cp.right >= WIDTH:
                        cp_directions[i] *= -1

                cp.x = max(0, min(WIDTH - cp.width, cp.x))

                # 攻撃
                if i == 0:
                    if random.randint(0, max(40 - level, 10)) == 0:
                        player_bullets.append({
                            "rect": pygame.Rect(cp.centerx, cp.y, 6, 12),
                            "power": 1 + attack_power,
                            "ally": True
                        })

                elif i == 1:
                    if random.randint(0, max(30 - level, 8)) == 0:
                        player_bullets.append({
                            "rect": pygame.Rect(cp.centerx, cp.y, 6, 12),
                            "power": 1.2 + attack_power,
                            "ally": True
                        })

                elif i == 2:
                    if random.randint(0, max(25 - level, 6)) == 0:
                        for _ in range(2):
                            player_bullets.append({
                                "rect": pygame.Rect(cp.centerx + random.randint(-10, 10), cp.y, 6, 12),
                                "power": 0.7 + attack_power,
                                "ally": True
                            })

            else:
                # 復活
                ally_respawn[i] += 1
                if ally_respawn[i] >= 300:
                    ally_hp[i] = 3 + level // 5
                    ally_respawn[i] = 0

        # ===== ボス弾 =====
        if random.randint(0, 15) == 0:
            bullets.append(pygame.Rect(boss.centerx, boss.bottom, 14, 14))
        # ===== 弾移動 =====
        for b in bullets:
            b.y += 5 + level

        for pb in player_bullets[:]:
            pb["rect"].y -= 8

        # ===== 弾相殺（全部対応）=====
        for pb in player_bullets[:]:
            for eb in bullets[:]:
                if pb["rect"].colliderect(eb):
                    bullets.remove(eb)
                    if not pb.get("pierce"):
                        player_bullets.remove(pb)
                    break

                # ===== ボスヒット（修正版）=====
                for pb in player_bullets[:]:
                    if boss.colliderect(pb["rect"]):

                        # ダメージ
                        boss_hp -= pb["power"]
                        shake_timer = 6
                        explosions.append([boss.centerx, boss.centery, 6])

                        # コンボ（味方弾は除外）
                        if not pb.get("ally"):
                            combo += 1
                            combo_timer = 180
                            buff_gauge = min(20, buff_gauge + 1)

                        # ===== 弾消す処理 =====
                        # 通常弾 → 必ず消える
                        # スペシャル弾 → 1回当たったら消える
                        player_bullets.remove(pb)

                boss_hp -= pb["power"]
                shake_timer = 6
                explosions.append([boss.centerx, boss.centery, 6])

                # 🔥 味方弾はコンボ＆バフに影響しない
                if not pb.get("ally"):
                    combo += 1
                    combo_timer = 180  # 3秒
                    buff_gauge = min(20, buff_gauge + 1)

                if not pb.get("pierce"):
                    player_bullets.remove(pb)

        # ===== 被弾 =====
        for b in bullets[:]:
            if not player_dead and player.colliderect(b):
                player_hp -= 1
                shake_timer = 8
                explosions.append([player.centerx, player.centery, 6])
                bullets.remove(b)

                if player_hp <= 0:
                    player_dead = True
                    combo = 0  # コンボリセット

        # ===== 味方被弾 =====
        for i, cp in enumerate(cp_allies):
            for b in bullets[:]:
                if ally_hp[i] > 0 and cp.colliderect(b):
                    ally_hp[i] -= 1
                    explosions.append([cp.centerx, cp.centery, 5])
                    bullets.remove(b)

        # ===== コンボ減少（3秒）=====
        if combo_timer > 0:
            combo_timer -= 1
        else:
            combo = 0

        # ===== 時間制限 =====
        time_sec = (pygame.time.get_ticks() - start_time) / 1000
        if time_sec >= 120:
            return "LOSE", 0, time_sec

        # ===== ボス撃破 =====
        if boss_hp <= 0:
            return "WIN", int((level + 1) ** 3 * 150), time_sec

        # ===== 描画 =====
        pygame.draw.rect(screen, BLUE, player.move(offset, 0) if not player_dead else player)
        pygame.draw.rect(screen, PURPLE, boss.move(offset, 0))

        # 味方
        for i, cp in enumerate(cp_allies):
            color = GREEN if ally_hp[i] > 0 else GRAY
            pygame.draw.rect(screen, color, cp.move(offset, 0))

        # ボス弾
        for b in bullets:
            pygame.draw.rect(screen, RED, b.move(offset, 0))

        # プレイヤー弾
        for pb in player_bullets:
            color = pb.get("color", WHITE)
            pygame.draw.rect(screen, color, pb["rect"].move(offset, 0))

        # ===== 爆発 =====
        for exp in explosions[:]:
            pygame.draw.circle(screen, (255, 200, 0), (exp[0] + offset, exp[1]), exp[2])
            pygame.draw.circle(screen, (255, 100, 0), (exp[0] + offset, exp[1]), exp[2] // 2)
            exp[2] += 2
            if exp[2] > 25:
                explosions.remove(exp)

        # ===== HPバー =====
        pygame.draw.rect(screen, WHITE, (50, HEIGHT - 40, 300, 20), 2)
        pygame.draw.rect(screen, BLUE, (50, HEIGHT - 40, 300 * (player_hp / max_player_hp), 20))

        pygame.draw.rect(screen, WHITE, (50, 10, 300, 20), 2)
        pygame.draw.rect(screen, RED, (50, 10, 300 * (boss_hp / max_boss_hp), 20))

        # ===== SPバー =====
        pygame.draw.rect(screen, WHITE, (WIDTH - 110, HEIGHT - 300, 80, 10), 2)
        pygame.draw.rect(screen, YELLOW, (WIDTH - 110, HEIGHT - 300, 80 * (special_gauge / 10), 10))

        # ===== ボタン =====
        pygame.draw.rect(screen, GREEN, left_btn)
        pygame.draw.rect(screen, GREEN, right_btn)

        shoot_color = GRAY if shoot_cooldown > 0 else RED
        pygame.draw.rect(screen, shoot_color, shoot_btn)

        pygame.draw.rect(screen, YELLOW if special_gauge >= 10 else GRAY, special_btn)

        buff_ready = buff_gauge >= 20
        pygame.draw.rect(screen, YELLOW if buff_ready else GRAY, buff_c_btn)
        pygame.draw.rect(screen, YELLOW if buff_ready else GRAY, buff_s_btn)
        pygame.draw.rect(screen, YELLOW if buff_ready else GRAY, buff_h_btn)

        # ===== テキスト =====
        screen.blit(font_small.render("L", True, WHITE),
                    font_small.render("L", True, WHITE).get_rect(center=left_btn.center))
        screen.blit(font_small.render("R", True, WHITE),
                    font_small.render("R", True, WHITE).get_rect(center=right_btn.center))
        screen.blit(font_small.render("SHOT", True, WHITE),
                    font_small.render("SHOT", True, WHITE).get_rect(center=shoot_btn.center))
        screen.blit(font_small.render("SP", True, WHITE),
                    font_small.render("SP", True, WHITE).get_rect(center=special_btn.center))

        screen.blit(font_small.render("C", True, WHITE),
                    font_small.render("C", True, WHITE).get_rect(center=buff_c_btn.center))
        screen.blit(font_small.render("S", True, WHITE),
                    font_small.render("S", True, WHITE).get_rect(center=buff_s_btn.center))
        screen.blit(font_small.render("H", True, WHITE),
                    font_small.render("H", True, WHITE).get_rect(center=buff_h_btn.center))

        # ===== バフゲージ =====
        pygame.draw.rect(screen, WHITE, (240, HEIGHT - 110, 100, 6), 1)
        pygame.draw.rect(screen, YELLOW, (240, HEIGHT - 110, 100 * (buff_gauge / 20), 6))

        # ===== 時間表示 =====
        screen.blit(font_small.render(f"{time_sec:.2f}s", True, WHITE), (10, 10))

        # ===== コンボ表示 =====
        if combo > 0:
            screen.blit(font_small.render(f"{combo} COMBO", True, YELLOW),
                        (WIDTH // 2 - 50, 120))

        pygame.display.flip()
        await asyncio.sleep(0)

# =========================
# 結果画面（全モード対応）
# =========================
async def show_result(result, level, score=0, time_sec=0):
    retry_button = Button((WIDTH // 2 - 100, HEIGHT // 2 + 20, 200, 60), GREEN, "RETRY")
    title_button = Button((WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 60), BLUE, "TITLE")

    while True:
        screen.fill(BLACK)

        if result == "WIN":
            text = font_small.render(f"YOU WIN! Level {level + 1}", True, YELLOW)
        elif result == "LOSE":
            text = font_small.render(f"YOU LOSE! Level {level + 1}", True, RED)
        else:
            text = font_small.render("GAME OVER", True, WHITE)

        screen.blit(text, text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80)))

        score_text = font_small.render(f"SCORE: {int(score)}", True, WHITE)
        time_text = font_small.render(f"TIME: {time_sec:.2f}s", True, WHITE)

        screen.blit(score_text, score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))
        screen.blit(time_text, time_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 10)))

        retry_button.draw(screen)
        title_button.draw(screen)

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                return "QUIT"

            if e.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                pos = e.pos if e.type == pygame.MOUSEBUTTONDOWN else (e.x * WIDTH, e.y * HEIGHT)

                if retry_button.rect.collidepoint(pos):
                    return "RETRY"

                if title_button.rect.collidepoint(pos):
                    return "TITLE"

        await asyncio.sleep(0)

# =========================
# メイン処理
# =========================
async def main():
    while True:

        screen.fill(BLACK)
        t = font_small.render("Tap to Start", True, WHITE)
        screen.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        pygame.display.flip()

        waiting = True
        while waiting:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return
                if e.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                    waiting = False
            await asyncio.sleep(0)

        mode_buttons = [
            Button((140, 200, 200, 60), BLUE, "SHOOTING"),
            Button((140, 300, 200, 60), GREEN, "DODGE"),
            Button((140, 400, 200, 60), PURPLE, "BOSS")
        ]

        selecting = True
        mode = "shoot"

        while selecting:
            screen.fill(BLACK)

            for b in mode_buttons:
                b.draw(screen)

            pygame.display.flip()

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return

                if e.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                    pos = e.pos if e.type == pygame.MOUSEBUTTONDOWN else (e.x * WIDTH, e.y * HEIGHT)

                    for b in mode_buttons:
                        if b.rect.collidepoint(pos):
                            if b.text == "SHOOTING":
                                mode = "shoot"
                            elif b.text == "DODGE":
                                mode = "dodge"
                            elif b.text == "BOSS":
                                mode = "boss"

                            selecting = False

            await asyncio.sleep(0)

        difficulty = "normal"

        if mode == "shoot":

            diff_buttons = [
                Button((140, 180, 200, 60), GREEN, "EASY"),
                Button((140, 260, 200, 60), BLUE, "NORMAL"),
                Button((140, 340, 200, 60), RED, "HARD"),
                Button((140, 420, 200, 60), PURPLE, "ULTRA"),
            ]

            selecting = True

            while selecting:
                screen.fill(BLACK)

                for b in diff_buttons:
                    b.draw(screen)

                pygame.display.flip()

                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        return

                    if e.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                        pos = e.pos if e.type == pygame.MOUSEBUTTONDOWN else (e.x * WIDTH, e.y * HEIGHT)

                        for b in diff_buttons:
                            if b.rect.collidepoint(pos):
                                difficulty = b.text.lower()
                                selecting = False

                await asyncio.sleep(0)

        level = 0
        selecting = True

        level_buttons = []
        for i in range(20):
            x = 20 + (i % 10) * 45
            y = 300 + (i // 10) * 60
            level_buttons.append(
                Button((x, y, 40, 40), (0, max(0, 255 - i * 10), 255), str(i + 1))
            )

        while selecting:
            screen.fill(BLACK)

            screen.blit(font_small.render("Select Level", True, WHITE), (150, 200))

            for b in level_buttons:
                b.draw(screen)

            pygame.display.flip()

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return

                if e.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                    pos = e.pos if e.type == pygame.MOUSEBUTTONDOWN else (e.x * WIDTH, e.y * HEIGHT)

                    for i, b in enumerate(level_buttons):
                        if b.rect.collidepoint(pos):
                            level = i
                            selecting = False

            await asyncio.sleep(0)

        if mode == "dodge":
            result, score, time_sec = await dodge_game(level)

        elif mode == "boss":
            result, score, time_sec = await boss_battle(level)

        else:
            max_player_hp = 10

            if difficulty == "easy":
                max_player_hp = 20
            elif difficulty == "normal":
                max_player_hp = 10
            elif difficulty == "hard":
                max_player_hp = 5
            elif difficulty == "ultra":
                max_player_hp = 1

            result, score, time_sec = await normal_game(level, max_player_hp)

        # ===== スコア計算 =====
        if mode == "dodge":
            score = int(time_sec * (level + 1) * 50)

        elif mode == "boss":
            if result == "LOSE":
                score = int(time_sec * 10)
            else:
                score = int((level + 1) * 5000 - time_sec * 200)

        else:
            if result == "LOSE":
                score = 0
            else:
                score = int((level + 1) ** 3 * 100 - time_sec * 10)

        action = await show_result(result, level, score, time_sec)

        if action == "QUIT":
            return
        elif action == "TITLE":
            continue
        elif action == "RETRY":
            continue


# 実行
asyncio.run(main())