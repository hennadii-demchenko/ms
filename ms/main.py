import random
from threading import Event
from typing import Iterator, Optional

import pygame

NUM_COLORS = {
    1: (0x0, 0x0, 0xFF),
    2: (0x0, 0x80, 0x0),
    3: (0xFF, 0x0, 0x0),
    4: (0x0, 0x0, 0x80),
    5: (0x80, 0x0, 0x0),
    6: (0x0, 0x0, 0x80),
    7: (0x0, 0x0, 0x0),
    8: (0x80, 0x80, 0x80),
}


class Grid:
    def __init__(self, rows: int, cols: int, mines: int):
        self.__rows = rows
        self.__cols = cols
        self.num_mines = mines
        self.board = [[0 for _ in range(rows)] for _ in range(cols)]
        self.clicked_at = None

    def __iter__(self) -> Iterator[tuple[int, int]]:
        """coordinates iterator"""
        yield from (
            (x, y)
            for x, col in enumerate(self.board)
            for y, _ in enumerate(col)
        )

    def __neighbors(self, x: int, y: int) -> Iterator[tuple[int, int]]:
        is_left_edge = x - 1 < 0
        is_top_edge = y - 1 < 0
        is_right_edge = x + 1 >= self.__cols
        is_bottom_edge = y + 1 >= self.__rows

        yield from (
            neigh
            for neigh in [
                is_left_edge or (x - 1, y),
                (is_top_edge or is_left_edge) or (x - 1, y - 1),
                is_top_edge or (x, y - 1),
                (is_top_edge or is_right_edge) or (x + 1, y - 1),
                is_right_edge or (x + 1, y),
                (is_bottom_edge or is_right_edge) or (x + 1, y + 1),
                is_bottom_edge or (x, y + 1),
                (is_bottom_edge or is_left_edge) or (x - 1, y + 1),
            ]
            if isinstance(neigh, tuple)
        )

    def __randomize(
        self, clicked_at: Optional[tuple[int, int]] = None
    ) -> list[tuple[int, int]]:
        clicked = clicked_at or self.clicked_at
        candidates = [coord for coord in self if coord != clicked]
        return random.sample(candidates, self.num_mines)

    def generate(self) -> None:
        mines = self.__randomize()

        for x, y in mines:
            self.board[x][y] = -1

            for n in self.__neighbors(x, y):
                nx, ny = n
                in_x_bounds = 0 <= nx <= self.__cols - 1
                in_y_bounds = 0 <= ny <= self.__rows - 1
                if in_x_bounds and in_y_bounds and n not in mines:
                    self.board[nx][ny] += 1


class Fog:
    """board uncovering"""


class Game:
    __TITLE = "imps ms"
    INITIAL_SIZE = 1200, 1600
    is_over: Event = Event()
    size: int = 100
    """
    facade for
    - settings
    - stats
    - start/restart game
    - tbd

    """

    def __init__(self) -> None:
        rows, cols, mines = 10, 9, 40  # FIXME
        self.screen = pygame.display.set_mode(self.INITIAL_SIZE)
        self.grid = Grid(rows, cols, mines)
        self.cell_font = pygame.font.SysFont("Calibri", self.size, bold=True)
        pygame.display.set_caption(self.__TITLE)

    @staticmethod
    def on_start() -> None:
        pygame.display.flip()

    def on_game_start(self) -> None:
        self.grid.generate()
        self.is_over.clear()

    def on_click(self, x: int, y: int) -> None:
        ...

    def update(self) -> None:
        for board_x, board_y in self.grid:
            value = self.grid.board[board_x][board_y]
            screen_x = board_x * self.size
            screen_y = board_y * self.size

            pygame.draw.rect(
                self.screen,
                (0x80, 0x80, 0x80),
                (screen_x, screen_y, self.size, self.size),
            )

            pygame.draw.rect(
                self.screen,
                "black",
                (screen_x, screen_y, self.size, self.size),
                2,
            )

            if value <= 0:
                continue  # FIXME handle empty and mines differently

            text = self.cell_font.render(str(value), True, NUM_COLORS[value])
            self.screen.blit(
                text,
                (
                    screen_x + (self.size / 2 - text.get_width() / 2),
                    screen_y + (self.size / 2 - text.get_height() / 2),
                ),
            )

        pygame.display.flip()


def main() -> int:
    pygame.init()
    game = Game()
    game.on_start()

    # game.on_game_start()  # FIXME REMOVE
    # game.update()  # FIXME REMOVE

    while not game.is_over.is_set():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.is_over.set()
            if event.type == pygame.MOUSEBUTTONUP:
                game.on_click(*pygame.mouse.get_pos())

    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
