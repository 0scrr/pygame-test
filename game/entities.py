import math
import pygame
from settings import COLOR_KING, COLOR_ENEMY, COLOR_PLAYER

def _draw_outline_circle(surf, pos, radius, fill, outline=(25,25,25), w=2, shadow=(0,0,0), so=(2,2)):
    pygame.draw.circle(surf, shadow, (int(pos.x+so[0]), int(pos.y+so[1])), radius)
    pygame.draw.circle(surf, outline, (int(pos.x), int(pos.y)), radius)
    pygame.draw.circle(surf, fill, (int(pos.x), int(pos.y)), max(0, radius - w))

def _draw_boat_icon(surf, center):
    x, y = int(center.x), int(center.y)
    # coque
    pygame.draw.polygon(surf, (35,35,35), [(x-10,y+6),(x+10,y+6),(x+6,y+12),(x-6,y+12)])
    # mât + voile
    pygame.draw.line(surf, (30,30,30), (x, y-10), (x, y+6), 2)
    pygame.draw.polygon(surf, (230,230,230), [(x,y-10),(x+10,y-2),(x,y-2)])
    # vague
    pygame.draw.arc(surf, (220,220,220), pygame.Rect(x-12, y+10, 24, 10), 3.6, 5.8, 2)

def _draw_boots_icon(surf, center):
    x, y = int(center.x), int(center.y)
    pygame.draw.rect(surf, (35,35,35), (x-10, y+4, 8, 6))
    pygame.draw.rect(surf, (35,35,35), (x+2, y+4, 8, 6))
    pygame.draw.rect(surf, (230,230,230), (x-10, y+1, 8, 4), 1)
    pygame.draw.rect(surf, (230,230,230), (x+2, y+1, 8, 4), 1)

class King:
    """Représente le roi avec mouvement et inventaire."""
    def __init__(self, x: float, y: float, speed: float = 200.0):
        self.pos = pygame.Vector2(x, y)  # monde
        self.speed = speed
        self.target: pygame.Vector2 | None = None
        self.mode = "land"  # "land" ou "boat"
        # Inventaire
        self.resources = {
            "gold": 1000,  # Or initial
            "food": 500,   # Nourriture pour recruter/maintenir l'armée
        }
        self.equipment = {}  # Dict d'équipements (nom: quantité)
        self.army = {}      # Dict de troupes (type: quantité)

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
            _draw_boat_icon(surf, screen_pos)
        else:
            # petite couronne stylisée
            crown_pts = [
                (screen_pos.x - 8, screen_pos.y - 12),
                (screen_pos.x - 3, screen_pos.y - 4),
                (screen_pos.x + 0, screen_pos.y - 12),
                (screen_pos.x + 3, screen_pos.y - 4),
                (screen_pos.x + 8, screen_pos.y - 12),
            ]
            pygame.draw.lines(surf, (35,25,10), False, crown_pts, 3)

    def add_resource(self, resource_type, amount):
        if resource_type in self.resources:
            self.resources[resource_type] += amount

    def remove_resource(self, resource_type, amount):
        if resource_type in self.resources and self.resources[resource_type] >= amount:
            self.resources[resource_type] -= amount
            return True
        return False

    def add_equipment(self, item_name):
        if item_name in self.equipment:
            self.equipment[item_name] += 1
        else:
            self.equipment[item_name] = 1

    def sell_equipment(self, item_name):
        if item_name in self.equipment and self.equipment[item_name] > 0:
            self.equipment[item_name] -= 1
            if self.equipment[item_name] == 0:
                del self.equipment[item_name]
            self.add_resource("gold", EQUIPMENTS[item_name]["price"] // 2)  # Vente à moitié prix
            return True
        return False

    def recruit_soldier(self, soldier_type):
        if soldier_type in self.army:
            self.army[soldier_type] += 1
        else:
            self.army[soldier_type] = 1

    def dismiss_soldier(self, soldier_type):
        if soldier_type in self.army and self.army[soldier_type] > 0:
            self.army[soldier_type] -= 1
            if self.army[soldier_type] == 0:
                del self.army[soldier_type]
            soldier = SOLDIERS[soldier_type]
            self.add_resource("gold", soldier["cost_gold"] // 2)
            self.add_resource("food", soldier["cost_food"] // 2)
            return True
        return False

# Constantes pour équipements et soldats
EQUIPMENTS = {
    "Épée": {"price": 50, "icon_func": lambda surf, center: pygame.draw.rect(surf, (200, 200, 200), (center[0]-10, center[1]-5, 20, 10))},
    "Arc": {"price": 60, "icon_func": lambda surf, center: pygame.draw.arc(surf, (150, 100, 50), (center[0]-10, center[1]-10, 20, 20), 0, math.pi, 2)},
    "Bouclier": {"price": 40, "icon_func": lambda surf, center: pygame.draw.circle(surf, (100, 100, 100), center, 10)},
    "Massue": {"price": 30, "icon_func": lambda surf, center: pygame.draw.line(surf, (120, 80, 40), (center[0], center[1]-10), (center[0], center[1]+10), 4)},
    "Lance": {"price": 70, "icon_func": lambda surf, center: pygame.draw.line(surf, (180, 180, 180), (center[0]-10, center[1]), (center[0]+10, center[1]), 3)},
    "Couteaux": {"price": 20, "icon_func": lambda surf, center: pygame.draw.polygon(surf, (150, 150, 150), [(center[0]-5, center[1]-5), (center[0]+5, center[1]-5), (center[0], center[1]+5)])},
    "Arbalète": {"price": 80, "icon_func": lambda surf, center: pygame.draw.rect(surf, (140, 90, 50), (center[0]-10, center[1]-5, 20, 10))},
    "Potion de vie": {"price": 25, "icon_func": lambda surf, center: pygame.draw.circle(surf, (200, 50, 50), center, 8)},
}

SOLDIERS = {
    "Guerrier": {"cost_gold": 100, "cost_food": 50, "icon_func": lambda surf, center: pygame.draw.rect(surf, (100, 100, 200), (center[0]-8, center[1]-8, 16, 16))},
    "Assassin": {"cost_gold": 150, "cost_food": 40, "icon_func": lambda surf, center: pygame.draw.polygon(surf, (50, 50, 50), [(center[0], center[1]-8), (center[0]-8, center[1]+8), (center[0]+8, center[1]+8)])},
    "Archer": {"cost_gold": 120, "cost_food": 30, "icon_func": lambda surf, center: pygame.draw.arc(surf, (150, 100, 50), (center[0]-8, center[1]-8, 16, 16), 0, math.pi, 2)},
    "Cavalier": {"cost_gold": 200, "cost_food": 80, "icon_func": lambda surf, center: pygame.draw.rect(surf, (200, 150, 100), (center[0]-10, center[1]-5, 20, 10))},
    "Soigneur": {"cost_gold": 180, "cost_food": 60, "icon_func": lambda surf, center: pygame.draw.circle(surf, (50, 200, 50), center, 8)},
}

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
