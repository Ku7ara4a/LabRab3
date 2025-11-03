import pygame
from copy import deepcopy
from random import choice, randrange

# КОНСТАНТЫ
FPS = 60
BLOCK_SIZE, CUP_H, CUP_W = 45, 20, 10
GAME_RES = CUP_W * BLOCK_SIZE, CUP_H * BLOCK_SIZE
RES = 750, 940
SCORES = {0: 0, 1: 100, 2: 300, 3: 500, 4: 800}

FIGURES_POS = [
    [(-1, 0), (-2, 0), (0, 0), (1, 0)],  # I
    [(0, -1), (-1, -1), (-1, 0), (0, 0)],  # O
    [(-1, 0), (-1, 1), (0, 0), (0, -1)],  # S
    [(0, 0), (-1, 0), (0, 1), (-1, -1)],  # Z
    [(0, 0), (0, -1), (0, 1), (-1, -1)],  # J
    [(0, 0), (0, -1), (0, 1), (1, -1)],  # L
    [(0, 0), (0, -1), (0, 1), (-1, 0)]  # T
]

# СОСТОЯНИЯ ИГРЫ
class GameState:
    MENU = 0
    PLAYING = 1
    GAME_OVER = 2

# ИНИЦИАЛИЗАЦИЯ PYGAME
pygame.init()
# Начальное окно - изменяемое для меню
screen = pygame.display.set_mode(RES, pygame.RESIZABLE)
game_screen = pygame.Surface(GAME_RES)
clock = pygame.time.Clock()

# ЗАГРУЗКА РЕСУРСОВ
bg = pygame.image.load('assets/background.png').convert()
game_bg = pygame.image.load('assets/game_bg.png').convert()

main_font = pygame.font.Font('assets/font.ttf', 65)
font = pygame.font.Font('assets/font.ttf', 45)
small_font = pygame.font.Font('assets/font.ttf', 35)

# ЗАГРУЗКА МУЗЫКИ
try:
    menu_music = pygame.mixer.Sound('assets/menu_music.mp3')
    game_music = pygame.mixer.Sound('assets/game_music.mp3')
    game_over_music = pygame.mixer.Sound('assets/game_over_music.mp3')

    rotate_sound = pygame.mixer.Sound('assets/rotate.wav')
    line_clear_sound = pygame.mixer.Sound('assets/line_clear.mp3')
    game_over_sound = pygame.mixer.Sound('assets/game_over_sound.mp3')

    music_loaded = True
    print("Музыка загружена")
except Exception as e:
    print(f"Музыка не загружена, проверьте папку assets: {e}")
    music_loaded = False

# НАСТРОЙКА МУЗЫКИ
MUSIC_VOLUME = 0.1
SFX_VOLUME = 0.1

if music_loaded:
    menu_music.set_volume(MUSIC_VOLUME)
    game_music.set_volume(SFX_VOLUME)
    game_over_music.set_volume(SFX_VOLUME)

    rotate_sound.set_volume(SFX_VOLUME)
    line_clear_sound.set_volume(SFX_VOLUME)
    game_over_sound.set_volume(SFX_VOLUME)

# ТЕКСТОВЫЕ ПОВЕРХНОСТИ
title_font = None
title_score = None
title_highscore = None
next_font = None
game_over_font = None
play_text = None
exit_text = None
menu_text = None
restart_text = None

# ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ИГРЫ
field = [[0 for i in range(CUP_W)] for j in range(CUP_H)]
grid = []
figures = []
figure_rect = pygame.Rect(0, 0, BLOCK_SIZE - 2, BLOCK_SIZE - 2)
a_count, a_speed, a_limit = 0, 60, 2000
score, lines = 0, 0
color, next_color = (0, 0, 0), (0, 0, 0)
figure, next_figure = [], []
current_music = None

def download_highscore():
    try:
        with open('assets/highscore.txt', 'r') as f:
            hs = int(f.read())
        print(f"Рекод загружен: {hs}")
        return hs
    except Exception as e:
        print(f"Ошибка при загрузке рекорда: {e}")

def play_music(state):
    global current_music

    if not music_loaded:
        return

    stop_music()

    if state == GameState.MENU:
        current_music = menu_music
    elif state == GameState.PLAYING:
        current_music = game_music
    elif state == GameState.GAME_OVER:
        current_music = game_over_music

    if current_music:
        current_music.play(-1) # -1 означает бесконечный цикл

