import pygame

WATER = 0
LAND  = 1

class King:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 180
        self.mode = "terre"   # "terre" ou "boat"
        self.target = None

        self.walk_surface = self._make_walk_sprite()
        self.boat_surface = self._make_boat_sprite()

    def _make_walk_sprite(self):
        surf = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(surf, (40, 40, 40), (10, 10), 9)
        pygame.draw.circle(surf, (230, 208, 170), (10, 8), 5)
        return surf

    def _make_boat_sprite(self):
        surf = pygame.Surface((28, 18), pygame.SRCALPHA)
        pygame.draw.polygon(surf, (88, 54, 35), [(2,15),(26,15),(22,12),(6,12)])
        pygame.draw.rect(surf, (160, 160, 160), (12,2,2,10))
        pygame.draw.polygon(surf, (230,230,230), [(14,3),(24,8),(14,8)])
        return surf

    def current_sprite(self):
        return self.boat_surface if self.mode == "boat" else self.walk_surface

    def set_target(self, pos_px):
        self.target = pos_px

    def update(self, dt, tiles, tile_size):
        if not self.target:
            return
        tx, ty = self.target
        dx = tx - self.x
        dy = ty - self.y
        dist = (dx*dx + dy*dy) ** 0.5
        if dist < 1:
            self.target = None
            return
        vx = dx / dist
        vy = dy / dist
        step = self.speed * dt
        nx = self.x + vx * step
        ny = self.y + vy * step
        if self._can_stand_at(nx, ny, tiles, tile_size):
            self.x, self.y = nx, ny
        else:
            self.target = None

    def _can_stand_at(self, px, py, tiles, tile_size):
        mx = int(px // tile_size)
        my = int(py // tile_size)
        if my < 0 or mx < 0 or my >= len(tiles) or mx >= len(tiles[0]):
            return False
        t = tiles[my][mx]
        if self.mode == "boat":
            return t == WATER
        else:
            return t == LAND

    def draw(self, surface, camera):
        sp = self.current_sprite()
        rect = sp.get_rect(center=(int(self.x - camera.x), int(self.y - camera.y)))
        surface.blit(sp, rect.topleft)

def draw_mode_icon(surface, mode):
    if mode == "boat":
        pygame.draw.rect(surface, (30,30,30), (8,8,40,40), border_radius=8)
        pygame.draw.polygon(surface, (230,230,230), [(16,18),(40,28),(16,28)])
        pygame.draw.rect(surface, (200,200,200), (26,12,2,10))
        pygame.draw.polygon(surface, (255,255,255), [(28,12),(38,18),(28,18)])
    else:
        pygame.draw.rect(surface, (30,30,30), (8,8,40,40), border_radius=8)
        pygame.draw.rect(surface, (220,220,220), (16,24,10,8))
        pygame.draw.rect(surface, (200,200,200), (26,26,10,6))
        pygame.draw.line(surface, (255,255,255), (18,20), (26,24), 3)
