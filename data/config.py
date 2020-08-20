import platform
import os
import json


class Config(object):
    RACES_DIR = 'races'
    MAIN_CONFIG = 'config.json'
    CONFIG_ITEMS_MAP = {
        "edsmApiKey": "edsm_api_key"
    }

    __config = {}

    def __init__(self, config_dir=None):
        if config_dir is None:
            if platform.system().lower() == 'linux':
                self.dir = '/home/{}/.edcompanion'.format(os.environ.get('USER', ''))
            elif platform.system().lower() == 'windows':
                self.dir = '{}\\Saved Games\\edcompanion'.format(os.environ.get('USERPROFILE', ''))
            else:
                raise OSError("Unsupported OS")

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

    def select_race(self):
        # todo
        pass

    def get_race_details(self):
        # todo
        pass

    def get_races(self):
        # todo
        pass
