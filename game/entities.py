import pygame

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

    def draw(self, surf: pygame.Surface, color=(240, 220, 90)):
        pygame.draw.circle(surf, color, (int(self.pos.x), int(self.pos.y)), 10)
        # petite "couronne" simplifiée
        pygame.draw.polygon(
            surf, color,
            [(self.pos.x - 8, self.pos.y - 14),
             (self.pos.x - 2, self.pos.y - 6),
             (self.pos.x + 2, self.pos.y - 14),
             (self.pos.x + 8, self.pos.y - 6),
             (self.pos.x - 8, self.pos.y - 6)]
        )


class Castle:
    def __init__(self, name: str, x: float, y: float, owner: str = "enemy", radius: int = 18):
        self.name = name
        self.pos = pygame.Vector2(x, y)
        self.owner = owner  # "enemy" ou "player"
        self.radius = radius

    def is_point_inside(self, x: float, y: float) -> bool:
        return self.pos.distance_to(pygame.Vector2(x, y)) <= self.radius

    def draw(self, surf: pygame.Surface, enemy_color=(200,60,60), player_color=(60,180,60)):
        color = enemy_color if self.owner != "player" else player_color
        pygame.draw.circle(surf, color, (int(self.pos.x), int(self.pos.y)), self.radius)
        # un petit drapeau
        pygame.draw.line(surf, (30,30,30), (self.pos.x, self.pos.y - self.radius),
                         (self.pos.x, self.pos.y - self.radius - 16), 2)
        pygame.draw.polygon(surf, color,
                            [(self.pos.x, self.pos.y - self.radius - 16),
                             (self.pos.x + 12, self.pos.y - self.radius - 12),
                             (self.pos.x, self.pos.y - self.radius - 8)])
