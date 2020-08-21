from overlays import constants
import pygame
from datetime import datetime, timedelta
from overlays.cards.BaseCard import BaseCard
import math


class RaceCard(BaseCard):
    waypoints = []
    race = None
    time_start = None
    time_end = None

    FIGHTER_MINIMUM_DEGREE = 0.02
    SRV_MINIMUM_DEGREE = 0.01

    def __init__(self, *args, **kwargs):
        super(RaceCard, self).__init__(*args, **kwargs)
        self.init_race()
        self.journal.include_pass_event()

    def init_race(self):
        self.race = self.journal.get_race_details()
        if self.race:
            self.waypoints = [None] * len(self.race['waypoints'])
        self.time_start = None
        self.time_end = None

    @staticmethod
    def watched():
        return ['LaunchFighter', 'DockFighter', 'Liftoff', 'Touchdown']

    def get_current_waypoint(self):
        index = -1
        for i, w in enumerate(self.waypoints):
            if w is None:
                index = i
                break

        if not self.is_race_done():
            return index, self.race['waypoints'][index]
        else:
            index = len(self.race['waypoints']) - 1
            return index, self.race['waypoints'][index]

    def is_race_done(self):
        return self.time_end is not None

    def is_race_started(self):
        return self.time_start is not None

    def waypoint_done(self, index):

        if index == 0:
            self.time_start = self.journal.now()
            self.waypoints[index] = self.time_start
        elif index == len(self.waypoints) - 1:
            self.time_end = self.journal.now()
            self.waypoints[index] = self.time_end
        else:
            self.waypoints[index] = self.journal.now()

    @staticmethod
    def get_km_per_degree(planet_radius):
        return (planet_radius / 1000) * 2 * math.pi / 360

    @staticmethod
    def get_distance_as_km(a, b, planet_radius):
        units_per_degree = RaceCard.get_km_per_degree(planet_radius)
        return RaceCard.get_distance_as_degree(a, b) * units_per_degree

    @staticmethod
    def get_distance_as_degree(a, b):
        return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

    def get_ship_position(self):
        status = self.journal.get_status()
        lat = status.get('Latitude', None)
        lng = status.get('Longitude', None)
        alt = status.get('Altitude', None)
        # km
        rad = status.get('PlanetRadius', 6371)
        return lat, lng, rad, alt

    def perform_build_data(self):

        current_waypoint_index, current_waypoint = self.get_current_waypoint()

        wp_lat = current_waypoint['lat']
        wp_lng = current_waypoint['lng']
        wp_range_km = current_waypoint.get('range', 0.5)
        wp_event = current_waypoint['event']

        for e in self.journal.events:
            if e['event'] == wp_event:
                lat, lng, planet_radius, alt = self.get_ship_position()
                if lat is not None and lng is not None:
                    distance = self.get_distance_as_km((lat, lng), (wp_lat, wp_lng), planet_radius)
                    if distance <= wp_range_km:
                        self.waypoint_done(current_waypoint_index)

    def __get_bounds(self, base_wp):
        x_max = None
        x_min = None
        y_max = None
        y_min = None

        # get bounds
        for w in base_wp:
            if x_max is None:
                x_max = w['lat']
            if y_max is None:
                y_max = w['lng']
            if x_min is None:
                x_min = w['lat']
            if y_min is None:
                y_min = w['lng']

            x_max = max(x_max, w['lat'])
            y_max = max(y_max, w['lng'])
            x_min = min(x_min, w['lat'])
            y_min = min(y_min, w['lng'])

        if x_max is not None and x_min is not None and y_max is not None and y_min is not None:
            return (x_min, y_min), (x_max, y_max)
        else:
            return None

    def draw_waypoints(self, base_wp, progress_wp=-1):
        top_pad = self.line_y

        size = min(self.surface.get_width(), self.surface.get_height())
        race_box = pygame.Surface((size - top_pad, size - top_pad), pygame.SRCALPHA)
        # draw race track
        # pygame.draw.rect(race_box, constants.COLOR_COCKPIT, (0, 0, race_box.get_width(), race_box.get_height()), 1)

        bounds = self.__get_bounds(base_wp)
        coord_list = []
        if bounds and bounds[1][0] - bounds[0][0] + bounds[1][-1] - bounds[0][1] != 0:
            for w_index, w in enumerate(base_wp):
                coord = self.__get_surface_coords_from_lat_lng((w['lat'], w['lng']), bounds, race_box)

                button_size = 10

                label = None
                if w['event'] == 'LaunchFighter':
                    label = "L"
                elif w['event'] == 'DockFighter':
                    label = "D"
                elif w['event'] == 'Liftoff':
                    label = "L"
                elif w['event'] == 'Touchdown':
                    label = "T"

                color = constants.COLOR_INTERESTING_3 if progress_wp >= w_index else constants.COLOR_COCKPIT

                if label:
                    pygame.draw.circle(race_box, color, coord, button_size)
                    dot_label = self.normal_font.render(label, False, pygame.Color("black"))
                    dot_label_rect = dot_label.get_rect()
                    dot_label_rect.center = coord
                    race_box.blit(dot_label, dot_label_rect)

                coord_list.append(coord)
                if len(coord_list) > 2:
                    coord_list = coord_list[-2:]

                if len(coord_list) >= 2:
                    pygame.draw.line(race_box, color, coord_list[0], coord_list[1], 2)

            self.surface.blit(race_box, (
                self.surface.get_width() // 2 - race_box.get_width() // 2,
                (self.surface.get_height() // 2 - race_box.get_height() // 2) + (top_pad // 2)
            ))

    @staticmethod
    def __get_surface_coords_from_lat_lng(coord, bounds, surface):

        padding = 0.1

        def get_percent(mi, ma, v):
            total = ma - mi
            amt = v - mi
            return amt / total

        def flip_y(y):
            return surface.get_height() - y

        def pad(v, total):
            return v * (1 - padding * 2) + (padding * total)

        (min_x, min_y), (max_x, max_y) = bounds
        x, y = coord

        new_x = get_percent(min_x, max_x, x)
        new_y = get_percent(min_y, max_y, y)

        new_x = new_x * surface.get_width()
        new_y = new_y * surface.get_height()
        new_y = flip_y(new_y)

        new_x = pad(new_x, surface.get_width())
        new_y = pad(new_y, surface.get_height())

        new_x = math.floor(new_x)
        new_y = math.floor(new_y)

        return new_x, new_y

    def __draw_time(self, start, end):

        text = None


        if end and start:
            elapsed = (end - start)
            text = "{:02}:{:02}:{:02}:{:02} FINISHED".format(elapsed.seconds // 60 // 60, elapsed.seconds // 60, elapsed.seconds,
                                                    elapsed.microseconds // 1000)
        elif start:
            elapsed = (datetime.now() - self.time_start)
            text = "{:02}:{:02}:{:02}:{:02}".format(elapsed.seconds // 60 // 60, elapsed.seconds // 60, elapsed.seconds,
                                                    elapsed.microseconds // 1000)

        if text:
            self.print_line(self.surface, self.h1_font, text, constants.COLOR_COCKPIT)

    def __draw_next_waypoint(self):
        index, _ = self.get_current_waypoint()
        index += 1

        if self.is_race_started():
            next_wp = self.race['waypoints'][index]
        else:
            next_wp = self.race['waypoints'][0]

        if self.journal.get_status():
            lat, lng, rad, alt = self.get_ship_position()
            t_lat = next_wp.get("lat", None)
            t_lng = next_wp.get("lng", None)

            if lat and lng and t_lat and t_lng:
                rad = math.atan2(t_lng - lng, t_lat - lat)
                deg = math.degrees(rad)

                text = "NEXT Lat: {:0.3f} Lng: {:0.3f}, Hdg: {:0.3f}".format(t_lat, t_lng, deg)
                self.print_line(self.surface, self.h1_font, text, constants.COLOR_COCKPIT)



    def perform_draw(self):
        index, _ = self.get_current_waypoint()
        self.__draw_time(self.time_start, self.time_end)
        self.__draw_next_waypoint()
        self.draw_waypoints(self.race['waypoints'], index)



class CreateRaceCard(RaceCard):
    new_map_waypoints = []

    def __init__(self, *args, **kwargs):
        super(CreateRaceCard, self).__init__(*args, **kwargs)
        self.race_create_start_time = datetime.now()
        self.race_name = self.race_create_start_time.strftime("Race %Y%m%d%H%M%S")
        self.race_filename = self.race_create_start_time.strftime("race_%Y%m%d%H%M%S.json")

    def save(self):
        self.journal.config.save_race(self.race_filename, self.race_name, self.new_map_waypoints)

    def perform_build_data(self):
        if len(self.new_map_waypoints) == 0:
            for e in self.journal.events:
                if e['event'] in ['LaunchFighter', 'Liftoff'] and e['timestamp'] > self.race_create_start_time:
                    lat, lng, planet_radius, alt = self.get_ship_position()
                    wp = {"event": e['event'], "lat": lat, "lng": lng}
                    self.new_map_waypoints.append(wp)
                    self.save()
                    break
        else:
            for e in self.journal.events:
                if e['event'] in ['DockFighter', 'Touchdown', 'Pass'] and e['timestamp'] > self.race_create_start_time:
                    lat, lng, planet_radius, alt = self.get_ship_position()
                    wp = {"event": e['event'], "lat": lat, "lng": lng}
                    self.new_map_waypoints.append(wp)
                    self.save()
                    break

    def perform_draw(self):
        self.draw_waypoints(self.new_map_waypoints)
