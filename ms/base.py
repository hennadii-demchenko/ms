import random
from dataclasses import dataclass
from enum import Enum
from typing import Iterator
from typing import Optional

import pygame

from ms.draw import BG_COLOR
from ms.draw import draw_border
from ms.draw import draw_empty
from ms.draw import draw_flag
from ms.draw import draw_mine
from ms.draw import draw_reset
from ms.draw import NUM_COLORS

T_COORD = tuple[int, int]
T_GAME_FIELD = list[list["Cell"]]
DEBUG = False


class Mode(Enum):
    EASY = 1, 9, 9, 10
    MEDIUM = 2, 16, 16, 40
    HARD = 3, 16, 30, 100
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


@dataclass(slots=True)
class Cell:
    x: int
    y: int
    size: int
    value: int = 0
    _rect: pygame.Rect = None
    is_pressed: bool = False
    has_exploded: bool = False
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
        # if self.dirty:
        #     return

        x, y = self.screen_pos
        font = pygame.font.SysFont("Calibri", int(self.size * 0.75), bold=True)
        debug_font = pygame.font.SysFont(
            "Calibri", int(self.size * 0.2), bold=True
        )
        text = font.render(str(self.value), True, NUM_COLORS[self.value])
        screen = pygame.display.get_surface()

        draw_reset(self.rect)
        if self.is_pressed:
            draw_empty(self.rect)
        elif self.is_flagged:
            draw_border(self.rect)
            draw_flag(self.rect)
        elif not self.is_opened:
            draw_border(self.rect)
        elif self.is_opened:
            draw_empty(self.rect)
            if self.has_mine:
                # TODO trigger game over
                draw_mine(self.rect, exploded=self.has_exploded)
                self.dirty = True
            else:
                if DEBUG:
                    screen.blit(
                        debug_font.render(str(self.pos), True, "black"),
                        self.rect.midleft,
                    )
                if self.value != 0:
                    screen.blit(
                        text,
                        (
                            x + (self.size / 2 - text.get_width() / 2),
                            y + (self.size / 2 - text.get_height() / 2),
                        ),
                    )

                self.dirty = True

    def __add__(self, other: int) -> "Cell":
        assert isinstance(other, int)
        self.value += other
        return self

    def __hash__(self) -> int:
        return hash((*self.pos, self.value))

    __radd__ = __add__


def is_safe(cell: Cell) -> bool:
    return (cell.is_opened and not cell.has_exploded) or (
        not cell.is_opened and cell.has_mine
    )


class Grid:
    mines: list[T_COORD] = []
    board: T_GAME_FIELD = []
    generated: bool

    def __init__(self, rows: int, cols: int, mines: int, scale: int):
        self.__rows = rows
        self.__cols = cols
        self.__scale = scale
        self.num_mines = mines
        self.num_opened = 0
        self.num_flagged = 0
        self.num_mines_left = self.num_mines - self.num_flagged
        self.reset_board()

    def __iter__(self) -> Iterator[Cell]:
        yield from self.cells()

    @property
    def num_total(self) -> int:
        return self.__rows * self.__cols

    @property
    def left_unflagged(self) -> int:
        return self.num_mines - self.num_flagged

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

    def cells(self) -> Iterator[Cell]:
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

    def unopened(self) -> Iterator[Cell]:
        yield from (cell for cell in self if not cell.is_opened)

    def neighbors(self, x: int, y: int) -> Iterator[Cell]:
        yield from (self.at(*pos) for pos in self.neighbor_coordinates(x, y))

    def unopened_neighbors(self, x: int, y: int) -> Iterator[Cell]:
        yield from (n for n in self.neighbors(x, y) if not n.is_opened)

    def eligible_neighbors(self, x: int, y: int) -> Iterator[Cell]:
        yield from (
            n
            for n in self.neighbors(x, y)
            if not n.is_opened and not n.is_flagged
        )

    def flagged_neighbors(self, x: int, y: int) -> Iterator[Cell]:
        yield from (n for n in self.neighbors(x, y) if n.is_flagged)

    def flags_around(self, x: int, y: int) -> int:
        return len(list(self.flagged_neighbors(x, y)))

    def __generate_cells(self) -> T_GAME_FIELD:
        return [
            [Cell(x, y, self.__scale) for y in range(self.__rows)]
            for x in range(self.__cols)
        ]

    def __sample_mine_positions(self, avoid: T_COORD) -> list[T_COORD]:
        return random.sample(
            [c for c in self.coordinates() if c != avoid], self.num_mines
        )

    def at(self, x: int, y: int) -> Cell:
        assert 0 <= x <= self.__cols - 1
        assert 0 <= y <= self.__rows - 1
        return self.board[x][y]

    def get_cell_under_cursor(self) -> Optional[Cell]:
        for cell in self:
            if cell.rect.collidepoint(*pygame.mouse.get_pos()):
                return cell
        else:
            return None

    def reset_board(self, new_mode: Optional[Mode] = None) -> None:
        if new_mode is not None:
            self.__rows = new_mode.rows
            self.__cols = new_mode.cols
            self.num_mines = new_mode.num_mines

        self.board.clear()
        self.generated = False
        self.num_opened = 0
        self.num_flagged = 0
        self.board = self.__generate_cells()

    def on_open(self, cell: Cell) -> None:
        # FIXME: get rid of recursion
        if cell.has_mine:
            cell.has_exploded = True

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

    def generate_board(self, starts_at: T_COORD) -> None:
        self.mines.clear()
        self.mines = self.__sample_mine_positions(starts_at)

        for x, y in self.mines:
            cell = self.at(x, y)
            cell.has_mine = True

        for cell in self:
            for neighbor in self.neighbors(*cell.pos):
                if neighbor.has_mine:
                    cell += 1

        self.generated = True

    def reveal(self) -> None:
        for cell in self.unopened():
            if cell.has_mine:
                cell.is_opened = True