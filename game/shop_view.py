import pygame
from settings import WIDTH, HEIGHT, COLOR_UI
from .scene import Scene

def _font(sz:int)->pygame.font.Font:
    return pygame.font.Font(None, sz)

class ShopView(Scene):
    """
    Boutique (placeholder fonctionnel) :
    - Affiche l’or du roi (si disponible plus tard)
    - Liste fictive d’objets à acheter/vendre
    - [ESC] pour revenir
    """
    def __init__(self, mgr, castle):
        super().__init__(mgr)
        self.castle = castle
        self.items = [
            ("Épée simple", 50),
            ("Bouclier en bois", 35),
            ("Armure de cuir", 80),
            ("Potion de soin", 20),
        ]
        self.font_big = _font(36)
        self.font = _font(24)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.mgr.pop()

    def update(self, dt: float): pass

    def draw(self, surface: pygame.Surface):
        surface.fill((30, 30, 36))
        title = self.font_big.render(f"Boutique — {self.castle.name}", True, COLOR_UI)
        surface.blit(title, (WIDTH//2 - title.get_width()//2, 40))

        y = 120
        surface.blit(self.font.render("(Prototype) Clique sur un objet : achat/vente à venir", True, COLOR_UI), (60, y))
        y += 30
        for name, price in self.items:
            y += 28
            line = self.font.render(f"- {name}  —  {price} or", True, COLOR_UI)
            surface.blit(line, (80, y))

        help_ = self.font.render("[ESC] Retour", True, COLOR_UI)
        surface.blit(help_, (20, HEIGHT-36))
