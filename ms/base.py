import random
from dataclasses import dataclass
from typing import Iterator

import pygame

from ms.draw import BG_COLOR
from ms.draw import draw_border
from ms.draw import draw_empty
from ms.draw import draw_flag
from ms.draw import draw_mine
from ms.draw import draw_reset
from ms.draw import NUM_COLORS

T_COORD = tuple[int, int]


@dataclass(slots=True)
class Cell:
    x: int
    y: int
    size: int
    value: int = 0
    _rect: pygame.Rect = None
    is_pressed: bool = False
    is_opened: bool = False
    has_mine: bool = False
    is_flagged: bool = False
    dirty: bool = False

    @property
    def rect(self) -> pygame.Rect:
        """Lazy rect"""
        if self._rect is None:
            self._rect = pygame.draw.rect(
                pygame.display.get_surface(),
                BG_COLOR,
                (self.x * self.size, self.y * self.size, self.size, self.size),
            )

        return self._rect

    @property
    def pos(self) -> T_COORD:
        return self.x, self.y

    @property
    def screen_pos(self) -> T_COORD:
        return self.x * self.size, self.y * self.size

    def draw(self) -> None:
        if self.dirty:
            return

        x, y = self.screen_pos
        font = pygame.font.SysFont("Calibri", int(self.size * 0.75), bold=True)
        text = font.render(str(self.value), True, NUM_COLORS[self.value])
        screen = pygame.display.get_surface()

        draw_reset(self.rect)
        if self.is_flagged:
            draw_border(self.rect)
            draw_flag(self.rect)
        elif not self.is_opened:
            draw_border(self.rect)
        elif self.is_opened:
            draw_empty(self.rect)
            if self.has_mine:
                # TODO trigger game over
                draw_mine(self.rect)
                self.dirty = True
            else:
                if self.value != 0:
                    screen.blit(
                        text,
                        (
                            x + (self.size / 2 - text.get_width() / 2),
                            y + (self.size / 2 - text.get_height() / 2),
                        ),
                    )

                self.dirty = True
        elif self.is_pressed:
            draw_empty(self.rect)

    def __add__(self, other: int) -> "Cell":
        assert isinstance(other, int)
        self.value += other
        return self

    __radd__ = __add__


class Grid:
    mines: list[T_COORD]
    board: list[list[Cell]] = []
    generated: bool

    def __init__(self, rows: int, cols: int, mines: int, scale: int):
        self.__rows = rows
        self.__cols = cols
        self.__scale = scale
        self.num_mines = mines
        self.clear_board()

    def __iter_coords__(self) -> Iterator[T_COORD]:
        """coordinates iterator"""
        yield from (
            (x, y)
            for x, col in enumerate(self.board)
            for y, _ in enumerate(col)
        )

    def __iter_board__(self) -> Iterator[Cell]:
        yield from (cell for col in self.board for cell in col)

    def __iter_neigh_coords__(self, x: int, y: int) -> Iterator[T_COORD]:
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

    def __iter_neighbors__(self, x: int, y: int) -> Iterator[Cell]:
        yield from (self.at(*pos) for pos in self.__iter_neigh_coords__(x, y))

    def __generate_cells(self) -> list[list[Cell]]:
        return [
            [Cell(x, y, self.__scale) for y in range(self.__rows)]
            for x in range(self.__cols)
        ]

    def __seed_mines(self, avoid: T_COORD) -> list[T_COORD]:
        return random.sample(
            [c for c in self.__iter_coords__() if c != avoid], self.num_mines
        )

    def at(self, x: int, y: int) -> Cell:
        assert 0 <= x <= self.__cols - 1
        assert 0 <= y <= self.__rows - 1
        return self.board[x][y]

    def clear_board(self) -> None:
        self.board.clear()
        self.generated = False
        self.board = self.__generate_cells()

    def on_open(self, cell: Cell) -> None:
        # FIXME: get rid of recursion
        if cell.is_opened:
            if cell.value == 0 or cell.has_mine:
                return
            neighbors = list(self.__iter_neighbors__(*cell.pos))
            flagged = len([c for c in neighbors if c.is_flagged])
            if flagged >= cell.value:
                for n in neighbors:
                    if not n.is_opened and not n.is_flagged:
                        self.on_open(n)
        else:
            cell.is_opened = True

        for neigh in self.__iter_neighbors__(*cell.pos):
            if cell.value == 0:
                self.on_open(neigh)

    def generate_board(self, starts_at: T_COORD) -> None:
        self.mines = self.__seed_mines(starts_at)

        for x, y in self.mines:
            cell = self.at(x, y)
            cell.has_mine = True

        for cell in self.__iter_board__():
            for neighbor in self.__iter_neighbors__(*cell.pos):
                if neighbor.has_mine:
                    cell += 1

        self.generated = True
