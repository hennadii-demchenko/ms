import pygame

from ms.base import Grid
from ms.draw import Button


class MouseHandler:
    __RESPONDS_TO = [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]

    def __init__(self, grid: Grid, *buttons: Button):
        self.left: bool = False
        self.clicked_left: bool = False
        self.clicked_right: bool = False
        self.middle: bool = False
        self.right: bool = False
        self._grid = grid
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

        cell = self._grid.get_cell_under(mouse_pos)
        if cell is None:
            return

        if not self._grid.generated:
            self._grid.generate_board(cell.pos)
            self._grid.generated = True

        self._grid.on_open(cell)

    def on_r_mouse_down(self) -> None:
        cell = self._grid.get_cell_under(pygame.mouse.get_pos())

        if cell is None or cell.is_opened:
            return

        cell.is_flagged = not cell.is_flagged
        self._grid.num_flagged += cell.is_flagged or -1

    def on_update(self) -> None:
        self.__on_mouse_hold()

    def __on_mouse_hold(self) -> None:
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            is_over = button.rect.collidepoint(*mouse_pos)
            button.pressed = self.left and is_over

        hovered = self._grid.get_cell_under(mouse_pos)

        for cell in self._grid:
            if not self.left or hovered is None:  # no mouse hold over any cell
                cell.is_pressed = False
            elif self.left and not hovered.is_opened:  # hold over unopened
                cell.is_pressed = cell is hovered and not cell.is_flagged
            elif self.left and hovered.is_opened:  # hold to reveal possible
                cell.is_pressed = cell in self._grid.eligible_neighbors(
                    *hovered.pos
                )
            else:
                cell.is_pressed = False
