from collections import OrderedDict
from overlays import constants
import math
from overlays.cards.BaseCard import BaseCard


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

    def __get_is_moonrise(self, body):
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
        if body_view_size >= self.PARENT_SIZE_IN_VIEW_THREASHOLD:
            return 'Moonrise {}% of the sky'.format(body_view_size)
        else:
            return False

    @staticmethod
    def __get_item_label(b):
        if b['BodyName'][0:len(b['StarSystem'])] == b['StarSystem'] and \
                b['BodyName'] != b['StarSystem']:
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
    def __get_is_interesting_star(b):
        is_interesting = False
        if 'StarType' in b and b['StarType'] != '':
            is_interesting = True if b['StarType'].upper() in [
                'H', 'N', 'X', 'TTS', 'AEBE',
                'SUPERMASSIVEBLACKHOLE', 'ROGUEPLANET'
            ] else False
        return 'Interesting' if is_interesting else False

    def __get_is_high_g(self, b):
        if 'Landable' in b and b['Landable']:
            if 'SurfaceGravity' in b:
                gravity = self.mpss_to_g(b['SurfaceGravity'])
                if gravity >= self.HIGH_GRAVITY_THREASHOLD:
                    return 'High G planet'
        return False

    def add_poi(self, function, body):
        value = function(body)
        if 'POI' not in body:
            body['POI'] = []
        if value:
            body['POI'].append(value)

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

                self.add_poi(self.__get_is_interesting_star, e)
                self.add_poi(self.__get_is_high_g, e)

            if e['event'] == 'FSSAllBodiesFound':
                for i, b in self.bodies.items():
                    self.add_poi(self.__get_is_moonrise, e)

        # re order by ID
        keys = self.bodies.keys()
        keys = sorted(keys)
        new_bodies = OrderedDict()
        for k in keys:
            new_bodies[k] = self.bodies[k]
        self.bodies = new_bodies

    def perform_draw(self):

        self.print_line(self.surface, self.h1_font, self.current_system)

        # printing
        for i, (k, b) in enumerate(self.bodies.items()):

            poi = b['POI']

            if b['ShouldScan']:
                color = constants.COLOR_SHOULD_SCAN
            elif len(poi) > 0:
                color = constants.COLOR_INTERESTING_1
            else:
                color = constants.COLOR_COCKPIT

            item_label = b['ItemLabel']
            if len(poi) > 0:
                item_label = "{} [{}]".format(item_label, ",".join(poi))
            self.print_line(self.surface, self.normal_font, item_label, color=color)