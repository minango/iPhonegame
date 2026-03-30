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

async def main():

    # ===== スタート =====
    waiting = True
    while waiting:
        screen.fill(BLACK)
        t = font_small.render("Tap to Start", True, WHITE)
        screen.blit(t, t.get_rect(center=(WIDTH//2, HEIGHT//2)))
        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            if e.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
                waiting = False

        await asyncio.sleep(0)

    while True:

        # ===== 難易度 =====
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
                if e.type==pygame.QUIT:
                    return

                if e.type == pygame.FINGERDOWN:
                    pos=(e.x*WIDTH,e.y*HEIGHT)
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    pos=e.pos
                else:
                    continue

                for b in buttons:
                    if b.rect.collidepoint(pos):
                        if b.text=="Easy": max_player_hp=20
                        elif b.text=="Normal": max_player_hp=10
                        elif b.text=="Hard": max_player_hp=5
                        elif b.text=="Ultra": max_player_hp=1
                        selecting=False

            await asyncio.sleep(0)

        # ===== ステージ =====
        level_buttons=[Button((20+i*45,350,40,40),(0,255-20*i,255),str(i+1)) for i in range(10)]
        selecting=True
        cp_level=0

        while selecting:
            screen.fill(BLACK)
            screen.blit(font_small.render("Select CP Level",True,WHITE),(130,100))
            for b in level_buttons: b.draw(screen)
            pygame.display.flip()

            for e in pygame.event.get():
                if e.type==pygame.QUIT:
                    return

                if e.type == pygame.FINGERDOWN:
                    pos=(e.x*WIDTH,e.y*HEIGHT)
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    pos=e.pos
                else:
                    continue

                for i,b in enumerate(level_buttons):
                    if b.rect.collidepoint(pos):
                        cp_level=i
                        selecting=False

            await asyncio.sleep(0)

        # ===== ゲーム =====
        player=pygame.Rect(WIDTH//2-25, HEIGHT-260,50,50)
        enemy=pygame.Rect(WIDTH//2-25,50,50,50)

        player_bullets=[]
        enemy_bullets=[]
        explosions=[]

        player_hp=max_player_hp
        enemy_hp=3+cp_level*2
        max_enemy_hp=enemy_hp

        start_time = pygame.time.get_ticks()

        left_btn = pygame.Rect(30, HEIGHT-120, 80, 80)
        right_btn = pygame.Rect(130, HEIGHT-120, 80, 80)
        shoot_btn = pygame.Rect(WIDTH-110, HEIGHT-120, 80, 80)

        shoot_cooldown = 0
        cooldown_time = 30

        active_touches={}

        running=True
        while running:
            clock.tick(60)
            screen.fill(BLACK)

            moving_left = moving_right = shooting = False

            for e in pygame.event.get():
                if e.type==pygame.QUIT:
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

            if shoot_cooldown>0:
                shoot_cooldown-=1

            if moving_left: player.x-=5
            if moving_right: player.x+=5

            if shooting and shoot_cooldown==0:
                player_bullets.append(pygame.Rect(player.centerx-5, player.y,10,10))
                shoot_cooldown=cooldown_time

            player.x = max(0,min(WIDTH-player.width,player.x))

            dx = player.centerx-enemy.centerx
            direction = dx/abs(dx) if dx!=0 else 0
            enemy.x += direction*cp_levels[cp_level]["speed"]
            enemy.x = max(0,min(WIDTH-enemy.width,enemy.x))

            if random.randint(0,cp_levels[cp_level]["shoot_rate"])==0:
                enemy_bullets.append(pygame.Rect(enemy.centerx-5,enemy.bottom,10,10))

            for b in player_bullets: b.y-=7
            for b in enemy_bullets: b.y+=7

            # 衝突
            for b in enemy_bullets[:]:
                if player.colliderect(b):
                    enemy_bullets.remove(b)
                    player_hp-=1
                    explosions.append([player.centerx, player.centery, 10])

            for b in player_bullets[:]:
                if enemy.colliderect(b):
                    player_bullets.remove(b)
                    enemy_hp-=1
                    explosions.append([enemy.centerx, enemy.centery, 10])

            # ===== 終了 =====
            if player_hp<=0 or enemy_hp<=0:

                end_time = pygame.time.get_ticks()
                time_sec = max(0.1, (end_time - start_time) / 1000)

                result = "WIN" if enemy_hp<=0 else "LOSE"

                if result == "WIN":
                    base_score = int(50000 / time_sec)
                    level_bonus = (cp_level + 1) * 1000
                    score = base_score + level_bonus
                else:
                    score = 0

                retry_btn = pygame.Rect(WIDTH//2-80, HEIGHT//2+30, 160, 50)

                waiting = True
                while waiting:
                    screen.fill(BLACK)

                    t = font_small.render(result, True, WHITE)
                    screen.blit(t, t.get_rect(center=(WIDTH//2, HEIGHT//2-50)))

                    s = font_small.render(f"Score: {score}", True, WHITE)
                    screen.blit(s, s.get_rect(center=(WIDTH//2, HEIGHT//2)))

                    pygame.draw.rect(screen, GREEN, retry_btn)
                    pygame.draw.rect(screen, WHITE, retry_btn, 2)
                    t2 = font_small.render("RETRY", True, WHITE)
                    screen.blit(t2, t2.get_rect(center=retry_btn.center))

                    pygame.display.flip()

                    for e in pygame.event.get():
                        if e.type==pygame.QUIT:
                            return

                        if e.type == pygame.FINGERDOWN:
                            pos=(e.x*WIDTH,e.y*HEIGHT)
                        elif e.type == pygame.MOUSEBUTTONDOWN:
                            pos=e.pos
                        else:
                            continue

                        if retry_btn.collidepoint(pos):
                            waiting=False

                    await asyncio.sleep(0)

                break

            # ===== 描画 =====
            pygame.draw.rect(screen, BLUE, player)
            pygame.draw.rect(screen, RED, enemy)

            for b in player_bullets:
                pygame.draw.rect(screen, WHITE, b)
            for b in enemy_bullets:
                pygame.draw.rect(screen, WHITE, b)

            # 爆発
            for exp in explosions[:]:
                pygame.draw.circle(screen, (255,200,0), (exp[0],exp[1]), exp[2])
                pygame.draw.circle(screen, (255,100,0), (exp[0],exp[1]), exp[2]//2)
                exp[2]+=2
                if exp[2]>30:
                    explosions.remove(exp)

            x = (WIDTH-200)//2

            # 敵HP
            y_enemy = 10
            er = enemy_hp/max_enemy_hp
            ec = RED if er>0.33 else (YELLOW if er>0.1 else (RED if pygame.time.get_ticks()%400<200 else BLACK))
            pygame.draw.rect(screen, WHITE, (x,y_enemy,200,20),2)
            pygame.draw.rect(screen, ec, (x,y_enemy,200*er,20))

            # プレイヤーHP
            pr = player_hp/max_player_hp
            pc = BLUE if pr>0.33 else (YELLOW if pr>0.1 else (RED if pygame.time.get_ticks()%400<200 else BLACK))
            pygame.draw.rect(screen, WHITE, (x,HEIGHT-40,200,20),2)
            pygame.draw.rect(screen, pc, (x,HEIGHT-40,200*pr,20))

            # ボタン
            pygame.draw.rect(screen, GREEN, left_btn)
            pygame.draw.rect(screen, GREEN, right_btn)
            pygame.draw.rect(screen, GRAY if shoot_cooldown>0 else RED, shoot_btn)

            screen.blit(font_small.render("L",True,WHITE),
                        font_small.render("L",True,WHITE).get_rect(center=left_btn.center))
            screen.blit(font_small.render("R",True,WHITE),
                        font_small.render("R",True,WHITE).get_rect(center=right_btn.center))
            screen.blit(font_small.render("SHOOT",True,WHITE),
                        font_small.render("SHOOT",True,WHITE).get_rect(center=shoot_btn.center))

            pygame.display.flip()
            await asyncio.sleep(0)

asyncio.run(main())