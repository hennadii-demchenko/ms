from contextlib import contextmanager
from threading import Event
from typing import Iterator

import pygame
from pygame.time import Clock

from ms.base import Grid
from ms.draw import BG_COLOR
from ms.mouse import MouseHandler


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
        for cell in self.grid.__iter_board__():
            cell.draw()
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
