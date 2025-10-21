import pygame
from settings import WIDTH, HEIGHT, COLOR_UI
from .scene import Scene

def _font(sz:int)->pygame.font.Font:
    return pygame.font.Font(None, sz)

class BarracksView(Scene):
    """
    Caserne (placeholder fonctionnel) :
    - Affichera plus tard la gestion des unités du joueur
    - [ESC] pour revenir
    """
    def __init__(self, mgr, castle):
        super().__init__(mgr)
        self.castle = castle
        self.font_big = _font(36)
        self.font = _font(24)
        self.roster = [
            ("Piquier", 5),
            ("Archer", 4),
            ("Chevalier", 2),
        ]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.mgr.pop()

    def update(self, dt: float): pass

    def draw(self, surface: pygame.Surface):
        surface.fill((32, 28, 24))
        title = self.font_big.render(f"Caserne — {self.castle.name}", True, COLOR_UI)
        surface.blit(title, (WIDTH//2 - title.get_width()//2, 40))

        y = 120
        surface.blit(self.font.render("(Prototype) Recrutement/congé à venir", True, COLOR_UI), (60, y))
        y += 20
        for name, cnt in self.roster:
            y += 28
            line = self.font.render(f"- {name}  —  effectif: {cnt}", True, COLOR_UI)
            surface.blit(line, (80, y))

        help_ = self.font.render("[ESC] Retour", True, COLOR_UI)
        surface.blit(help_, (20, HEIGHT-36))
