from pathlib import Path
from typing import Callable

import pygame.draw
from pygame import Color
from pygame import Rect

BG_COLOR = Color(0xC0, 0xC0, 0xC0)
SHADOW_COLOR = Color(0x80, 0x80, 0x80)
HIGHLIGHT_COLOR = Color(0xFF, 0xFF, 0xFF)
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
ROOT_DIR = Path(__file__).parent.parent

T_CALLBACK = Callable[..., None]


class Button:
    def __init__(self, rect: Rect):
        self.dirty = True
        self.rect = rect
        self.__pressed = False
        self.__release_callbacks: list[T_CALLBACK] = []
        self.__press_callbacks: list[T_CALLBACK] = []

    def add_press_callbacks(self, *cbs: T_CALLBACK) -> None:
        self.__press_callbacks.extend(cbs)

    def add_release_callbacks(self, *cbs: T_CALLBACK) -> None:
        self.__release_callbacks.extend(cbs)

    @property
    def pressed(self) -> bool:
        return self.__pressed

    @pressed.setter
    def pressed(self, value: bool) -> None:
        self.dirty = self.__pressed != value
        self.__pressed = value

    def trigger_pressed(self) -> None:
        for callback in self.__press_callbacks:
            callback()

    def trigger_released(self) -> None:
        for callback in self.__release_callbacks:
            callback()


