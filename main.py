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
    def is_clicked(self,pos):
        return self.rect.collidepoint(pos)

async def main():

    while True:

        # ===== 難易度 =====
        difficulty_buttons = [
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
            for b in difficulty_buttons: b.draw(screen)
            pygame.display.flip()

            for e in pygame.event.get():
                if e.type==pygame.QUIT: return
                if e.type==pygame.MOUSEBUTTONDOWN:
                    for b in difficulty_buttons:
                        if b.is_clicked(pygame.mouse.get_pos()):
                            if b.text=="Easy": max_player_hp=20
                            elif b.text=="Normal": max_player_hp=10
                            elif b.text=="Hard": max_player_hp=5
                            elif b.text=="Ultra": max_player_hp=1
                            selecting=False
            await asyncio.sleep(0)

        # ===== ステージ =====
        level_buttons=[]
        for i in range(10):
            level_buttons.append(Button((20+i*45,350,40,40),(0,255-20*i,255),str(i+1)))

        selecting=True
        cp_level=0

        while selecting:
            screen.fill(BLACK)
            screen.blit(font_small.render("Select CP Level",True,WHITE),(130,100))
            for b in level_buttons: b.draw(screen)
            pygame.display.flip()

            for e in pygame.event.get():
                if e.type==pygame.QUIT: return
                if e.type==pygame.MOUSEBUTTONDOWN:
                    for i,b in enumerate(level_buttons):
                        if b.is_clicked(pygame.mouse.get_pos()):
                            cp_level=i
                            selecting=False
            await asyncio.sleep(0)

        # ===== ゲーム =====
        player=pygame.Rect(WIDTH//2-25, HEIGHT-150,50,50)
        enemy=pygame.Rect(WIDTH//2-25,50,50,50)

        player_bullets=[]
        enemy_bullets=[]

        player_hp=max_player_hp
        enemy_hp=3+cp_level*2
        max_enemy_hp=enemy_hp

        left_btn = pygame.Rect(30, HEIGHT-120, 80, 80)
        right_btn = pygame.Rect(130, HEIGHT-120, 80, 80)
        shoot_btn = pygame.Rect(WIDTH-110, HEIGHT-120, 80, 80)

        shoot_cooldown = 0
        cooldown_time = 30

        active_touches = {}

        running=True
        while running:
            clock.tick(60)
            screen.fill(BLACK)

            moving_left = moving_right = shooting = False

            for e in pygame.event.get():
                if e.type==pygame.QUIT: return
                if e.type in (pygame.FINGERDOWN, pygame.FINGERMOTION):
                    active_touches[e.finger_id] = (e.x,e.y)
                if e.type==pygame.FINGERUP:
                    active_touches.pop(e.finger_id, None)

            # 同時押し
            for tx,ty in active_touches.values():
                x,y = tx*WIDTH, ty*HEIGHT
                if left_btn.collidepoint((x,y)): moving_left=True
                if right_btn.collidepoint((x,y)): moving_right=True
                if shoot_btn.collidepoint((x,y)): shooting=True

            if pygame.mouse.get_pressed()[0]:
                mx,my = pygame.mouse.get_pos()
                if left_btn.collidepoint((mx,my)): moving_left=True
                if right_btn.collidepoint((mx,my)): moving_right=True
                if shoot_btn.collidepoint((mx,my)): shooting=True

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

            for pb in player_bullets[:]:
                for eb in enemy_bullets[:]:
                    if pb.colliderect(eb):
                        player_bullets.remove(pb)
                        enemy_bullets.remove(eb)
                        break

            for b in enemy_bullets[:]:
                if player.colliderect(b):
                    enemy_bullets.remove(b)
                    player_hp-=1

            for b in player_bullets[:]:
                if enemy.colliderect(b):
                    player_bullets.remove(b)
                    enemy_hp-=1

            # ===== ゲーム終了 → 即リトライ画面 =====
            if player_hp<=0 or enemy_hp<=0:
                while True:
                    screen.fill(BLACK)

                    retry_rect = pygame.Rect(WIDTH//2-60, HEIGHT//2,120,50)

                    pygame.draw.rect(screen, GREEN, retry_rect)
                    pygame.draw.rect(screen, WHITE, retry_rect,2)
                    screen.blit(font_small.render("RETRY",True,WHITE),
                                font_small.render("RETRY",True,WHITE).get_rect(center=retry_rect.center))

                    pygame.display.flip()

                    for e in pygame.event.get():
                        if e.type==pygame.QUIT: return
                        if e.type==pygame.MOUSEBUTTONDOWN:
                            if retry_rect.collidepoint(e.pos):
                                return
                        if e.type==pygame.FINGERDOWN:
                            x,y=e.x*WIDTH,e.y*HEIGHT
                            if retry_rect.collidepoint((x,y)):
                                return

                    await asyncio.sleep(0)

            # 描画
            pygame.draw.rect(screen, BLUE, player)
            pygame.draw.rect(screen, RED, enemy)

            for b in player_bullets:
                pygame.draw.rect(screen, WHITE, b)
            for b in enemy_bullets:
                pygame.draw.rect(screen, WHITE, b)

            # HPバー
            x = (WIDTH-200)//2
            pygame.draw.rect(screen, WHITE, (x,20,200,20),2)
            pygame.draw.rect(screen, RED, (x,20,200*(enemy_hp/max_enemy_hp),20))

            pygame.draw.rect(screen, WHITE, (x,HEIGHT-60,200,20),2)
            pygame.draw.rect(screen, BLUE, (x,HEIGHT-60,200*(player_hp/max_player_hp),20))

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

while True:
    asyncio.run(main())