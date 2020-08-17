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

    def __init__(self, *args, **kwargs):
        super(RaceCard, self).__init__(*args, **kwargs)
        self.init_race()

    def init_race(self):
        self.race = self.journal.get_race()
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

        return index, self.race['waypoints'][index]

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
    def get_distance(a, b, planet_radius):
        units_per_decree = planet_radius * 2 * math.pi / 360
        return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) * units_per_decree

    def get_ship_position(self):
        status = self.journal.get_status()
        lat = status['Latitude'] if 'Latitude' in status else None
        lng = status['Longitude'] if 'Longitude' in status else None
        alt = status['Altitude'] if 'Altitude' in status else None
        # meters
        rad = status['PlanetRadius'] if 'PlanetRadius' in status else 6371000
        return lat, lng, rad, alt

    def perform_build_data(self):

        current_waypoint_index, current_waypoint = self.get_current_waypoint()

        wp_lat = current_waypoint['lat']
        wp_lng = current_waypoint['lng']
        wp_range = current_waypoint['range']
        wp_event = current_waypoint['event']

        if wp_event == 'Pass':
            lat, lng, planet_radius, alt = self.get_ship_position()
            if lat is not None and lng is not None:
                distance = self.get_distance((lat, lng), (wp_lat, wp_lng), planet_radius)
                if distance <= wp_range:
                    self.waypoint_done(current_waypoint_index)
        else:
            for e in self.journal.events:
                if e['event'] == wp_event:
                    lat, lng, planet_radius, alt = self.get_ship_position()
                    if lat is not None and lng is not None:
                        distance = self.get_distance((lat, lng), (wp_lat, wp_lng), planet_radius)
                        if distance <= wp_range:
                            self.waypoint_done(current_waypoint_index)

    def perform_draw(self):
        pass
