from contextlib import contextmanager
from time import perf_counter
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


@contextmanager
def pygame_runner() -> Iterator[None]:
    pygame.init()
    pygame.mixer.quit()
    pygame.display.init()
    yield
    pygame.font.quit()
    pygame.display.quit()
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
    __STATS_HEIGHT = 50
    __MOUSE_EVENTS = [
        pygame.MOUSEBUTTONDOWN,
        pygame.MOUSEBUTTONUP,
        pygame.MOUSEMOTION,
    ]
    __mode: Mode

    def __init__(self, mode: Mode = Mode.EASY) -> None:
        # TODO persistent settings
        self.__screen = pygame.display.set_mode(mode.size)
        pygame.display.set_caption("imps ms")

        self.is_over: bool = False
        self.running: bool = False
        self.grid_border_width = self.size // 5
        self.left: bool = False
        self.clicked_left: bool = False
        self.clicked_right: bool = False
        self.middle: bool = False
        self.right: bool = False
        self.__started_at = perf_counter()
        self.time_displayed = 0

        self.__clock = Clock()
        self.__artist = AssetArtist(self.size, self.grid_border_width)
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
        self.__artist.derive_nums_size(self.rect_unflagged)

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
            (
                self.grid_container.w,
                self.grid_container.h
                + self.__TOP_MARGIN
                + self.__STATS_HEIGHT,
            )
        )
        self.__screen.fill(BG_COLOR)

        self.rect_unflagged = pygame.rect.Rect(
            self.header.left + self.grid_border_width * 2,
            self.new_button.rect.top,
            self.__DISPLAYS_WIDTH,
            self.new_button.rect.h,
        )
        self.rect_elapsed = pygame.rect.Rect(
            self.header.right
            - self.__DISPLAYS_WIDTH
            - 2 * self.grid_border_width,
            self.new_button.rect.top,
            self.__DISPLAYS_WIDTH,
            self.new_button.rect.h,
        )
        self.rect_stats = pygame.rect.Rect(
            self.grid_container.left,
            self.grid_container.bottom,
            self.header.width,
            self.__STATS_HEIGHT,
        )

    def start_new(self, mode: Optional[Mode] = None) -> None:
        if mode is not None:
            self.mode = mode
        self.is_over = False
        self.time_displayed = 0
        self.__grid.reset_board(mode)

        self.__artist.draw_border(self.header)
        self.__artist.draw_score_value(
            self.rect_unflagged, self.__grid.left_unflagged
        )
        self.__artist.draw_score_value(self.rect_elapsed, self.time_displayed)
        self.new_button.dirty = True
        self.__artist.draw_new(self.new_button)
        self.__artist.draw_border(self.grid_container)
        pygame.draw.rect(self.__screen, BG_COLOR, self.rect_stats)

    def __on_key_up(self, key: int) -> None:
        if key == pygame.K_F2:
            self.start_new()
        elif key == pygame.K_1:
            self.start_new(Mode.EASY)
        elif key == pygame.K_2:
            self.start_new(Mode.MEDIUM)
        elif key == pygame.K_3:
            self.start_new(Mode.HARD)

    def __update_mouse_over(self, pos: T_COORD) -> None:
        hovered = self.__grid.get_cell_under(pos)

        for cell in self.__grid:
            if not hovered:  # out of grid bounds
                cell.is_pressed = False
            elif self.left and not hovered.is_opened:  # highlight just one
                cell.is_pressed = cell is hovered and not cell.is_flagged
            elif self.left and hovered.is_opened:
                eligible = self.__grid.eligible_neighbors(*hovered.pos)
                cell.is_pressed = cell in eligible  # highlight possible
            else:
                cell.is_pressed = False  # release otherwise

    def __on_l_mouse_up(self, pos: T_COORD) -> None:
        if self.new_button.rect.collidepoint(*pos):
            self.new_button.pressed = False
            self.new_button.trigger_released()

        released = self.__grid.get_cell_under(pos)

        if released is not None:
            if not self.__grid.generated:
                self.__grid.generate_board(released.pos)
                self.__grid.generated = True
                self.running = True
                self.__started_at = perf_counter()
            if not self.is_over:
                self.__grid.on_open(released)
                self.__update_mouse_over(pos)

    def __on_r_mouse_down(self, pos: T_COORD) -> None:
        cell = self.__grid.get_cell_under(pos)

        if cell is None or cell.is_opened:
            return

        cell.is_flagged = not cell.is_flagged
        self.__grid.num_flagged += int(cell.is_flagged) or -1
        self.__artist.draw_score_value(
            self.rect_unflagged, self.__grid.left_unflagged
        )

    def __handle_mouse(self) -> None:
        for event in pygame.event.get(self.__MOUSE_EVENTS):
            self.left, self.middle, self.right = pygame.mouse.get_pressed()

            if event.type == pygame.MOUSEBUTTONUP:
                self.__handle_new_game_button(event.pos)

                if not self.left and not self.right and self.clicked_left:
                    self.__on_l_mouse_up(event.pos)

                # order matters as we have to keep button state ourselves,
                # otherwise we don't know which button(s) was previously down
                self.clicked_left, self.clicked_right = self.left, self.right

            if event.type == pygame.MOUSEBUTTONDOWN:
                self.clicked_left, self.clicked_right = self.left, self.right

                self.__handle_new_game_button(event.pos)

                if not self.is_over and self.left and not self.right:
                    self.__update_mouse_over(event.pos)
                if not self.is_over and not self.left and self.right:
                    self.__on_r_mouse_down(event.pos)

            if event.type == pygame.MOUSEMOTION:
                self.__handle_new_game_button(event.pos)
                if not self.is_over:
                    self.__update_mouse_over(event.pos)

    def __handle_new_game_button(self, mouse_pos: T_COORD) -> None:
        hovers = self.new_button.rect.collidepoint(mouse_pos)
        self.new_button.pressed = self.left and hovers
        self.__artist.draw_new(self.new_button)

    def __handle_game_timer(self) -> None:
        elapsed = perf_counter() - self.__started_at
        if elapsed - self.time_displayed >= 1:
            self.time_displayed = int(elapsed)
            self.__artist.draw_score_value(
                self.rect_elapsed, self.time_displayed
            )

    @staticmethod
    def setup_events() -> None:
        pygame.event.set_blocked(None)  # blocks all
        pygame.event.set_allowed(pygame.QUIT)
        pygame.event.set_allowed(pygame.MOUSEBUTTONUP)
        pygame.event.set_allowed(pygame.MOUSEBUTTONDOWN)
        pygame.event.set_allowed(pygame.MOUSEMOTION)
        pygame.event.set_allowed(pygame.KEYUP)

    def handle_events(self) -> None:
        pygame.event.pump()
        for event in pygame.event.get([pygame.QUIT, pygame.KEYUP]):
            if event.type == pygame.QUIT:
                self.quit_invoked = True

            if event.type == pygame.KEYUP:
                self.__on_key_up(event.key)

        self.__handle_mouse()

    def update(self) -> None:
        if not self.is_over and self.__grid.generated:
            self.__handle_game_timer()

        self.is_over = self.__grid.generated and self.__grid.is_finished

        if self.is_over:
            if self.running and not any([c.has_exploded for c in self.__grid]):
                completed_at = perf_counter() - self.__started_at
                self.__artist.draw_stats_value(
                    self.rect_stats, f"Completed in {completed_at:.03f}"
                )

            self.__grid.reveal()
            self.running = False

        for cell in self.__grid:
            cell.draw(self.__artist, self.is_over)

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
