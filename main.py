import pygame
import asyncio
import random

pygame.init()

# ===== 画面 =====
WIDTH, HEIGHT = 480, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

WHITE = (255,255,255)
RED = (255,0,0)
BLUE = (0,0,255)
BLACK = (0,0,0)
GREEN = (0,180,0)
ORANGE = (255,165,0)

font = pygame.font.SysFont(None,40)
font_small = pygame.font.SysFont(None,28)

# ===== CPレベル =====
cp_levels = [
    {"shoot_rate":80,"speed":2,"tracking":0.05},
    {"shoot_rate":60,"speed":3,"tracking":0.1},
    {"shoot_rate":50,"speed":4,"tracking":0.15},
    {"shoot_rate":40,"speed":5,"tracking":0.2},
    {"shoot_rate":30,"speed":6,"tracking":0.3},
    {"shoot_rate":20,"speed":7,"tracking":0.4},
    {"shoot_rate":15,"speed":8,"tracking":0.5},
    {"shoot_rate":10,"speed":9,"tracking":0.6},
    {"shoot_rate":6,"speed":10,"tracking":0.7},
    {"shoot_rate":3,"speed":12,"tracking":0.8},
]

# ===== ボタンクラス =====
class Button:
    def __init__(self, rect, color, text):
        self.rect = pygame.Rect(rect)
        self.color = color
        self.text = text
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        text_surf = font_small.render(self.text, True, WHITE)
        screen.blit(text_surf, text_surf.get_rect(center=self.rect.center))
    def is_clicked(self,pos):
        return self.rect.collidepoint(pos)

