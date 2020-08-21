from collections import OrderedDict
from overlays import constants
from overlays.cards.BaseCard import BaseCard


class ExplorationCard(BaseCard):
    planets = {}

    @staticmethod
    def watched():
        return ['Scan']

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

    def perform_draw(self):
        # scanned bodies
        self.print_line(self.surface, self.h1_font, 'Scanned Bodies')
        self.print_discovery_count(self.surface, self.normal_font, self.planets)