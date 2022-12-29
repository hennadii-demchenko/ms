import random
from enum import Enum
from time import perf_counter
from typing import Any
from typing import Iterator
from typing import Optional
from typing import TypeVar

import pygame
from pygame import Color
from pygame.rect import Rect

from ms.draw import BG_COLOR
from ms.draw import SHADOW_COLOR
from ms.draw import SpriteLib

T_COORD = tuple[int, int]
NUM_COLORS = {
    0: BG_COLOR,
    1: Color(0x0, 0x0, 0xFF),
    2: Color(0x0, 0x80, 0x0),
    3: Color(0xFF, 0x0, 0x0),
    4: Color(0x0, 0x0, 0x80),
    5: Color(0x80, 0x0, 0x0),
    6: Color(0x0, 0x80, 0x80),
    7: Color(0x0, 0x0, 0x0),
    8: SHADOW_COLOR,
}


class Mode(Enum):
    EASY = 1, 9, 9, 10
    MEDIUM = 2, 16, 16, 40
    HARD = 3, 16, 30, 99
    CUSTOM = 4, -1, -1, -1

    @property
    def rows(self) -> int:  # rows, cols
        return self.value[1]

    @property
    def cols(self) -> int:  # rows, cols
        return self.value[2]

    @property
    def size(self) -> T_COORD:
        return self.rows, self.cols

    @property
    def num_mines(self) -> int:
        return self.value[3]


T_Co_Cell = TypeVar("T_Co_Cell", bound="Cell", covariant=True)


class Cell:
    def __init__(self, x: int, y: int, rect: Rect, value: int = 0):
        self.x = x
        self.y = y
        self.rect = rect
        self.value = value
        self.is_pressed = False
        self.has_exploded = False
        self.is_opened = False
        self.has_mine = False
        self.is_flagged = False

    @property
    def pos(self) -> T_COORD:
        return self.x, self.y

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, type(self))
            and other.x == self.x
            and other.y == self.y
        )

    def __add__(self, other: int) -> "Cell":
        assert isinstance(other, int)
        self.value += other
        return self

    def __hash__(self) -> int:
        return hash((*self.pos, self.value))

    __radd__ = __add__


class CellButton(Cell):
    __tracked__ = [
        "is_pressed",
        "has_exploded",
        "is_opened",
        "has_mine",
        "is_flagged",
    ]

    def __init__(self, x: int, y: int, rect: Rect, value: int = 0):
        super().__init__(x, y, rect, value=value)
        self.neighbors: list["CellButton"] = []
        self.dirty = True

    def __setattr__(self, key: Any, value: Any) -> None:
        if (
            hasattr(self, key)
            and key in self.__tracked__
            and value != self.__getattribute__(key)
        ):
            self.dirty = True
        super().__setattr__(key, value)

    def draw(self, is_game_over: bool) -> None:
        if not self.dirty:
            return

        screen = pygame.display.get_surface()

        if self.is_pressed:
            screen.blit(SpriteLib.EMPTY, self.rect)
        elif self.is_flagged:
            if not self.has_mine and is_game_over:
                screen.blit(SpriteLib.FALSE_MINE, self.rect)
            else:
                screen.blit(SpriteLib.FLAG, self.rect)
        elif not self.is_opened:
            screen.blit(SpriteLib.UNOPENED, self.rect)
        elif self.is_opened:
            if self.has_mine:
                if self.has_exploded:
                    screen.blit(SpriteLib.EXPLODED_MINE, self.rect)
                else:
                    screen.blit(SpriteLib.MINE, self.rect)
            else:
                screen.blit(SpriteLib.EMPTY, self.rect)
                if self.value != 0:
                    text = SpriteLib.GRID_FONT.render(
                        str(self.value), True, NUM_COLORS[self.value]
                    )
                    screen.blit(
                        text,
                        (
                            self.rect.left
                            + 0.5 * self.rect.w
                            - 0.5 * text.get_width(),
                            self.rect.top
                            + 0.5 * self.rect.h
                            - 0.5 * text.get_height(),
                        ),
                    )

        self.dirty = False


T_GAME_FIELD = list[list[CellButton]]


