import pygame

from pygame.locals import *


class Window(object):
    def __init__(self, size=None):
        self.mask_color = 0, 255, 0
        self.fps = 60
        self.clock = pygame.time.Clock()

        pygame.init()
        pygame.display.set_caption("Elite: Dangerous Overlay")

        if size is None:
            size = (0, 0)

        self.screen = pygame.display.set_mode(size)
        self.screen.fill(self.mask_color)

    @property
    def width(self):
        width, height = pygame.display.get_surface().get_size()
        return width

    @property
    def height(self):
        width, height = pygame.display.get_surface().get_size()
        return height

    def loop(self):
        self.clock.tick(self.fps)
        events = pygame.event.get()

        for e in events:
            if e.type == pygame.QUIT:
                return False
        return True
