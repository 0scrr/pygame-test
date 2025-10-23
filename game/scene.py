import pygame
from .entities import King

class Scene:
    def __init__(self, mgr):
        self.mgr = mgr
    # Hooks optionnels
    def on_enter(self): pass
    def on_exit(self): pass
    def on_child_popped(self, child): pass  # appelé quand une scène enfant se ferme
    def handle_event(self, event): pass
    def update(self, dt: float): pass
    def draw(self, surface: pygame.Surface): pass

class SceneManager:
    def __init__(self):
        self.stack: list[Scene] = []
        self.quit = False
        self.game_state = GameState()  # État global du jeu avec le roi

    @property
    def current(self) -> Scene | None:
        return self.stack[-1] if self.stack else None

    def push(self, scene: Scene):
        self.stack.append(scene)
        scene.on_enter()

    def pop(self):
        if not self.stack:
            return
        child = self.stack.pop()
        child.on_exit()
        # informer la scène du dessous
        parent = self.current
        if parent:
            parent.on_child_popped(child)

    # IMPORTANT: ne délègue qu'à la scène **courante**
    def handle_event(self, event):
        cur = self.current
        if cur:
            cur.handle_event(event)

    def update(self, dt: float):
        cur = self.current
        if cur:
            cur.update(dt)

    def draw(self, surface: pygame.Surface):
        cur = self.current
        if cur:
            cur.draw(surface)

class GameState:
    def __init__(self):
        self.king = King(400, 300)  # Position initiale par défaut
