from overlays import constants
import pygame


class BaseCard:
    __line_y = 0

    def __init__(self, screen, journal, position=(0, 0), text_align='left', card_size=(1, 1)):
        self.screen = screen
        self.journal = journal
        self.position = position
        self.card_size = card_size
        self.text_align = text_align
        self.h1_font = pygame.font.Font(constants.FONT, 16)
        self.normal_font = pygame.font.Font(constants.FONT, 12)

        width, height = screen.get_size()
        self.width, self.height = size = ((width // (3 / self.card_size[0])), height // (3 / self.card_size[1]))

        self.surface = pygame.Surface(size, pygame.SRCALPHA)
        self.clear()

    def clear(self):
        self.surface.fill((0, 0, 0, 0))
        self.__line_y = 0

    @staticmethod
    def mpss_to_g(mpss):
        return mpss / 9.80665

    def print_line(self, screen, font, text, color=None):
        if color is None:
            color = constants.COLOR_COCKPIT
        name_text = font.render(text, False, color)
        name_rect = name_text.get_rect()
        if self.text_align == 'left':
            name_rect.left = constants.MARGIN
        else:
            name_rect.right = self.width - constants.MARGIN
        name_rect.top = self.__line_y
        screen.blit(name_text, name_rect)
        self.__line_y = name_rect.bottom
        return name_rect

    def get_blit_position(self):
        width, height = self.screen.get_size()
        card_width, card_height = (width // 3, height // 3)
        return (
            (self.position[0] * card_width, self.position[1] * card_height),
            (self.position[0] * card_width + card_width, self.position[1] * card_height + card_height),
        )

    def perform_draw(self):
        raise NotImplementedError()

    def perform_build_data(self):
        raise NotImplementedError()

    def render(self):
        self.clear()
        if self.journal.is_modified:
            self.perform_build_data()
        self.perform_draw()
        self.screen.blit(self.surface, self.get_blit_position())

    @staticmethod
    def watched():
        raise NotImplementedError()