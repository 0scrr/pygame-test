import math
import pygame
from settings import COLOR_KING, COLOR_ENEMY, COLOR_PLAYER

def _draw_outline_circle(surf, pos, radius, fill, outline=(25,25,25), w=2, shadow=(0,0,0), so=(2,2)):
    # ombre simple
    pygame.draw.circle(surf, shadow, (int(pos.x+so[0]), int(pos.y+so[1])), radius)
    # contour
    pygame.draw.circle(surf, outline, (int(pos.x), int(pos.y)), radius)
    # remplissage
    pygame.draw.circle(surf, fill, (int(pos.x), int(pos.y)), max(0, radius - w))

class King:
    def __init__(self, x: float, y: float, speed: float = 200.0):
        self.pos = pygame.Vector2(x, y)
        self.speed = speed
        self.target: pygame.Vector2 | None = None

    def move_to(self, x: float, y: float):
        self.target = pygame.Vector2(x, y)

    @property
    def moving(self) -> bool:
        return self.target is not None

    def update(self, dt: float):
        if not self.target:
            return
        to = self.target - self.pos
        dist = to.length()
        step = self.speed * dt
        if dist <= step:
            self.pos = self.target
            self.target = None
        else:
            self.pos += to.normalize() * step

    def is_near(self, x: float, y: float, radius: float = 16.0) -> bool:
        return self.pos.distance_to(pygame.Vector2(x, y)) <= radius

    def draw(self, surf: pygame.Surface, color=COLOR_KING):
        # halo respirant
        t = pygame.time.get_ticks() * 0.003
        pulse = 2 + int(2 * (1 + math.sin(t)))
        _draw_outline_circle(surf, self.pos, 12 + pulse, color)

        # couronne (accent)
        crown_pts = [
            (self.pos.x - 8, self.pos.y - 12),
            (self.pos.x - 3, self.pos.y - 4),
            (self.pos.x + 0, self.pos.y - 12),
            (self.pos.x + 3, self.pos.y - 4),
            (self.pos.x + 8, self.pos.y - 12),
        ]
        pygame.draw.lines(surf, (35,25,10), False, crown_pts, 3)

class Castle:
    def __init__(self, name: str, x: float, y: float, owner: str = "enemy", radius: int = 18):
        self.name = name
        self.pos = pygame.Vector2(x, y)
        self.owner = owner  # "enemy" ou "player"
        self.radius = radius

    def is_point_inside(self, x: float, y: float) -> bool:
        return self.pos.distance_to(pygame.Vector2(x, y)) <= self.radius

    def draw(self, surf: pygame.Surface):
        col = COLOR_PLAYER if self.owner == "player" else COLOR_ENEMY
        # base tour
        _draw_outline_circle(surf, self.pos, self.radius, col)
        # petit drapeau
        pole_top = (self.pos.x, self.pos.y - self.radius - 16)
        pygame.draw.line(surf, (30,30,30), (self.pos.x, self.pos.y - self.radius), pole_top, 2)
        pygame.draw.polygon(surf, col,
                            [pole_top,
                             (pole_top[0] + 12, pole_top[1] + 4),
                             (pole_top[0], pole_top[1] + 8)])
