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

    def perform_draw(self):
        raise NotImplementedError()

    def perform_build_data(self):
        raise NotImplementedError()

    def render(self):
        self.clear()
        self.perform_build_data()
        self.perform_draw()
        self.screen.blit(self.surface, self.get_blit_position())

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

    def perform_build_data(self):
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

    def perform_draw(self):
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


class CurrentSystemCard(BaseCard):
    bodies = OrderedDict()
    current_system = ''

    HIGH_GRAVITY_THREASHOLD = 1
    PARENT_SIZE_IN_VIEW_THREASHOLD = 10

    @staticmethod
    def watched():
        return ['Scan', 'FSDJump', 'FSSAllBodiesFound']

    @staticmethod
    def get_orbital_radius(b):
        # get orbital radius
        if 'Eccentricity' in b and 'SemiMajorAxis' in b:
            orbit_major = b['SemiMajorAxis']
            orbit_minor = orbit_major * math.sqrt(1 - (b['Eccentricity'] ** 2))
            return (orbit_major + orbit_minor) / 2
        else:
            return None

    def __get_is_good_moon_photo(self, body):
        body_id = str(body['BodyID'])
        if 'ParentSizeInPicturePlane' in body:
            return False
        if 'OrbitalRadius' not in body:
            return False
        if 'Parents' not in body:
            return False

        parent_id = None
        for _, id in body['Parents'][0].items():
            if id == 0:
                continue
            parent_id = str(id)

        if parent_id not in self.bodies.keys():
            return False

        parent = self.bodies[parent_id]

        if 'Radius' not in parent:
            return False
        if 'Radius' not in body:
            return False

        parent_diameter = parent['Radius'] * 2
        distance_to_parent = body['OrbitalRadius'] - body['Radius']
        picture_plane_size = math.tan(45) * distance_to_parent * 2
        body_view_size = parent_diameter / picture_plane_size * 100
        return body_view_size >= self.PARENT_SIZE_IN_VIEW_THREASHOLD

    @staticmethod
    def __get_item_label(b):
        if b['BodyName'][0:len(b['StarSystem'])] == b['StarSystem']:
            item_label = b['BodyName'][len(b['StarSystem']):]
        else:
            item_label = b['BodyName']

        if 'StarType' in b and b['StarType'] != '':

            if 'Subclass' in b and b['Subclass'] != '':
                item_label = "{} ({}{})".format(item_label, b['StarType'], b['Subclass'])
            else:
                item_label = "{} ({})".format(item_label, b['StarType'])

        elif 'PlanetClass' in b:
            item_label = "{} ({})".format(item_label, b['PlanetClass'])

        return item_label

    @staticmethod
    def __get_should_scan(b):
        if 'PlanetClass' in b and b['PlanetClass'] != '':
            class_lower = b['PlanetClass'].lower()
            if class_lower.find('earth') >= 0 or \
                    class_lower.find('water world') >= 0 or \
                    class_lower.find('ammonia world') >= 0:
                return True

        if 'TerraformState' in b and b['TerraformState'] != '':
            return True

        return False

    @staticmethod
    def __get_is_scoopable(b):
        if 'StarType' in b and b['StarType'] != '':
            is_star = True

            is_interesting_star_type = True if b['StarType'].upper() in [
                'H', 'N', 'X', 'TTS', 'AEBE',
                'SUPERMASSIVEBLACKHOLE', 'ROGUEPLANET'
            ] else False

            return True if b['StarType'].upper() in [
                'K', 'B', 'G', 'F', 'O', 'A', 'M'
            ] else False

        return False

    @staticmethod
    def __get_is_interesting_star(b):
        if 'StarType' in b and b['StarType'] != '':
            return True if b['StarType'].upper() in [
                'H', 'N', 'X', 'TTS', 'AEBE',
                'SUPERMASSIVEBLACKHOLE', 'ROGUEPLANET'
            ] else False
        return False

    def __get_is_high_g(self, b):
        if 'Landable' in b and b['Landable']:
            if 'SurfaceGravity' in b:
                gravity = self.mpss_to_g(b['SurfaceGravity'])
                if gravity >= self.HIGH_GRAVITY_THREASHOLD:
                    return True
        return False

    def perform_build_data(self):
        for e in self.journal.events:
            if e['event'] == 'Scan' and 'BodyID' in e:

                if 'PlanetClass' not in e and 'StarType' not in e:
                    continue

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

                self.bodies[body_id]['ItemLabel'] = self.__get_item_label(e)
                self.bodies[body_id]['ShouldScan'] = self.__get_should_scan(e)
                self.bodies[body_id]['HighG'] = self.__get_is_high_g(e)
                self.bodies[body_id]['POI'] = {
                    'is_interesting_star': self.__get_is_interesting_star(e),
                }

            if e['event'] == 'FSSAllBodiesFound':
                for i, b in self.bodies.items():
                    self.bodies[i]['POI']['is_good_moon_photo'] = self.__get_is_good_moon_photo(b)

        # re order by ID
        keys = self.bodies.keys()
        keys = sorted(keys)
        new_bodies = OrderedDict()
        for k in keys:
            new_bodies[k] = self.bodies[k]
        self.bodies = new_bodies

    def perform_draw(self):

        rect = self.print_line(self.surface, self.h1_font, self.current_system, x=constants.MARGIN)

        # printing
        for i, (k, b) in enumerate(self.bodies.items()):
            if rect.top > self.height - rect.height * 3:
                rect = self.print_line(self.surface, self.normal_font,
                                       "{} more...".format(len(self.bodies.items()) - i), y=rect.bottom,
                                       x=constants.MARGIN)
                break
            else:

                poi = b['POI']

                interest_level = len([i for i in poi.values() if i is True]) / len(poi)
                interest_level = math.ceil(interest_level * 3)
                if b['ShouldScan']:
                    color = constants.COLOR_SHOULD_SCAN
                elif b['HighG']:
                    color = constants.COLOR_DANGER
                elif interest_level == 1:
                    color = constants.COLOR_INTERESTING_1
                elif interest_level == 2:
                    color = constants.COLOR_INTERESTING_2
                elif interest_level == 3:
                    color = constants.COLOR_INTERESTING_3
                else:
                    color = constants.COLOR_COCKPIT
                item_label = b['ItemLabel']
                rect = self.print_line(self.surface, self.normal_font, item_label, x=constants.MARGIN, y=rect.bottom,
                                       color=color)


class RouteCard(BaseCard):
    route = []
    current_address = None
    position_in_route = -1

    @staticmethod
    def watched():
        return ['NavRoute', 'FSDJump']

    def perform_build_data(self):
        for e in self.journal.events:
            if e['event'] == 'NavRoute':
                self.route = self.journal.get_route()
            elif e['event'] == 'FSDJump':
                self.current_address = e['SystemAddress']
                self.route = self.journal.get_route()

            if 'SystemAddress' in e:
                self.position_in_route = -1
                for route_pos, r in enumerate(self.route):
                    if r['SystemAddress'] == self.current_address:
                        self.position_in_route = route_pos
                        break

    def perform_draw(self):

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
                    radius,
                )
                dot_label = self.normal_font.render(str(len(self.route) - position_index), False, pygame.Color("black"))
                dot_label_rect = dot_label.get_rect()
                dot_label_rect.center = (x, y)
                self.surface.blit(dot_label, dot_label_rect)
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
