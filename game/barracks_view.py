import pygame
from settings import WIDTH, HEIGHT, COLOR_UI
from .scene import Scene
from .entities import SOLDIERS

def _font(sz:int)->pygame.font.Font:
    return pygame.font.Font(None, sz)

class BarracksView(Scene):
    """
    Caserne : Recrutement et congé de soldats avec l'inventaire du roi.
    - Ligne haut : Troupes à recruter
    - Ligne bas : Armée actuelle (clic pour congédier)
    - [ESC] pour revenir
    """
    def __init__(self, mgr, castle):
        super().__init__(mgr)
        self.castle = castle
        self.king = mgr.game_state.king
        self.font_big = _font(36)
        self.font = _font(24)
        self.t = 0.0
        self.icon_size = 40
        self.spacing = 60

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.mgr.pop()
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # Vérifier clics sur troupes à recruter (ligne haut)
            for i, soldier_type in enumerate(SOLDIERS):
                soldier_rect = pygame.Rect(50 + i * self.spacing, 120, self.icon_size, self.icon_size)
                if soldier_rect.collidepoint(mx, my):
                    soldier = SOLDIERS[soldier_type]
                    if self.king.remove_resource("gold", soldier["cost_gold"]) and self.king.remove_resource("food", soldier["cost_food"]):
                        self.king.recruit_soldier(soldier_type)
                    return
            # Vérifier clics sur troupes à congédier (ligne bas, armée)
            for i, (soldier_type, qty) in enumerate(self.king.army.items()):
                soldier_rect = pygame.Rect(50 + i * self.spacing, HEIGHT - 120 - self.icon_size, self.icon_size, self.icon_size)
                if soldier_rect.collidepoint(mx, my):
                    if self.king.dismiss_soldier(soldier_type):
                        pass  # Congé déjà géré dans dismiss_soldier
                    return

    def update(self, dt: float):
        self.t += dt

    def draw(self, surface: pygame.Surface):
        surface.fill((32, 28, 24))
        title = self.font_big.render(f"Caserne — {self.castle.name}", True, COLOR_UI)
        surface.blit(title, (WIDTH//2 - title.get_width()//2, 40))

        # Ressources du roi
        res_text = self.font.render(f"Or: {self.king.resources['gold']} | Nourriture: {self.king.resources['food']}", True, COLOR_UI)
        surface.blit(res_text, (50, 80))

        # Ligne haut : Troupes à recruter
        recruit_text = self.font.render("À recruter (cliquez sur l'icône) :", True, COLOR_UI)
        surface.blit(recruit_text, (50, 100))
        for i, soldier_type in enumerate(SOLDIERS):
            soldier = SOLDIERS[soldier_type]
            icon_surf = pygame.Surface((self.icon_size, self.icon_size), pygame.SRCALPHA)
            soldier["icon_func"](icon_surf, (self.icon_size//2, self.icon_size//2))
            surface.blit(icon_surf, (50 + i * self.spacing, 120))
            cost_text = self.font.render(f"{soldier['cost_gold']} or", True, COLOR_UI)
            surface.blit(cost_text, (50 + i * self.spacing, 120 + self.icon_size + 5))

        # Ligne bas : Armée actuelle (à congédier)
        dismiss_text = self.font.render("Votre armée (cliquez sur l'icône pour congédier) :", True, COLOR_UI)
        surface.blit(dismiss_text, (50, HEIGHT - 120 - self.icon_size - 20))
        for i, (soldier_type, qty) in enumerate(self.king.army.items()):
            soldier = SOLDIERS[soldier_type]
            icon_surf = pygame.Surface((self.icon_size, self.icon_size), pygame.SRCALPHA)
            soldier["icon_func"](icon_surf, (self.icon_size//2, self.icon_size//2))
            surface.blit(icon_surf, (50 + i * self.spacing, HEIGHT - 120 - self.icon_size))
            qty_text = self.font.render(f"x{qty}", True, COLOR_UI)
            surface.blit(qty_text, (50 + i * self.spacing + self.icon_size - 20, HEIGHT - 120 - self.icon_size + self.icon_size - 20))

        help_ = self.font.render("[ESC] Retour", True, COLOR_UI)
        surface.blit(help_, (20, HEIGHT-36))
