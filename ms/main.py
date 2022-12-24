from contextlib import contextmanager
from typing import Iterator
from typing import Optional

import pygame
from pygame.time import Clock

from ms.base import Grid
from ms.base import Mode
from ms.base import T_COORD
from ms.draw import AssetArtist
from ms.draw import BG_COLOR
from ms.draw import Button
from ms.draw import draw_border


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
    __FRAME_RATE = 100
    __NEW_BUTTON_SIZE = 75
    __DISPLAYS_WIDTH = 110
    __TOP_MARGIN = 100
    __MOUSE_EVENTS = [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]
    __mode: Mode

    def __init__(self, mode: Mode = Mode.EASY) -> None:
        # TODO persistent settings
        self.__screen = pygame.display.set_mode((0, 0))
        pygame.display.set_caption("imps ms")

        self.is_over: bool = False
        self.grid_border_width = self.size // 5
        self.left: bool = False
        self.clicked_left: bool = False
        self.clicked_right: bool = False
        self.middle: bool = False
        self.right: bool = False
        self.elapsed = 0

        self.__clock = Clock()
        self.artist = AssetArtist(self.size)
        self.__grid = Grid((0, 0), mode, scale=self.size)

        self.header = pygame.rect.Rect(0, 0, 0, self.__TOP_MARGIN)
        self.new_button = Button(
            pygame.Rect(
                *self.header.center,
                self.__NEW_BUTTON_SIZE,
                self.__NEW_BUTTON_SIZE,
            )
        )
        self.new_button.add_release_callbacks(self.start_new)
        self.grid_container = pygame.rect.Rect(0, self.__TOP_MARGIN, 0, 0)
        self.mode = mode

        self.artist.setup_assets()
        self.artist.derive_nums_size(self.rect_unflagged)

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
            (self.grid_container.w, self.grid_container.h + self.__TOP_MARGIN)
        )
        self.__screen.fill(BG_COLOR)

        self.rect_unflagged = pygame.rect.Rect(
            self.header.left + self.grid_border_width * 2,
            self.new_button.rect.top,
            self.__DISPLAYS_WIDTH,
            self.new_button.rect.h,
        )
        self.rect_elapsed = pygame.rect.Rect(
            self.header.right - 100 - 2 * self.grid_border_width,
            self.new_button.rect.top,
            self.__DISPLAYS_WIDTH,
            self.new_button.rect.h,
        )

    def start_new(self, mode: Optional[Mode] = None) -> None:
        if mode is not None:
            self.mode = mode
        self.is_over = False
        self.__grid.reset_board(mode)
        self.new_button.dirty = True
        draw_border(
            self.grid_container,
            inverted=True,
            inside=True,
            width=self.grid_border_width,
        )
        draw_border(
            self.header,
            inverted=True,
            inside=True,
            width=self.grid_border_width,
        )

        self.artist.draw_score_value(
            self.rect_unflagged, self.__grid.left_unflagged
        )

    def __on_key_up(self, key: int) -> None:
        if key == pygame.K_F2:
            self.start_new()
        elif key == pygame.K_1:
            self.start_new(Mode.EASY)
        elif key == pygame.K_2:
            self.start_new(Mode.MEDIUM)
        elif key == pygame.K_3:
            self.start_new(Mode.HARD)

    def __on_l_mouse_up(self) -> None:
        mouse_pos = pygame.mouse.get_pos()

        if self.new_button.rect.collidepoint(*mouse_pos):
            self.new_button.pressed = False
            self.new_button.trigger_released()

        cell = self.__grid.get_cell_under(mouse_pos)
        if cell is not None:
            if not self.__grid.generated:
                self.__grid.generate_board(cell.pos)
                self.__grid.generated = True
            self.__grid.on_open(cell)

    def __on_r_mouse_down(self) -> None:
        cell = self.__grid.get_cell_under(pygame.mouse.get_pos())

        if cell is None or cell.is_opened:
            return

        cell.is_flagged = not cell.is_flagged
        self.__grid.num_flagged += int(cell.is_flagged) or -1
        self.artist.draw_score_value(
            self.rect_unflagged, self.__grid.left_unflagged
        )

    def __handle_mouse(self) -> None:
        for event in pygame.event.get(self.__MOUSE_EVENTS):
            self.left, self.middle, self.right = pygame.mouse.get_pressed()

            if event.type == pygame.MOUSEBUTTONUP:
                if not self.left and not self.right and self.clicked_left:
                    self.__on_l_mouse_up()

                # order matters as we have to keep button state ourselves,
                # otherwise we don't know which button(s) was previously down
                self.clicked_left, self.clicked_right = self.left, self.right

            if event.type == pygame.MOUSEBUTTONDOWN:
                self.clicked_left, self.clicked_right = self.left, self.right

                if not self.left and self.right:
                    self.__on_r_mouse_down()

    def __handle_new_game_button(self, mouse_pos: T_COORD) -> None:
        hovers = self.new_button.rect.collidepoint(mouse_pos)
        self.new_button.pressed = self.left and hovers

    def __on_mouse_hold(self, mouse_pos: T_COORD) -> None:
        hovered = self.__grid.get_cell_under(mouse_pos)

        for cell in self.__grid:
            # no mouse hold over any cell
            if not self.left or hovered is None:
                cell.is_pressed = False
            # hold over unopened
            elif self.left and not hovered.is_opened:
                cell.is_pressed = cell is hovered and not cell.is_flagged
            # hold to reveal possible
            elif self.left and hovered.is_opened and not hovered.is_flagged:
                cell.is_pressed = cell in self.__grid.eligible_neighbors(
                    *hovered.pos
                )
            else:
                cell.is_pressed = False

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
                self.__on_key_up(event.key)

        if not self.is_over:
            self.__handle_mouse()

    def update(self) -> None:
        self.artist.draw_new(self.new_button)
        mouse_pos = pygame.mouse.get_pos()
        self.__handle_new_game_button(mouse_pos)

        if not self.is_over:
            self.__on_mouse_hold(mouse_pos)

        self.is_over = self.__grid.generated and self.__grid.is_finished
        if self.is_over:
            self.__grid.reveal()

        for cell in self.__grid:
            cell.draw(self.artist)

        self.__clock.tick(self.__FRAME_RATE)

        pygame.display.flip()


def main() -> int:

    with pygame_runner():
        game = Game()
        game.setup_events()
        game.start_new()  # FIXME REMOVE

        while not game.quit_invoked:
            game.handle_events()
            game.update()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
