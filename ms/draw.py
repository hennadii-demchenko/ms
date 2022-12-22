import math
from typing import Optional

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


def draw_new_button(
    rect: Rect, border_width: int, pressed: bool = False
) -> None:
    draw_border(
        rect,
        inverted=pressed,
        inside=True,
        border_size=border_width,
    )
    r = (rect.w * 0.45) - border_width
    screen = pygame.display.get_surface()
    pygame.draw.circle(screen, "yellow", rect.center, r)
    pygame.draw.circle(screen, "black", rect.center, r, 2)
    pygame.draw.circle(
        screen, "black", (rect.centerx - r // 3, rect.centery - r // 4), 2
    )
    pygame.draw.circle(
        screen, "black", (rect.centerx + r // 3, rect.centery - r // 4), 2
    )

    pygame.draw.arc(
        screen,
        "black",
        Rect(rect.centerx - r // 2, rect.centery + r // 16, r, r // 2),
        math.pi,
        2 * math.pi,
    )


def draw_flag(rect: Rect) -> None:
    screen = pygame.display.get_surface()
    offset = max(rect.height, rect.width) // 4
    pygame.draw.polygon(
        screen,
        "black",
        [
            (rect.left + offset * 1.2, rect.bottom - offset * 0.6),
            (rect.centerx, rect.centery + offset),
            (rect.right - offset * 1.2, rect.bottom - offset * 0.6),
        ],
    )
    pygame.draw.line(
        screen,
        "black",
        (rect.centerx, rect.centery + offset * 1.25),
        rect.center,
        offset // 3,
    )
    pygame.draw.line(
        screen,
        "red",
        (rect.centerx, rect.centery + offset * 0.3),
        (rect.centerx, rect.top + offset * 0.75),
        offset // 3,
    )

    pygame.draw.polygon(
        screen,
        "red",
        [
            (rect.centerx, rect.centery + offset * 0.3),
            (rect.centerx, rect.top + offset * 0.75),
            (rect.centerx - rect.width // 3.25, rect.centery - offset // 2),
        ],
        offset // 6,
    )
    pygame.draw.polygon(
        screen,
        "red",
        [
            (rect.centerx, rect.centery + offset * 0.3),
            (rect.centerx, rect.top + offset * 0.75),
            (rect.centerx - rect.width // 3.25, rect.centery - offset // 2),
        ],
    )


def draw_reset(rect: Rect) -> None:
    pygame.draw.rect(pygame.display.get_surface(), BG_COLOR, rect)


def draw_empty(rect: Rect, shadow: Color = SHADOW_COLOR) -> None:
    pygame.draw.rect(pygame.display.get_surface(), shadow, rect, width=1)


def draw_mine(rect: Rect, exploded: bool = False) -> None:
    screen = pygame.display.get_surface()
    if exploded:
        pygame.draw.rect(screen, "red", rect)

    pygame.draw.rect(screen, SHADOW_COLOR, rect, width=1)
    radius = max(rect.height, rect.width) / 3.5
    rays_size = int(radius // 4)
    circle = pygame.draw.circle(screen, "black", rect.center, radius)
    cx, cy = circle.center

    # gloss
    reflect_center = (
        circle.center[0] - radius / 6,
        circle.center[1] - radius / 6,
    )

    pygame.draw.circle(screen, SHADOW_COLOR, reflect_center, radius // 2)
    pygame.draw.circle(screen, BG_COLOR, reflect_center, radius // 3)
    pygame.draw.circle(screen, HIGHLIGHT_COLOR, reflect_center, radius // 8)

    # radial rays
    pygame.draw.line(  # top
        screen,
        "black",
        circle.midtop,
        (circle.centerx, circle.top - rays_size),
        rays_size,
    )
    pygame.draw.line(  # bottom
        screen,
        "black",
        circle.midbottom,
        (circle.centerx, circle.bottom + rays_size),
        rays_size,
    )
    pygame.draw.line(  # right
        screen,
        "black",
        circle.midright,
        (circle.right + rays_size, circle.centery),
        rays_size,
    )
    pygame.draw.line(  # left
        screen,
        "black",
        circle.midleft,
        (circle.left - rays_size, circle.centery),
        rays_size,
    )

    pygame.draw.rect(  # top right (45)
        screen,
        "black",
        (
            cx - rays_size // 2 + radius * math.cos(-(math.pi / 4)),
            cy - rays_size // 2 + radius * math.sin(-(math.pi / 4)),
            rays_size,
            rays_size,
        ),
    )

    pygame.draw.rect(  # top left (315)
        screen,
        "black",
        (
            cx - rays_size // 2 + radius * math.cos(-(3 * math.pi / 4)),
            cy - rays_size // 2 + radius * math.sin(-(3 * math.pi / 4)),
            rays_size,
            rays_size,
        ),
    )

    pygame.draw.rect(  # bottom right (135)
        screen,
        "black",
        (
            cx - rays_size // 2 + radius * math.cos(math.pi / 4),
            cy - rays_size // 2 + radius * math.sin(math.pi / 4),
            rays_size,
            rays_size,
        ),
    )

    pygame.draw.rect(  # bottom left (225)
        screen,
        "black",
        (
            cx - rays_size // 2 + radius * math.cos(3 * math.pi / 4),
            cy - rays_size // 2 + radius * math.sin(3 * math.pi / 4),
            rays_size,
            rays_size,
        ),
    )


def draw_border(
    rect: Rect,
    inverted: bool = False,
    inside: bool = True,
    border_size: Optional[int] = None,
) -> None:
    screen = pygame.display.get_surface()
    thickness = border_size or max(rect.height, rect.width) // 10
    direction = int(inside) or -1

    if inverted:
        highlight, shadow = SHADOW_COLOR, HIGHLIGHT_COLOR
    else:
        highlight, shadow = HIGHLIGHT_COLOR, SHADOW_COLOR

    pygame.draw.polygon(
        screen,
        highlight,
        [
            rect.bottomleft,
            rect.topleft,
            rect.topright,
            (
                rect.right - thickness * direction,
                rect.top + thickness * direction,
            ),
            (
                rect.left + thickness * direction,
                rect.top + thickness * direction,
            ),
            (
                rect.left + thickness * direction,
                rect.bottom - thickness * direction,
            ),
            rect.bottomleft,
        ],
    )

    pygame.draw.polygon(
        screen,
        shadow,
        [
            rect.bottomleft,
            rect.bottomright,
            rect.topright,
            (
                rect.right - thickness * direction,
                rect.top + thickness * direction,
            ),
            (
                rect.right - thickness * direction,
                rect.bottom - thickness * direction,
            ),
            (
                rect.left + thickness * direction,
                rect.bottom - thickness * direction,
            ),
            rect.bottomleft,
        ],
    )
    draw_empty(rect, shadow)
