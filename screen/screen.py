import pygame

from pygame.locals import *
import os


class Window(object):
    def __init__(self, size=None, is_overlay=False, color=(0, 255, 0)):
        self.mask_color = color
        self.fps = 60
        self.clock = pygame.time.Clock()

        pygame.init()
        pygame.display.set_caption("Elite: Dangerous Companion")

        if size is None:
            size = (0, 0)

        if is_overlay and os.name == 'nt':
            import win32api
            import win32con
            import win32gui
            self.mask_color = 0, 255, 0
            self.screen = pygame.display.set_mode((0, 0), NOFRAME)

            hwnd = pygame.display.get_wm_info()["window"]
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                                   win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
            win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(*self.mask_color), 0, win32con.LWA_COLORKEY)

        else:
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
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return False
        return True
