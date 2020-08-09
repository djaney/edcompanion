from collections import OrderedDict
from overlays import constants
import pygame
import math


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
        self.width, self.height = size = ((width // (3 / self.card_size[0])), height // (3 / self.card_size[1]))

        self.surface = pygame.Surface(size, pygame.SRCALPHA)
        self.clear()

    def clear(self):
        self.surface.fill((0, 0, 0, 0))

    @staticmethod
    def mpss_to_g(mpss):
        return mpss / 9.80665

    def print_line(self, screen, font, text, x=0, y=0, color=None):
        if color is None:
            color = constants.COLOR_COCKPIT
        name_text = font.render(text, False, color)
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
        return ['Scan']

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
        
        if len(data_dict) == 0:
            item_text = font.render("Go Explore!", False, constants.COLOR_COCKPIT)
            items_rect = item_text.get_rect()
            if self.text_align == 'left':
                items_rect.left = x
            else:
                items_rect.right = self.width - x
            items_rect.top = y
            last_rect = items_rect
                
        for i, (item_name, count) in enumerate(data_dict.items()):
            x = (i % columns) * (width // columns) + x
            if i < columns:
                y = line_y
            else:
                y = (i // columns) * line_height + line_y
            if count is not None:
                item_text = font.render("{}: {}".format(item_name, count), False,
                                        constants.COLOR_COCKPIT)
            else:
                item_text = font.render("{}".format(item_name), False,
                                        constants.COLOR_COCKPIT)
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
        self.clear()
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
            if rect.top > self.height - rect.height * 3:
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

    HIGH_GRAVITY_THREASHOLD = 1
    PARENT_SIZE_IN_VIEW_THREASHOLD = 10

    @staticmethod
    def watched():
        return ['Scan', 'FSDJump']

    @staticmethod
    def get_orbital_radius(b):
        # get orbital radius
        if 'Eccentricity' in b and 'SemiMajorAxis' in b:
            orbit_major = b['SemiMajorAxis']
            orbit_minor = orbit_major * math.sqrt(1 - (b['Eccentricity'] ** 2))
            return (orbit_major + orbit_minor) / 2
        else:
            return None

    def calculate_parent_percent_in_picture_plane(self):
        for i, (body_id, body) in enumerate(self.bodies.items()):
            if 'ParentSizeInPicturePlane' in body:
                continue
            if 'OrbitalRadius' not in body:
                continue
            if 'Parents' not in body:
                continue

            parent_id = None
            for _, id in body['Parents'][0].items():
                if id == 0:
                    continue
                parent_id = str(id)

            if parent_id not in self.bodies.keys():
                continue

            parent = self.bodies[parent_id]

            if 'Radius' not in parent:
                continue
            if 'Radius' not in body:
                continue

            parent_diameter = parent['Radius'] * 2
            distance_to_parent = body['OrbitalRadius'] - body['Radius']
            picture_plane_size = math.tan(45) * distance_to_parent * 2
            self.bodies[body_id]['ParentSizeInPicturePlane'] = parent_diameter / picture_plane_size * 100

    def render(self):
        self.clear()
        for e in self.journal.events:
            if e['event'] == 'Scan' and 'BodyID' in e:

                if 'StarSystem' in e and e['StarSystem'] != self.current_system:
                    self.bodies = OrderedDict()
                    self.current_system = e['StarSystem']

                body_id = str(e['BodyID'])
                if body_id in self.bodies:
                    self.bodies[body_id].update(e)
                else:
                    self.bodies[body_id] = e

                if 'OrbitalRadius' not in self.bodies[body_id]:
                    orbital_radius = self.get_orbital_radius(self.bodies[body_id])
                    if orbital_radius is not None:
                        self.bodies[body_id]['OrbitalRadius'] = orbital_radius

                self.calculate_parent_percent_in_picture_plane()

        rect = self.print_line(self.surface, self.h1_font, self.current_system, x=constants.MARGIN)

        # printing
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
                is_terraformable = False
                is_star = False
                is_scoopable = False
                is_interesting_star_type = False
                is_planet = False
                is_expensive = False
                is_parent_close_for_photo = False
                if b['BodyName'][0:len(b['StarSystem'])] == b['StarSystem']:
                    item_label = b['BodyName'][len(b['StarSystem']):]
                else:
                    item_label = b['BodyName']

                if 'PlanetClass' in b and b['PlanetClass'] != '':
                    is_planet = True
                    item_label = "{} ({})".format(item_label, b['PlanetClass'])
                    class_lower = b['PlanetClass'].lower()
                    if class_lower.find('earth') >= 0 or \
                            class_lower.find('water world') >= 0 or \
                            class_lower.find('ammonia world') >= 0:
                        is_expensive = True

                if 'StarType' in b and b['StarType'] != '':
                    is_star = True

                    is_interesting_star_type = True if b['StarType'].upper() in [
                        'H', 'N', 'X', 'TTS', 'AEBE',
                        'SUPERMASSIVEBLACKHOLE', 'ROGUEPLANET'
                    ] else False

                    is_scoopable = True if b['StarType'].upper() in [
                        'K', 'B', 'G', 'F', 'O', 'A', 'M'
                    ] else False

                    if 'Subclass' in b and b['Subclass'] != '':
                        item_label = "{} ({}{})".format(item_label, b['StarType'], b['Subclass'])
                    else:
                        item_label = "{} ({})".format(item_label, b['StarType'])

                flags = []
                if 'TerraformState' in b and b['TerraformState'] != '':
                    flags.append('T')
                    is_terraformable = True

                if 'Landable' in b and b['Landable']:
                    flags.append('L')
                    is_landable = True
                    if 'SurfaceGravity' in b:
                        gravity = self.mpss_to_g(b['SurfaceGravity'])
                        if gravity >= self.HIGH_GRAVITY_THREASHOLD:
                            flags.append("{}G".format(round(gravity)))
                            is_high_g = True

                if 'Rings' in b and len(b['Rings']) > 0:
                    has_ring = True
                    ring_size = 0
                    for r in b['Rings']:
                        ring_size += r['OuterRad'] - r['InnerRad']
                    flags.append('R')

                if 'ParentSizeInPicturePlane' in b and b[
                    'ParentSizeInPicturePlane'] >= self.PARENT_SIZE_IN_VIEW_THREASHOLD:
                    is_parent_close_for_photo = False

                if len(flags) > 0:
                    item_label = "{} ({})".format(item_label, "".join(flags))

                interest_level = 0

                color = None

                if is_terraformable or is_expensive:
                    color = constants.COLOR_TERRAFORMABLE
                elif is_high_g and is_landable:
                    color = constants.COLOR_DANGER
                else:

                    if has_ring and is_landable:
                        interest_level += 1
                    if is_interesting_star_type:
                        interest_level += 1
                    if is_parent_close_for_photo:
                        interest_level += 1


                item_label += "*" * interest_level


                rect = self.print_line(self.surface, self.normal_font, item_label, x=constants.MARGIN, y=rect.bottom,
                                       color=color)

        self.screen.blit(self.surface, self.get_blit_position())


class RouteCard(BaseCard):
    route = []
    current_address = None
    position_in_route = -1

    @staticmethod
    def watched():
        return ['NavRoute', 'FSDJump']

    def render(self):
        self.clear()

        for e in self.journal.events:
            if e['event'] == 'NavRoute':
                self.route = self.journal.get_route()
            elif e['event'] == 'FSDJump':
                self.current_address = e['SystemAddress']

            if 'SystemAddress' in e:
                self.position_in_route = -1
                for route_pos, r in enumerate(self.route):
                    if r['SystemAddress'] == self.current_address:
                        self.position_in_route = route_pos
                        break

        route_slice = list(enumerate(self.route))
        pad = 5
        if self.position_in_route < pad:
            route_slice = route_slice[:10]
        elif self.position_in_route >= len(route_slice) - pad:
            route_slice = route_slice[10:]
        else:
            route_slice = route_slice[self.position_in_route - pad:self.position_in_route + pad]

        width = self.surface.get_width()
        height = self.surface.get_height()
        distance = width // (len(route_slice) + 1)

        for list_index, (position_index, stop) in enumerate(route_slice):
            radius = 20
            x = distance + (list_index * distance)
            y = height // 4

            if stop['StarClass'] not in 'KBGFOAM':
                color = constants.COLOR_DANGER
            else:
                color = constants.COLOR_COCKPIT

            if position_index == self.position_in_route:
                pygame.draw.circle(
                    self.surface,
                    color,
                    (x, y),
                    radius
                )
            else:
                pygame.draw.circle(
                    self.surface,
                    color,
                    (x, y),
                    radius,
                    1
                )
                dot_label = self.normal_font.render(str(len(self.route) - position_index), False, color)
                dot_label_rect = dot_label.get_rect()
                dot_label_rect.center = (x, y)
                self.surface.blit(dot_label, dot_label_rect)

            if list_index < len(route_slice) - 1:
                pygame.draw.line(self.surface, constants.COLOR_COCKPIT, (x + radius, y), (x + distance - radius, y))

        self.screen.blit(self.surface, self.get_blit_position())


