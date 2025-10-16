import json, math, random
from pathlib import Path
import pygame

from .scene import Scene
from .entities import King, Castle, Port
from .castle_view import CastleView
from .battle_view import BattleView
from settings import (
    WIDTH, HEIGHT, WORLD_W, WORLD_H,
    COLOR_UI,
    COLOR_WATER_DEEP, COLOR_WATER_SHALLOW, COLOR_SAND, COLOR_GRASS, COLOR_HILL, COLOR_MOUNTAIN
)

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
FONT_CACHE = {}
SEED = 1337

def get_font(size: int) -> pygame.font.Font:
    key = f"default-{size}"
    if key not in FONT_CACHE:
        FONT_CACHE[key] = pygame.font.Font(None, size)
    return FONT_CACHE[key]

# ----- bruit simple (value noise + fbm) -----
def _hash2(ix, iy, seed):
    n = (ix * 374761393) ^ (iy * 668265263) ^ (seed * 1442695041)
    n = (n ^ (n >> 13)) * 1274126177
    n = n ^ (n >> 16)
    return (n & 0xFFFFFFFF) / 0xFFFFFFFF

def _smoothstep(t): return t * t * (3 - 2 * t)
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
    return (
        0.55 * _value_noise(x, y, 1.2, seed) +
        0.30 * _value_noise(x, y, 3.1, seed+11) +
        0.15 * _value_noise(x, y, 6.4, seed+29)
    )

def _classify(v):
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

# ------------- masque "îlots" : forcer de la terre dans l'eau -------------
class LandOverrides:
    def __init__(self):
        self.circles: list[tuple[float,float,float]] = []  # (x,y,r)

    def add_islet(self, x, y, r):
        self.circles.append((x,y,r))

    def is_land_here(self, x, y):
        for cx, cy, r in self.circles:
            if pygame.Vector2(x - cx, y - cy).length() <= r:
                return True
        return False

