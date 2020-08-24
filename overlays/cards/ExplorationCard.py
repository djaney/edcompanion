from collections import OrderedDict
from overlays import constants
from overlays.cards.BaseCard import BaseCard
import requests
import logging


class ExplorationCard(BaseCard):
    planets = {}
    estimated_value = 0
    estimate_request_cache = {}
    current_system = {}

    @staticmethod
    def watched():
        return ['Scan', 'SAAScanComplete', 'FSSAllBodiesFound']

    def print_discovery_count(self, screen, font, data_dict, y=0, x=0):

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
            self.print_line(self.surface,
                            font,
                            "{}: {}".format(item_name, count) if count is not None else "{}".format(item_name),

                            )

    def perform_build_data(self):
        for e in self.journal.events:
            if e['event'] == 'FSSAllBodiesFound':
                self.estimated_value += self.system_value(e)
            elif e['event'] == 'SAAScanComplete':
                self.estimated_value += self.scan_max_value(e)
            elif e['event'] == 'Scan':
                self.current_system = e['StarSystem']
                if 'PlanetClass' in e:
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

    def scan_max_value(self, e):
        if 'BodyID' not in e:
            return 0
        url = "https://www.edsm.net/api-system-v1/estimated-value?systemName={}".format(self.current_system)
        response = self.estimate_request_cache.get('url')
        if response is None:
            try:
                response = requests.get(url).json()
                self.estimate_request_cache[url] = response
            except Exception as e:
                logging.getLogger("ExplorationCard").info(str(e))

        if response is None:
            return 0
        value = 0
        for b in response.get('valuableBodies', []):
            if b.get('bodyName') == e['BodyName']:
                value += b.get('valueMax')
        return value

    def system_value(self, e):
        url = "https://www.edsm.net/api-system-v1/estimated-value?systemName={}".format(self.current_system)
        response = self.estimate_request_cache.get('url')
        if response is None:
            try:
                response = requests.get(url).json()
                self.estimate_request_cache[url] = response
            except Exception as e:
                logging.getLogger("ExplorationCard").info(str(e))

        if response is None:
            return 0
        return response.get('estimatedValue')

    def perform_draw(self):
        # scanned bodies
        self.print_line(self.surface, self.h1_font, 'Scanned Bodies')
        self.print_line(self.surface, self.normal_font, 'Session value: {:0,}'.format(self.estimated_value))
        self.print_discovery_count(self.surface, self.normal_font, self.planets)