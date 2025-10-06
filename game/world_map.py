import json, math, random
from pathlib import Path
import pygame

from .scene import Scene
from .entities import King, Castle
from .castle_view import CastleView
from .battle_view import BattleView
from settings import (
    WIDTH, HEIGHT,
    COLOR_UI,
    COLOR_WATER_DEEP, COLOR_WATER_SHALLOW, COLOR_SAND, COLOR_GRASS, COLOR_HILL, COLOR_MOUNTAIN
)

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
FONT_CACHE = {}

def get_font(size: int) -> pygame.font.Font:
    key = f"default-{size}"
    if key not in FONT_CACHE:
        FONT_CACHE[key] = pygame.font.Font(None, size)
    return FONT_CACHE[key]

# ----------- bruit/cohérence 2D sans numpy (value noise) -----------
def _hash2(ix, iy, seed):
    n = (ix * 374761393) ^ (iy * 668265263) ^ (seed * 1442695041)
    n = (n ^ (n >> 13)) * 1274126177
    n = n ^ (n >> 16)
    return (n & 0xFFFFFFFF) / 0xFFFFFFFF

def _smoothstep(t):
    return t * t * (3 - 2 * t)

def _value_noise(x, y, freq, seed):
    x *= freq; y *= freq
    ix, iy = int(x), int(y)
    fx, fy = x - ix, y - iy
    v00 = _hash2(ix,   iy,   seed)
    v10 = _hash2(ix+1, iy,   seed)
    v01 = _hash2(ix,   iy+1, seed)
    v11 = _hash2(ix+1, iy+1, seed)
    ux, uy = _smoothstep(fx), _smoothstep(fy)
    a = v00 + (v10 - v00) * ux
    b = v01 + (v11 - v01) * ux
    return a + (b - a) * uy

def _fbm(x, y, seed):
    # fractal brownian motion: 3 octaves
    return (
        0.55 * _value_noise(x, y, 1.2, seed) +
        0.30 * _value_noise(x, y, 3.1, seed+11) +
        0.15 * _value_noise(x, y, 6.4, seed+29)
    )

def _classify(v):
    # seuils terrain
    if v < 0.35: return COLOR_WATER_DEEP
    if v < 0.40: return COLOR_WATER_SHALLOW
    if v < 0.45: return COLOR_SAND
    if v < 0.75: return COLOR_GRASS
    if v < 0.90: return COLOR_HILL
    return COLOR_MOUNTAIN

def _make_vignette(size):
    w, h = size
    vg = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w/2, h/2
    rmax = math.hypot(cx, cy)
    # 6 anneaux sombres
    for i in range(6):
        r = rmax * (0.65 + 0.05 * i)
        alpha = 20 + i*15
        pygame.draw.circle(vg, (0,0,0,alpha), (int(cx), int(cy)), int(r))
    return vg

def _draw_dotted_line(surf, a, b, dash=12, gap=8, color=(245,245,245)):
    vec = pygame.Vector2(b) - pygame.Vector2(a)
    dist = vec.length()
    if dist <= 1: return
    dir = vec.normalize()
    n = int(dist // (dash + gap)) + 1
    pos = pygame.Vector2(a)
    for _ in range(n):
        end = pos + dir * dash
        pygame.draw.line(surf, color, (int(pos.x), int(pos.y)), (int(end.x), int(end.y)), 2)
        pos = end + dir * gap

class WorldMap(Scene):
    """Map interactive avec fond procédural + survol/chemin."""
    def __init__(self, manager):
        super().__init__(manager)
        self.king: King | None = None
        self.castles: list[Castle] = []
        self.selected: Castle | None = None
        self.hovered: Castle | None = None

        self._event_timer = 0.0
        self._event_interval = 4.0
        self._event_chance = 0.12

        self._bg: pygame.Surface | None = None
        self._vignette: pygame.Surface | None = None

        self._last_target: pygame.Vector2 | None = None

        self._load_world()

    def on_enter(self):
        self._render_background()

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

    def _render_background(self):
        # génère une fois un fond "peint" basse résolution puis upscale
        seed = 1337
        low_w, low_h = WIDTH // 4, HEIGHT // 4
        low = pygame.Surface((low_w, low_h))
        for y in range(low_h):
            ny = y / low_h
            for x in range(low_w):
                nx = x / low_w
                v = _fbm(nx, ny, seed)
                # léger éclairage diagonale (haut-gauche -> clair)
                light = 0.08 * (1 - (nx + (1 - ny)) / 2)
                v = max(0.0, min(1.0, v + light))
                low.set_at((x, y), _classify(v))
        self._bg = pygame.transform.smoothscale(low, (WIDTH, HEIGHT))

        # petite bordure côte (accent) : contours eau/sable
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for c in range(6):
            alpha = 18 - c*3
            pygame.draw.rect(overlay, (0,0,0,alpha), overlay.get_rect(), width=1+c)
        self._bg.blit(overlay, (0,0))

        self._vignette = _make_vignette((WIDTH, HEIGHT))

    # ---- events ----
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.hovered = None
            for c in self.castles:
                if c.is_point_inside(mx, my):
                    self.hovered = c
                    break

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            clicked = None
            for c in self.castles:
                if c.is_point_inside(mx, my):
                    clicked = c
                    break
            if clicked:
                self.selected = clicked
                self.king.move_to(clicked.pos.x, clicked.pos.y)
                self._last_target = pygame.Vector2(clicked.pos)
            else:
                self.selected = None
                self.king.move_to(mx, my)
                self._last_target = pygame.Vector2(mx, my)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.mgr.quit = True

    def update(self, dt: float):
        self.king.update(dt)

        if self.selected and not self.king.moving and self.king.is_near(self.selected.pos.x, self.selected.pos.y, radius=20):
            self.mgr.push(CastleView(self.mgr, self.selected))

        if self.king.moving:
            self._event_timer += dt
            if self._event_timer >= self._event_interval:
                self._event_timer = 0.0
                if random.random() < self._event_chance:
                    self.mgr.push(BattleView(self.mgr))

    def draw(self, surface: pygame.Surface):
        if self._bg:
            surface.blit(self._bg, (0,0))

        # chemin pointillé vers la cible
        if self.king.moving and self.king.target is not None:
            _draw_dotted_line(surface, self.king.pos, self.king.target, color=(250,250,250))
        elif self._last_target is not None and self.king.pos.distance_to(self._last_target) > 4:
            _draw_dotted_line(surface, self.king.pos, self._last_target, color=(220,220,220))

        # châteaux
        for c in self.castles:
            c.draw(surface)
            # survol : anneau
            if self.hovered is c:
                pygame.draw.circle(surface, (255,255,255), (int(c.pos.x), int(c.pos.y)), c.radius+6, 2)
            # label
            f = get_font(20)
            name = f.render(c.name, True, (20,20,20))
            surface.blit(name, (c.pos.x - name.get_width()/2 + 1, c.pos.y + c.radius + 8 + 1))
            surface.blit(f.render(c.name, True, (245,245,245)),
                         (c.pos.x - name.get_width()/2, c.pos.y + c.radius + 8))

        # roi au-dessus
        self.king.draw(surface)

        # vignette
        if self._vignette:
            surface.blit(self._vignette, (0,0))

        # aide
        f = get_font(22)
        info = "Clic : se déplacer / entrer | Survol: nom | ESC : quitter"
        panel = f.render(info, True, COLOR_UI)
        surface.blit(panel, (16, HEIGHT - 32))
