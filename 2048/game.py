import pygame
import random
import sys
import moviepy

# 初始化 Pygame
pygame.init()

# 游戏常量
WINDOW_SIZE = 400
GRID_SIZE = 4
CELL_SIZE = WINDOW_SIZE // GRID_SIZE
PADDING = 10

# 颜色定义
COLORS = {
    0: (205, 193, 180),
    2: (238, 228, 218),
    4: (237, 224, 200),
    8: (242, 177, 121),
    16: (245, 149, 99),
    32: (246, 124, 95),
    64: (246, 94, 59),
    128: (237, 207, 114),
    256: (237, 204, 97),
    512: (237, 200, 80),
    1024: (237, 197, 63),
    2048: (237, 194, 46)
}

BACKGROUND_COLOR = (187, 173, 160)
TEXT_COLOR = (119, 110, 101)

class Game2048:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
        pygame.display.set_caption('2048')
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.font = pygame.font.Font(None, 36)
        self.add_new_tile()
        self.add_new_tile()

    def add_new_tile(self):
        empty_cells = [(i, j) for i in range(GRID_SIZE) for j in range(GRID_SIZE) if self.grid[i][j] == 0]
        if empty_cells:
            i, j = random.choice(empty_cells)
            self.grid[i][j] = 2 if random.random() < 0.9 else 4

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                value = self.grid[i][j]
                cell_rect = pygame.Rect(
                    j * CELL_SIZE + PADDING,
                    i * CELL_SIZE + PADDING,
                    CELL_SIZE - 2 * PADDING,
                    CELL_SIZE - 2 * PADDING
                )
                pygame.draw.rect(self.screen, COLORS[value], cell_rect, border_radius=8)
                
                if value != 0:
                    text = self.font.render(str(value), True, TEXT_COLOR)
                    text_rect = text.get_rect(center=cell_rect.center)
                    self.screen.blit(text, text_rect)
        
        pygame.display.flip()

    def move(self, direction):
        moved = False
        if direction in ['UP', 'DOWN']:
            for j in range(GRID_SIZE):
                column = [self.grid[i][j] for i in range(GRID_SIZE)]
                if direction == 'UP':
                    new_column = self.merge(column)
                else:
                    new_column = self.merge(column[::-1])[::-1]
                
                for i in range(GRID_SIZE):
                    if self.grid[i][j] != new_column[i]:
                        moved = True
                        self.grid[i][j] = new_column[i]
        
        else:  # LEFT or RIGHT
            for i in range(GRID_SIZE):
                row = self.grid[i][:]
                if direction == 'LEFT':
                    new_row = self.merge(row)
                else:
                    new_row = self.merge(row[::-1])[::-1]
                
                if row != new_row:
                    moved = True
                    self.grid[i] = new_row
        
        if moved:
            self.add_new_tile()

    def merge(self, line):
        # 移除零
        non_zero = [x for x in line if x != 0]
        # 合并相同的数字
        for i in range(len(non_zero) - 1):
            if non_zero[i] == non_zero[i + 1]:
                non_zero[i] *= 2
                non_zero[i + 1] = 0
        # 再次移除零并补齐
        non_zero = [x for x in non_zero if x != 0]
        return non_zero + [0] * (GRID_SIZE - len(non_zero))

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.move('UP')
                    elif event.key == pygame.K_DOWN:
                        self.move('DOWN')
                    elif event.key == pygame.K_LEFT:
                        self.move('LEFT')
                    elif event.key == pygame.K_RIGHT:
                        self.move('RIGHT')
            
            self.draw()

if __name__ == '__main__':
    game = Game2048()
    game.run()