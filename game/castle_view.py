import math
import pygame
from settings import WIDTH, HEIGHT, COLOR_UI
from .scene import Scene
from .battle_view import BattleView
from .shop_view import ShopView
from .barracks_view import BarracksView

def _font(sz: int) -> pygame.font.Font:
    return pygame.font.Font(None, sz)

# =============== Base ===============
class _Entity:
    """Élément dessinable avec z-order basé sur le bas du rect (effet de profondeur)."""
    def __init__(self, name: str, rect: pygame.Rect, kind: str,
                 hint: str | None = None, interactive: bool = False):
        self.name = name
        self.rect = rect  # ancré au SOL : rect.bottom = ligne de sol
        self.kind = kind
        self.hint = hint
        self.interactive = interactive
        self.hover = False

    @property
    def z(self) -> int:
        return self.rect.bottom

    def draw(self, surf: pygame.Surface, t: float):
        pass

def _rect_centered_on_line(cx: int, base_y: int, w: int, h: int, offset_x: int = 0) -> pygame.Rect:
    """Rect vertical centré horizontalement, posé sur base_y (ligne de sol), avec offset horizontal pour perspective."""
    return pygame.Rect(cx - w // 2 + offset_x, base_y - h, w, h)

# =============== Bâtiments ===============
class _Building(_Entity):
    def draw(self, surf: pygame.Surface, t: float):
        x, y, w, h = self.rect
        # Ombre améliorée : directionnelle, plus longue pour front, avec gradient doux
        shadow_offset = (int(w * 0.12), int(h * 0.18)) if self.rect.bottom > HEIGHT * 0.7 else (int(w * 0.06), int(h * 0.10))
        sh_w, sh_h = w + shadow_offset[0], int(h * 0.25) + shadow_offset[1]
        shadow = pygame.Surface((sh_w, sh_h), pygame.SRCALPHA)
        for i in range(sh_h):
            alpha = int(120 * (1 - i / sh_h))  # Ombre plus prononcée
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha), (0, i, sh_w, 1))
        surf.blit(shadow, (x + (w - sh_w)//2, y + h - sh_h//2))
        
        by = y - h
        if self.kind == "townhall":
            self._draw_townhall(surf, x, by, w, h)
        elif self.kind == "shop":
            self._draw_shop(surf, x, by, w, h)
        elif self.kind == "barracks":
            self._draw_barracks(surf, x, by, w, h)
        elif self.kind == "stable":
            self._draw_stable(surf, x, by, w, h)
        elif self.kind == "church":
            self._draw_church(surf, x, by, w, h)
        elif self.kind == "mill":
            self._draw_mill(surf, x, by, w, h, t)
        elif self.kind == "house":
            self._draw_house(surf, x, by, w, h)
        
        # Label avec ombre pour lisibilité
        label = _font(18).render(self.name, True, COLOR_UI)
        label_shadow = _font(18).render(self.name, True, (0, 0, 0))
        surf.blit(label_shadow, (x + w // 2 - label.get_width() // 2 + 2, y + 8))
        surf.blit(label, (x + w // 2 - label.get_width() // 2, y + 6))
        
        if self.interactive and self.hover:
            # Surbrillance subtile sur le bâtiment
            highlight = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(highlight, (255, 240, 200, 80), (0, 0, w, h))  # Teinte dorée lumineuse
            surf.blit(highlight, (x, y - h))

    # ---- Helpers ----
    @staticmethod
    def _roof(surf, pts, color=(168, 86, 68), line=(62, 38, 34)):
        pygame.draw.polygon(surf, color, pts)
        pygame.draw.lines(surf, line, False, pts, 2)

    def _draw_gradient_body(self, surf, rect, base_color, dark_color):
        """Gradient vertical pour volume (haut clair, bas sombre)."""
        for i in range(rect.height):
            k = i / rect.height
            c = (
                int(base_color[0] * (1 - k) + dark_color[0] * k),
                int(base_color[1] * (1 - k) + dark_color[1] * k),
                int(base_color[2] * (1 - k) + dark_color[2] * k)
            )
            pygame.draw.line(surf, c, (rect.left, rect.top + i), (rect.right, rect.top + i))

    # ---- Types (améliorés avec détails médiévaux) ----
    def _draw_house(self, surf, x, by, w, h):
        body = pygame.Rect(x + int(w*0.08), by + int(h*0.40), int(w*0.84), int(h*0.60))
        self._draw_gradient_body(surf, body, (210, 180, 140), (160, 130, 90))
        pygame.draw.rect(surf, (70, 50, 30), body, 2, border_radius=8)
        roof = [(x, by + int(h*0.40)), (x + w//2, by - int(h*0.25)), (x + w, by + int(h*0.40))]
        self._roof(surf, roof, (120, 60, 40), (50, 25, 15))
        for i in range(x + 10, x + w - 10, 20):
            pygame.draw.line(surf, (80, 60, 40), (i, by + int(h*0.40)), (i, by + int(h*0.60)), 2)
        win = pygame.Rect(x + int(w*0.65), by + int(h*0.50), 20, 20)
        pygame.draw.rect(surf, (200, 220, 230), win)
        pygame.draw.rect(surf, (50, 30, 20), win, 2)

    def _draw_shop(self, surf, x, by, w, h):
        body = pygame.Rect(x + int(w*0.06), by + int(h*0.38), int(w*0.88), int(h*0.62))
        self._draw_gradient_body(surf, body, (200, 160, 120), (150, 110, 70))
        pygame.draw.rect(surf, (60, 40, 20), body, 2, border_radius=8)
        roof = [(x, by + int(h*0.38)), (x + w//2, by - int(h*0.28)), (x + w, by + int(h*0.38))]
        self._roof(surf, roof, (140, 70, 50))
        awn = pygame.Rect(x + int(w*0.16), by + int(h*0.46), int(w*0.68), int(h*0.12))
        pygame.draw.rect(surf, (220, 200, 180), awn, border_radius=6)
        for i in range(awn.x, awn.right, 12):
            pygame.draw.rect(surf, (160, 80, 60), (i, awn.y, 6, awn.height))
        pygame.draw.rect(surf, (40, 20, 10), awn, 2, border_radius=6)
        door = pygame.Rect(x + w//2 - 12, by + int(h*0.68), 24, int(h*0.28))
        pygame.draw.rect(surf, (100, 70, 40), door, border_radius=4)

    def _draw_barracks(self, surf, x, by, w, h):
        base = pygame.Rect(x + 4, by + int(h*0.46), w - 8, int(h*0.54))
        self._draw_gradient_body(surf, base, (180, 160, 140), (130, 110, 90))
        pygame.draw.rect(surf, (50, 40, 30), base, 2, border_radius=6)
        tw = int(w * 0.36)
        tower = pygame.Rect(x + w - tw - 4, by + int(h*0.20), tw, int(h*0.60))
        self._draw_gradient_body(surf, tower, (170, 150, 130), (120, 100, 80))
        pygame.draw.rect(surf, (50, 40, 30), tower, 2, border_radius=6)
        top_y = tower.y - 8
        for i in range(tower.x + 6, tower.right - 6, 16):
            pygame.draw.rect(surf, (140, 120, 100), (i, top_y, 12, 10))
        mx = tower.centerx
        pygame.draw.line(surf, (40, 30, 20), (mx, tower.y - 16), (mx, tower.y + 12), 4)
        flag = [(mx, tower.y - 16), (mx + 24, tower.y - 10), (mx, tower.y)]
        pygame.draw.polygon(surf, (180, 50, 50), flag)
        door = pygame.Rect(x + 12, base.bottom - int(h*0.32), 24, int(h*0.32) - 8)
        pygame.draw.rect(surf, (90, 70, 50), door, border_radius=4)

    def _draw_townhall(self, surf, x, by, w, h):
        body = pygame.Rect(x + int(w*0.08), by + int(h*0.40), int(w*0.84), int(h*0.60))
        self._draw_gradient_body(surf, body, (220, 200, 180), (170, 150, 130))
        pygame.draw.rect(surf, (70, 60, 50), body, 2, border_radius=10)
        roof = [(x - 10, by + int(h*0.40)), (x + w//2, by - int(h*0.35)), (x + w + 10, by + int(h*0.40))]
        self._roof(surf, roof, (160, 80, 60))
        rp = [(x + int(w*0.22), by + int(h*0.40)), (x + w//2, by - int(h*0.48)), (x + int(w*0.78), by + int(h*0.40))]
        self._roof(surf, rp, (150, 70, 50))
        door = pygame.Rect(x + w//2 - 16, by + int(h*0.70), 32, int(h*0.26))
        pygame.draw.rect(surf, (100, 80, 60), door, border_radius=6)

    def _draw_church(self, surf, x, by, w, h):
        body = pygame.Rect(x + int(w*0.14), by + int(h*0.42), int(w*0.72), int(h*0.58))
        self._draw_gradient_body(surf, body, (230, 220, 210), (180, 170, 160))
        pygame.draw.rect(surf, (60, 50, 40), body, 2, border_radius=8)
        roof = [(body.x - 10, body.y), (body.centerx, by - int(h*0.32)), (body.right + 10, body.y)]
        self._roof(surf, roof, (150, 70, 60))
        tower = pygame.Rect(x + int(w*0.74), by + int(h*0.16), int(w*0.20), int(h*0.62))
        self._draw_gradient_body(surf, tower, (230, 220, 210), (180, 170, 160))
        pygame.draw.rect(surf, (60, 50, 40), tower, 2, border_radius=6)
        spire = [(tower.centerx, tower.y - int(h*0.20)), (tower.x, tower.y + 10), (tower.right, tower.y + 10)]
        self._roof(surf, spire, (140, 60, 50))
        c = (tower.centerx, tower.y - int(h*0.10))
        pygame.draw.line(surf, (200, 190, 180), (c[0], c[1]-10), (c[0], c[1]+10), 3)
        pygame.draw.line(surf, (200, 190, 180), (c[0]-8, c[1]), (c[0]+8, c[1]), 3)

    def _draw_mill(self, surf, x, by, w, h, t):
        base = pygame.Rect(x + int(w*0.30), by + int(h*0.70), int(w*0.40), int(h*0.30))
        self._draw_gradient_body(surf, base, (170, 150, 130), (120, 100, 80))
        pygame.draw.rect(surf, (90, 70, 50), base, 2, border_radius=6)
        tower = pygame.Rect(x + int(w*0.34), by + int(h*0.36), int(w*0.32), int(h*0.48))
        self._draw_gradient_body(surf, tower, (160, 130, 100), (110, 80, 50))
        pygame.draw.rect(surf, (70, 50, 30), tower, 2, border_radius=6)
        for i in range(tower.x + 6, tower.right - 6, 12):
            pygame.draw.line(surf, (130, 100, 70), (i, tower.y + 6), (i, tower.bottom - 6), 2)
        tip = (tower.centerx, by + int(h*0.20))
        self._roof(surf, [(tower.x - 8, tower.y), tip, (tower.right + 8, tower.y)], (150, 70, 50))
        cx, cy = tower.centerx, tower.y + 6
        angle = (t * 30.0) % 360
        self._blades_with_lattice(surf, cx, cy, angle, int(w*0.65))
        door = pygame.Rect(tower.centerx - 10, base.y + 6, 20, base.height - 10)
        pygame.draw.rect(surf, (90, 70, 50), door, border_radius=4)

    def _blades_with_lattice(self, surf, cx, cy, a_deg, size):
        arm = int(size * 0.50)
        hub = 8
        for i in range(4):
            a = math.radians(a_deg + i * 90)
            ex, ey = cx + int(math.cos(a) * arm), cy + int(math.sin(a) * arm)
            pygame.draw.line(surf, (50, 40, 30), (cx, cy), (ex, ey), 4)
            pw, ph = 20, 45
            nx, ny = ex - int(math.cos(a) * ph / 2), ey - int(math.sin(a) * ph / 2)
            r = pygame.Rect(0, 0, pw, ph); r.center = (nx, ny)
            pygame.draw.rect(surf, (220, 200, 180), r, border_radius=4)
            pygame.draw.rect(surf, (60, 40, 20), r, 2, border_radius=4)
            pygame.draw.line(surf, (140, 110, 80), (r.left + 4, r.top + 4), (r.right - 4, r.bottom - 4), 2)
            pygame.draw.line(surf, (140, 110, 80), (r.right - 4, r.top + 4), (r.left + 4, r.bottom - 4), 2)
        pygame.draw.circle(surf, (220, 200, 180), (cx, cy), hub)
        pygame.draw.circle(surf, (60, 40, 20), (cx, cy), hub, 2)

    def _draw_stable(self, surf, x, by, w, h):
        body = pygame.Rect(x + 4, by + int(h*0.46), w - 8, int(h*0.54))
        self._draw_gradient_body(surf, body, (180, 120, 100), (130, 70, 50))
        pygame.draw.rect(surf, (50, 30, 20), body, 2, border_radius=6)
        roof = [(x - 12, body.y), (x + w//2, by - int(h*0.28)), (x + w + 12, body.y)]
        self._roof(surf, roof, (130, 60, 40))
        door = pygame.Rect(x + w//2 - 22, body.bottom - int(h*0.38), 44, int(h*0.38) - 8)
        pygame.draw.rect(surf, (80, 60, 40), door, border_radius=6)
        pygame.draw.line(surf, (150, 130, 110), door.topleft, door.bottomright, 3)
        pygame.draw.line(surf, (150, 130, 110), door.topright, door.bottomleft, 3)

# =============== Décor léger ===============
class _Tree(_Entity):
    def draw(self, surf: pygame.Surface, t: float):
        x, y, w, h = self.rect
        by = y - h
        sway = int(4 * math.sin(t * 2.5))
        trunk = pygame.Rect(x + w//2 - 8 + sway, by + int(h*0.55), 16, int(h*0.45))
        pygame.draw.rect(surf, (80, 60, 40), trunk)
        cx = x + w//2 + sway//2
        pygame.draw.circle(surf, (40, 100, 60), (cx, by + int(h*0.45)), int(w*0.50))
        pygame.draw.circle(surf, (30, 90, 50), (x + int(w*0.30) + sway//2, by + int(h*0.58)), int(w*0.36))
        pygame.draw.circle(surf, (30, 90, 50), (x + int(w*0.70) + sway//2, by + int(h*0.58)), int(w*0.36))

# =============== Scène ===============
class CastleView(Scene):
    """
    Mini-village : 3 PLANS VERTICAUX RÉELS (exploite toute la hauteur)
      BACK (petit, centré) : Moulin + Église
      MID (moyen, espacé) : Hôtel de ville (gauche) + Caserne (droite)
      FRONT(grand, bas et décalé) : Boutique (centre-bas) + Écurie (droite-bas)
    Un seul chemin discret. Arbres en bordure. Style médiéval.
    """
    def __init__(self, mgr, castle):
        super().__init__(mgr)
        self.castle = castle
        self._title_font = _font(40)
        self._ui_font = _font(22)
        self._t = 0.0
        self.horizon_y = int(HEIGHT * 0.35)
        self.line_back = self.horizon_y + 130
        self.line_mid = self.horizon_y + 280
        self.line_front = self.horizon_y + 420
        back_offset = -25
        self.back_xs = [int(WIDTH * 0.35) + back_offset, int(WIDTH * 0.65) + back_offset]
        self.mid_xs = [int(WIDTH * 0.25), int(WIDTH * 0.75)]
        self.front_xs = [int(WIDTH * 0.40), int(WIDTH * 0.80)]
        BW_BACK, BH_BACK = 130, 90
        BW_MID, BH_MID = 170, 120
        BW_FRONT, BH_FRONT = 200, 140
        self.entities: list[_Entity] = []
        self.entities += [
            _Building("Moulin", _rect_centered_on_line(self.back_xs[0], self.line_back, BW_BACK, BH_BACK), "mill"),
            _Building("Église", _rect_centered_on_line(self.back_xs[1], self.line_back, BW_BACK + 10, BH_BACK + 10), "church"),
        ]
        self.entities += [
            _Building("Hôtel de ville",
                      _rect_centered_on_line(self.mid_xs[0], self.line_mid, BW_MID, BH_MID),
                      "townhall", "Assaut du château ou duel contre le chef.", True),
            _Building("Caserne",
                      _rect_centered_on_line(self.mid_xs[1], self.line_mid, BW_MID + 5, BH_MID),
                      "barracks", "Recruter / congédier des soldats.", True),
        ]
        self.entities += [
            _Building("Boutique",
                      _rect_centered_on_line(self.front_xs[0], self.line_front, BW_FRONT, BH_FRONT),
                      "shop", "Acheter / vendre des équipements.", True),
            _Building("Écurie",
                      _rect_centered_on_line(self.front_xs[1], self.line_front, int(BW_FRONT*0.80), int(BH_FRONT*0.80)),
                      "stable"),
        ]
        margin = 70
        self.entities += [
            _Tree("Arbre Gauche Back", _rect_centered_on_line(int(WIDTH * 0.10), self.line_back + 20, 60, 80), "tree"),
            _Tree("Arbre Gauche Mid", _rect_centered_on_line(margin - 30, self.line_mid + 10, 70, 90), "tree"),
            _Tree("Arbre Droit Mid", _rect_centered_on_line(WIDTH - margin + 30, self.line_mid + 10, 70, 90), "tree"),
            _Tree("Arbre Droit Front", _rect_centered_on_line(WIDTH - margin + 50, self.line_front + 10, 80, 100), "tree"),
        ]
        for ent in self.entities:
            if ent.kind == "tree" and ent.rect.bottom > self.line_mid:
                ent.rect.bottom += 2
        self._tooltip: str | None = None

    def _draw_background(self, surf: pygame.Surface):
        top, bot = (18, 20, 26), (34, 36, 42)
        for i in range(self.horizon_y):
            k = i / max(1, self.horizon_y)
            c = (int(top[0]*(1-k)+bot[0]*k), int(top[1]*(1-k)+bot[1]*k), int(top[2]*(1-k)+bot[2]*k))
            surf.fill(c, rect=pygame.Rect(0, i, WIDTH, 1))
        pygame.draw.ellipse(surf, (44, 64, 58, 120), (-int(WIDTH*0.2), self.horizon_y-140, int(WIDTH*1.2), 280))
        pygame.draw.ellipse(surf, (48, 74, 62, 140), (int(WIDTH*0.28), self.horizon_y-120, int(WIDTH*0.9), 260))
        pygame.draw.ellipse(surf, (52, 84, 66, 100), (int(WIDTH*0.5), self.horizon_y-100, int(WIDTH*0.6), 220))
        pygame.draw.rect(surf, (86, 142, 88), (0, self.horizon_y, WIDTH, HEIGHT - self.horizon_y))
        path_y = self.line_mid + 20
        pygame.draw.rect(surf, (146, 138, 124), (0, path_y, WIDTH, 40))
        for i in range(0, WIDTH, 10):
            wy = path_y + 20 + int(5 * math.sin(i / 50))
            pygame.draw.line(surf, (126, 118, 104), (i, wy), (i+10, wy), 2)
        title = self._title_font.render(self.castle.name, True, COLOR_UI)
        surf.blit(title, (WIDTH // 2 - title.get_width() // 2, 18))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.mgr.pop(); return
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self._tooltip = None
            for e in self.entities:
                if isinstance(e, _Building) and e.interactive:
                    e.hover = e.rect.collidepoint(mx, my)
                    if e.hover and e.hint:
                        self._tooltip = e.hint
                else:
                    e.hover = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for b in self.entities:
                if isinstance(b, _Building) and b.interactive and b.rect.collidepoint(mx, my):
                    if b.kind == "townhall":
                        self.mgr.push(BattleView(self.mgr))
                    elif b.kind == "shop":
                        self.mgr.push(ShopView(self.mgr, self.castle))
                    elif b.kind == "barracks":
                        self.mgr.push(BarracksView(self.mgr, self.castle))
                    break

    def update(self, dt: float):
        self._t += dt

    def draw(self, surface: pygame.Surface):
        self._draw_background(surface)
        for ent in sorted(self.entities, key=lambda e: e.z):
            ent.draw(surface, self._t)
        bar = pygame.Rect(0, HEIGHT - 44, WIDTH, 44)
        pygame.draw.rect(surface, (24, 24, 24), bar)
        txt = self._ui_font.render("⇦ ESC • Clique : Hôtel de ville / Boutique / Caserne", True, (235, 235, 235))
        surface.blit(txt, (16, HEIGHT - 34))
        if self._tooltip:
            tt = self._ui_font.render(self._tooltip, True, (16, 16, 16))
            box = tt.get_rect()
            mx, my = pygame.mouse.get_pos()
            box.topleft = (mx + 18, my + 6)
            pygame.draw.rect(surface, (240, 240, 240), box.inflate(14, 10), border_radius=6)
            pygame.draw.rect(surface, (64, 64, 64), box.inflate(14, 10), 2, border_radius=6)
            surface.blit(tt, box)
