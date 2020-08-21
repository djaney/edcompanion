import tempfile
import math
from datetime import date, datetime
import json
from collections import OrderedDict
import time
import random
import os
import glob
import argparse


class Simulator:
    part = 1
    line_count = 0
    type = None

    def __init__(self, type):
        if type not in ['race', 'exploration']:
            raise NotImplementedError(type+ " simulator")
        self.type = type

    def get_generator(self):
        return getattr(self, self.type)()

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
                      star_type=None,
                      planet_class=None,
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
            "DistanceFromArrivalLS": random.uniform(distance_index * 100 + 1, distance_index * 100 + 100),
            "WasDiscovered": discovered,
            "WasMapped": mapped,
            "TidalLock": False,
            "TerraformState": terraform_state,
            "Atmosphere": "",
            "Landable": landable
        })
        if star_type is not None:
            obj['StarType'] = star_type
        if planet_class is not None:
            obj['PlanetClass'] = planet_class
        return json.dumps(obj)

    def write_route(self, start):

        route_dict = {
            'timestamp': self.get_timestamp(),
            'event': 'NavRoute',
            'Route': []
        }

        for i in range(start, start + random.randint(3, 30)):
            system_name = self.get_system_name(i)
            route_dict['Route'].append({
                'StarSystem': system_name,
                'SystemAddress': self.get_system_address(i),
                'StarPos': self.get_star_pos(i),
                'StarClass': random.choice('KBGFOAMTBH'),
            })

        with open('.tmp/NavRoute.json', 'w') as file:
            json.dump(route_dict, file)

        def route_event():
            return json.dumps({"timestamp": self.get_timestamp(), "event": "NavRoute"})

        self.write((route_event, {}))

        return route_dict

    def write(self, event, sleep=True):
        func, kwargs = event
        with open(self.get_filename(), 'a') as file:
            line = func(**kwargs)
            file.write(line + "\n")
            print(line)
        self.line_count += 1
        if sleep:
            time.sleep(0.5)

        if self.line_count % 10 == 0:
            self.part += 1
            self.write((self.gen_file_header, {}), sleep=sleep)

    def write_status(self, event):
        with open(os.path.join('.tmp', 'status.json'), 'w') as file:
            json.dump(event, file)
        print(event)

    def get_filename(self):
        return os.path.join(
            '.tmp',
            'Journal.{}.{:02d}.log'.format(self.get_date_stamp(), self.part),
        )

    def get_system_name(self, index):
        return 'Sample Sector - {}'.format(index)

    def get_system_address(self, index):
        return index

    def get_star_pos(self, index):
        return [500 * index, 500 * index, 500 * index]

    def get_fsd_jump(self, index):
        return json.dumps(
            {"timestamp": self.get_timestamp(), "event": "FSDJump", "StarSystem": self.get_system_name(index),
             "SystemAddress": self.get_system_address(index), "StarPos": self.get_star_pos(index),
             "SystemAllegiance": "",
             "SystemEconomy": "$economy_None;", "SystemEconomy_Localised": "None",
             "SystemSecondEconomy": "$economy_None;", "SystemSecondEconomy_Localised": "None",
             "SystemGovernment": "$government_None;", "SystemGovernment_Localised": "None",
             "SystemSecurity": "$GAlAXY_MAP_INFO_state_anarchy;", "SystemSecurity_Localised": "Anarchy",
             "Population": 0, "Body": self.get_system_name(index) + " A", "BodyID": 1,
             "BodyType": "Star", "JumpDist": 54.522,
             "FuelUsed": 10, "FuelLevel": 50})

    def exploration(self):

        # clear temporary journal
        self.reset()

        # write initial heading
        self.write((self.gen_file_header, {}))

        # each loop iteration is one star system
        system_index = 1

        while True:
            # generate route
            route = self.write_route(system_index)
            for r in route['Route']:
                # generate system for each route
                system_events = [
                    (self.gen_scan_body, {'body_id': 6, 'body': 'A5', 'mapped': False, 'planet_class': 'Icy Body'}),
                    (self.gen_scan_body, {'body_id': 1, 'body': 'A', 'star_type': r['StarClass']}),
                    (self.gen_scan_body,
                     {'body_id': 2, 'body': 'A1', 'terraform_state': 'Terraformable', 'planet_class': 'Icy Body'}),
                    (self.gen_scan_body, {'body_id': 3, 'body': 'A2', 'landable': True, 'planet_class': 'Icy Body'}),
                    (self.gen_scan_body, {'body_id': 4, 'body': 'A3', 'planet_class': 'Earth-like world'}),
                    (self.gen_scan_body, {'body_id': 5, 'body': 'A4', 'discovered': False, 'planet_class': 'Icy Body'}),
                ]
                # write bodies
                for body_index, (func, args) in enumerate(system_events):
                    star_system = self.get_system_name(system_index)

                    args.update({
                        'star_system': star_system,
                        'distance_index': body_index
                    })
                    self.write((func, args))
                # jump to next
                system_index += 1
                self.write((self.get_fsd_jump, {'index': system_index}))

    def race(self):

        def status_params(coord, rad):
            return {
                "timestamp": self.get_timestamp(),
                "Latitude": coord[0],
                "Longitude": coord[1],
                "PlanetRadius": rad,
            }

        def journal_params(event=None):
            return json.dumps({
                "timestamp": self.get_timestamp(),
                "event": event,
            })

        # clear temporary journal
        self.reset()
        self.write((self.gen_file_header, {}))
        lat = 0
        lng = 0
        heading = 1
        speed = 0.02
        self.write_status(status_params((lat, lng), 5000))
        self.write((journal_params, {"event": "LaunchFighter"}), sleep=False)

        yield True

        random.seed('funky race')

        iteration = 0
        while True:
            # skip frames
            for _ in range(30):
                yield True

            iteration += 1
            if iteration == 100:
                self.write((journal_params, {"event": "DockFighter"}), sleep=False)
                yield False
                continue

            heading += random.randrange(-45, 45, 1)
            heading = heading % 360

            rad = math.radians(heading)

            lat += speed * math.cos(rad)
            lng += speed * math.sin(rad)
            self.write_status(status_params((lat, lng), 5000))
            yield True

    def reset(self):
        files = glob.glob('.tmp/*')
        for f in files:
            os.remove(f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Simulator')
    parser.add_argument('activity', type=str, choices=['exploration', 'race'])
    args = parser.parse_args()
    if args.activity == 'exploration':
        Simulator().exploration()
    elif args.activity == 'race':
        Simulator().race()
