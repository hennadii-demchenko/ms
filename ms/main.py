import random
from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import Event
from typing import Iterator, Optional

import pygame
from pygame.event import Event as GameEvent

from ms.draw import NUM_COLORS, draw_border, BG_COLOR, draw_mine

TITLE = "impss' minesweeper"


@dataclass(slots=True)
class Cell:
    x: int
    y: int
    value: int
    has_mine: bool = False
    is_flagged: bool = False
    neighbors: list["Cell"] = field(default_factory=list)

    @property
    def pos(self) -> tuple[int, int]:
        return self.x, self.y

    def __add__(self, other: int) -> "Cell":
        assert isinstance(other, int)
        self.value += other
        return self

    __radd__ = __add__


class Grid:
    def __init__(self, rows: int, cols: int, mines: int):
        self.__rows = rows
        self.__cols = cols
        self.num_mines = mines
        self.clicked_at = None
        self.board: list[list[Cell]] = [
            [Cell(x, y, 0) for y in range(self.__rows)]
            for x in range(self.__cols)
        ]

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

    def __maybe_add_neighbor(
        self, cell: Cell, mines: list[tuple[int, int]], x: int, y: int
    ) -> None:
        in_bounds = 0 <= x <= self.__cols - 1 and 0 <= x <= self.__rows - 1
        if in_bounds and (x, y) not in mines:
            cell.neighbors.append(self.at(x, y))

    def at(self, x: int, y: int) -> Cell:
        assert 0 <= x <= self.__cols - 1
        assert 0 <= y <= self.__rows - 1
        return self.board[x][y]

    def generate(self) -> None:
        mines = self.__randomize()

        for x, y in mines:
            cell = self.at(x, y)
            cell.has_mine = True

            is_left_edge = x == 0
            is_top_edge = y == 0
            is_right_edge = x + 1 == self.__cols
            is_bottom_edge = y + 1 == self.__rows

            if not is_left_edge:
                self.__maybe_add_neighbor(cell, mines, x - 1, y)
            if not is_right_edge:
                self.__maybe_add_neighbor(cell, mines, x + 1, y)
            if not is_top_edge:
                self.__maybe_add_neighbor(cell, mines, x, y - 1)
            if not is_bottom_edge:
                self.__maybe_add_neighbor(cell, mines, x, y + 1)

            if not is_left_edge and not is_top_edge:
                self.__maybe_add_neighbor(cell, mines, x - 1, y - 1)
            if not is_left_edge and not is_bottom_edge:
                self.__maybe_add_neighbor(cell, mines, x - 1, y + 1)
            if not is_right_edge and not is_bottom_edge:
                self.__maybe_add_neighbor(cell, mines, x + 1, y + 1)
            if not is_right_edge and not is_top_edge:
                self.__maybe_add_neighbor(cell, mines, x + 1, y - 1)

            for neighbor in cell.neighbors:
                neighbor += 1


class Fog:
    """board uncovering"""


@contextmanager
def pygame_runner() -> Iterator[None]:
    pygame.init()
    pygame.display.init()
    pygame.font.init()
    pygame.display.set_caption(TITLE)
    yield
    pygame.quit()


class Game:
    __TITLE = "imps ms"
    INITIAL_SIZE = 1200, 1600
    is_over: Event = Event()
    size: int = 80
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
        self.screen.fill(BG_COLOR)
        self.grid = Grid(rows, cols, mines)
        self.cell_font = pygame.font.SysFont(
            "Calibri", int(self.size * 0.75), bold=True
        )
        pygame.display.set_caption(self.__TITLE)

    def on_start_new(self) -> None:
        self.grid.generate()
        self.is_over.clear()

    def on_click(self, x: int, y: int) -> None:
        ...

    def handle(self, event: GameEvent) -> None:
        if event.type == pygame.QUIT:
            self.is_over.set()
        if event.type == pygame.MOUSEBUTTONUP:
            self.on_click(*pygame.mouse.get_pos())

    def update(self) -> None:
        for board_x, board_y in self.grid:
            cell = self.grid.at(board_x, board_y)
            screen_x = board_x * self.size
            screen_y = board_y * self.size

            r = pygame.draw.rect(
                self.screen,
                BG_COLOR,
                (screen_x, screen_y, self.size, self.size),
            )

            if cell.has_mine:
                draw_mine(self.screen, r)
                continue

            draw_border(self.screen, r)

            if cell.value == 0:
                continue  # FIXME handle empty differently

            text = self.cell_font.render(
                str(cell.value), True, NUM_COLORS[cell.value]
            )

            self.screen.blit(
                text,
                (
                    screen_x + (self.size / 2 - text.get_width() / 2),
                    screen_y + (self.size / 2 - text.get_height() / 2),
                ),
            )

        pygame.display.flip()


def main() -> int:

    with pygame_runner():
        game = Game()
        game.on_start_new()  # FIXME REMOVE
        game.update()
        # FIXME REMOVE

        while not game.is_over.is_set():
            for event in pygame.event.get():
                game.handle(event)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
