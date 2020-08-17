from overlays import constants
import pygame
from datetime import datetime, timedelta
from overlays.cards.BaseCard import BaseCard


class RaceCard(BaseCard):

    @staticmethod
    def watched():
        return ['LaunchFighter', 'DockFighter', 'Liftoff', 'Touchdown']

    def perform_build_data(self):
        pass

    def perform_draw(self):
        pass