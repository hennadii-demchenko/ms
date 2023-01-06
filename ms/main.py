from pathlib import Path
from typing import Any

import arcade
import pyglet.window
from arcade import key
from arcade import Sprite
from arcade import SpriteList
from arcade import SpriteSolidColor as Fill
from arcade import Window

from ms.base import Mode
from ms.color import BG_COLOR

SPRITE_DIR = Path(__file__).parent.parent / "sprites"


class Img(Sprite):  # type: ignore[misc]
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs, hit_box_algorithm="None")


class ResourceFactory:
    __BORDER_LIGHT = SPRITE_DIR / "border_light.png"
    __BORDER_DARK = SPRITE_DIR / "border_dark.png"
    __BORDER_CORNER = SPRITE_DIR / "border_corner.png"

    def __init__(self, scale: int):
        self.__scale = scale
        self.__dark_scale = scale // 5 / Img(self.__BORDER_DARK).height
        self.__light_scale = scale // 5 / Img(self.__BORDER_LIGHT).height
        self.__corner_scale = scale // 5 / Img(self.__BORDER_CORNER).height

    def get_dark(self) -> Img:
        return Img(self.__BORDER_DARK, scale=self.__dark_scale)

    def get_light(self) -> Img:
        return Img(self.__BORDER_LIGHT, scale=self.__light_scale)

    def get_corner(self) -> Img:
        return Img(self.__BORDER_CORNER, scale=self.__corner_scale)


class UI(Window):  # type: ignore[misc]
    __INITIAL_SIZE = 1, 1
    __TITLE = "imps ms"
    __HEADER_H = 100

    __mode: Mode
    __grid_w: int
    __grid_h: int
    __h: int
    __w: int

    def __init__(self) -> None:
        super().__init__(
            *self.__INITIAL_SIZE,
            title=self.__TITLE,
            style=pyglet.window.Window.WINDOW_STYLE_DIALOG,
        )
        arcade.set_background_color(BG_COLOR)

        self.__scale = 50  # FIXME: set from settings
        self.__border = self.__scale // 5
        self.__resources = ResourceFactory(self.__scale)
        self.wireframe = SpriteList()

        self.set_mode(Mode.HARD)

    def resize_layout(self, mode: Mode) -> None:
        self.__grid_w = mode.cols * self.__scale
        self.__grid_h = mode.rows * self.__scale
        self.__w = 2 * self.__border + self.__grid_w
        self.__h = 2 * self.__border + self.__grid_h + self.__HEADER_H

    def resize_wireframe(self) -> None:
        grid_section_h = 2 * self.__border + self.__grid_h
        bg = Fill(self.__w, self.__h, BG_COLOR)

        self.wireframe.clear(deep=True)
        self.clear()

        bg.left = bg.bottom = 0
        self.wireframe.append(bg)

        g_corner_bot = self.__resources.get_corner()
        h_corner_bot = self.__resources.get_corner()
        h_corner_top = self.__resources.get_corner()
        g_corner_top = self.__resources.get_corner()

        g_corner_bot.left = h_corner_bot.left = 0
        g_corner_bot.bottom = 0
        g_corner_top.left = h_corner_top.left = self.__w - self.__border
        g_corner_top.bottom = self.__border + self.__grid_h
        h_corner_bot.bottom = self.__h - self.__HEADER_H
        h_corner_top.bottom = self.__h - self.__border

        for x in range(0, self.__w, self.__border):
            g_top = self.__resources.get_light()
            h_top = self.__resources.get_light()
            g_bot = self.__resources.get_dark()
            h_bot = self.__resources.get_dark()
            h_top.left = g_top.left = h_bot.left = g_bot.left = x
            g_bot.bottom = 0
            g_top.bottom = self.__border + self.__grid_h
            h_bot.bottom = g_top.top
            h_top.top = self.__h
            self.wireframe.append(h_top)
            self.wireframe.append(g_top)
            self.wireframe.append(h_bot)
            self.wireframe.append(g_bot)

        for y in range(grid_section_h, self.__h, self.__border):
            h_left = self.__resources.get_light()
            h_right = self.__resources.get_dark()
            h_left.bottom = h_right.bottom = y
            h_left.left = 0
            h_right.left = self.__w - self.__border
            self.wireframe.append(h_left)
            self.wireframe.append(h_right)

        for y in range(0, grid_section_h, self.__border):
            g_left = self.__resources.get_light()
            g_right = self.__resources.get_dark()
            g_left.bottom = g_right.bottom = y
            g_left.left = 0
            g_right.left = self.__w - self.__border
            self.wireframe.append(g_left)
            self.wireframe.append(g_right)

        self.wireframe.append(g_corner_top)
        self.wireframe.append(h_corner_top)
        self.wireframe.append(g_corner_bot)
        self.wireframe.append(h_corner_bot)

    def draw_grid(self) -> None:
        ...

    def set_mode(self, mode: Mode) -> None:
        self.__mode = mode
        self.resize_layout(mode)
        self.set_size(self.__w, self.__h)
        self.resize_wireframe()

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        if symbol == key.KEY_1:
            self.set_mode(Mode.EASY)
        elif symbol == key.KEY_2:
            self.set_mode(Mode.MEDIUM)
        elif symbol == key.KEY_3:
            self.set_mode(Mode.HARD)

    def on_draw(self) -> None:
        self.wireframe.draw()


class Game:
    def __init__(self) -> None:
        self.ui = UI()
        self.ui.event("on_key_release")(self.on_key_release)

    def on_key_release(self, sym: int, modifiers: int) -> None:
        ...  # TODO: Handle new game/update grid


def main() -> int:
    Game()
    arcade.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
