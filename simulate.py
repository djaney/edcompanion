import tempfile
from datetime import date, datetime
import json
from collections import OrderedDict
import time
import random
import os
import glob


class Simulator:
    part = 1
    line_count = 0

    def get_date_stamp(self):
        today = date.today()
        return today.strftime('%y%m%d%H%M%d')

    def get_timestamp(self):
        return datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

    def gen_file_header(self, **kwargs):
        obj = OrderedDict({
            'timestamp': self.get_timestamp(),
            'event': 'Fileheader',
            'part': self.part,
            'language': 'English\\UK',
            'gameversion': 'January Update - Patch 2',
            'build': 'r220863/r0 ',
        })
        return json.dumps(obj)

    def gen_scan_body(self,
                      body_id='',
                      star_system='',
                      body='',
                      terraform_state='',
                      landable=False,
                      discovered=True,
                      mapped=True,
                      distance_index=1):
        obj = OrderedDict({
            "timestamp": self.get_timestamp(),
            "event": "Scan",
            "ScanType": "AutoScan",
            "BodyName": "{} {}".format(star_system, body),
            "BodyID": body_id,
            "Parents": [],
            "StarSystem": star_system,
            "SystemAddress": random.randint(1, 1000000),
            "DistanceFromArrivalLS": random.uniform(distance_index*100+1, distance_index*100+100),
            "WasDiscovered": discovered,
            "WasMapped": mapped,
            "TidalLock": False,
            "TerraformState": terraform_state,
            "PlanetClass": "Icy body",
            "Atmosphere": "",
            "Landable": landable
        })
        return json.dumps(obj)

    def write(self, event):
        func, kwargs = event
        with open(self.get_filename(), 'a') as file:
            line = func(**kwargs)
            file.write(line + "\n")
            print(line)
        self.line_count += 1
        time.sleep(0.5)

        if self.line_count % 10 == 0:
            self.part += 1
            self.write((self.gen_file_header, {}))

    def get_filename(self):
        return os.path.join(
            '.tmp',
            'Journal.{}.{:02d}.log'.format(self.get_date_stamp(), self.part),
        )

    def simulate(self):
        system_events = [
            (self.gen_scan_body, {'body': 'A1', 'terraform_state': 'Terraformable'}),
            (self.gen_scan_body, {'body': 'A2', 'landable': True}),
            (self.gen_scan_body, {'body': 'A3'}),
            (self.gen_scan_body, {'body': 'A4', 'discovered': False}),
            (self.gen_scan_body, {'body': 'A5', 'mapped': False}),
        ]


        # clear temporary journal
        files = glob.glob('.tmp/*')
        for f in files:
            os.remove(f)

        # write initial heading
        self.write((self.gen_file_header, {}))

        # each loop iteration is one star system
        system_index = 1
        while True:
            # write system events
            for body_index, (func, args) in enumerate(system_events):
                star_system = 'Sample Sector - {}'.format(system_index)
                args.update({
                    'star_system': star_system,
                    'body_id': str(body_index + 1),
                    'distance_index': body_index
                })
                self.write((func, args))
            system_index += 1


if __name__ == "__main__":
    Simulator().simulate()