class WorldMap(Scene):
    def __init__(self, manager):
        super().__init__(manager)
        self.king: King | None = None
        self.castles: list[Castle] = []
        self.ports: list[Port] = []
        self.selected: Castle | None = None
        self.hovered_castle: Castle | None = None
        self.hovered_port: Port | None = None

        self._event_timer = 0.0
        self._event_interval = 4.0
        self._event_chance = 0.12

        self._bg: pygame.Surface | None = None
        self._vignette: pygame.Surface | None = None

        self.cam = pygame.Vector2(0, 0)  # caméra
        self._last_target: pygame.Vector2 | None = None

        self.land_over = LandOverrides()

        self._load_world()

    # ---------- terrain helpers ----------
    def _height(self, x, y):
        nx, ny = x / WORLD_W, y / WORLD_H
        v = _fbm(nx, ny, SEED)
        light = 0.08 * (1 - (nx + (1 - ny)) / 2)
        return max(0.0, min(1.0, v + light))

    def is_water(self, x, y):
        if self.land_over.is_land_here(x, y):
            return False
        v = self._height(x, y)
        return v < 0.40  # eau (deep+shallow)

    def is_land(self, x, y):
        return not self.is_water(x, y)

    def on_enter(self):
        self._render_background()
        self._generate_islets_and_ports()
        self._reposition_water_castles()
        # Assurer un spawn du roi sur la terre
        if self.is_water(self.king.pos.x, self.king.pos.y):
            nx, ny = self._nearest_land(self.king.pos.x, self.king.pos.y, max_r=300)
            self.king.pos.update(nx, ny)
            self.king.mode = "land"

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
        scale = 4
        low_w, low_h = max(1, WORLD_W // scale), max(1, WORLD_H // scale)
        low = pygame.Surface((low_w, low_h))
        for y in range(low_h):
            ny = y / low_h
            for x in range(low_w):
                nx = x / low_w
                v = _fbm(nx, ny, SEED)
                light = 0.08 * (1 - (nx + (1 - ny)) / 2)
                v = max(0.0, min(1.0, v + light))
                low.set_at((x, y), _classify(v))
        bg = pygame.transform.smoothscale(low, (WORLD_W, WORLD_H))
        # bordure douce
        overlay = pygame.Surface((WORLD_W, WORLD_H), pygame.SRCALPHA)
        for c in range(6):
            alpha = 18 - c*3
            pygame.draw.rect(overlay, (0,0,0,alpha), overlay.get_rect(), width=1+c)
        bg.blit(overlay, (0,0))
        self._bg = bg
        self._vignette = _make_vignette((WIDTH, HEIGHT))

    def _generate_islets_and_ports(self):
        random.seed(SEED + 2025)
        # 1) îlots (cercles de terre forcée)
        for _ in range(6):
            x = random.randint(WORLD_W//4, WORLD_W - WORLD_W//4)
            y = random.randint(WORLD_H//4, WORLD_H - WORLD_H//4)
            if not self.is_water(x, y):
                continue
            r = random.randint(40, 110)
            self.land_over.add_islet(x, y, r)
            pygame.draw.circle(self._bg, COLOR_GRASS, (x, y), r)
            pygame.draw.circle(self._bg, COLOR_SAND, (x, y), max(1, r-6), 2)

        # 2) ports : points de côte (terre à côté de l'eau)
        self.ports = []
        def _find_coast():
            for _ in range(2000):
                x = random.randint(24, WORLD_W-24)
                y = random.randint(24, WORLD_H-24)
                if self.is_land(x, y):
                    for dx, dy in ((16,0),(-16,0),(0,16),(0,-16)):
                        if self.is_water(x+dx, y+dy):
                            return x, y
            return None

        # ports continent
        for i in range(5):
            p = _find_coast()
            if p: self.ports.append(Port(f"Port-{i+1}", *p))
        # ports îlots (côté est approximatif)
        for i, (cx,cy,r) in enumerate(self.land_over.circles):
            self.ports.append(Port(f"Îlot-Port-{i+1}", int(cx+r*0.7), int(cy)))

    def _nearest_land(self, x, y, max_r=80):
        p = pygame.Vector2(x, y)
        for r in range(2, max_r, 2):
            for a in range(0, 360, 15):
                off = pygame.Vector2(1,0).rotate(a) * r
                test = p + off
                if 0 <= test.x < WORLD_W and 0 <= test.y < WORLD_H and self.is_land(test.x, test.y):
                    return int(test.x), int(test.y)
        return int(x), int(y)

    def _reposition_water_castles(self):
        for c in self.castles:
            if self.is_water(c.pos.x, c.pos.y):
                nx, ny = self._nearest_land(c.pos.x, c.pos.y, max_r=160)
                c.pos.update(nx, ny)

    # ------------- helpers -------------
    def _screen_to_world(self, sx, sy):
        return (sx + self.cam.x, sy + self.cam.y)

    def _center_camera_on_king(self):
        self.cam.x = self.king.pos.x - WIDTH / 2
        self.cam.y = self.king.pos.y - HEIGHT / 2
        self.cam.x = max(0, min(self.cam.x, WORLD_W - WIDTH))
        self.cam.y = max(0, min(self.cam.y, WORLD_H - HEIGHT))

    # ------------- events -------------
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            wx, wy = self._screen_to_world(mx, my)
            self.hovered_castle = None
            self.hovered_port = None
            for c in self.castles:
                if c.is_point_inside(wx, wy):
                    self.hovered_castle = c
                    break
            if not self.hovered_castle:
                for p in self.ports:
                    if p.is_point_inside(wx, wy):
                        self.hovered_port = p
                        break

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            wx, wy = self._screen_to_world(mx, my)
            clicked_castle = None
            for c in self.castles:
                if c.is_point_inside(wx, wy):
                    clicked_castle = c
                    break
            clicked_port = None
            if not clicked_castle:
                for p in self.ports:
                    if p.is_point_inside(wx, wy):
                        clicked_port = p
                        break

            if clicked_castle:
                self.selected = clicked_castle
                self.king.move_to(clicked_castle.pos.x, clicked_castle.pos.y)
                self._last_target = pygame.Vector2(clicked_castle.pos)
            elif clicked_port:
                self.selected = None
                self.king.move_to(clicked_port.pos.x, clicked_port.pos.y)
                self._last_target = pygame.Vector2(clicked_port.pos)
            else:
                if self.king.mode == "land" and self.is_land(wx, wy):
                    self.selected = None
                    self.king.move_to(wx, wy)
                    self._last_target = pygame.Vector2(wx, wy)
                elif self.king.mode == "boat" and self.is_water(wx, wy):
                    self.selected = None
                    self.king.move_to(wx, wy)
                    self._last_target = pygame.Vector2(wx, wy)
                # sinon: clic ignoré

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.mgr.quit = True

    def update(self, dt: float):
        prev = self.king.pos.copy()
        self.king.update(dt)

        # bloquer si terrain interdit
        if self.king.mode == "land" and self.is_water(self.king.pos.x, self.king.pos.y):
            self.king.pos.update(prev)
            self.king.target = None
        elif self.king.mode == "boat" and self.is_land(self.king.pos.x, self.king.pos.y):
            self.king.pos.update(prev)
            self.king.target = None

        self._center_camera_on_king()

        if self.selected and not self.king.moving and self.king.is_near(self.selected.pos.x, self.selected.pos.y, radius=20):
            self.mgr.push(CastleView(self.mgr, self.selected))

        # embarquement/débarquement auto sur port à l'arrivée
        if not self.king.moving:
            for p in self.ports:
                if self.king.is_near(p.pos.x, p.pos.y, radius=20):
                    self.king.mode = "boat" if self.king.mode == "land" else "land"
                    break

        # événements seulement en mode "land"
        if self.king.moving and self.king.mode == "land":
            self._event_timer += dt
            if self._event_timer >= self._event_interval:
                self._event_timer = 0.0
                if random.random() < self._event_chance:
                    self.mgr.push(BattleView(self.mgr))

    def draw(self, surface: pygame.Surface):
        if self._bg:
            surface.blit(self._bg, (-int(self.cam.x), -int(self.cam.y)))

        if self.king.moving and self.king.target is not None:
            a = self.king.pos - self.cam
            b = self.king.target - self.cam
            _draw_dotted_line(surface, a, b, color=(250,250,250))
        elif self._last_target is not None and self.king.pos.distance_to(self._last_target) > 4:
            a = self.king.pos - self.cam
            b = self._last_target - self.cam
            _draw_dotted_line(surface, a, b, color=(220,220,220))

        for c in self.castles:
            c.draw(surface, offset=self.cam)
            if self.hovered_castle is c:
                sp = c.pos - self.cam
                pygame.draw.circle(surface, (255,255,255), (int(sp.x), int(sp.y)), c.radius+6, 2)
            f = get_font(20)
            name_shadow = f.render(c.name, True, (20,20,20))
            sp = c.pos - self.cam
            surface.blit(name_shadow, (sp.x - name_shadow.get_width()/2 + 1, sp.y + c.radius + 8 + 1))
            surface.blit(f.render(c.name, True, (245,245,245)),
                         (sp.x - name_shadow.get_width()/2, sp.y + c.radius + 8))

        for p in self.ports:
            p.draw(surface, offset=self.cam)
            if self.hovered_port is p:
                sp = p.pos - self.cam
                pygame.draw.circle(surface, (245,245,245), (int(sp.x), int(sp.y)), p.radius+6, 2)

        self.king.draw(surface, offset=self.cam)

        if self._vignette:
            surface.blit(self._vignette, (0,0))

        # Aide claire
        f = get_font(20)
        help_text = f"[Mode: {'Bateau' if self.king.mode=='boat' else 'Terre'}]  Clic gauche: se déplacer  |  Clic sur un PORT: embarquer/débarquer  |  ESC: quitter"
        surface.blit(f.render(help_text, True, COLOR_UI), (16, HEIGHT - 28))
