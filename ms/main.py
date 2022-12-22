from contextlib import contextmanager
from typing import Iterator
from typing import Optional

import pygame
from pygame.time import Clock

from ms.base import Grid
from ms.base import Mode
from ms.draw import BG_COLOR
from ms.mouse import GridClicksHandler


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

    quit_invoked: bool = False
    size: int = 40  # TODO configure
    INITIAL_SIZE = 1200, 1600  # FIXME derive
    FRAME_RATE = 100

    def __init__(self, mode: Mode = Mode.EASY) -> None:
        # TODO persistent settings
        self.mode = mode
        self.__screen = pygame.display.set_mode(self.INITIAL_SIZE)
        self.__clock = Clock()
        self.__frame_rate = 100
        grid_offset = 100, 100

        self.__grid = Grid(
            grid_offset,
            self.mode.rows,
            self.mode.cols,
            self.mode.num_mines,
            scale=self.size,
        )
        self.grid_handler = GridClicksHandler(self.__grid)
        self.is_over: bool = False

        self.__screen.fill(BG_COLOR)
        pygame.display.set_caption("imps ms")

    def start_new(self, new_mode: Optional[Mode] = None) -> None:
        self.is_over = False
        self.__grid.reset_board(new_mode=new_mode)

    def on_key_up(self, key: int) -> None:
        if key == pygame.K_F2:
            self.start_new()
        elif key == pygame.K_1:
            self.start_new(new_mode=Mode.EASY)
        elif key == pygame.K_2:
            self.start_new(new_mode=Mode.MEDIUM)
        elif key == pygame.K_3:
            self.start_new(new_mode=Mode.HARD)

    @staticmethod
    def setup_events() -> None:
        pygame.event.set_blocked(None)  # blocks all
        pygame.event.set_allowed(pygame.QUIT)
        pygame.event.set_allowed(pygame.MOUSEBUTTONUP)
        pygame.event.set_allowed(pygame.MOUSEBUTTONDOWN)
        pygame.event.set_allowed(pygame.KEYUP)

    def handle_events(self) -> None:
        pygame.event.pump()
        for event in pygame.event.get([pygame.QUIT, pygame.KEYUP]):
            if event.type == pygame.QUIT:
                self.quit_invoked = True

            if event.type == pygame.KEYUP:
                self.on_key_up(event.key)

    def on_update(self) -> None:
        if not self.is_over:
            self.grid_handler.on_update()

        self.is_over = self.__grid.generated and self.__grid.is_finished

        if self.is_over:
            self.__grid.reveal()

        for cell in self.__grid:
            cell.draw()

        self.__clock.tick(self.FRAME_RATE)
        pygame.display.flip()


def main() -> int:

    with pygame_runner():
        game = Game()
        game.setup_events()
        game.start_new()  # FIXME REMOVE

        while not game.quit_invoked:
            game.handle_events()
            if not game.is_over:
                game.grid_handler.handle_events()
            game.on_update()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
