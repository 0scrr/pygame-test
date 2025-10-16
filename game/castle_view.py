import pygame
from settings import WIDTH, HEIGHT, COLOR_UI
from .scene import Scene

class CastleView(Scene):
    def __init__(self, mgr, castle):
        super().__init__(mgr)
        self.castle = castle
        self.font_title = pygame.font.Font(None, 36)
        self.font_text  = pygame.font.Font(None, 24)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            # Quitte la vue château et revient à la carte
            self.mgr.pop()
        elif event.type == pygame.QUIT:
            self.mgr.quit = True

    def update(self, dt: float):
        pass

    def draw(self, surface: pygame.Surface):
        surface.fill((10,10,12))
        title = self.font_title.render(self.castle.name, True, COLOR_UI)
        surface.blit(title, (WIDTH//2 - title.get_width()//2, 60))

        lines = [
            "Vue du château",
            "Appuie sur ESC pour revenir à la carte."
        ]
        y = 130
        for line in lines:
            r = self.font_text.render(line, True, COLOR_UI)
            surface.blit(r, (WIDTH//2 - r.get_width()//2, y))
            y += 28
