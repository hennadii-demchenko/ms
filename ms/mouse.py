import pygame

from ms.base import Grid


class GridClicksHandler:
    __RESPONDS_TO = [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]

    def __init__(self, grid: Grid):
        self.left: bool = False
        self.clicked_left: bool = False
        self.clicked_right: bool = False
        self.middle: bool = False
        self.right: bool = False
        self._grid = grid

    def handle_events(self) -> None:
        for event in pygame.event.get(self.__RESPONDS_TO):
            self.left, self.middle, self.right = pygame.mouse.get_pressed()

            if event.type == pygame.MOUSEBUTTONUP:
                if not self.left and not self.right and self.clicked_left:
                    self.on_l_mouse_up()

                self.clicked_left, self.clicked_right = self.left, self.right

            if event.type == pygame.MOUSEBUTTONDOWN:
                self.clicked_left, self.clicked_right = self.left, self.right

                if not self.left and self.right:
                    self.on_r_mouse_down()

    def on_l_mouse_up(self) -> None:
        cell = self._grid.get_cell_under_cursor()
        if cell is None:
            return

        if not self._grid.generated:
            self._grid.generate_board(cell.pos)
            self._grid.generated = True

        self._grid.on_open(cell)

    def on_r_mouse_down(self) -> None:
        cell = self._grid.get_cell_under_cursor()

        if cell is None or cell.is_opened:
            return

        cell.is_flagged = not cell.is_flagged
        self._grid.num_flagged += cell.is_flagged or -1

    def on_update(self) -> None:
        self.__on_mouse_hold()

    def __on_mouse_hold(self) -> None:
        hovered = self._grid.get_cell_under_cursor()

        for cell in self._grid:
            if not self.left or hovered is None:  # no mouse hold over any cell
                cell.is_pressed = False
            elif self.left and not hovered.is_opened:  # hold over unopened
                cell.is_pressed = cell is hovered and not cell.is_flagged
            elif self.left and hovered.is_opened:
                cell.is_pressed = cell in self._grid.eligible_neighbors(
                    *hovered.pos
                )
            else:
                cell.is_pressed = False
