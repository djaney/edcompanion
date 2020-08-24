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
import requests


class Simulator:
    part = 1
    line_count = 0
    type = None

    def __init__(self, type):
        if type not in ['race', 'exploration']:
            raise NotImplementedError(type + " simulator")
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
            "BodyName": body,
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

        # get systems
        stars = requests.get('https://www.edsm.net/api-v1/sphere-systems?radius=10&showPrimaryStar=1&showCoordinates=1'
                             '&systemName=Sol').json()

        for i, star in enumerate(stars):

            if 'primaryStar' in star:
                star_class = star['primaryStar']['type'].split(" ")[0]
            else:
                star_class = random.choice('KBGFOAMTBH')

            route_dict['Route'].append({
                'StarSystem': star.get('name'),
                'SystemAddress': self.get_system_address(i),
                'StarPos': [star['coords'][j] for j in 'xyz'],
                'StarClass': star_class,
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

    def get_all_scanned(self, **kwargs):
        return json.dumps({
            "timestamp": self.get_timestamp(),
            "event": "FSSAllBodiesFound",
            "SystemName": kwargs.get('name', ''),
            "SystemAddress": 0,
            "Count": kwargs.get('bodyCount', 0)
        })

    def get_saa_scanned(self, **kwargs):
        return json.dumps({
            "timestamp": self.get_timestamp(),
            "event": "SAAScanComplete",
            "BodyName": kwargs.get('name'),
            "SystemAddress": 634950357410,
            "BodyID": kwargs.get('bodyId', 0),
            "ProbesUsed": 10,
            "EfficiencyTarget": 7
        })

    def exploration(self):

        # clear temporary journal
        self.reset()

        # write initial heading
        self.write((self.gen_file_header, {}), sleep=False)
        yield True
        for _ in range(30):
            yield True
        # each loop iteration is one star system
        system_index = 1

        while True:
            # generate route
            route = self.write_route(system_index)
            for r in route['Route']:
                # generate system for each route
                s = requests.get(
                    'https://www.edsm.net/api-system-v1/bodies?systemName={}'.format(r['StarSystem'])).json()

                system_events = []
                for b in s['bodies']:
                    b_dict = {
                        'body_id': b['bodyId'],
                        'body': b['name'],
                        'mapped': False,
                        'discovered': False,
                    }
                    if b['type'] == 'Planet' and 'subType' in b:
                        b_dict['planet_class'] = b['subType']
                    if b['type'] == 'Star' and 'subType' in b:
                        b_dict['star_type'] = b['subType'].split(" ")[0]
                    if b['type'] == 'Planet' and 'terraformingState' in b:
                        b_dict['terraform_state'] = b['terraformingState'] if b[
                                                                                  'terraformingState'] == 'Terraformable' else ''
                    if b['type'] == 'Planet' and 'isLandable' in b:
                        b_dict['landable'] = b['isLandable']
                    system_events.append((self.gen_scan_body, b_dict))
                    system_events.append((self.get_saa_scanned, b))
                # write bodies
                for body_index, (func, args) in enumerate(system_events):
                    star_system = r['StarSystem']

                    args.update({
                        'star_system': star_system,
                        'distance_index': body_index
                    })
                    self.write((func, args), sleep=False)
                    yield True
                    for _ in range(30):
                        yield True
                self.write((self.get_all_scanned, s), sleep=False)
                # jump to next
                system_index += 1

                self.write((self.get_fsd_jump, {'index': system_index}), sleep=False)

                for _ in range(30):
                    yield True
                yield True

    def race(self):

        def status_params(coord, rad):
            return {
                "timestamp": self.get_timestamp(),
                "Latitude": coord[0],
                "Longitude": coord[1],
                "PlanetRadius": rad,
                'BodyName': 'Sample 1'
            }

        def journal_params(event=None):
            return json.dumps({
                "timestamp": self.get_timestamp(),
                "event": event,
            })

        # clear temporary journal
        self.reset()
        self.write((self.gen_file_header, {}))

        # skip frames
        for _ in range(30):
            yield True

        lat = 0
        lng = 0
        heading = 1
        speed = 0.02

        random.seed('funky race')

        iteration = 0
        while True:
            # skip frames
            for _ in range(15):
                yield True

            iteration += 1

            if iteration == 20:
                self.write((journal_params, {"event": "LaunchFighter"}), sleep=False)
                yield True
                continue

            elif iteration == 100:
                self.write((journal_params, {"event": "DockFighter"}), sleep=False)
                yield False
                continue

            heading += random.randrange(-45, 45, 1)
            heading = heading % 360

            rad = math.radians(heading)

            lat += speed * math.cos(rad)
            lng += speed * math.sin(rad)
            self.write_status(status_params((lat, lng), 6371000))
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
