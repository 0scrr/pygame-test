import pygame
from settings import WIDTH, HEIGHT, COLOR_UI, COLOR_PLAYER
from .scene import Scene

def _font(size: int) -> pygame.font.Font:
    return pygame.font.Font(None, size)

class CastleView(Scene):
    """Interface très simple d'un château : capture + retour."""
    def __init__(self, manager, castle):
        super().__init__(manager)
        self.castle = castle
        self.msg = ""

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.mgr.pop()  # retour à la carte
            elif event.key == pygame.K_c:
                if self.castle.owner != "player":
                    self.castle.owner = "player"
                    self.msg = f"Vous avez pris le contrôle de {self.castle.name}."
                else:
                    self.msg = f"{self.castle.name} est déjà sous votre contrôle."
            elif event.key == pygame.K_h:
                self.msg = "Hôtel de ville (placeholder)"
            elif event.key == pygame.K_b:
                self.msg = "Boutique (placeholder)"
            elif event.key == pygame.K_r:
                self.msg = "Caserne (placeholder)"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            # clic droit = retour (fallback si ESC capricieux)
            self.mgr.pop()

    def update(self, dt: float):
        pass

    def draw(self, surface: pygame.Surface):
        surface.fill((40, 40, 55))

        title = _font(40).render(self.castle.name, True, COLOR_UI)
        surface.blit(title, (WIDTH//2 - title.get_width()//2, 60))

        owner = "Allié" if self.castle.owner == "player" else "Ennemi"
        owner_col = COLOR_PLAYER if self.castle.owner == "player" else (200,60,60)
        owner_surf = _font(28).render(f"Contrôle : {owner}", True, owner_col)
        surface.blit(owner_surf, (WIDTH//2 - owner_surf.get_width()//2, 120))

        lines = [
            "[C] Capturer le château",
            "[H] Hôtel de ville   [B] Boutique   [R] Caserne",
            "[ESC] Retour à la carte  |  Clic droit: retour"
        ]
        y = 200
        for line in lines:
            surf = _font(26).render(line, True, COLOR_UI)
            surface.blit(surf, (WIDTH//2 - surf.get_width()//2, y))
            y += 36

        if self.msg:
            msg_surf = _font(24).render(self.msg, True, COLOR_UI)
            surface.blit(msg_surf, (WIDTH//2 - msg_surf.get_width()//2, HEIGHT - 80))
