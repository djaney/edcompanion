import tempfile
from datetime import date, datetime
import json
from collections import OrderedDict
import time
import random
import os
import glob


def get_date_stamp():
    today = date.today()
    return today.strftime('%y%m%d%H%M%d')


def get_timestamp():
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')


def gen_file_header(**kwargs):
    obj = OrderedDict({
        'timestamp': get_timestamp(),
        'event': 'Fileheader',
        'part': kwargs.get('part', 1),
        'language': 'English\\UK',
        'gameversion': 'January Update - Patch 2',
        'build': 'r220863/r0 ',
    })
    return json.dumps(obj)


def gen_scan_body(body_id='', star_system='', body='', terraform_state='', landable=False):
    obj = OrderedDict({
        "timestamp": get_timestamp(),
        "event": "Scan",
        "ScanType": "AutoScan",
        "BodyName": "{} {}".format(star_system, body),
        "BodyID": body_id,
        "Parents": [],
        "StarSystem": star_system,
        "SystemAddress": random.randint(1, 1000000),
        "DistanceFromArrivalLS": random.uniform(1, 100),
        "WasDiscovered": True,
        "WasMapped": False,
        "TidalLock": False,
        "TerraformState": terraform_state,
        "PlanetClass": "Icy body",
        "Atmosphere": "",
        "Landable": landable
    })
    return json.dumps(obj)


def write(file, event):
    func, kwargs = event
    file.write(func(**kwargs) + "\n")

def get_filename(part):
    return os.path.join(
        '.tmp',
        'Journal.{}.{:02d}.log'.format(get_date_stamp(), part),
    )

def main():
    events = [
        (gen_scan_body, {'body': 'A1', 'terraform_state': 'Terraformable'}),
        (gen_scan_body, {'body': 'A2', 'landable': True}),
        (gen_scan_body, {'body': 'A3'}),
    ]
    star_index = 1
    part = 1

    files = glob.glob('.tmp/*')
    for f in files:
        os.remove(f)

    with open(get_filename(part), 'a') as file:
        write(file, (gen_file_header, {'part': part}))

    while True:
        for body_index, (func, args) in enumerate(events):
            star_system = 'Sample Sector - {}'.format(star_index)
            args.update({'star_system': star_system, 'body_id': str(body_index+1) })
            with open(get_filename(part), 'a') as file:
                write(file, (func, args))
            time.sleep(1)
        star_index += 1
        if star_index % 10 == 0:
            part += 1
            with open(get_filename(part), 'a') as file:
                write(file, (gen_file_header, {'part': part}))


if __name__ == "__main__":
    main()