class Grid:
    mines: list[T_COORD] = []
    board: T_GAME_FIELD = []

    def __init__(self, rect: Rect, mode: Mode, scale: int):
        self.mode = mode
        self.__rows = self.mode.rows
        self.__cols = self.mode.cols
        self.__scale = scale
        self.rect = rect
        self.generated = False
        self.revealed = False
        self.__started_at: float = perf_counter()
        self.elapsed: float = 0.0
        self.num_mines: int = self.mode.num_mines
        self.num_opened = 0
        self.num_flagged = 0
        self.reset_board()

    def __iter__(self) -> Iterator[CellButton]:
        yield from self.cells()

    @property
    def num_total(self) -> int:
        return self.__rows * self.__cols

    @property
    def left_unflagged(self) -> int:
        return max(self.num_mines - self.num_flagged, 0)

    @property
    def left_unopened(self) -> int:
        return self.num_total - self.num_opened

    @property
    def is_finished(self) -> bool:
        for cell in self:
            if cell.has_exploded:
                return True
        else:
            return all([cell.has_mine for cell in self.unopened()])

    def coordinates(self) -> Iterator[T_COORD]:
        """coordinates iterator"""
        yield from (
            (x, y)
            for x, col in enumerate(self.board)
            for y, _ in enumerate(col)
        )

    def cells(self) -> Iterator[CellButton]:
        yield from (cell for col in self.board for cell in col)

    def neighbor_coordinates(self, x: int, y: int) -> Iterator[T_COORD]:
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

    def unopened(self) -> Iterator[CellButton]:
        yield from (cell for cell in self if not cell.is_opened)

    def unopened_neighbors(self, x: int, y: int) -> Iterator[CellButton]:
        yield from (n for n in self.at(x, y).neighbors if not n.is_opened)

    def eligible_neighbors(self, x: int, y: int) -> Iterator[CellButton]:
        yield from (
            n
            for n in self.at(x, y).neighbors
            if not n.is_opened and not n.is_flagged
        )

    def flagged_neighbors(self, x: int, y: int) -> Iterator[CellButton]:
        yield from (n for n in self.at(x, y).neighbors if n.is_flagged)

    def flags_around(self, x: int, y: int) -> int:
        return len(list(self.flagged_neighbors(x, y)))

    def __generate_cells(self) -> T_GAME_FIELD:
        return [
            [
                CellButton(
                    x,
                    y,
                    Rect(
                        self.rect.left + x * self.__scale,
                        self.rect.top + y * self.__scale,
                        self.__scale,
                        self.__scale,
                    ),
                )
                for y in range(self.__rows)
            ]
            for x in range(self.__cols)
        ]

    def __sample_mine_positions(self, avoid: T_COORD) -> list[T_COORD]:
        return random.sample(
            [c for c in self.coordinates() if c != avoid], self.num_mines
        )

    def at(self, x: int, y: int) -> CellButton:
        assert 0 <= x <= self.__cols - 1, x
        assert 0 <= y <= self.__rows - 1, y
        return self.board[x][y]

    def get_cell_under(self, pos: T_COORD) -> Optional[CellButton]:
        x, y = pos
        x_min, y_min = self.at(0, 0).rect.topleft
        x_max, y_max = self.at(
            self.__cols - 1, self.__rows - 1
        ).rect.bottomright

        if x_min < x < x_max and y_min < y < y_max:
            return self.at(
                (x - x_min) // self.__scale, (y - y_min) // self.__scale
            )
        else:
            return None

    def reset_board(self, mode: Optional[Mode] = None) -> None:
        if mode is not None:
            self.__rows = mode.rows
            self.__cols = mode.cols
            self.num_mines = mode.num_mines

        self.board.clear()
        self.generated = False
        self.revealed = False
        self.elapsed = 0.0
        self.num_opened = 0
        self.num_flagged = 0
        self.board = self.__generate_cells()

    def on_open(self, cell: CellButton) -> None:
        # FIXME: replace recursion with dfs traversal
        if cell.is_flagged:
            return

        if cell.has_mine:
            cell.has_exploded = True
            return

        if cell.is_opened:
            if self.flags_around(*cell.pos) >= cell.value:
                for neighbor in self.unopened_neighbors(*cell.pos):
                    if not neighbor.is_flagged:
                        self.on_open(neighbor)
        else:
            cell.is_opened = True
            self.num_opened += 1

        for neigh in self.unopened_neighbors(*cell.pos):
            if cell.value == 0:
                self.on_open(neigh)

        cell.dirty = True

    def generate_board(self, starts_at: T_COORD) -> None:
        self.mines.clear()
        self.mines = self.__sample_mine_positions(starts_at)

        for cell in self:
            cell.neighbors = [
                self.at(*pos) for pos in self.neighbor_coordinates(*cell.pos)
            ]

        for x, y in self.mines:
            cell = self.at(x, y)
            cell.has_mine = True

        for cell in self:
            for neighbor in self.at(*cell.pos).neighbors:
                if neighbor.has_mine:
                    cell.value += 1

        self.generated = True
        self.__started_at = perf_counter()

    def reveal(self) -> None:
        for cell in self.unopened():
            if cell.has_mine:
                cell.is_opened = True

        if not self.revealed:
            self.elapsed = perf_counter() - self.__started_at
            self.revealed = True
