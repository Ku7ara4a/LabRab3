import pygame
from copy import deepcopy
from random import choice, randrange

FPS = 30
block, cup_h, cup_w = 45, 20, 10
GAME_RES = cup_w * block, cup_h * block
RES = 750, 940

pygame.init()
screen = pygame.display.set_mode(RES)
game_screen = pygame.Surface((GAME_RES))
clock = pygame.time.Clock()

grid = [pygame.Rect(x * block, y * block, block, block) for x in range(cup_w) for y in range(cup_h)]

figures_pos = [[(-1,0),(-2,0),(0,0),(1,0)], #I
               [(0,-1),(-1,-1),(-1,0),(0,0)], #O
               [(-1,0),(-1,1),(0,0),(0,-1)], # S
               [(0,0),(-1,0),(0,1),(-1,-1)], # Z
               [(0,0),(0,-1),(0,1),(-1,-1)], # J
               [(0,0),(0,-1),(0,1),(1,-1)], # L
               [(0,0),(0,-1),(0,1),(-1,0)]] # T

figures = [[pygame.Rect(x + cup_w//2 ,y + 1, 1, 1) for x,y in fig_pos] for fig_pos in figures_pos]
figure_rect = pygame.Rect(0, 0, block - 2, block-2)
field = [[0 for i in range(cup_w)] for j in range(cup_h)]

#animations
a_count, a_speed, a_limit = 0, 60, 2000

def get_color():
    return (randrange(30,256), randrange(30,256), randrange(30,256))
color, next_color = get_color(), get_color()

figure, next_figure = deepcopy(choice(figures)) , deepcopy(choice(figures))

score , lines = 0, 0
scores = {0: 0, 1: 100, 2: 300, 3: 500, 4: 800}
#оформление
bg = pygame.image.load('assets/background.png').convert()
game_bg = pygame.image.load('assets/game_bg.png').convert()

main_font = pygame.font.Font('assets/font.ttf', 65)
font = pygame.font.Font('assets/font.ttf', 45)

title_font = main_font.render('TETRIS', True, pygame.Color('lightblue'))
title_score = main_font.render('SCORE', True, pygame.Color('lightblue'))
next_font = font.render('NEXT', True, pygame.Color('lightgreen'))

def check_borders(fig=None):
    if fig is None:
        fig = figure
    for i in range(4):
        if fig[i].x < 0 or fig[i].x > cup_w - 1:
            return False
        elif fig[i].y > cup_h - 1 or (fig[i].y >= 0 and field[fig[i].y][fig[i].x]):
            return False
    return True

while True:
    dx, rotate = 0, False
    screen.blit(bg, (0, 0))
    screen.blit(game_screen, (20, 20))
    game_screen.blit(game_bg, (0, 0))
    #задержка при удалении линии
    for i in range(lines):
        pygame.time.wait(200)
    #управление
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                dx = -1
            elif event.key == pygame.K_RIGHT:
                dx = 1
            elif event.key == pygame.K_DOWN:
                a_limit = 100
            elif event.key == pygame.K_UP:
                rotate = True

    #move x
    figure_old = deepcopy(figure)
    for i in range(4):
        figure[i].x += dx
    if not check_borders():
        figure = deepcopy(figure_old)

    #move y
    a_count += a_speed
    if a_count > a_limit:
        a_count = 0
        figure_old = deepcopy(figure)
        for i in range(4):
            figure[i].y += 1
        if not check_borders():
            for i in range(4):
                if figure_old[i].y >= 0:  # Проверяем, что фигура в пределах поля
                    field[figure_old[i].y][figure_old[i].x] = color
            figure, color = next_figure, next_color
            next_figure, next_color = deepcopy(choice(figures)) , get_color()
            a_limit = 2000

    #rotate
    center = figure[0]
    figure_old = deepcopy(figure)
    if rotate:
        for i in range(4):
            x = figure[i].y - center.y
            y = figure[i].x - center.x
            figure[i].x = center.x - x
            figure[i].y = center.y + y
        if not check_borders():
            figure = deepcopy(figure_old)

    #ряд заполнен
    line , lines = cup_h - 1 , 0
    for row in range(cup_h - 1, -1, -1):
        count = 0
        for i in range(cup_w):
            if field[row][i]:
                count += 1
            field[line][i] = field[row][i]
        if count < cup_w:
            line -=1
        else:
            a_count += 3
            lines += 1
    #счёт
    score += scores[lines]
    #отрисовка сетки
    [pygame.draw.rect(game_screen,(40,40,40),i_rect,1) for i_rect in grid]

    #отрисовка фигуры
    for i in range(4):
        figure_rect.x = figure[i].x * block
        figure_rect.y = figure[i].y * block
        pygame.draw.rect(game_screen,color,figure_rect)

    #отрисовка поля
    for y, row in enumerate(field):
        for x, col in enumerate(row):
            if col:
                figure_rect.x, figure_rect.y = x * block, y * block
                pygame.draw.rect(game_screen,col ,figure_rect)

    # отрисовка следующей фигуры
    screen.blit(next_font, (545, 100))  # Заголовок "NEXT"
    next_figure_rect = pygame.Rect(0, 0, block - 2, block - 2)
    for i in range(4):
        next_figure_rect.x = next_figure[i].x * block + 430 - block  # Центрируем по горизонтали
        next_figure_rect.y = next_figure[i].y * block + 175  # Смещаем вниз
        pygame.draw.rect(screen, next_color, next_figure_rect)

    #рендер надписей
    screen.blit(title_font, (475, 10))
    screen.blit(title_score, (500, 780))
    screen.blit(font.render(str(score), True, pygame.Color('white')),(500,840))

    #game over
    for i in range(cup_w):
        if field[0][i]:
            field = [[0 for i in range(cup_w)] for i in range(cup_h)]
            a_count, a_speed,a_limit = 0, 60, 2000
            score = 0
            for i_rect in grid:
                pygame.draw.rect(game_screen,get_color(),i_rect)
                screen.blit(game_screen,(20,20))
                pygame.display.flip()
                clock.tick(200)
    pygame.display.flip()
    clock.tick(FPS)