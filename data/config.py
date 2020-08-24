import platform
import os
import json
import logging
import sys


def get_config_dir():
    if platform.system().lower() == 'linux':
        config_dir = '/home/{}/.edcompanion'.format(os.environ.get('USER', ''))
    elif platform.system().lower() == 'windows':
        config_dir = '{}\\Saved Games\\edcompanion'.format(os.environ.get('USERPROFILE', ''))
    else:
        raise OSError("Unsupported OS")

    return config_dir


def get_logger_config():
    logs_dir = os.path.join(get_config_dir(), Config.LOGS_DIR)
    os.makedirs(logs_dir, exist_ok=True)
    crash_log = os.path.join(logs_dir, "crash.log")

    return dict(filename=crash_log,
                format='[%(levelname)s][%(asctime)s]  %(message)s',
                datefmt='%H:%M:%S',
                level=logging.ERROR)


class Config(object):
    RACES_DIR = 'races'
    LOGS_DIR = 'logs'
    MAIN_CONFIG = 'config.json'
    CONFIG_ITEMS_MAP = {
        "edsmApiKey": "edsm_api_key"
    }

    __config = {}

    selected_race = None

    def __init__(self, config_dir=None):
        if config_dir is None:
            if platform.system().lower() == 'linux':
                self.dir = '/home/{}/.edcompanion'.format(os.environ.get('USER', ''))
            elif platform.system().lower() == 'windows':
                self.dir = '{}\\Saved Games\\edcompanion'.format(os.environ.get('USERPROFILE', ''))
            else:
                raise OSError("Unsupported OS")
        else:
            self.dir = config_dir

        if not os.path.isdir(self.dir):
            os.makedirs(self.dir, exist_ok=True)

        os.makedirs(os.path.join(self.dir, self.RACES_DIR), exist_ok=True)

    def set(self, key, value):
        if key not in self.CONFIG_ITEMS_MAP.values():
            raise KeyError("key not in {}".format(",".join(self.CONFIG_ITEMS_MAP.values())))

        self.__config[key] = value
        self.save()

    def get(self, key, default=None):
        if key not in self.CONFIG_ITEMS_MAP.values():
            raise KeyError("key not in {}".format(",".join(self.CONFIG_ITEMS_MAP.values())))
        self.load()
        return self.__config.get(key, default)

    def save(self):

        data = {}
        for file_field, class_field in self.CONFIG_ITEMS_MAP.items():
            if class_field in self.__config:
                data[file_field] = self.__config[class_field]

        filename = os.path.join(self.dir, self.MAIN_CONFIG)
        with open(filename, 'w') as fp:
            json.dump(data, fp)

    def load(self):
        filename = os.path.join(self.dir, self.MAIN_CONFIG)
        if os.path.isfile(filename):
            with open(filename, 'r') as fp:
                data = json.load(fp)
            for file_field, class_field in self.CONFIG_ITEMS_MAP.items():
                if file_field in data:
                    self.__config[class_field] = data[file_field]

    def select_race(self, name):
        self.selected_race = name

    def get_race_details(self):
        if not self.selected_race:
            return None
        with open(self.selected_race, 'r') as fp:
            return json.load(fp)

    def save_race(self, filename, name, body, waypoints):
        os.makedirs(os.path.join(self.dir, self.RACES_DIR), exist_ok=True)
        with open(os.path.join(self.dir, self.RACES_DIR, filename), 'w') as fp:
            json.dump({
                "name": name,
                "body": body,
                "waypoints": waypoints
            }, fp)
