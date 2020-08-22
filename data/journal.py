import time
import os
import re
import json
from datetime import datetime
from data.config import Config


class JournalWatcher:
    is_modified = False
    def __init__(self, directory=None, watch=None, config=None):
        self.directory = directory
        # track file last update
        self.last_update = None
        self.last_status_update = None
        # last line in file
        self.last_line = None
        # last filename
        self.last_filename = None
        self.__events = []
        self.__status = None
        self.__last_status = None
        self.is_include_pass_event = False
        self.has_new_status = False

        if watch is None:
            self.watch = []
        else:
            self.watch = watch

        if config is None:
            self.config = Config()
        else:
            self.config = config

    def include_pass_event(self):
        self.is_include_pass_event = True

    def __get_journal_files(self):
        """
        get all parts of latest file
        :return: sorted by old to new
        """
        # get all journal files
        pattern_journals = re.compile('Journal\.(\d+)\.\d+\.log')
        file_list = os.listdir(self.directory)
        journal_files = list(filter(lambda s: pattern_journals.match(s), file_list))
        # get latest journal
        timestamps = map(lambda s: int(pattern_journals.match(s)[1]), journal_files)
        max_timestamp = max(timestamps)
        # get all latest file
        pattern_latest = re.compile('Journal\.{}\.\d+\.log'.format(max_timestamp))
        return sorted(filter(lambda s: pattern_latest.match(s), journal_files))

    def __journal_event_generator(self, files):

        for filename in files:

            if self.last_filename != filename:
                self.last_filename = filename
                self.last_line = 0

            full_path = os.path.join(self.directory, filename)
            file_stat = os.stat(os.path.join(self.directory, full_path))
            # if self.last_update is not None and file_stat.st_mtime < self.last_update:
            #     continue

            with open(full_path, 'r') as fp:
                current_file_line = 0
                while True:
                    line = fp.readline()
                    current_file_line += 1

                    if self.last_line > current_file_line:
                        continue

                    if not line:
                        break

                    try:
                        decoded = json.loads(line)
                        yield decoded
                    except json.decoder.JSONDecodeError:
                        pass

                self.last_line = current_file_line

    def __parse_timestamp(self, timestamp_string):
        return datetime.strptime(timestamp_string, '%Y-%m-%dT%H:%M:%SZ')

    def __encode_timestamp(self, now):
        return now.strftime('%Y-%m-%dT%H:%M:%SZ')

    def __extract(self, file):
        for e in self.__journal_event_generator([file]):
            event_name = e['event']

            if 'timestamp' in e:
                e['timestamp'] = self.__parse_timestamp(e['timestamp'])
            # record events
            if event_name in self.watch:
                self.__events.append(e)

    def refresh(self):
        self.is_modified = False
        self.__events = []
        files = self.__get_journal_files()
        if len(files) > 0:
            for file in files:
                last_file_stat = os.stat(os.path.join(self.directory, file))
                if self.last_update is None or last_file_stat.st_mtime > self.last_update:
                    self.__extract(file)
                    self.last_update = last_file_stat.st_mtime
                    self.is_modified = True

        if self.is_include_pass_event:
            self.get_status()

            if len(self.__events) > 0:
                timestamp = self.__events[-1]['timestamp']
            else:
                timestamp = datetime.utcnow()

            if self.has_new_status:
                self.__events.append({
                    "timestamp": timestamp,
                    "event": "Pass",
                })
                self.is_modified = True

        return self.is_modified

    def get_route(self):
        path = os.path.join(self.directory, 'NavRoute.json')

        if not os.path.isfile(path):
            return None

        route = None
        with open(path, 'r') as file:
            route = json.load(file)

        if 'Route' not in route:
            return []

        return route['Route']

    def get_status(self):
        file = "status.json"
        file_path = os.path.join(self.directory, file)
        try:
            last_file_stat = os.stat(file_path)
        except FileNotFoundError:
            return None
        self.has_new_status = False
        if self.last_status_update is None or last_file_stat.st_mtime > self.last_status_update:
            for _ in range(10):
                try:
                    with open(file_path, 'r') as fp:
                        tmp = self.__status
                        self.__status = json.load(fp)
                        self.__last_status = tmp
                    self.last_status_update = last_file_stat.st_mtime
                    self.has_new_status = True
                    break
                except json.decoder.JSONDecodeError:
                    time.sleep(0.1)

        return self.__status

    def get_race_details(self):
        return self.config.get_race_details()

    @property
    def events(self):
        return self.__events

    def now(self):
        return datetime.now()