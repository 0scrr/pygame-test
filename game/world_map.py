import json
import random
from pathlib import Path
import pygame

from .scene import Scene
from .entities import King, Castle
from .castle_view import CastleView
from .battle_view import BattleView
from settings import WIDTH, HEIGHT, COLOR_BG, COLOR_UI

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
FONT_CACHE = {}

def get_font(size: int) -> pygame.font.Font:
    key = f"default-{size}"
    if key not in FONT_CACHE:
        FONT_CACHE[key] = pygame.font.Font(None, size)
    return FONT_CACHE[key]

class WorldMap(Scene):
    """Map interactive : déplacement du roi, clics sur châteaux, événements aléatoires."""
    def __init__(self, manager):
        super().__init__(manager)
        self.king: King | None = None
        self.castles: list[Castle] = []
        self.selected: Castle | None = None

        self._event_timer = 0.0
        self._event_interval = 4.0  # toutes les ~4s on a une chance d'événement
        self._event_chance = 0.12   # 12% de chance

        self._load_world()

    def _load_world(self):
        world_path = DATA_DIR / "world_map.json"
        data = {
            "king": {"x": 200, "y": 400, "speed": 200},
            "castles": [
                {"name": "Château du Nord", "x": 320, "y": 160, "owner": "enemy"},
                {"name": "Fort de l'Est",   "x": 980, "y": 220, "owner": "enemy"},
                {"name": "Village du Sud",  "x": 640, "y": 560, "owner": "enemy"}
            ]
        }
        if world_path.exists():
            data = json.loads(world_path.read_text(encoding="utf-8"))

        k = data["king"]
        self.king = King(k["x"], k["y"], speed=k.get("speed", 200))
        self.castles = [Castle(c["name"], c["x"], c["y"], c.get("owner","enemy"))
                        for c in data["castles"]]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            clicked = None
            for c in self.castles:
                if c.is_point_inside(mx, my):
                    clicked = c
                    break
            if clicked:
                self.selected = clicked
                self.king.move_to(clicked.pos.x, clicked.pos.y)
            else:
                self.selected = None
                self.king.move_to(mx, my)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.mgr.quit = True

    def update(self, dt: float):
        self.king.update(dt)

        # Si un château est sélectionné et que le roi est arrivé → ouvrir l'interface
        if self.selected and not self.king.moving and self.king.is_near(self.selected.pos.x, self.selected.pos.y, radius=20):
            self.mgr.push(CastleView(self.mgr, self.selected))

        # Événements aléatoires (ex: combat) pendant le déplacement
        if self.king.moving:
            self._event_timer += dt
            if self._event_timer >= self._event_interval:
                self._event_timer = 0.0
                if random.random() < self._event_chance:
                    self.mgr.push(BattleView(self.mgr))

    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_BG)

        # Terrain simplifié (quadrillage léger pour l'ambiance)
        for x in range(0, surface.get_width(), 64):
            pygame.draw.line(surface, (20, 70, 45), (x, 0), (x, surface.get_height()))
        for y in range(0, surface.get_height(), 64):
            pygame.draw.line(surface, (20, 70, 45), (0, y), (surface.get_width(), y))

        # Châteaux
        for c in self.castles:
            c.draw(surface)

        # Roi par-dessus
        self.king.draw(surface)

        # UI basique
        f = get_font(22)
        info = "Clic gauche : se déplacer / entrer dans un château | ESC : quitter"
        surface.blit(f.render(info, True, COLOR_UI), (16, HEIGHT - 32))
