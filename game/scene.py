import pygame

class Scene:
    """Base de scène : handle_event, update, draw."""
    def __init__(self, manager):
        self.mgr = manager

    def on_enter(self): pass
    def on_leave(self): pass
    def handle_event(self, event): pass
    def update(self, dt: float): pass
    def draw(self, surface: pygame.Surface): pass


class SceneManager:
    """Gestionnaire avec un petit stack (push/pop)."""
    def __init__(self):
        self._stack: list[Scene] = []
        self.quit = False

    def current(self) -> Scene | None:
        return self._stack[-1] if self._stack else None

    def push(self, scene: Scene):
        self._stack.append(scene)
        scene.on_enter()

    def pop(self):
        if self._stack:
            top = self._stack.pop()
            top.on_leave()
        if not self._stack:
            self.quit = True

    def replace(self, scene: Scene):
        self.pop()
        if not self.quit:
            self.push(scene)

    def handle_event(self, event):
        cur = self.current()
        if cur:
            cur.handle_event(event)

    def update(self, dt: float):
        cur = self.current()
        if cur:
            cur.update(dt)

    def draw(self, surface: pygame.Surface):
        cur = self.current()
        if cur:
            cur.draw(surface)
