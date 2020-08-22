from overlays import constants
import pygame
from datetime import datetime, timedelta
from overlays.cards.BaseCard import BaseCard


class RouteCard(BaseCard):
    route = []
    current_address = None
    position_in_route = -1
    start_coords = None
    end_coords = None
    current_coords = None
    last_jump_time = None
    jump_time_history = []
    last_time_in_system = None
    eta = None

    @staticmethod
    def watched():
        return ['NavRoute', 'FSDJump']

    def perform_build_data(self):
        for e in self.journal.events:
            if e['event'] == 'NavRoute':
                self.route = self.journal.get_route()
                self.jump_time_history = []
            elif e['event'] == 'FSDJump':
                self.current_address = e['SystemAddress']
                self.route = self.journal.get_route()
                self.jump_time_history = []

                current_time = datetime.now()
                if self.last_jump_time is not None:
                    self.last_time_in_system = current_time - self.last_jump_time
                    self.jump_time_history.append(self.last_time_in_system)

                self.last_jump_time = current_time
                if 'StarPos' in e:
                    self.current_coords = e['StarPos']

            if len(self.route) == 0:
                self.start_coords = None
                self.end_coords = None
            elif len(self.route) > 0:
                if 'StarPos' in self.route[0]:
                    self.start_coords = self.route[0]['StarPos']
                if 'StarPos' in self.route[-1]:
                    self.end_coords = self.route[-1]['StarPos']

            if 'SystemAddress' in e:
                self.position_in_route = -1
                for route_pos, r in enumerate(self.route):
                    if r['SystemAddress'] == self.current_address:
                        self.position_in_route = route_pos
                        break

            if self.last_time_in_system and self.position_in_route and len(self.route) > 0 and len(
                    self.jump_time_history) > 0:
                self.eta = timedelta(seconds=(len(self.route) - self.position_in_route - 1) * (
                        sum([t.seconds for t in self.jump_time_history]) / len(self.jump_time_history)))
            else:
                self.eta = None

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

        if self.eta:
            if self.eta.total_seconds() < 60:
                self.print_line(self.surface, self.normal_font,
                                "ETA: {:0.1f} seconds".format(self.eta.seconds))
            elif self.eta.total_seconds() < 60 * 60:
                self.print_line(self.surface, self.normal_font,
                                "ETA: {:0.1f} minutes".format(self.eta.seconds / 60))
            elif self.eta.total_seconds() < 60 * 60 * 24:
                self.print_line(self.surface, self.normal_font,
                                "ETA: {:0.1f} hours".format(self.eta.seconds / 60 / 60))
            elif self.eta.total_seconds() < 60 * 60 * 24 * 7:
                self.print_line(self.surface, self.normal_font,
                                "ETA: {:0.1f} days".format(self.eta.seconds / 60 / 60 / 24))
            else:
                self.print_line(self.surface, self.normal_font,
                                "ETA: {:0.1f} weeks".format(self.eta.seconds / 60 / 60 / 24 / 7))

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
