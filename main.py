import sys
import pygame
from settings import WIDTH, HEIGHT, FPS
from game.scene import SceneManager
from game.world_map import WorldMap

def main():
    pygame.init()
    pygame.display.set_caption("Proto - Feudal Map")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    mgr = SceneManager()
    mgr.push(WorldMap(mgr))

    while not mgr.quit:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                mgr.quit = True
            else:
                mgr.handle_event(event)

        dt = clock.tick(FPS) / 1000.0
        mgr.update(dt)
        mgr.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()
