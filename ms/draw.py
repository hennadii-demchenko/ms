import math

import pygame.draw
from pygame import Rect, Surface, Color

BG_COLOR = Color(0xC0, 0xC0, 0xC0)
SHADOW_COLOR = Color(0x80, 0x80, 0x80)
HIGHLIGHT_COLOR = Color(0xFF, 0xFF, 0xFF)
NUM_COLORS = {
    1: Color(0x0, 0x0, 0xFF),
    2: Color(0x0, 0x80, 0x0),
    3: Color(0xFF, 0x0, 0x0),
    4: Color(0x0, 0x0, 0x80),
    5: Color(0x80, 0x0, 0x0),
    6: Color(0x0, 0x80, 0x80),
    7: Color(0x0, 0x0, 0x0),
    8: SHADOW_COLOR,
}


def draw_mine(surface: Surface, rect: Rect, exploded: bool = False) -> None:
    if exploded:
        pygame.draw.rect(surface, "red", rect)

    pygame.draw.rect(surface, SHADOW_COLOR, rect, width=1)
    radius = max(rect.height, rect.width) / 3.5
    rays_size = int(radius // 4)
    circle = pygame.draw.circle(surface, "black", rect.center, radius)
    cx, cy = circle.center

    # gloss
    reflect_center = (
        circle.center[0] - radius / 6,
        circle.center[1] - radius / 6,
    )
    pygame.draw.circle(surface, SHADOW_COLOR, reflect_center, radius // 2)
    pygame.draw.circle(surface, BG_COLOR, reflect_center, radius // 3)
    pygame.draw.circle(surface, HIGHLIGHT_COLOR, reflect_center, radius // 8)

    # radial rays
    pygame.draw.line(  # top
        surface,
        "black",
        circle.midtop,
        (circle.midtop[0], circle.midtop[1] - rays_size),
        rays_size,
    )
    pygame.draw.line(  # bottom
        surface,
        "black",
        circle.midbottom,
        (circle.midbottom[0], circle.midbottom[1] + rays_size),
        rays_size,
    )
    pygame.draw.line(  # right
        surface,
        "black",
        circle.midright,
        (circle.midright[0] + rays_size, circle.midright[1]),
        rays_size,
    )
    pygame.draw.line(  # left
        surface,
        "black",
        circle.midleft,
        (circle.midleft[0] - rays_size, circle.midleft[1]),
        rays_size,
    )

    pygame.draw.rect(  # top right (45)
        surface,
        "black",
        (
            cx - rays_size // 2 + radius * math.cos(-(math.pi / 4)),
            cy - rays_size // 2 + radius * math.sin(-(math.pi / 4)),
            rays_size,
            rays_size,
        ),
    )

    pygame.draw.rect(  # top left (315)
        surface,
        "black",
        (
            cx - rays_size // 2 + radius * math.cos(-(3 * math.pi / 4)),
            cy - rays_size // 2 + radius * math.sin(-(3 * math.pi / 4)),
            rays_size,
            rays_size,
        ),
    )

    pygame.draw.rect(  # bottom right (135)
        surface,
        "black",
        (
            cx - rays_size // 2 + radius * math.cos(math.pi / 4),
            cy - rays_size // 2 + radius * math.sin(math.pi / 4),
            rays_size,
            rays_size,
        ),
    )

    pygame.draw.rect(  # bottom left (225)
        surface,
        "black",
        (
            cx - rays_size // 2 + radius * math.cos(3 * math.pi / 4),
            cy - rays_size // 2 + radius * math.sin(3 * math.pi / 4),
            rays_size,
            rays_size,
        ),
    )


def draw_border(surface: Surface, rect: Rect, inverted: bool = False) -> None:
    thickness = max(rect.height, rect.width) // 12
    if inverted:
        highlight, shadow = SHADOW_COLOR, HIGHLIGHT_COLOR
    else:
        highlight, shadow = HIGHLIGHT_COLOR, SHADOW_COLOR

    pygame.draw.polygon(
        surface,
        highlight,
        [
            rect.bottomleft,
            rect.topleft,
            rect.topright,
            (rect.topright[0] - thickness, rect.topright[1] + thickness),
            (rect.topleft[0] + thickness, rect.topleft[1] + thickness),
            (rect.bottomleft[0] + thickness, rect.bottomleft[1] - thickness),
            rect.bottomleft,
        ],
    )

    pygame.draw.polygon(
        surface,
        shadow,
        [
            rect.bottomleft,
            rect.bottomright,
            rect.topright,
            (rect.topright[0] - thickness, rect.topright[1] + thickness),
            (rect.bottomright[0] - thickness, rect.bottomright[1] - thickness),
            (rect.bottomleft[0] + thickness, rect.bottomleft[1] - thickness),
            rect.bottomleft,
        ],
    )
