#!/usr/bin/env python3

import threading
import subprocess
import time

devices = {}


class Killer(threading.Thread):
    def __init__(self, timeout, process):
        threading.Thread.__init__(self)
        self.timeout = timeout
        self.process = process

    def run(self):
        time.sleep(self.timeout)
        self.process.kill()


def parse_manufacturer_specific(data):
    # print(data.hex())
    manufacturer = data[:2]
    data = data[2:]
    if manufacturer == b'L\x00':
        manufacturer = 'apple'

    ty = data[0]
    data = data[1:]
    if ty == 6:
        ty = 'HomeKit'

        ail = data[0]
        # print('{0:08b}'.format(ail))
        advertising_interval = ail >> 5
        # print('{0:08b}'.format(advertising_interval))
        l = ail & 0b00011111
        # print('{0:08b}'.format(l), l)
        data = data[1:]
        # print(l, len(data))

        sf = data[0]
        if sf == 0:
            sf = 'paired'
        elif sf == 1:
            sf = 'unpaired'
        else:
            sf = 'error'
        data = data[1:]

        deviceId = data[:6]
        data = data[6:]

        acid = int.from_bytes(data[:2], byteorder='little')
        data = data[2:]

        gsn = int.from_bytes(data[:2], byteorder='little')
        data = data[2:]

        cn = data[0]
        data = data[1:]

        cv = data[0]
        data = data[1:]
        # print(data.hex())
        return {'manufacturer': manufacturer, 'type': ty, 'sf': sf, 'deviceId': deviceId.hex(), 'acid': acid,
                'gsn': gsn, 'cn': cn, 'cv': cv}

    return {'manufacturer': manufacturer, 'type': ty}


def parseBleMeta(data):
    # print('-' * 80)
    total_length = data[0]
    data = data[1:1 + total_length]

    if total_length != len(data):
        print('length issue', total_length, len(data), ' -- ', data.hex())
        # return

    if not data[0] == 0x02:
        print('No Sub Event: LE Advertising Report', data.hex())
        # return
    data = data[1:]

    if not data[0] == 0x01:
        print('No Num Reports: 1', data.hex())
        # return
    data = data[1:]

    if data[0] == 0x00:
        event_type = 'Connectable Undirected Advertising'
    elif data[0] == 0x03:
        event_type = 'Non-Connectable Undirected Advertising'
    elif data[0] == 0x04:
        event_type = 'Scan Response'
    else:
        print('Unknown Event Type:', data[0], ' -- ', data.hex())
        event_type = 'unknown'
    data = data[1:]

    if data[0] == 0x00:
        # Peer Address Type: Public Device Address (0x00)
        address_type = 'public'
    elif data[0] == 0x01:
        address_type = 'public'
    else:
        print('Unknown Address Type:', data[0], ' -- ', data.hex())
        address_type = 'unknown'
        # return
    data = data[1:]

    mac = data[:6].hex()
    if mac not in devices:
        devices[mac] = {}

    devices[mac]['address_type'] = address_type
    devices[mac]['event_type'] = event_type
    # print('MAC', mac)
    data = data[6:]

    data_length = data[0]
    data = data[1:1 + data_length]
    # print(data.hex())

    while len(data) > 0:
        # print('data', data.hex())
        part_length = data[0]
        data = data[1:]

        part_type = data[0]
        data = data[1:]

        part_data = data[0:part_length - 1]
        data = data[part_length - 1:]

        if part_type == 1:
            devices[mac]['Flags'] = part_data
        elif part_type == 8:
            devices[mac]['Short Device Name'] = part_data
        elif part_type == 9:
            devices[mac]['Device Name'] = part_data.decode('ascii')
        elif part_type == 255:
            devices[mac]['Manufacturer Specific'] = parse_manufacturer_specific(part_data)
        else:
            devices[mac][part_type] = part_data


if __name__ == '__main__':
    # hcitool = HciTool()
    # hcitool.start()
    p0 = subprocess.Popen(['hcitool', 'lescan', '--duplicates'], stdout=subprocess.PIPE)
    Killer(10, p0).start()
    p1 = subprocess.Popen(['hcidump', '--raw', '2>&1'], stdout=subprocess.PIPE)
    Killer(10, p1).start()
    data = None
    for line in p1.stdout:
        if line[0] == 62:
            if data:
                data = data.decode('ascii')
                data = bytes.fromhex(data.replace(' ', ''))
                if data[0] == 0x04 and data[1] == 0x3E:
                    parseBleMeta(data[2:])

            data = line[2:-2]
        elif data is not None:
            data = (data + line[1:-2])
            raw = data

    for mac in devices:
        device = devices[mac]
        if 'Manufacturer Specific' in device \
            and 'type' in device['Manufacturer Specific'] \
            and device['Manufacturer Specific']['type'] == 'HomeKit':
            print('Name: {name}'.format(name=device['Device Name']))
            # print('Url: http_impl://{ip}:{port}'.format(ip=info['address'], port=info['port']))
            print('MAC: {mac}'.format(mac=mac))
            print('Configuration number (c#): {conf}'.format(conf=device['Manufacturer Specific']['cn']))
            # print('Feature Flags (ff): {f} (Flag: {flags})'.format(f=info['flags'], flags=info['ff']))
            print('Device ID (id): {id}'.format(id=device['Manufacturer Specific']['deviceId']))
            # print('Model Name (md): {md}'.format(md=info['md']))
            print('Compatible Version (cv): {cv}'.format(cv=device['Manufacturer Specific']['cv']))
            print('State Number (s#): {sn}'.format(sn=device['Manufacturer Specific']['gsn']))
            print('Status Flags (sf): {sf}'.format(sf=device['Manufacturer Specific']['sf']))
            # print('Category Identifier (ci): {c} (Id: {ci})'.format(c=info['category'], ci=info['ci']))
            print('Category Identifier (ci): (Id: {ci})'.format(ci=device['Manufacturer Specific']['acid']))
            print()
