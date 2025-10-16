import math
import pygame
from settings import COLOR_KING, COLOR_ENEMY, COLOR_PLAYER

def _draw_outline_circle(surf, pos, radius, fill, outline=(25,25,25), w=2, shadow=(0,0,0), so=(2,2)):
    pygame.draw.circle(surf, shadow, (int(pos.x+so[0]), int(pos.y+so[1])), radius)
    pygame.draw.circle(surf, outline, (int(pos.x), int(pos.y)), radius)
    pygame.draw.circle(surf, fill, (int(pos.x), int(pos.y)), max(0, radius - w))

class King:
    def __init__(self, x: float, y: float, speed: float = 200.0):
        self.pos = pygame.Vector2(x, y)  # monde
        self.speed = speed
        self.target: pygame.Vector2 | None = None
        self.mode = "land"  # "land" ou "boat"

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

    def draw(self, surf: pygame.Surface, offset=pygame.Vector2(), color=COLOR_KING):
        screen_pos = self.pos - offset
        t = pygame.time.get_ticks() * 0.003
        pulse = 2 + int(2 * (1 + math.sin(t)))
        _draw_outline_circle(surf, screen_pos, 12 + pulse, color)

        if self.mode == "boat":
            # petit gouvernail stylisé
            pygame.draw.circle(surf, (30,30,30), (int(screen_pos.x), int(screen_pos.y)), 6, 2)
            pygame.draw.line(surf, (30,30,30),
                             (screen_pos.x, screen_pos.y-9), (screen_pos.x, screen_pos.y+9), 2)
            pygame.draw.line(surf, (30,30,30),
                             (screen_pos.x-9, screen_pos.y), (screen_pos.x+9, screen_pos.y), 2)
        else:
            crown_pts = [
                (screen_pos.x - 8, screen_pos.y - 12),
                (screen_pos.x - 3, screen_pos.y - 4),
                (screen_pos.x + 0, screen_pos.y - 12),
                (screen_pos.x + 3, screen_pos.y - 4),
                (screen_pos.x + 8, screen_pos.y - 12),
            ]
            pygame.draw.lines(surf, (35,25,10), False, crown_pts, 3)

class Castle:
    def __init__(self, name: str, x: float, y: float, owner: str = "enemy", radius: int = 18):
        self.name = name
        self.pos = pygame.Vector2(x, y)  # monde
        self.owner = owner
        self.radius = radius

    def is_point_inside(self, x: float, y: float) -> bool:
        return self.pos.distance_to(pygame.Vector2(x, y)) <= self.radius

    def draw(self, surf: pygame.Surface, offset=pygame.Vector2()):
        col = COLOR_PLAYER if self.owner == "player" else COLOR_ENEMY
        screen_pos = self.pos - offset
        _draw_outline_circle(surf, screen_pos, self.radius, col)
        pole_top = (screen_pos.x, screen_pos.y - self.radius - 16)
        pygame.draw.line(surf, (30,30,30), (screen_pos.x, screen_pos.y - self.radius), pole_top, 2)
        pygame.draw.polygon(surf, col,
                            [pole_top,
                             (pole_top[0] + 12, pole_top[1] + 4),
                             (pole_top[0], pole_top[1] + 8)])

class Port:
    def __init__(self, name: str, x: float, y: float):
        self.name = name
        self.pos = pygame.Vector2(x, y)  # monde
        self.radius = 16

    def is_point_inside(self, x: float, y: float) -> bool:
        return self.pos.distance_to(pygame.Vector2(x, y)) <= self.radius

    def draw(self, surf: pygame.Surface, offset=pygame.Vector2()):
        sp = self.pos - offset
        # Halo de vagues concentriques (très visible)
        for i in range(3, 0, -1):
            pygame.draw.circle(surf, (255,255,255), (int(sp.x), int(sp.y)), self.radius + i*6, 1)
        # Quai bois + contour clair
        rect = pygame.Rect(0, 0, 26, 20); rect.center = (int(sp.x), int(sp.y))
        pygame.draw.rect(surf, (112, 84, 62), rect)         # bois
        pygame.draw.rect(surf, (235, 235, 235), rect, 2)    # bord clair
        # Poteau + fanion
        pygame.draw.line(surf, (240,240,240), (sp.x, sp.y-18), (sp.x, sp.y-32), 2)
        pygame.draw.polygon(surf, (240,240,240),
                            [(sp.x, sp.y-32),(sp.x+12, sp.y-28),(sp.x, sp.y-24)])
        # Label "PORT"
        f = pygame.font.Font(None, 22)
        lab = f.render("PORT", True, (245,245,245))
        surf.blit(lab, (sp.x - lab.get_width()/2, sp.y + rect.height/2 + 6))
