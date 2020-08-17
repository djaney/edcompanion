import platform
import os


class Config():

    def __init__(self, config_dir=None):
        if config_dir is None:
            if platform.system().lower() == 'linux':
                self.dir = '/home/{}/.local/share/Steam/steamapps/compatdata/359320/pfx/drive_c/users/steamuser/' \
                              'Saved Games/edcompanion'.format(os.environ.get('USER', ''))
            elif platform.system().lower() == 'windows':
                self.dir = '{}\\Saved Games\\edcompanion'.format(os.environ.get('USERPROFILE', ''))
            else:
                raise OSError("Unsupported OS")

        if not os.path.isdir(self.dir):
            os.makedirs(self.dir, exist_ok=True)

    def get_race(self):
        # todo
        pass
