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

# ----- bruit (value noise + fbm) -----
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

# ----- overrides de terre via mask (îlots organiques) -----
class LandOverrides:
    def __init__(self, w, h):
        self.surface = pygame.Surface((w, h), pygame.SRCALPHA)  # alpha>0 => terre forcée
        self.mask: pygame.Mask | None = None
    def _commit(self):
        self.mask = pygame.mask.from_surface(self.surface)
    def add_polygon(self, pts):
        pygame.draw.polygon(self.surface, (255,255,255,255), [(int(px),int(py)) for px,py in pts])
        self._commit()
    def is_land_here(self, x, y):
        if self.mask is None: return False
        xi, yi = int(x), int(y)
        if 0 <= xi < self.mask.get_size()[0] and 0 <= yi < self.mask.get_size()[1]:
            return self.mask.get_at((xi, yi)) == 1
        return False

def _island_mask(nx, ny):
    # masque radial: centre plus haut, bords plus bas -> île centrale, mer autour
    dx = nx - 0.5
    dy = ny - 0.5
    r = math.hypot(dx, dy) / 0.7071
    falloff = 1.0 - (r**1.6)
    return max(0.0, min(1.0, falloff))

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

        self.cam = pygame.Vector2(0, 0)
        self._last_target: pygame.Vector2 | None = None

        self.land_over = LandOverrides(WORLD_W, WORLD_H)

        # Flash visuel après embarquement/débarquement
        self._mode_flash_timer = 0.0
        self._mode_flash_kind = None  # "boat"|"land"|None

        # Cooldown pour éviter la réouverture immédiate d'un château
        self._castle_cooldown = 0.0

        self._load_world()

    # --- appelé quand une scène enfant (CastleView) se ferme ---
    def on_child_popped(self, child):
        if isinstance(child, CastleView):
            self.selected = None
            self._castle_cooldown = 0.45  # ~1/2 seconde pour éviter re-pop immédiat

    # ---------- terrain helpers ----------
    def _height(self, x, y):
        nx, ny = x / WORLD_W, y / WORLD_H
        v = _fbm(nx, ny, SEED)
        v *= 0.75 + 0.25 * _island_mask(nx, ny)  # île au centre
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
            nx, ny = self._nearest_land(self.king.pos.x, self.king.pos.y, max_r=600)
            self.king.pos.update(nx, ny)
            self.king.mode = "land"

    def _load_world(self):
        world_path = DATA_DIR / "world_map.json"
        data = {
            "king": {"x": WORLD_W//2 - 200, "y": WORLD_H//2 + 80, "speed": 220},
            "castles": [
                {"name": "Château du Nord", "x": WORLD_W//2 - 320, "y": WORLD_H//2 - 260, "owner": "enemy"},
                {"name": "Fort de l'Est",   "x": WORLD_W//2 + 420, "y": WORLD_H//2 - 120, "owner": "enemy"},
                {"name": "Village du Sud",  "x": WORLD_W//2 +  40, "y": WORLD_H//2 + 340, "owner": "enemy"}
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
                v *= 0.75 + 0.25 * _island_mask(nx, ny)  # île centrale
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

    # ---------- îlots organiques “décollés” ----------
    def _make_blob_islet(self, cx, cy, r_base, spikes=14):
        pts = []
        for i in range(spikes):
            ang = (i / spikes) * math.tau
            jitter = random.uniform(-0.35, 0.35)
            rad = r_base * (0.8 + 0.5 * math.sin(ang*2 + random.random()*0.6) + jitter)
            pts.append((cx + math.cos(ang)*rad, cy + math.sin(ang)*rad))
        # lissage simple
        smooth = []
        for i in range(len(pts)):
            a = pygame.Vector2(pts[i-1]); b = pygame.Vector2(pts[i]); c = pygame.Vector2(pts[(i+1)%len(pts)])
            m = (a + b*2 + c) / 4
            smooth.append((m.x, m.y))
        return smooth

    def _ring_is_mostly_water(self, cx, cy, r, gap=36, step_deg=10, ratio=0.85):
        water = 0; total = 0
        rr = r + gap
        for ang in range(0, 360, step_deg):
            px = int(cx + math.cos(math.radians(ang)) * rr)
            py = int(cy + math.sin(math.radians(ang)) * rr)
            if 0 <= px < WORLD_W and 0 <= py < WORLD_H:
                total += 1
                if self.is_water(px, py):
                    water += 1
        return total > 0 and (water / total) >= ratio

    def _generate_islets_and_ports(self):
        random.seed(SEED + 2025)
        self.ports = []

        # -------- îlots (loin des bords & du continent) --------
        margin = 180
        wanted_islets = 6
        min_islet_spacing = 150
        blobs = []
        attempts = 0

        while len(blobs) < wanted_islets and attempts < 800:
            attempts += 1
            x = random.randint(margin, WORLD_W - margin)
            y = random.randint(margin, WORLD_H - margin)
            if not self.is_water(x, y):
                continue
            r = random.randint(70, 120)
            if any(pygame.Vector2(x-bx, y-by).length() < (br + min_islet_spacing) for bx,by,br in blobs):
                continue
            if not self._ring_is_mostly_water(x, y, r, gap=40, step_deg=8, ratio=0.9):
                continue
            blobs.append((x, y, r))

        # dessiner + override en terre
        for (cx, cy, r) in blobs:
            poly = self._make_blob_islet(cx, cy, r, spikes=random.randint(12,18))
            pygame.draw.polygon(self._bg, COLOR_SAND, [(int(px),int(py)) for px,py in poly])
            inner = [(cx + (px-cx)*0.82, cy + (py-cy)*0.82) for (px,py) in poly]
            pygame.draw.polygon(self._bg, COLOR_GRASS, [(int(px),int(py)) for px,py in inner])
            pygame.draw.polygon(self._bg, (235,235,235), [(int(px),int(py)) for px,py in poly], 1)
            self.land_over.add_polygon(poly)

        # -------- Ports --------
        def _find_coast():
            for _ in range(3500):
                x = random.randint(24, WORLD_W-24)
                y = random.randint(24, WORLD_H-24)
                if self.is_land(x, y) and any(self.is_water(x+dx, y+dy) for dx,dy in ((18,0),(-18,0),(0,18),(0,-18))):
                    return x, y
            return None

        # Ports continent (max 3), espacés
        mainland_ports_target = 3
        min_port_spacing = 160
        tries = 0
        while len([p for p in self.ports if not p.name.startswith("Îlot-")]) < mainland_ports_target and tries < 800:
            tries += 1
            p = _find_coast()
            if not p: break
            if p[0] < margin or p[0] > WORLD_W-margin or p[1] < margin or p[1] > WORLD_H-margin:
                continue
            if any(pygame.Vector2(p[0]-pp.pos.x, p[1]-pp.pos.y).length() < min_port_spacing for pp in self.ports):
                continue
            self.ports.append(Port(f"Port-{len(self.ports)+1}", *p))

        # 1 port par îlot (sur la côte de l’îlot)
        for i, (cx,cy,r) in enumerate(blobs, start=1):
            placed = False
            for ang in range(0, 360, 10):
                px = int(cx + math.cos(math.radians(ang)) * int(r*0.9))
                py = int(cy + math.sin(math.radians(ang)) * int(r*0.9))
                if self.is_land(px, py) and any(self.is_water(px+dx, py+dy) for dx,dy in ((16,0),(-16,0),(0,16),(0,-16))):
                    if all(pygame.Vector2(px-pp.pos.x, py-pp.pos.y).length() >= 140 for pp in self.ports):
                        self.ports.append(Port(f"Îlot-Port-{i}", px, py))
                        placed = True
                        break
            if not placed:
                # fallback unique (mais on garde UN seul port)
                px = int(cx + r*0.8); py = int(cy)
                self.ports.append(Port(f"Îlot-Port-{i}", px, py))

    def _nearest_land(self, x, y, max_r=600):
        p = pygame.Vector2(x, y)
        for r in range(2, max_r, 2):
            for a in range(0, 360, 8):
                off = pygame.Vector2(1,0).rotate(a) * r
                test = p + off
                if 0 <= test.x < WORLD_W and 0 <= test.y < WORLD_H and self.is_land(test.x, test.y):
                    return int(test.x), int(test.y)
        return int(x), int(y)

    def _reposition_water_castles(self):
        for c in self.castles:
            if self.is_water(c.pos.x, c.pos.y):
                nx, ny = self._nearest_land(c.pos.x, c.pos.y, max_r=800)
                if self.is_water(nx, ny) and self.ports:
                    # secours: proche d'un port
                    near = min(self.ports, key=lambda p: pygame.Vector2(p.pos - c.pos).length())
                    nx, ny = int(near.pos.x + 24), int(near.pos.y + 24)
                c.pos.update(nx, ny)

    # ------------- helpers caméra -------------
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
                # mouvement manuel -> on annule la sélection pour éviter repop auto
                self.selected = None
                if self.king.mode == "land" and self.is_land(wx, wy):
                    self.king.move_to(wx, wy)
                    self._last_target = pygame.Vector2(wx, wy)
                elif self.king.mode == "boat" and self.is_water(wx, wy):
                    self.king.move_to(wx, wy)
                    self._last_target = pygame.Vector2(wx, wy)

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.mgr.quit = True

    def update(self, dt: float):
        # cooldown château
        if self._castle_cooldown > 0:
            self._castle_cooldown = max(0.0, self._castle_cooldown - dt)

        prev = self.king.pos.copy()
        self.king.update(dt)

        # blocage terrain interdit
        if self.king.mode == "land" and self.is_water(self.king.pos.x, self.king.pos.y):
            self.king.pos.update(prev); self.king.target = None
        elif self.king.mode == "boat" and self.is_land(self.king.pos.x, self.king.pos.y):
            self.king.pos.update(prev); self.king.target = None

        self._center_camera_on_king()

        # Ouverture de château (seulement si pas en cooldown)
        if (self.selected and self._castle_cooldown == 0.0 and
            not self.king.moving and self.king.is_near(self.selected.pos.x, self.selected.pos.y, radius=20)):
            self.mgr.push(CastleView(self.mgr, self.selected))

        # Embarquement/débarquement auto
        if not self.king.moving:
            for p in self.ports:
                if self.king.is_near(p.pos.x, p.pos.y, radius=20):
                    self.king.mode = "boat" if self.king.mode == "land" else "land"
                    self._mode_flash_kind = self.king.mode
                    self._mode_flash_timer = 1.2
                    break

        # timer du flash d’icône
        if self._mode_flash_timer > 0:
            self._mode_flash_timer -= dt
            if self._mode_flash_timer <= 0:
                self._mode_flash_kind = None

        # événements aléatoires en mode terre uniquement
        if self.king.moving and self.king.mode == "land":
            self._event_timer += dt
            if self._event_timer >= self._event_interval:
                self._event_timer = 0.0
                if random.random() < self._event_chance:
                    self.mgr.push(BattleView(self.mgr))

    def draw(self, surface: pygame.Surface):
        if self._bg:
            surface.blit(self._bg, (-int(self.cam.x), -int(self.cam.y)))

        # Trace du chemin
        if self.king.moving and self.king.target is not None:
            a = self.king.pos - self.cam
            b = self.king.target - self.cam
            _draw_dotted_line(surface, a, b, color=(250,250,250))
        elif self._last_target is not None and self.king.pos.distance_to(self._last_target) > 4:
            a = self.king.pos - self.cam
            b = self._last_target - self.cam
            _draw_dotted_line(surface, a, b, color=(220,220,220))

        # Châteaux
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

        # Ports
        for p in self.ports:
            p.draw(surface, offset=self.cam)
            if self.hovered_port is p:
                sp = p.pos - self.cam
                pygame.draw.circle(surface, (245,245,245), (int(sp.x), int(sp.y)), p.radius+6, 2)

        # Roi
        self.king.draw(surface, offset=self.cam)

        # Flash d’icône “mode”
        if self._mode_flash_kind:
            sp = self.king.pos - self.cam
            y = sp.y - 32
            if self._mode_flash_kind == "boat":
                pygame.draw.polygon(surface, (30,30,30), [(sp.x-12,y+2),(sp.x+12,y+2),(sp.x+8,y+12),(sp.x-8,y+12)])
                pygame.draw.line(surface, (30,30,30), (sp.x, y-14), (sp.x, y+2), 2)
                pygame.draw.polygon(surface, (240,240,240), [(sp.x,y-14),(sp.x+12,y-4),(sp.x,y-4)])
            else:
                pygame.draw.rect(surface, (30,30,30), (sp.x-12, y, 10, 7))
                pygame.draw.rect(surface, (30,30,30), (sp.x+2,  y, 10, 7))
                pygame.draw.rect(surface, (240,240,240), (sp.x-12, y-3, 10, 3), 1)
                pygame.draw.rect(surface, (240,240,240), (sp.x+2,  y-3, 10, 3), 1)

        # Vignette
        if self._vignette:
            surface.blit(self._vignette, (0,0))

        # Aide
        f = get_font(20)
        help_text = f"[Mode: {'Bateau' if self.king.mode=='boat' else 'Terre'}]  Clic: se déplacer  |  Clic PORT: embarquer/débarquer  |  En bateau: clic sur l'eau pour naviguer  |  ESC: quitter"
        surface.blit(f.render(help_text, True, COLOR_UI), (16, HEIGHT - 28))
