#!/usr/bin/env python3
from screen import Window
from data.journal import JournalWatcher
import pygame
import argparse
import re
from datetime import datetime
from overlays import cards
import platform
import os


def main():

    if platform.system().lower() == 'linux':
        default_dir = '/home/{}/.local/share/Steam/steamapps/compatdata/359320/pfx/drive_c/users/steamuser/' \
                       'Saved Games/Frontier Developments/Elite Dangerous'.format(os.environ.get('USER',''))
    elif platform.system().lower() == 'windows':
        default_dir = '{}\\Saved Games\\Frontier Developments\\Elite Dangerous'\
            .format(os.environ.get('USERPROFILE', ''))
    else:
        default_dir = None

    parser = argparse.ArgumentParser(description='Show overlay for streaming purposes')
    parser.add_argument('activity', type=str, choices=['exploration'], default='exploration')
    parser.add_argument('--time', '-t', type=str, choices=['now', 'all', 'today'], default='now',
                        help='timestamp to start watching the journal')
    parser.add_argument('--background', '-b', type=str, default='black', help='background color name (ex. black)')
    parser.add_argument('--size', '-s', type=str, default='720p', help="[width]x[height] or 720p or 1080p")
    parser.add_argument('--dir', '-d', type=str, default=default_dir, help="path to journal directory")


    args = parser.parse_args()

    if args.time == 'now':
        last_update = datetime.now().timestamp()
    elif args.time == 'today':
        last_update = datetime.now().replace(hour=0, minute=0).timestamp()
    else:
        last_update = None

    journal_path = args.dir

    print('Journal directory: {}'.format(journal_path))
    if args.size == '720p':
        size = (1280, 720)
    elif args.size == '1080p':
        size = (1920, 1080)
    else:
        size_pattern = re.compile("^[0-9]+x[0-9]+$")
        if args.size != '' and size_pattern.match(args.size):
            size = tuple(map(lambda i: int(i), args.size.split("x")))
        else:
            size = None

    win = Window(size=size)

    if args.background != '':
        win.mask_color = pygame.Color(args.background)

    watch_list = []
    card_list = []

    journal = JournalWatcher(
        watch=[],
        directory=journal_path
    )

    if args.activity == 'exploration':
        # exploration card
        card = cards.ExplorationCard(win.screen, journal, position=(0, 1), card_size=(1, 2))
        watch_list += card.watched()
        card_list.append(card)
        # current system card
        card = cards.CurrentSystemCard(win.screen, journal, position=(2, 1), text_align='right', card_size=(1, 2))
        watch_list += card.watched()
        card_list.append(card)
    else:
        raise NotImplementedError("{} not implemented".format(args.activity))

    journal.watch = list(set(watch_list))

    win.screen.fill(win.mask_color)

    while win.loop():
        if journal.has_new(last_update=last_update):
            win.screen.fill(win.mask_color)
            for card in card_list:
                card.render()

        pygame.display.update()


if __name__ == "__main__":

    main()
