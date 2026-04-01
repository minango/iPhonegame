import pygame
import asyncio
import random

pygame.init()

WIDTH, HEIGHT = 480, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

WHITE = (255,255,255)
RED = (255,0,0)
BLUE = (0,0,255)
BLACK = (0,0,0)
GREEN = (0,180,0)
GRAY = (100,100,100)
YELLOW = (255,255,0)
PURPLE = (180,0,255)

font_small = pygame.font.SysFont(None,28)

cp_levels = [
    {"shoot_rate":80,"speed":2},
    {"shoot_rate":60,"speed":3},
    {"shoot_rate":50,"speed":4},
    {"shoot_rate":40,"speed":5},
    {"shoot_rate":30,"speed":6},
    {"shoot_rate":20,"speed":7},
    {"shoot_rate":15,"speed":8},
    {"shoot_rate":10,"speed":9},
    {"shoot_rate":6,"speed":10},
    {"shoot_rate":3,"speed":12},
]

for i in range(10,20):
    cp_levels.append({
        "shoot_rate": max(1, 3 - (i-9)),
        "speed": 12 + (i-9)*2
    })

best_scores = [0]*20

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
# ボス戦（修正版）
# =========================
async def boss_raid():
    player_hp = 10
    max_player_hp = 10
    allies = []
    for i in range(3):
        allies.append({
            "rect": pygame.Rect(100 + i * 100, HEIGHT - 200, 40, 40),
            "hp": 5,
            "cooldown": random.randint(0, 30)
        })
    player = pygame.Rect(WIDTH // 2 - 25, HEIGHT - 260, 50, 50)

    boss = pygame.Rect(WIDTH // 2 - 60, 50, 120, 120)
    boss_hp = 300

    bullets = []
    enemy_bullets = []

    shoot_cd = 0
    shoot_cooldown = 0  # ★これ追加
    cooldown_time = 10  # ★これもあると便利
    special_gauge = 20

    player_alive = True
    respawn_timer = 0

    invincible_timer = 0  # 無敵時間
    player_hp = 10
    max_player_hp = 10

    left_btn = pygame.Rect(30, HEIGHT-160, 80, 80)
    right_btn = pygame.Rect(130, HEIGHT-160, 80, 80)
    shoot_btn = pygame.Rect(WIDTH-110, HEIGHT-160, 80, 80)
    special_btn = pygame.Rect(WIDTH-110, HEIGHT-250, 80, 60)

    active_touches = {}
    # ===== 味方AI（毎フレーム動く）=====

    while True:
        # ===== 無敵タイマー減少 =====
        if invincible_timer > 0:
            invincible_timer -= 1
        # ===== ボス移動 =====
        boss.x += random.choice([-3, -2, -1, 1, 2, 3])

        # 画面外に出ないようにする
        boss.x = max(0, min(WIDTH - boss.width, boss.x))
        for a in allies:
            dx = boss.centerx - a["rect"].centerx

            # 移動
            if abs(dx) > 3:
                a["rect"].x += dx * 0.05

            # 画面外防止
            a["rect"].x = max(0, min(WIDTH - a["rect"].width, a["rect"].x))

            # 攻撃（クールダウン）
            a["cooldown"] -= 1
            if a["cooldown"] <= 0:
                bullets.append({
                    "rect": pygame.Rect(a["rect"].centerx - 5, a["rect"].y, 10, 10),
                    "power": 1
                })
                a["cooldown"] = 30
        if shoot_cooldown > 0:
            shoot_cooldown -= 1
        clock.tick(60)
        screen.fill(BLACK)

        moving_left = moving_right = shooting = special = False

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            if e.type in (pygame.FINGERDOWN, pygame.FINGERMOTION):
                active_touches[e.finger_id]=(e.x,e.y)
            if e.type==pygame.FINGERUP:
                active_touches.pop(e.finger_id,None)

        for tx,ty in active_touches.values():
            x,y=tx*WIDTH,ty*HEIGHT
            if left_btn.collidepoint((x,y)): moving_left=True
            if right_btn.collidepoint((x,y)): moving_right=True
            if shoot_btn.collidepoint((x,y)): shooting=True
            if special_btn.collidepoint((x,y)): special=True

            if player_alive:
                if moving_left: player.x -= 5
                if moving_right: player.x += 5

                player.x = max(0, min(WIDTH - player.width, player.x))

        if shoot_cd > 0: shoot_cd -= 1

        if not player_alive:
            respawn_timer -= 1
            if respawn_timer <= 0:
                player_alive = True
                player.x = WIDTH // 2
                invincible_timer = 120
        else:
            if shooting and shoot_cooldown == 0:
                bullets.append({
                    "rect": pygame.Rect(player.centerx - 5, player.y, 10, 10),
                    "power": 1
                })
                shoot_cooldown = cooldown_time

        if special and special_gauge >= 20:
            bullets.append({"rect": pygame.Rect(player.centerx - 20, player.y, 40, 40), "power": 5})
            special_gauge = 0

            # ===== 味方AI（ここに入れる！！）=====
            for a in allies:
                # ボスに向かって動く
                dx = boss.centerx - a["rect"].centerx
                if abs(dx) > 5:
                    a["rect"].x += dx * 0.05

                # 画面外に出ないようにする
                a["rect"].x = max(0, min(WIDTH - a["rect"].width, a["rect"].x))

                # 攻撃（クールダウン）
                a["cooldown"] -= 1
                if a["cooldown"] <= 0:
                    bullets.append({
                        "rect": pygame.Rect(a["rect"].centerx - 5, a["rect"].y, 10, 10),
                        "power": 1
                    })
                    a["cooldown"] = 30

        for i in range(3):
            if random.randint(0, 10) == 0:
                enemy_bullets.append(
                    pygame.Rect(boss.centerx - 5 + i * 15, boss.bottom, 10, 10)
                )

        for b in bullets:
            b["rect"].y -= 8
        for b in enemy_bullets:
            b.y += 6

        for b in bullets[:]:
            if boss.colliderect(b["rect"]):
                boss_hp -= b["power"]
                bullets.remove(b)

                for b in enemy_bullets[:]:
                    if player_alive and invincible_timer == 0 and player.colliderect(b):
                        enemy_bullets.remove(b)
                        player_hp -= 1

                        if player_hp <= 0:
                            player_alive = False
                            respawn_timer = 600
                            player_hp = max_player_hp
                if player_alive and invincible_timer == 0 and player.colliderect(b):
                    enemy_bullets.remove(b)

                    player_hp -= 1

                    if player_hp <= 0:
                        player_alive = False
                        respawn_timer = 600  # 10秒
                        player_hp = max_player_hp
                enemy_bullets.remove(b)
                player_hp -= 1

                if player_hp <= 0:
                    player_alive = False
                    respawn_timer = 600
                    player_hp = max_player_hp  # 復活時に全回復
                respawn_timer = 600

        # プレイヤー描画（外に出す！）
            if player_alive:
                if moving_left: player.x -= 5
                if moving_right: player.x += 5
            pygame.draw.rect(screen, BLUE, player)
        else:
            screen.blit(font_small.render("RESPAWN...", True, WHITE), (180, HEIGHT - 200))
        if player_alive:
            # 無敵中は点滅
            if invincible_timer > 0 and pygame.time.get_ticks() % 300 < 150:
                pass
            else:
                pygame.draw.rect(screen, BLUE, player)
        else:
            screen.blit(font_small.render("RESPAWN...", True, WHITE), (180, HEIGHT - 200))
        pygame.draw.rect(screen, RED, boss)

        # 味方を描画
        for a in allies:
            pygame.draw.rect(screen, GREEN, a["rect"])

        for b in bullets:
            pygame.draw.rect(screen, WHITE, b["rect"])
        for b in enemy_bullets:
            pygame.draw.rect(screen, YELLOW, b)

        # HPバー
        x = (WIDTH-200)//2
        pygame.draw.rect(screen, WHITE, (x,10,200,20),2)
        pygame.draw.rect(screen, RED, (x,10,200*(boss_hp/300),20))

        # ===== プレイヤーHPバー =====
        pygame.draw.rect(screen, WHITE, (140, HEIGHT - 40, 200, 20), 2)
        pygame.draw.rect(screen, BLUE, (140, HEIGHT - 40, 200 * (player_hp / max_player_hp), 20))

        # ボタン
        pygame.draw.rect(screen, GREEN, left_btn)
        pygame.draw.rect(screen, GREEN, right_btn)
        # クールタイム中は灰色
        if shoot_cooldown > 0:
            shoot_color = GRAY
        else:
            shoot_color = RED

        pygame.draw.rect(screen, shoot_color, shoot_btn)
        pygame.draw.rect(screen, YELLOW if special_gauge>=20 else GRAY, special_btn)

        screen.blit(font_small.render("L",True,WHITE), font_small.render("L",True,WHITE).get_rect(center=left_btn.center))
        screen.blit(font_small.render("R",True,WHITE), font_small.render("R",True,WHITE).get_rect(center=right_btn.center))
        screen.blit(font_small.render("SHOOT",True,WHITE), font_small.render("SHOOT",True,WHITE).get_rect(center=shoot_btn.center))
        screen.blit(font_small.render("SP",True,WHITE), font_small.render("SP",True,WHITE).get_rect(center=special_btn.center))

        pygame.display.flip()
        if boss_hp <= 0:
            return


# =========================
# メイン
# =========================
async def main():
    while True:
        screen.fill(BLACK)
        t = font_small.render("Tap to Start", True, WHITE)
        screen.blit(t, t.get_rect(center=(WIDTH//2, HEIGHT//2)))
        pygame.display.flip()

        start = False
        while not start:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return
                if e.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
                    start = True
            await asyncio.sleep(0)

        # ===== モード選択 =====
        normal_btn = Button((80, 300, 140, 80), BLUE, "NORMAL")
        boss_btn = Button((260, 300, 140, 80), RED, "BOSS")

        selecting = True
        mode = "normal"
        active_touches = {}
        while selecting:
            screen.fill(BLACK)
            screen.blit(font_small.render("Select Mode", True, WHITE), (150, 200))

            normal_btn.draw(screen)
            boss_btn.draw(screen)

            pygame.display.flip()

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return
                if e.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
                    pos = (e.x * WIDTH, e.y * HEIGHT) if e.type == pygame.FINGERDOWN else e.pos

                    if normal_btn.rect.collidepoint(pos):
                        mode = "normal"
                        selecting = False

                    if boss_btn.rect.collidepoint(pos):
                        mode = "boss"
                        selecting = False

            await asyncio.sleep(0)

        # ===== 分岐 =====
        if mode == "boss":
            await boss_raid()
            continue

        buttons = [
            Button((60,200,120,50),GREEN,"Easy"),
            Button((200,200,120,50),BLUE,"Normal"),
            Button((60,270,120,50),GRAY,"Hard"),
            Button((200,270,120,50),RED,"Ultra"),
        ]
        selecting=True
        max_player_hp=10
        while selecting:
            screen.fill(BLACK)
            screen.blit(font_small.render("Select Difficulty",True,WHITE),(120,100))
            for b in buttons: b.draw(screen)
            pygame.display.flip()
            for e in pygame.event.get():
                if e.type==pygame.QUIT: return
                if e.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
                    pos = (e.x*WIDTH,e.y*HEIGHT) if e.type==pygame.FINGERDOWN else e.pos
                    for b in buttons:
                        if b.rect.collidepoint(pos):
                            if b.text=="Easy": max_player_hp=20
                            elif b.text=="Normal": max_player_hp=10
                            elif b.text=="Hard": max_player_hp=5
                            elif b.text=="Ultra": max_player_hp=1
                            selecting=False
            await asyncio.sleep(0)

        # ===== ステージ選択 =====
        # ===== ステージ選択 =====
        level_buttons = [Button((20 + (i % 10) * 45, 350 + (i // 10) * 60, 40, 40), (0, 255 - 10 * i, 255), str(i + 1))
                         for i in range(20)]
        selecting=True
        cp_level=0
        while selecting:
            screen.fill(BLACK)
            screen.blit(font_small.render("Select CP Level",True,WHITE),(130,100))
            for b in level_buttons: b.draw(screen)
            pygame.display.flip()
            for e in pygame.event.get():
                if e.type==pygame.QUIT: return
                if e.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):

                    if e.type == pygame.FINGERDOWN:
                        pos = (e.x * WIDTH, e.y * HEIGHT)
                    else:
                        pos = e.pos

                    for b in buttons:
                        if b.rect.collidepoint(pos):
                            if b.text == "Easy":
                                max_player_hp = 20
                            elif b.text == "Normal":
                                max_player_hp = 10
                            elif b.text == "Hard":
                                max_player_hp = 5
                            elif b.text == "Ultra":
                                max_player_hp = 1
                            selecting = False
                    if e.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):

                        if e.type == pygame.FINGERDOWN:
                            pos = (e.x * WIDTH, e.y * HEIGHT)
                        else:
                            pos = e.pos

                        for i, b in enumerate(level_buttons):
                            if b.rect.collidepoint(pos):
                                cp_level = i
                                selecting = False
                    for i,b in enumerate(level_buttons):
                        if b.rect.collidepoint(pos):
                            cp_level=i
                            selecting=False
            await asyncio.sleep(0)

        # ===== ゲーム開始 =====
        player=pygame.Rect(WIDTH//2-25, HEIGHT-260,50,50)
        enemy=pygame.Rect(WIDTH//2-25,50,50,50)

        player_bullets=[]
        enemy_bullets=[]
        explosions=[]

        player_hp=max_player_hp
        enemy_hp=3+cp_level*2
        max_enemy_hp=enemy_hp

        start_time = pygame.time.get_ticks()

        left_btn = pygame.Rect(30, HEIGHT-160, 80, 80)
        right_btn = pygame.Rect(130, HEIGHT-160, 80, 80)
        shoot_btn = pygame.Rect(WIDTH-110, HEIGHT-160, 80, 80)
        special_btn = pygame.Rect(WIDTH-110, HEIGHT-250, 80, 60)

        shoot_cooldown = 0
        cooldown_time = 30

        special_gauge = 0
        special_timer = 0

        combo = 0
        combo_timer = 0

        shake_timer = 0
        blink_timer = 0

        active_touches={}

        running=True
        result=None

        while running:
            clock.tick(60)
            screen.fill(BLACK)
            blink_timer += 1

            offset = random.randint(-3,3) if shake_timer>0 else 0
            if shake_timer>0: shake_timer -= 1

            moving_left = moving_right = shooting = special = False
            for e in pygame.event.get():
                if e.type==pygame.QUIT: return
                if e.type in (pygame.FINGERDOWN, pygame.FINGERMOTION):
                    active_touches[e.finger_id]=(e.x,e.y)
                if e.type==pygame.FINGERUP:
                    active_touches.pop(e.finger_id,None)
            for tx,ty in active_touches.values():
                x,y=tx*WIDTH,ty*HEIGHT
                if left_btn.collidepoint((x,y)): moving_left=True
                if right_btn.collidepoint((x,y)): moving_right=True
                if shoot_btn.collidepoint((x,y)): shooting=True
                if special_btn.collidepoint((x,y)): special=True

            if shoot_cooldown>0: shoot_cooldown-=1

            special_timer += 1
            if special_timer >= 60:
                special_timer = 0
                special_gauge = min(20, special_gauge + 1)

            if shooting and shoot_cooldown==0:
                player_bullets.append({"rect":pygame.Rect(player.centerx-5, player.y,10,10),"power":1+combo})
                shoot_cooldown=cooldown_time

            if special and special_gauge>=20:
                player_bullets.append({
                    "rect":pygame.Rect(player.centerx-15, player.y,30,30),
                    "power":3,
                    "pierce":True,
                    "hit_enemy":False
                })
                special_gauge=0

            player.x = max(0,min(WIDTH-player.width,player.x))

            dx = player.centerx-enemy.centerx
            direction = dx/abs(dx) if dx!=0 else 0
            enemy.x += direction*cp_levels[cp_level]["speed"]

            if random.randint(0,cp_levels[cp_level]["shoot_rate"])==0:
                enemy_bullets.append(pygame.Rect(enemy.centerx-5,enemy.bottom,10,10))

            for b in player_bullets:
                b["rect"].y-=7
            for b in enemy_bullets:
                b.y+=7

            # 相殺
            for pb in player_bullets[:]:
                for eb in enemy_bullets[:]:
                    if pb["rect"].colliderect(eb):
                        if not pb.get("pierce"):
                            player_bullets.remove(pb)
                        enemy_bullets.remove(eb)
                        break

            for b in player_bullets[:]:
                if enemy.colliderect(b["rect"]):
                    if b.get("pierce") and b.get("hit_enemy"):
                        continue
                    if b.get("pierce"):
                        b["hit_enemy"]=True
                    enemy_hp -= b["power"]
                    shake_timer=3
                    explosions.append([enemy.centerx, enemy.centery, 5])
                    if not b.get("pierce"): player_bullets.remove(b)
                    combo += 1
                    combo_timer = 180

            for b in enemy_bullets[:]:
                if player.colliderect(b):
                    enemy_bullets.remove(b)
                    player_hp-=1
                    shake_timer=5
                    explosions.append([player.centerx, player.centery, 5])

            if combo_timer>0:
                combo_timer-=1
            else:
                combo=0

            if player_hp<=0:
                result="LOSE"
                running=False
            if enemy_hp<=0:
                result="WIN"
                running=False

            # ===== 描画 =====
            pygame.draw.rect(screen, BLUE, player.move(offset,0))
            pygame.draw.rect(screen, RED, enemy.move(offset,0))

            for b in player_bullets:
                color = PURPLE if b.get("pierce") else WHITE
                pygame.draw.rect(screen, color, b["rect"].move(offset,0))
            for b in enemy_bullets:
                pygame.draw.rect(screen, WHITE, b.move(offset,0))

            for exp in explosions[:]:
                pygame.draw.circle(screen, (255,200,0), (exp[0]+offset, exp[1]), exp[2])
                pygame.draw.circle(screen, (255,100,0), (exp[0]+offset, exp[1]), exp[2]//2)
                exp[2]+=2
                if exp[2]>20: explosions.remove(exp)

            def get_hp_color(hp,max_hp):
                ratio=hp/max_hp
                if ratio<0.2: return RED if blink_timer%20<10 else BLACK
                elif ratio<0.4: return YELLOW
                else: return RED
            def get_player_color(hp,max_hp):
                ratio=hp/max_hp
                if ratio<0.2: return RED if blink_timer%20<10 else BLACK
                elif ratio<0.4: return YELLOW
                else: return BLUE

            x = (WIDTH-200)//2
            pygame.draw.rect(screen, WHITE, (x,10,200,20),2)
            pygame.draw.rect(screen, get_hp_color(enemy_hp,max_enemy_hp), (x,10,200*(enemy_hp/max_enemy_hp),20))
            pygame.draw.rect(screen, WHITE, (x,HEIGHT-40,200,20),2)
            pygame.draw.rect(screen, get_player_color(player_hp,max_player_hp), (x,HEIGHT-40,200*(player_hp/max_player_hp),20))

            pygame.draw.rect(screen, WHITE, (WIDTH-110, HEIGHT-300, 80, 10), 2)
            pygame.draw.rect(screen, YELLOW, (WIDTH-110, HEIGHT-300, 80*(special_gauge/20), 10))

            pygame.draw.rect(screen, GREEN, left_btn)
            pygame.draw.rect(screen, GREEN, right_btn)
            if shoot_cooldown > 0:
                shoot_color = GRAY
            else:
                shoot_color = RED

            pygame.draw.rect(screen, shoot_color, shoot_btn)
            pygame.draw.rect(screen, YELLOW if special_gauge>=20 else GRAY, special_btn)

            screen.blit(font_small.render("L",True,WHITE), font_small.render("L",True,WHITE).get_rect(center=left_btn.center))
            screen.blit(font_small.render("R",True,WHITE), font_small.render("R",True,WHITE).get_rect(center=right_btn.center))
            screen.blit(font_small.render("SHOOT",True,WHITE), font_small.render("SHOOT",True,WHITE).get_rect(center=shoot_btn.center))
            screen.blit(font_small.render("SP",True,WHITE), font_small.render("SP",True,WHITE).get_rect(center=special_btn.center))

            time_sec = (pygame.time.get_ticks() - start_time)/1000
            screen.blit(font_small.render(f"{time_sec:.2f}s",True,WHITE),(10,10))

            if combo>0:
                screen.blit(font_small.render(f"{combo} COMBO",True,YELLOW),(WIDTH//2-50,100))

            pygame.display.flip()
            await asyncio.sleep(0)

        # ===== 結果画面 =====
        end_time = pygame.time.get_ticks()
        time_sec = (end_time - start_time)/1000

        if result=="WIN":
            score = int((cp_level + 1)**2.5 * 500 / (time_sec + 1))
        else:
            score = 0

        # ステージごとにベストスコア更新
        if score > best_scores[cp_level]:
            best_scores[cp_level]=score

        retry_btn = Button((140,500,200,60),GREEN,"RETRY")
        waiting=True
        active_touches.clear()

        while waiting:
            screen.fill(BLACK)
            t1 = font_small.render(result,True,WHITE)
            t2 = font_small.render(f"TIME: {time_sec:.2f}s",True,WHITE)
            t3 = font_small.render(f"SCORE: {score}",True,WHITE)
            t4 = font_small.render(f"BEST: {best_scores[cp_level]}",True,YELLOW)

            screen.blit(t1,t1.get_rect(center=(WIDTH//2,200)))
            screen.blit(t2,t2.get_rect(center=(WIDTH//2,260)))
            screen.blit(t3,t3.get_rect(center=(WIDTH//2,320)))
            screen.blit(t4,t4.get_rect(center=(WIDTH//2,380)))

            retry_btn.draw(screen)
            pygame.display.flip()

            for e in pygame.event.get():
                if e.type==pygame.QUIT: return
                if e.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
                    pos = (e.x*WIDTH,e.y*HEIGHT) if e.type==pygame.FINGERDOWN else e.pos
                    if retry_btn.rect.collidepoint(pos):
                        active_touches.clear()
                        waiting=False

            await asyncio.sleep(0)

asyncio.run(main())