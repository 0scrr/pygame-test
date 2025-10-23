import pygame
from settings import WIDTH, HEIGHT, COLOR_UI
from .scene import Scene
from .entities import EQUIPMENTS

def _font(sz:int)->pygame.font.Font:
    return pygame.font.Font(None, sz)

class ShopView(Scene):
    """
    Boutique : Achat et vente d'équipements avec l'inventaire du roi.
    - Ligne haut : Items à acheter
    - Ligne bas : Inventaire du roi (clic pour vendre)
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
            # Vérifier clics sur items à acheter (ligne haut)
            for i, item_name in enumerate(EQUIPMENTS):
                item_rect = pygame.Rect(50 + i * self.spacing, 120, self.icon_size, self.icon_size)
                if item_rect.collidepoint(mx, my):
                    item = EQUIPMENTS[item_name]
                    if self.king.remove_resource("gold", item["price"]):
                        self.king.add_equipment(item_name)
                    return
            # Vérifier clics sur items à vendre (ligne bas, inventaire)
            for i, (item_name, qty) in enumerate(self.king.equipment.items()):
                item_rect = pygame.Rect(50 + i * self.spacing, HEIGHT - 120 - self.icon_size, self.icon_size, self.icon_size)
                if item_rect.collidepoint(mx, my):
                    if self.king.sell_equipment(item_name):
                        pass  # Vente déjà gérée dans sell_equipment
                    return

    def update(self, dt: float):
        self.t += dt

    def draw(self, surface: pygame.Surface):
        surface.fill((30, 30, 36))
        title = self.font_big.render(f"Boutique — {self.castle.name}", True, COLOR_UI)
        surface.blit(title, (WIDTH//2 - title.get_width()//2, 40))

        # Ressources du roi
        gold_text = self.font.render(f"Or: {self.king.resources['gold']}", True, COLOR_UI)
        surface.blit(gold_text, (50, 80))

        # Ligne haut : Items à acheter
        buy_text = self.font.render("À acheter (cliquez sur l'icône) :", True, COLOR_UI)
        surface.blit(buy_text, (50, 100))
        for i, item_name in enumerate(EQUIPMENTS):
            item = EQUIPMENTS[item_name]
            icon_surf = pygame.Surface((self.icon_size, self.icon_size), pygame.SRCALPHA)
            item["icon_func"](icon_surf, (self.icon_size//2, self.icon_size//2))
            surface.blit(icon_surf, (50 + i * self.spacing, 120))
            price_text = self.font.render(f"{item['price']} or", True, COLOR_UI)
            surface.blit(price_text, (50 + i * self.spacing, 120 + self.icon_size + 5))

        # Ligne bas : Inventaire du roi (à vendre)
        sell_text = self.font.render("Votre inventaire (cliquez sur l'icône pour vendre) :", True, COLOR_UI)
        surface.blit(sell_text, (50, HEIGHT - 120 - self.icon_size - 20))
        for i, (item_name, qty) in enumerate(self.king.equipment.items()):
            item = EQUIPMENTS[item_name]
            icon_surf = pygame.Surface((self.icon_size, self.icon_size), pygame.SRCALPHA)
            item["icon_func"](icon_surf, (self.icon_size//2, self.icon_size//2))
            surface.blit(icon_surf, (50 + i * self.spacing, HEIGHT - 120 - self.icon_size))
            qty_text = self.font.render(f"x{qty}", True, COLOR_UI)
            surface.blit(qty_text, (50 + i * self.spacing + self.icon_size - 20, HEIGHT - 120 - self.icon_size + self.icon_size - 20))

        help_ = self.font.render("[ESC] Retour", True, COLOR_UI)
        surface.blit(help_, (20, HEIGHT-36))
