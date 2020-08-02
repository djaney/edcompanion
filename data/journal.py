import os
import re
import json
from datetime import datetime


class JournalWatcher:
    def __init__(self, directory=None, watch=None):
        self.directory = directory
        self.last_update = None
        self.last_timestamp = None
        self.__events = []

        if watch is None:
            self.watch = []
        else:
            self.watch = watch

    def __get_journal_files(self):
        """

        :return: sorted by old to new
        """
        # get all journal files
        pattern_journals = re.compile('Journal\.(\d+)\.\d+\.log')
        file_list = os.listdir(self.directory)
        journal_files = list(filter(lambda s: pattern_journals.match(s), file_list))
        return sorted(journal_files)
        # get latest journal
        timestamps = map(lambda s: int(pattern_journals.match(s)[1]), journal_files)
        max_timestamp = max(timestamps)
        # get all latest file
        pattern_latest = re.compile('Journal\.{}\.\d+\.log'.format(max_timestamp))
        return sorted(filter(lambda s: pattern_latest.match(s), journal_files))

    def __journal_event_generator(self, files):

        for filename in files:
            full_path = os.path.join(self.directory, filename)
            file_stat = os.stat(os.path.join(self.directory, full_path))
            # if self.last_update is not None and file_stat.st_mtime < self.last_update:
            #     continue
            with open(full_path, 'r') as fp:
                line = fp.readline()
                while line:
                    try:
                        decoded = json.loads(line)
                        yield decoded
                    except json.decoder.JSONDecodeError:
                        pass
                    line = fp.readline()

    def __parse_timestamp(self, timestamp_string):
        return datetime.strptime(timestamp_string, '%Y-%m-%dT%H:%M:%SZ')

    def __extract(self, *args, **kwargs):
        for e in self.__journal_event_generator(*args, **kwargs):
            ts = self.__parse_timestamp(e['timestamp'])
            if self.last_timestamp is not None and ts <= self.last_timestamp:
                continue
            self.last_timestamp = ts
            event_name = e['event']

            # record events
            if event_name in self.watch:
                self.__events.append(e)

    def has_new(self, last_update=None):

        if last_update is not None:
            self.last_update = last_update

        is_modified = False
        self.__events = []
        files = self.__get_journal_files()
        if len(files) > 0:
            last_file_stat = os.stat(os.path.join(self.directory, files[-1]))
            if self.last_update is None or last_file_stat.st_mtime > self.last_update:
                self.__extract(files[-1:])
                self.last_update = last_file_stat.st_mtime
                is_modified = True

        return is_modified

    @property
    def events(self):
        return self.__events
