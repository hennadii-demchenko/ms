import pygame

from ms.base import Grid


class MouseHandler:
    __RESPONDS_TO = [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]

    def __init__(self, grid: Grid):
        self.left: bool = False
        self.middle: bool = False
        self.right: bool = False
        self._grid = grid

    def handle_events(self) -> None:
        for event in pygame.event.get(self.__RESPONDS_TO):
            if event.type == pygame.MOUSEBUTTONUP:
                self.left, self.middle, self.right = False, False, False

            if event.type == pygame.MOUSEBUTTONDOWN:
                self.left, self.middle, self.right = pygame.mouse.get_pressed()

    def on_update(self, x: int, y: int) -> None:
        self.__on_mouse_hold(x, y)

    def __on_mouse_hold(self, x: int, y: int) -> None:
        for cell in self._grid.__iter_board__():
            if cell.rect.collidepoint(x, y):
                # TODO chords
                if self.left and not cell.is_pressed:
                    cell.is_pressed = True
                elif not self.left:
                    cell.is_pressed = False
            else:
                cell.is_pressed = False
