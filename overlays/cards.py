from collections import OrderedDict
from overlays import constants
import pygame


class BaseCard:
    def __init__(self, screen, journal, position=(0, 0), text_align='left', card_size=(1, 1)):
        self.screen = screen
        self.journal = journal
        self.position = position
        self.card_size = card_size
        self.text_align = text_align
        self.h1_font = pygame.font.Font(constants.FONT, 16)
        self.normal_font = pygame.font.Font(constants.FONT, 12)

        width, height = screen.get_size()
        self.width, self.height = size = ((width // (3/self.card_size[0])), height // (3/self.card_size[1]))

        self.surface = pygame.Surface(size, pygame.SRCALPHA)
        self.surface.fill((0, 0, 0, 0))

    def print_line(self, screen, font, text, x=0, y=0):
        name_text = font.render(text, True, constants.COCKPIT_COLOR)
        name_rect = name_text.get_rect()
        if self.text_align == 'left':
            name_rect.left = x
        else:
            name_rect.right = self.width - x
        name_rect.top = y
        screen.blit(name_text, name_rect)
        return name_rect

    def get_blit_position(self):
        width, height = self.screen.get_size()
        card_width, card_height = (width // 3, height // 3)
        return (
            (self.position[0] * card_width, self.position[1] * card_height),
            (self.position[0] * card_width + card_width, self.position[1] * card_height + card_height),
        )

    def render(self):
        raise NotImplementedError()

    @staticmethod
    def watched():
        raise NotImplementedError()


class ExplorationCard(BaseCard):
    planets = {}
    first_discoveries = []

    @staticmethod
    def watched():
        return ['Scan' ,'FSSSignalDiscovered']

    def print_discovery_count(self, screen, font, data_dict, columns=1, y=0, x=0):
        last_rect = None
        line_height = None
        width, height = screen.get_size()
        line_y = y

        # re-order
        data_dict = OrderedDict(
            sorted(data_dict.items(), key=lambda i: -100 if i[0] == 'Worthless' else i[1], reverse=True)
        )

        # print
        for i, (item_name, count) in enumerate(data_dict.items()):
            x = (i % columns) * (width // columns) + x
            if i < columns:
                y = line_y
            else:
                y = (i // columns) * line_height + line_y
            if count is not None:
                item_text = font.render("{}: {}".format(item_name, count), True,
                                        constants.COCKPIT_COLOR)
            else:
                item_text = font.render("{}".format(item_name), True,
                                        constants.COCKPIT_COLOR)
            items_rect = item_text.get_rect()
            if self.text_align == 'left':
                items_rect.left = x
            else:
                items_rect.right = self.width - x
            items_rect.top = y
            screen.blit(item_text, items_rect)
            if line_height is None:
                line_height = items_rect.height
            last_rect = items_rect
        return last_rect

    def render(self):

        for e in self.journal.events:
            if e['event'] == 'Scan' and 'PlanetClass' in e:
                n = e['PlanetClass']
                n_lower = n.lower()
                if 'TerraformState' in e and e['TerraformState'] != '':
                    n = "{} (T)".format(n)
                elif n_lower.find('earth') >= 0 or \
                        n_lower.find('water world') >= 0 or \
                        n_lower.find('ammonia world') >= 0:
                    pass
                else:
                    n = 'Worthless space rock'

                if n not in self.planets:
                    self.planets[n] = 0
                self.planets[n] += 1

                # first discovery
                if 'WasDiscovered' in e and not e['WasDiscovered']:
                    n = e['BodyName']
                    if n not in self.first_discoveries:
                        self.first_discoveries.insert(0, n)
        # scanned bodies
        rect = self.print_line(self.surface, self.h1_font, 'Scanned Bodies', x=constants.MARGIN)
        rect = self.print_discovery_count(self.surface, self.normal_font, self.planets, y=rect.bottom,
                                          x=constants.MARGIN)
        rect = self.print_line(self.surface, self.h1_font, 'First discoveries', y=rect.bottom + constants.MARGIN,
                               x=constants.MARGIN)

        for i, f in enumerate(self.first_discoveries):
            if rect.top > self.height - rect.height*3:
                rect = self.print_line(self.surface, self.normal_font,
                                       "{} more...".format(len(self.first_discoveries) - i), y=rect.bottom,
                                       x=constants.MARGIN)
                break
            else:
                rect = self.print_line(self.surface, self.normal_font, f, y=rect.bottom, x=constants.MARGIN)

        self.screen.blit(self.surface, self.get_blit_position())


class CurrentSystemCard(BaseCard):

    bodies = OrderedDict()
    current_system = ''

    @staticmethod
    def watched():
        return ['Scan', 'FSDJump']

    def render(self):

        for e in self.journal.events:

            if e['event'] == 'FSDJump':
                self.bodies = OrderedDict()
                self.current_system = e['StarSystem']
            elif e['event'] == 'Scan' and 'BodyID' in e:
                if str(e['BodyID']) in self.bodies:
                    self.bodies[str(e['BodyID'])].update(e)
                else:
                    self.bodies[str(e['BodyID'])] = e

        rect = self.print_line(self.surface, self.h1_font, self.current_system, x=constants.MARGIN)

        for i, (k, b) in enumerate(self.bodies.items()):
            if rect.top > self.height - rect.height * 3:
                rect = self.print_line(self.surface, self.normal_font,
                                       "{} more...".format(len(self.bodies.items()) - i), y=rect.bottom,
                                       x=constants.MARGIN)
                break
            else:
                is_high_g = False
                is_landable = False
                has_ring = False
                if b['BodyName'][0:len(b['StarSystem'])] == b['StarSystem']:
                    item_label = b['BodyName'][len(b['StarSystem']):]
                else:
                    item_label = b['BodyName']

                if 'PlanetClass' in b and b['PlanetClass'] != '':
                    item_label = "{} ({})".format(item_label, b['PlanetClass'])

                if 'StarType' in b and b['StarType'] != '':
                    if 'Subclass' in b and b['Subclass'] != '':
                        item_label = "{} ({}{})".format(item_label, b['StarType'], b['Subclass'])
                    else:
                        item_label = "{} ({})".format(item_label, b['StarType'])

                flags = []
                if 'TerraformState' in b and b['TerraformState'] != '':
                    flags.append('T')

                if 'Landable' in b and b['Landable'] != '':
                    flags.append('L')
                    is_landable = True
                    if 'SurfaceGravity' in b and b['SurfaceGravity'] >= 10:
                        flags.append("{}G".format(round(b['SurfaceGravity'])))
                        is_high_g = True

                if 'Rings' in b and len(b['Rings']) > 0:
                    has_ring = True
                    ring_size = 0
                    for r in b['Rings']:
                        ring_size += r['OuterRad'] - r['InnerRad']
                    flags.append('R{}'.format(round(ring_size)))

                if len(flags) > 0:
                    item_label = "{} ({})".format(item_label, "".join(flags))

                rect = self.print_line(self.surface, self.normal_font, item_label, x=constants.MARGIN, y=rect.bottom)

        self.screen.blit(self.surface, self.get_blit_position())