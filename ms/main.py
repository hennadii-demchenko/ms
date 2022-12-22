from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from typing import Optional

import pygame
from pygame.time import Clock

from ms.base import Button
from ms.base import Grid
from ms.base import Mode
from ms.draw import BG_COLOR
from ms.draw import draw_border
from ms.draw import draw_new_button
from ms.mouse import MouseHandler


ROOT_DIR = Path(__file__).parent.parent


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
    FRAME_RATE = 1020
    TOP_MARGIN = 100
    __mode: Mode

    def __init__(self, mode: Mode = Mode.EASY) -> None:
        # TODO persistent settings
        self.__screen = pygame.display.set_mode((0, 0))
        self.__clock = Clock()
        self.__frame_rate = 100

        self.font = pygame.font.Font(
            ROOT_DIR / "fonts" / "ms.otf", int(self.size * 0.55)
        )
        self.debug_font = pygame.font.SysFont(
            "Calibri", int(self.size * 0.2), bold=True
        )
        self.grid_border_width = self.size // 5
        self.header = pygame.rect.Rect(0, 0, 0, self.TOP_MARGIN)
        self.new_button = Button(pygame.Rect(*self.header.center, 75, 75))
        self.grid_container = pygame.rect.Rect(0, self.TOP_MARGIN, 0, 0)
        self.__grid = Grid((0, 0), mode, scale=self.size)
        self.mode = mode

        self.mouse_handler = MouseHandler(self.__grid, self.new_button)
        self.new_button.add_release_callback(self.start_new)
        self.is_over: bool = False

        pygame.display.set_caption("imps ms")

    @property
    def mode(self) -> Mode:
        return self.__mode

    @mode.setter
    def mode(self, mode: Mode) -> None:
        self.__mode = mode
        self.__grid.mode = mode
        self.header.w = self.mode.cols * self.size + 2 * self.grid_border_width
        self.new_button.rect.center = self.header.center
        self.grid_container.w = (
            self.mode.cols * self.size + 2 * self.grid_border_width
        )
        self.grid_container.h = (
            self.mode.rows * self.size + 2 * self.grid_border_width
        )
        self.__grid.offset_x = self.grid_container.x + self.grid_border_width
        self.__grid.offset_y = self.grid_container.y + self.grid_border_width

        pygame.display.set_mode(
            (self.grid_container.w, self.grid_container.h + self.TOP_MARGIN)
        )
        self.__screen.fill(BG_COLOR)

    def start_new(self, mode: Optional[Mode] = None) -> None:
        if mode is not None:
            self.mode = mode
        self.is_over = False
        self.__grid.reset_board(mode)

    def on_key_up(self, key: int) -> None:
        if key == pygame.K_F2:
            self.start_new()
        elif key == pygame.K_1:
            self.start_new(Mode.EASY)
        elif key == pygame.K_2:
            self.start_new(Mode.MEDIUM)
        elif key == pygame.K_3:
            self.start_new(Mode.HARD)

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
        draw_border(
            self.grid_container,
            inverted=True,
            inside=True,
            border_size=self.grid_border_width,
        )
        draw_border(
            self.header,
            inverted=True,
            inside=True,
            border_size=self.grid_border_width,
        )

        draw_new_button(
            self.new_button.rect,
            self.grid_border_width,
            self.new_button.pressed,
        )

        if not self.is_over:
            self.mouse_handler.on_update()

        self.is_over = self.__grid.generated and self.__grid.is_finished

        if self.is_over:
            self.__grid.reveal()

        for cell in self.__grid:
            cell.draw(self.font, self.debug_font)

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
                game.mouse_handler.handle_events()
            game.on_update()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