def stop_music():
    """Остановка всей музыки"""
    if not music_loaded:
        return

    pygame.mixer.stop()

def play_sound(sound_name):
    """Воспроизведение звукового эффекта"""
    if not music_loaded:
        return

    if sound_name == "rotate":
        rotate_sound.play()
    elif sound_name == "line_clear":
        line_clear_sound.play()
    elif sound_name == "game_over":
        game_over_sound.play()

def create_text_surfaces():
    """Создание текстовых поверхностей с учетом текущего размера экрана"""
    global title_font, title_score, next_font, game_over_font, title_highscore
    global play_text, exit_text, menu_text, restart_text

    # Адаптивные размеры шрифтов в зависимости от размера экрана
    screen_width = screen.get_width()
    base_font_size = max(40, min(65, screen_width // 12))
    small_font_size = max(25, min(45, screen_width // 16))

    main_font = pygame.font.Font('assets/font.ttf', base_font_size)
    font = pygame.font.Font('assets/font.ttf', small_font_size)

    title_font = main_font.render('TETRIS', True, pygame.Color('lightblue'))
    title_score = main_font.render('SCORE', True, pygame.Color('lightblue'))
    title_highscore = font.render('RECORD', True, pygame.Color('darkgoldenrod1'))
    next_font = font.render('NEXT', True, pygame.Color('lightgreen'))
    game_over_font = main_font.render('GAME OVER', True, pygame.Color('red'))
    play_text = font.render('PLAY', True, pygame.Color('white'))
    exit_text = font.render('EXIT', True, pygame.Color('white'))
    menu_text = font.render('MAIN MENU', True, pygame.Color('white'))
    restart_text = font.render('RESTART', True, pygame.Color('white'))

#ФУНКЦИИ ИГРЫ
def init_game():
    """Инициализация игровых переменных"""
    global field, grid, figures, figure_rect
    global a_count, a_speed, a_limit, score, lines
    global color, next_color, figure, next_figure

    grid = [pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
            for x in range(CUP_W) for y in range(CUP_H)]

    figures = [[pygame.Rect(x + CUP_W // 2, y + 1, 1, 1) for x, y in fig_pos]
               for fig_pos in FIGURES_POS]

    figure_rect = pygame.Rect(0, 0, BLOCK_SIZE - 2, BLOCK_SIZE - 2)
    field = [[0 for i in range(CUP_W)] for j in range(CUP_H)]

    a_count, a_speed, a_limit = 0, 60, 2000
    score, lines = 0, 0

    color, next_color = get_color(), get_color()
    figure, next_figure = deepcopy(choice(figures)), deepcopy(choice(figures))

def get_color():
    return randrange(30, 256), randrange(30, 256), randrange(30, 256)

def check_borders(fig=None):
    if fig is None:
        fig = figure
    for i in range(4):
        if fig[i].x < 0 or fig[i].x > CUP_W - 1:
            return False
        elif fig[i].y > CUP_H - 1 or (fig[i].y >= 0 and field[fig[i].y][fig[i].x]):
            return False
    return True

def draw_menu():
    """Отрисовка главного меню с адаптивным размером"""
    current_res = screen.get_size()

    #Масштабируем фон под текущий размер окна
    scaled_bg = pygame.transform.scale(bg, current_res)
    screen.blit(scaled_bg, (0, 0))

    #Заголовок по центру
    title_x = current_res[0] // 2 - title_font.get_width() // 2
    screen.blit(title_font, (title_x, current_res[1] // 6))

    #Адаптивный размер кнопок
    button_width = max(150, min(300, current_res[0] // 4))
    button_height = max(50, min(80, current_res[1] // 12))
    button_x = current_res[0] // 2 - button_width // 2

    #Кнопки
    play_button = pygame.Rect(button_x, current_res[1] // 2, button_width, button_height)
    exit_button = pygame.Rect(button_x, current_res[1] // 2 + button_height + 20, button_width, button_height)

    #Отрисовка кнопок
    pygame.draw.rect(screen, (50, 50, 150), play_button, border_radius=15)
    pygame.draw.rect(screen, (150, 50, 50), exit_button, border_radius=15)

    #Текст на кнопках по центру
    screen.blit(play_text, (play_button.centerx - play_text.get_width() // 2,
                            play_button.centery - play_text.get_height() // 2))
    screen.blit(exit_text, (exit_button.centerx - exit_text.get_width() // 2,
                            exit_button.centery - exit_text.get_height() // 2))

    return play_button, exit_button

def draw_game_over():
    """Отрисовка экрана Game Over с адаптивным размером"""
    current_res = screen.get_size()

    #Масштабируем фон
    scaled_bg = pygame.transform.scale(bg, current_res)
    screen.blit(scaled_bg, (0, 0))

    #Текст Game Over по центру
    screen.blit(game_over_font, (current_res[0] // 2 - game_over_font.get_width() // 2,
                                 current_res[1] // 6))

    #Финальный счет
    score_text = font.render(f'Score: {score}', True, pygame.Color('white'))
    screen.blit(score_text, (current_res[0] // 2 - score_text.get_width() // 2,
                             current_res[1] // 6 + 100))

    #Адаптивный размер кнопок
    button_width = max(150, min(300, current_res[0] // 4))
    button_height = max(50, min(80, current_res[1] // 12))
    button_x = current_res[0] // 2 - button_width // 2

    #Кнопки
    restart_button = pygame.Rect(button_x, current_res[1] // 2, button_width, button_height)
    menu_button = pygame.Rect(button_x, current_res[1] // 2 + button_height + 20, button_width, button_height)

    #Отрисовка кнопок
    pygame.draw.rect(screen, (50, 150, 50), restart_button, border_radius=15)
    pygame.draw.rect(screen, (50, 50, 150), menu_button, border_radius=15)

    #Текст на кнопках
    screen.blit(restart_text, (restart_button.centerx - restart_text.get_width() // 2,
                               restart_button.centery - restart_text.get_height() // 2))
    screen.blit(menu_text, (menu_button.centerx - menu_text.get_width() // 2,
                            menu_button.centery - menu_text.get_height() // 2))

    return restart_button, menu_button

def draw_game():
    """Отрисовка игрового экрана (фиксированный размер)"""
    # Используем оригинальный размер без масштабирования
    screen.blit(bg, (0, 0))
    screen.blit(game_screen, (20, 20))
    game_screen.blit(game_bg, (0, 0))

    #Сетка
    for i_rect in grid:
        pygame.draw.rect(game_screen, (40, 40, 40), i_rect, 1)

    #Поле
    for y, row in enumerate(field):
        for x, col in enumerate(row):
            if col:
                figure_rect.x, figure_rect.y = x * BLOCK_SIZE, y * BLOCK_SIZE
                pygame.draw.rect(game_screen, col, figure_rect)

    #Текущая фигура
    for i in range(4):
        figure_rect.x = figure[i].x * BLOCK_SIZE
        figure_rect.y = figure[i].y * BLOCK_SIZE
        pygame.draw.rect(game_screen, color, figure_rect)

    #Следующая фигура
    screen.blit(next_font, (545, 100))
    for i in range(4):
        figure_rect.x = next_figure[i].x * BLOCK_SIZE + 430 - BLOCK_SIZE
        figure_rect.y = next_figure[i].y * BLOCK_SIZE + 175
        pygame.draw.rect(screen, next_color, figure_rect)

    #Интерфейс
    screen.blit(title_font, (475, 10))
    screen.blit(title_score, (500, 780))
    screen.blit(font.render(str(score), True, pygame.Color('white')), (500, 840))
    screen.blit(title_highscore,(500,650))
    screen.blit(font.render(str(highscore), True, pygame.Color('white')),(500,710))

def game_loop():
    """Основной игровой цикл (фиксированный размер)"""
    global a_count, a_limit, score, lines, field, figure, next_figure, color, next_color, highscore

    #Переключаем на фиксированный размер для игрового процесса
    pygame.display.set_mode(RES)  # Без pygame.RESIZABLE - фиксированный размер

    running = True
    while running:
        dx, rotate = 0, False

        #Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    dx = -1
                elif event.key == pygame.K_RIGHT:
                    dx = 1
                elif event.key == pygame.K_DOWN:
                    a_limit = 100
                elif event.key == pygame.K_UP:
                    rotate = True
                    if music_loaded:
                        play_sound("rotate")
                    pygame.time.delay(50)
                elif event.key == pygame.K_ESCAPE:
                    #Возвращаем изменяемый размер при выходе в меню
                    pygame.display.set_mode(RES, pygame.RESIZABLE)
                    create_text_surfaces()
                    return GameState.MENU
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN:
                    a_limit = 2000

        #Движение по X
        figure_old = deepcopy(figure)
        for i in range(4):
            figure[i].x += dx
        if not check_borders():
            figure = deepcopy(figure_old)

        #Движение по Y
        a_count += a_speed
        if a_count > a_limit:
            a_count = 0
            figure_old = deepcopy(figure)
            for i in range(4):
                figure[i].y += 1
            if not check_borders():
                for i in range(4):
                    if figure_old[i].y >= 0:
                        field[figure_old[i].y][figure_old[i].x] = color
                figure, color = next_figure, next_color
                next_figure, next_color = deepcopy(choice(figures)), get_color()
                a_limit = 2000

        #Вращение
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

        #Проверка заполненных линий
        line, lines = CUP_H - 1, 0
        for row in range(CUP_H - 1, -1, -1):
            count = 0
            for i in range(CUP_W):
                if field[row][i]:
                    count += 1
                field[line][i] = field[row][i]
            if count < CUP_W:
                line -= 1
            else:
                lines += 1
                if music_loaded and lines > 0:
                    play_sound("line_clear")
                pygame.time.delay(200)

        #Обновление счета
        score += SCORES[lines]

        #Отрисовка игры
        draw_game()

        # Проверка Game Over
        game_over = False
        for i in range(CUP_W):
            if field[0][i]:
                game_over = True
                break

        if game_over:
            new_highscore = max(score, highscore)
            print(score,new_highscore)
            if new_highscore > highscore:
                highscore = new_highscore
                try:
                    with open('assets/highscore.txt', 'w') as file:
                        file.write(str(new_highscore))
                        print("highscore saved")
                except:
                    print("Ошибка сохранения рекорда")
            if music_loaded:
                play_sound("game_over")
            # Анимация Game Over
            for i in range(10):
                for i_rect in grid:
                    pygame.draw.rect(game_screen, get_color(), i_rect)
                screen.blit(game_screen, (20, 20))
                pygame.display.flip()
                pygame.time.delay(230)



            pygame.time.delay(500)

            # Возвращаем изменяемый размер при Game Over
            pygame.display.set_mode(RES, pygame.RESIZABLE)
            create_text_surfaces()
            return GameState.GAME_OVER
        pygame.display.flip()
        clock.tick(FPS)

    return GameState.MENU

#ОСНОВНОЙ ЦИКЛ ПРОГРАММЫ
def main():
    global screen, highscore

    current_state = GameState.MENU
    init_game()
    create_text_surfaces()  #Создаем текстовые поверхности при запуске
    highscore = download_highscore()
    play_music(GameState.MENU)

    running = True
    while running:
        if current_state == GameState.MENU:
            #Главное меню - изменяемый размер
            play_button, exit_button = draw_menu()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    #Обработка изменения размера окна в меню
                    screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    create_text_surfaces()  # Пересоздаем текстовые поверхности
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if play_button.collidepoint(event.pos):
                        init_game()
                        play_music(GameState.PLAYING)
                        current_state = GameState.PLAYING
                    elif exit_button.collidepoint(event.pos):
                        running = False

            pygame.display.flip()
            clock.tick(FPS)

        elif current_state == GameState.PLAYING:
            #Игровой процесс - фиксированный размер
            result = game_loop()
            if not result:
                running = False
            else:
                if result == GameState.GAME_OVER:
                    play_music(GameState.GAME_OVER)
                current_state = result

        elif current_state == GameState.GAME_OVER:
            #Экран Game Over - изменяемый размер
            restart_button, menu_button = draw_game_over()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    #Обработка изменения размера окна в Game Over
                    screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    create_text_surfaces()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if restart_button.collidepoint(event.pos):
                        init_game()
                        play_music(GameState.PLAYING)
                        current_state = GameState.PLAYING
                    elif menu_button.collidepoint(event.pos):
                        play_music(GameState.MENU)
                        current_state = GameState.MENU
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        init_game()
                        current_state = GameState.PLAYING
                    elif event.key == pygame.K_ESCAPE:
                        current_state = GameState.MENU

            pygame.display.flip()
            clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()