from pathlib import Path
from typing import Callable

import pygame.draw
from pygame import Color
from pygame import Rect
from pygame.image import load as load_image

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
SPRITE_DIR = ROOT_DIR / "sprites"

T_CALLBACK = Callable[..., None]


class SpriteLib:
    FLAG: pygame.Surface
    MINE: pygame.Surface
    FALSE_MINE: pygame.Surface
    EXPLODED_MINE: pygame.Surface
    UNOPENED: pygame.Surface
    EMPTY: pygame.Surface
    GRID_FONT: pygame.font.Font

    @classmethod
    def setup_sprites(cls, side: int) -> None:
        size = side, side
        font_size = int(side * 0.55)
        cls.FLAG = load_image(SPRITE_DIR / "flag.png").convert()
        cls.MINE = load_image(SPRITE_DIR / "mine.png").convert()
        cls.FALSE_MINE = load_image(SPRITE_DIR / "false_mine.png").convert()
        cls.EXPLODED_MINE = load_image(
            SPRITE_DIR / "mine_exploded.png"
        ).convert()
        cls.UNOPENED = load_image(SPRITE_DIR / "unopened.png").convert()
        cls.EMPTY = load_image(SPRITE_DIR / "empty.png").convert()

        cls.FLAG = pygame.transform.scale(cls.FLAG, size)
        cls.MINE = pygame.transform.scale(cls.MINE, size)
        cls.FALSE_MINE = pygame.transform.scale(cls.FALSE_MINE, size)
        cls.EXPLODED_MINE = pygame.transform.scale(cls.EXPLODED_MINE, size)
        cls.UNOPENED = pygame.transform.scale(cls.UNOPENED, size)
        cls.EMPTY = pygame.transform.scale(cls.EMPTY, size)
        cls.GRID_FONT = pygame.font.Font(ROOT_DIR / "fonts/ms.otf", font_size)


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

        self.new_pressed = pygame.image.load(
            ROOT_DIR / "sprites/new_pressed.png"
        ).convert()
        self.new_unpressed = pygame.image.load(
            ROOT_DIR / "sprites/new_unpressed.png"
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

    def draw_cell_value(self, rect: Rect, value: int) -> None:
        if value == 0:
            return

        text = self.font.render(str(value), False, NUM_COLORS[value])
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
