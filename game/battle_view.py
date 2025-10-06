import pygame
from settings import WIDTH, HEIGHT, COLOR_UI
from .scene import Scene

def _font(size: int) -> pygame.font.Font:
    return pygame.font.Font(None, size)

class BattleView(Scene):
    """Placeholder combat : juste un écran avec issue rapide."""
    def __init__(self, manager):
        super().__init__(manager)
        self.msg = "Combat (prototype) ! [V] Victoire  |  [ESC] Fuir"

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_v or event.key == pygame.K_ESCAPE:
                # Pour l'instant, quelle que soit l'issue -> retour carte
                self.mgr.pop()

    def update(self, dt: float):
        pass

    def draw(self, surface: pygame.Surface):
        surface.fill((55, 40, 40))
        title = _font(42).render("Combat !", True, COLOR_UI)
        surface.blit(title, (WIDTH//2 - title.get_width()//2, 160))

        info = _font(28).render(self.msg, True, COLOR_UI)
        surface.blit(info, (WIDTH//2 - info.get_width()//2, 250))
