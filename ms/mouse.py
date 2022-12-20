import pygame

from ms.base import Grid


class MouseHandler:
    __RESPONDS_TO = [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]

    def __init__(self, grid: Grid):
        self.left: bool = False
        self._left_was_pressed: bool = False
        self.middle: bool = False
        self.right: bool = False
        self._grid = grid

    def handle_events(self) -> None:
        for event in pygame.event.get(self.__RESPONDS_TO):
            self.left, self.middle, self.right = pygame.mouse.get_pressed()

            if event.type == pygame.MOUSEBUTTONUP:
                if not self.left and not self.right and self._left_was_pressed:
                    self.on_l_mouse_up()
                    self._left_was_pressed = self.left

            if event.type == pygame.MOUSEBUTTONDOWN:
                self._left_was_pressed = self.left
                if not self.left and self.right:
                    self.on_r_mouse_down()

    def on_l_mouse_up(self) -> None:
        for cell in self._grid.__iter_board__():
            if cell.rect.collidepoint(*pygame.mouse.get_pos()):
                if not self._grid.generated:
                    self._grid.generate_board(cell.pos)
                    self._grid.generated = True

                self._grid.on_open(cell)

    def on_r_mouse_down(self) -> None:
        for cell in self._grid.__iter_board__():
            if cell.rect.collidepoint(*pygame.mouse.get_pos()):
                cell.is_flagged = not cell.is_flagged

    def on_update(self, x: int, y: int) -> None:
        self.__on_mouse_hold(x, y)

    def __on_mouse_hold(self, x: int, y: int) -> None:
        for cell in self._grid.__iter_board__():
            if cell.rect.collidepoint(x, y):
                neighbors = []

                if cell.is_opened:
                    neighbors += [
                        c
                        for c in self._grid.__iter_neighbors__(*cell.pos)
                        if not c.is_opened
                    ]

                for c in self._grid.__iter_board__():
                    c.is_pressed = self.left and c in [cell, *neighbors]
