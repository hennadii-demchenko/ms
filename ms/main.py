from contextlib import contextmanager
from threading import Event
from typing import Iterator

import pygame
from pygame.time import Clock

from ms.base import Grid, Cell
from ms.draw import BG_COLOR
from ms.mouse import MouseHandler


class Fog:
    """board uncovering"""


@contextmanager
def pygame_runner() -> Iterator[None]:
    pygame.init()
    pygame.mixer.quit()
    pygame.display.init()
    pygame.font.init()
    yield
    pygame.quit()


class Game:
    """
    facade for
    - settings
    - stats
    - start/restart game
    - tbd

    """

    INITIAL_SIZE = 1200, 1600
    is_over: Event = Event()
    size: int = 50

    def __init__(self) -> None:
        rows, cols, mines = 9, 9, 10  # FIXME: set from settings
        self.__screen = pygame.display.set_mode(self.INITIAL_SIZE)
        self.__screen.fill(BG_COLOR)
        pygame.display.set_caption("imps ms")

        self.__clock = Clock()
        self.__frame_rate = 100

        self.grid = Grid(rows, cols, mines, scale=self.size)
        self.generated = False

        self.mouse_handler = MouseHandler(self.grid)

    def start_new(self) -> None:
        self.is_over.clear()
        self.grid.clear_board()

    def dfs_traverse(self, node: Cell) -> Iterator[Cell]:
        visited = []
        if node in visited:
            return

        yield node
        visited.append(node)

        for inner in self.grid.__iter_neighbors__(*node.pos):
            if inner not in visited:
                self.dfs_traverse(self.grid.at(*inner))
    #
    # def on_left_mdown(self, x: int, y: int):
    #     for cell in self.grid.__iter_board__():
    #         if cell.rect.collidepoint(x, y):
    #             if cell.is_opened or cell.is_flagged:
    #                 continue
    #
    #             if not cell.is_pressed:
    #                 cell.is_pressed = True
    #
    # def on_right(self, x: int, y: int) -> None:
    #     for cell in self.grid.__iter_board__():
    #         if cell.rect.collidepoint(x, y):
    #             if not cell.is_flagged:
    #                 cell.is_flagged = True
    #             else:
    #                 cell.is_flagged = False
    #                 draw_reset(cell.rect)
    #



    # def on_mdown(self, x: int, y: int, left: bool, right: bool) -> None:
    #     for cell in self.grid.__iter_board__():
    #         if cell.rect.collidepoint(x, y):
    #             if not self.grid.generated:
    #                 self.grid.generate_board(cell.pos)
    #
    #             if cell.is_opened:
    #                 continue
    #
    #             if left and not cell.is_pressed:
    #                 cell.is_pressed = True
    #
    #             # if left and not cell.is_opened and not cell.is_flagged:
    #             #     cell.is_opened = True
    #
    #                 # if cell.has_mine: # FIXME
    #                 #     cell.is_pressed = True
    #
    #                 # if cell.value == 0 and not cell.has_mine:
    #                 #     for adjacent in self.dfs_traverse(cell):
    #                 #         adjacent.is_opened = True
    #
    #             # elif left and cell.is_opened and not cell.is_pressed:
    #             #     cell.is_pressed = True
    #             #     # for neighbor in self.grid.__iter_neighbors__(*cell.pos):
    #             #     #     self.grid.at(*neighbor).is_pressed = True
    #             #
    #
    #             if right and not cell.is_flagged:
    #                 cell.is_flagged = True
    #             elif right and cell.is_flagged:
    #                 cell.is_flagged = False
    #                 draw_reset(cell.rect)
    #
    # def on_mup(self, x: int, y: int) -> None:
    #     for cell in self.grid.__iter_board__():
    #         if cell.rect.collidepoint(x, y):
    #             if cell.is_pressed:
    #                 cell.is_pressed = False


    def on_key_up(self, key: int) -> None:
        if key == pygame.K_F2:
            self.start_new()
        elif key == pygame.K_2:
            ...
        elif key == pygame.K_3:
            ...
        elif key == pygame.K_1:
            ...

    def handle_events(self) -> None:
        for event in pygame.event.get([pygame.QUIT, pygame.KEYUP]):
            if event.type == pygame.QUIT:
                self.is_over.set()

            if event.type == pygame.KEYUP:
                self.on_key_up(event.key)

    def update(self) -> None:
        self.mouse_handler.on_update(*pygame.mouse.get_pos())
        [self.grid.at(*pos).draw() for pos in self.grid.__iter_coords__()]
        self.__clock.tick(self.__frame_rate)
        pygame.display.flip()


def main() -> int:

    with pygame_runner():
        game = Game()
        game.start_new()  # FIXME REMOVE

        pygame.event.set_blocked(None)
        pygame.event.set_allowed(pygame.QUIT)
        pygame.event.set_allowed(pygame.MOUSEBUTTONUP)
        pygame.event.set_allowed(pygame.MOUSEBUTTONDOWN)
        pygame.event.set_allowed(pygame.KEYUP)

        while not game.is_over.is_set():
            pygame.event.pump()
            game.mouse_handler.handle_events()
            game.handle_events()
            game.update()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