async def main():
    # ===== 難易度選択 =====
    difficulty_buttons = [
        Button((60,200,120,50),GREEN,"Easy"),
        Button((200,200,120,50),BLUE,"Normal"),
        Button((60,270,120,50),ORANGE,"Hard"),
        Button((200,270,120,50),RED,"Ultra"),
    ]

    selecting=True
    max_player_hp=10
    difficulty_text="Normal"
    while selecting:
        screen.fill(BLACK)
        screen.blit(font.render("Select Difficulty",True,WHITE),(100,100))
        for btn in difficulty_buttons: btn.draw(screen)
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.quit(); return
            if e.type==pygame.MOUSEBUTTONDOWN:
                for btn in difficulty_buttons:
                    if btn.is_clicked(pygame.mouse.get_pos()):
                        if btn.text=="Easy": max_player_hp=20
                        elif btn.text=="Normal": max_player_hp=10
                        elif btn.text=="Hard": max_player_hp=5
                        elif btn.text=="Ultra": max_player_hp=1
                        difficulty_text=btn.text
                        selecting=False
        await asyncio.sleep(0)

    player_hp = max_player_hp

    # ===== レベル選択 =====
    colors=[
        (180,180,180),(160,160,220),(140,140,255),(120,180,255),(100,200,255),
        (80,220,255),(60,240,255),(40,255,200),(20,255,100),(0,255,0)
    ]
    level_buttons=[]
    for i in range(10):
        level_buttons.append(Button((20+i*45,350,40,40),colors[i],str(i+1)))

    selecting=True
    cp_level=0
    while selecting:
        screen.fill(BLACK)
        screen.blit(font.render("Select CP Level",True,WHITE),(100,100))
        for btn in level_buttons: btn.draw(screen)
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.quit(); return
            if e.type==pygame.MOUSEBUTTONDOWN:
                for i,btn in enumerate(level_buttons):
                    if btn.is_clicked(pygame.mouse.get_pos()):
                        cp_level=i
                        selecting=False
        await asyncio.sleep(0)

    # ===== 初期化 =====
    player=pygame.Rect(WIDTH//2-25, HEIGHT-150,50,50)
    enemy=pygame.Rect(WIDTH//2-25,50,50,50)
    player_bullets=[]
    enemy_bullets=[]
    enemy_hp=3+cp_level*2
    max_enemy_hp=enemy_hp

    # ===== 操作ボタン =====
    left_btn = pygame.Rect(30, HEIGHT-120, 80, 80)
    right_btn = pygame.Rect(130, HEIGHT-120, 80, 80)
    shoot_btn = pygame.Rect(WIDTH-110, HEIGHT-120, 80, 80)

    running=True
    # タッチ管理リスト（スマホ用）
    active_touches = []

    while running:
        clock.tick(60)
        screen.fill(BLACK)

        # ===== 入力処理（PC・スマホ共通） =====
        moving_left = moving_right = shooting = False

        # PCマウス判定
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:
            mx, my = pygame.mouse.get_pos()
            if left_btn.collidepoint((mx,my)): moving_left = True
            if right_btn.collidepoint((mx,my)): moving_right = True
            if shoot_btn.collidepoint((mx,my)): shooting = True

        # イベント処理（スマホタッチ用）
        for e in pygame.event.get():
            if e.type==pygame.QUIT:
                running=False
            # タッチ開始または移動
            if e.type in [pygame.FINGERDOWN, pygame.FINGERMOTION]:
                tx, ty = e.x*WIDTH, e.y*HEIGHT
                if left_btn.collidepoint((tx,ty)): moving_left = True
                if right_btn.collidepoint((tx,ty)): moving_right = True
                if shoot_btn.collidepoint((tx,ty)): shooting = True

        # ===== プレイヤー操作 =====
        if moving_left: player.x -= 5
        if moving_right: player.x += 5
        if shooting:
            player_bullets.append(pygame.Rect(player.centerx-5, player.y,10,10))
        player.x = max(0,min(WIDTH-player.width,player.x))

        # ===== 敵追跡と射撃 =====
        dx = player.centerx - enemy.centerx
        direction = dx / abs(dx) if dx != 0 else 0
        tracking_speed = cp_levels[cp_level]["speed"]
        enemy.x += direction * tracking_speed
        enemy.x = max(0, min(WIDTH-enemy.width,enemy.x))
        if random.randint(0, cp_levels[cp_level]["shoot_rate"])==0:
            enemy_bullets.append(pygame.Rect(enemy.centerx-5, enemy.bottom, 10,10))

        # ===== 弾移動 =====
        for b in player_bullets: b.y -= 7
        for b in enemy_bullets: b.y += 7

        # 弾同士
        for pb in player_bullets[:]:
            for eb in enemy_bullets[:]:
                if pb.colliderect(eb):
                    player_bullets.remove(pb)
                    enemy_bullets.remove(eb)
                    break
        # 弾とキャラ
        for b in enemy_bullets[:]:
            if player.colliderect(b):
                enemy_bullets.remove(b)
                player_hp -= 1
        for b in player_bullets[:]:
            if enemy.colliderect(b):
                player_bullets.remove(b)
                enemy_hp -= 1

        # ===== 描画 =====
        pygame.draw.rect(screen, BLUE, player)
        pygame.draw.rect(screen, RED, enemy)
        for b in player_bullets: pygame.draw.rect(screen, WHITE, b)
        for b in enemy_bullets: pygame.draw.rect(screen, WHITE, b)

        # HPバー
        x = (WIDTH-200)//2
        pygame.draw.rect(screen, WHITE, (x,20,200,20),2)
        pygame.draw.rect(screen, RED, (x,20,200*(enemy_hp/max_enemy_hp),20))
        pygame.draw.rect(screen, WHITE, (x,HEIGHT-60,200,20),2)
        pygame.draw.rect(screen, BLUE, (x,HEIGHT-60,200*(player_hp/max_player_hp),20))

        # ボタン描画
        pygame.draw.rect(screen, GREEN, left_btn)
        pygame.draw.rect(screen, GREEN, right_btn)
        pygame.draw.rect(screen, RED, shoot_btn)
        screen.blit(font_small.render("L",True,WHITE),(left_btn.x+30,left_btn.y+25))
        screen.blit(font_small.render("R",True,WHITE),(right_btn.x+30,right_btn.y+25))
        screen.blit(font_small.render("SHOOT",True,WHITE),(shoot_btn.x+5,shoot_btn.y+25))

        # 勝敗
        if player_hp<=0: print("LOSE"); running=False
        if enemy_hp<=0: print("WIN"); running=False

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()

asyncio.run(main())