class AssetArtist:
    __NEW_BUTTON_SIZE = 75, 75

    def __init__(self, size: int, border_width: int):
        self.__screen = pygame.display.get_surface()
        self.font = pygame.font.Font(
            ROOT_DIR / "fonts/ms.otf", int(size * 0.55)
        )
        self.stats_font = pygame.font.SysFont(
            ["Courier", "Calibri", "Arial"], size // 2, bold=True
        )
        self.debug_font = pygame.font.SysFont(
            "Calibri", int(size * 0.2), bold=True
        )
        self.border_width = border_width
        self.nums_margin = 0
        self.nums_width = 0

        self.flag = pygame.image.load(ROOT_DIR / "sprites/flag.png").convert()
        self.mine = pygame.image.load(ROOT_DIR / "sprites/mine.png").convert()
        self.false_mine = pygame.image.load(
            ROOT_DIR / "sprites/false_mine.png"
        ).convert()
        self.exploded_mine = pygame.image.load(
            ROOT_DIR / "sprites/mine_exploded.png"
        ).convert()
        self.unopened = pygame.image.load(
            ROOT_DIR / "sprites/unopened.png"
        ).convert()
        self.new_pressed = pygame.image.load(
            ROOT_DIR / "sprites/new_pressed.png"
        ).convert()
        self.new_unpressed = pygame.image.load(
            ROOT_DIR / "sprites/new_unpressed.png"
        ).convert()
        self.empty = pygame.image.load(
            ROOT_DIR / "sprites/empty.png"
        ).convert()
        self.nums_bg = pygame.image.load(
            ROOT_DIR / "sprites/nums_bg.png"
        ).convert()
        self.nums_map = {
            x: pygame.image.load(ROOT_DIR / f"sprites/d{x}.png").convert()
            for x in range(10)
        }

        self.border_dark = pygame.image.load(
            ROOT_DIR / "sprites/border_dark.png"
        ).convert()
        self.border_light = pygame.image.load(
            ROOT_DIR / "sprites/border_light.png"
        ).convert()
        self.border_corner = pygame.image.load(
            ROOT_DIR / "sprites/border_corner.png"
        ).convert()

        square_size = size, size
        self.flag = pygame.transform.scale(self.flag, square_size)
        self.mine = pygame.transform.scale(self.mine, square_size)
        self.false_mine = pygame.transform.scale(self.false_mine, square_size)
        self.exploded_mine = pygame.transform.scale(
            self.exploded_mine, square_size
        )
        self.unopened = pygame.transform.scale(self.unopened, square_size)
        self.empty = pygame.transform.scale(self.empty, square_size)
        self.new_pressed = pygame.transform.scale(
            self.new_pressed, self.__NEW_BUTTON_SIZE
        )
        self.new_unpressed = pygame.transform.scale(
            self.new_unpressed, self.__NEW_BUTTON_SIZE
        )
        self.border_corner = pygame.transform.scale(
            self.border_corner, (self.border_width, self.border_width)
        )

    def derive_nums_size(self, mines_nums_rect: Rect) -> None:
        self.nums_bg = pygame.transform.scale(
            self.nums_bg, mines_nums_rect.size
        )

        margin = mines_nums_rect.w // 20
        width = (mines_nums_rect.width - 3 * margin) // 3
        height = mines_nums_rect.height - 2 * margin

        self.nums_margin = margin
        self.nums_width = width

        for num, image in self.nums_map.items():
            self.nums_map[num] = pygame.transform.scale(image, (width, height))

    def draw_empty(self, rect: Rect) -> None:
        self.__screen.blit(self.empty, rect)

    def draw_unopen(self, rect: Rect) -> None:
        self.__screen.blit(self.unopened, rect)

    def draw_cell_value(self, rect: Rect, value: int) -> None:
        if value == 0:
            return

        text = self.font.render(str(value), True, NUM_COLORS[value])
        centered_position = (
            rect.left + (rect.w / 2 - text.get_width() / 2.33),
            rect.top + (rect.h / 2 - text.get_height() / 2),
        )
        self.__screen.blit(text, centered_position)

    def draw_score_value(self, rect: Rect, value: int) -> None:
        self.__screen.blit(self.nums_bg, rect)
        self.__screen.blit(
            self.nums_map[value // 100],
            (rect.left + self.nums_margin, rect.top + self.nums_margin),
        )
        self.__screen.blit(
            self.nums_map[value // 10 % 10],
            (
                rect.left + 2 * self.nums_margin + self.nums_width,
                rect.top + self.nums_margin,
            ),
        )
        self.__screen.blit(
            self.nums_map[value % 10],
            (
                rect.left + 3 * self.nums_margin + 2 * self.nums_width,
                rect.top + self.nums_margin,
            ),
        )

    def draw_new(self, button: Button) -> None:
        if not button.dirty:
            return
        sprite = self.new_pressed if button.pressed else self.new_unpressed
        self.__screen.blit(sprite, button.rect)
        button.dirty = False

    def draw_stats_value(self, rect: Rect, value: str) -> None:
        text = self.stats_font.render(value, True, "black")
        centered_position = (
            rect.left + (rect.w / 2 - text.get_width() / 2),
            rect.top + (rect.h / 2 - text.get_height() / 2),
        )
        self.__screen.blit(text, centered_position)

    def draw_border(self, rect: Rect) -> None:
        vertical = self.border_width, rect.height
        horizontal = rect.width, self.border_width

        border_left = pygame.transform.scale(self.border_dark, vertical)
        border_top = pygame.transform.scale(self.border_dark, horizontal)
        border_right = pygame.transform.scale(self.border_light, vertical)
        border_bot = pygame.transform.scale(self.border_light, horizontal)

        border_right_rect = border_right.get_rect()
        border_bot_rect = border_bot.get_rect()
        top_right_corner_rect = self.border_corner.get_rect()
        bot_left_corner_rect = self.border_corner.get_rect()
        border_right_rect.topright = rect.topright
        top_right_corner_rect.topright = rect.topright
        border_bot_rect.bottomleft = rect.bottomleft
        bot_left_corner_rect.bottomleft = rect.bottomleft

        self.__screen.blit(border_left, rect.topleft)
        self.__screen.blit(border_top, rect.topleft)
        self.__screen.blit(border_right, border_right_rect)
        self.__screen.blit(self.border_corner, top_right_corner_rect)
        self.__screen.blit(border_bot, border_bot_rect)
        self.__screen.blit(self.border_corner, bot_left_corner_rect)

    def draw_flag(self, rect: Rect) -> None:
        self.__screen.blit(self.flag, rect)

    def draw_mine(self, rect: Rect, exploded: bool = False) -> None:
        sprite = self.exploded_mine if exploded else self.mine
        self.__screen.blit(sprite, rect)

    def draw_false_mine(self, rect: Rect) -> None:
        self.__screen.blit(self.false_mine, rect)
