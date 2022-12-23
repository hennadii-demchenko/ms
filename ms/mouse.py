from typing import Callable

import pygame

from ms.base import Grid
from ms.draw import Button

T_CB = Callable[..., None]


class MouseHandler:
    __RESPONDS_TO = [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]

    def __init__(
        self,
        grid: Grid,
        on_flag_callback: T_CB,
        *buttons: Button,
    ):
        self.left: bool = False
        self.clicked_left: bool = False
        self.clicked_right: bool = False
        self.middle: bool = False
        self.right: bool = False
        self.__grid = grid
        self.__on_flag_callback = on_flag_callback
        self.buttons = buttons

    def handle_events(self) -> None:
        for event in pygame.event.get(self.__RESPONDS_TO):
            self.left, self.middle, self.right = pygame.mouse.get_pressed()

            if event.type == pygame.MOUSEBUTTONUP:
                if not self.left and not self.right and self.clicked_left:
                    self.on_l_mouse_up()

                # order matters as we have to keep button state ourselves,
                # otherwise we don't know which button(s) was previously down
                self.clicked_left, self.clicked_right = self.left, self.right

            if event.type == pygame.MOUSEBUTTONDOWN:
                self.clicked_left, self.clicked_right = self.left, self.right

                if not self.left and self.right:
                    self.on_r_mouse_down()

    def on_l_mouse_up(self) -> None:
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            if button.rect.collidepoint(*mouse_pos):
                button.pressed = False
                button.trigger_released()

        cell = self.__grid.get_cell_under(mouse_pos)
        if cell is None:
            return

        if not self.__grid.generated:
            self.__grid.generate_board(cell.pos)
            self.__grid.generated = True

        self.__grid.on_open(cell)

    def on_r_mouse_down(self) -> None:
        cell = self.__grid.get_cell_under(pygame.mouse.get_pos())

        if cell is None or cell.is_opened:
            return

        cell.is_flagged = not cell.is_flagged
        self.__grid.num_flagged += int(cell.is_flagged) or -1
        self.__on_flag_callback()

    def on_update(self) -> None:
        self.__on_mouse_hold()

    def __on_mouse_hold(self) -> None:
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            is_over = button.rect.collidepoint(*mouse_pos)
            button.pressed = self.left and is_over

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
