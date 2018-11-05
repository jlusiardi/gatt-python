import gatt.gatt_linux
import binascii

# OpCodes (table 6-7 page 97)
HAP_CHAR_SIG_READ = 1
HAP_CHAR_WRITE = 2
HAP_CHAR_READ = 3
HAP_CHAR_TIMED_WRITE = 4
HAP_CHAR_EXEC_WRITE = 5
HAP_SERVICES_SIG_READ = 6



ServiceInstanceId = 'e604e95d-a759-4817-87d3-aa005083a0d1'
HAP_Accessory_Information_Service = '0000003e-0000-1000-8000-0026bb765291'
HAP_Battery_Service = '00000096-0000-1000-8000-0026bb765291'
HAP_SERVICE_SIG_CHAR = '000000a5-0000-1000-8000-0026bb765291'
HAP_BLE_2_0_Protocol_Information_Service = '000000a2-0000-1000-8000-0026bb765291'
CHAR_VERSION = '00000037-0000-1000-8000-0026bb765291'
CHAR_SERIAL_NUMBER = '00000030-0000-1000-8000-0026bb765291'
CHAR_BATTERYY_LEVEL = '00000068-0000-1000-8000-0026bb765291'
HAP_Contact_Sensor_Service = '00000080-0000-1000-8000-0026bb765291'
CHAR_NAME = '00000023-0000-1000-8000-0026bb765291'
HAP_PAIRING_SERVICE='00000055-0000-1000-8000-0026bb765291'
CharacteristicInstanceID='dc46f0fe-81d2-4616-b5d9-6abdd796939a'

def parse_sig_read_response(data, tid):
    print('\t', data[0]==2, data[1] == tid, data[2] == 0)
    length = int.from_bytes(data[3:5], byteorder='little')
    #print(data[5:7])

    # chr type
    chr_type = [int(a) for a in data[7:23]]
    chr_type.reverse()
    chr_type = ''.join('%02x' % b for b in chr_type)

    svc_id = int.from_bytes(data[25:27], byteorder='little')

    svc_type = [int(a) for a in data[29:45]]
    svc_type.reverse()
    svc_type = ''.join('%02x' % b for b in svc_type)

    if int(data[45]) == 10:
        chr_prop = [int(a) for a in data[47:49]]
        chr_prop.reverse()
        chr_prop = ''.join('%02x' % b for b in chr_prop)
    else:
        chr_prop = None

    desc = ''
    if int(data[49]) == 11:
        d_length = int(data[50])
        for i in data[51:51+d_length]:
            desc += str(i).encode("utf-8").decode("utf-8")
        print('desc len ', d_length, desc)

    print('\t', 'chr_type', chr_type, 'svc_id', svc_id, 'svc_type', svc_type, 'chr_prop', chr_prop, 'desc', desc)


    pass

class AnyDevice(gatt.gatt_linux.Device):
    def services_resolved(self):
        print('resolved')
        super().services_resolved()

        for service in self.services:
            print('S', service.uuid)
            # if service.uuid == HAP_PAIRING_SERVICE:
                # print(service, service.uuid)
            for characteristic in service.characteristics:
                if characteristic.uuid == ServiceInstanceId:
                    print('\t', 'C', 'ServiceInstanceId', int.from_bytes(characteristic.read_value(), byteorder='little'))
                else:
                    print('\t', 'C', characteristic.uuid)
                cid = None
                for descriptor in characteristic.descriptors:
                    value = descriptor.read_value()
                    if descriptor.uuid == CharacteristicInstanceID:
                        cid = int.from_bytes(value, byteorder='little')
                        print('\t\t', 'D', 'CharacteristicInstanceID', cid)
                    else:
                        print('\t\t', 'D', descriptor.uuid, value)
                if cid:
                    v = cid.to_bytes(length=2, byteorder='little')

                    tid = 42
                    characteristic.write_value([0x00, 0x01, tid, v[0], v[1]])
                    parse_sig_read_response(characteristic.read_value(), tid)

                    # if characteristic.uuid == '00000068-0000-1000-8000-0026bb765291':
                    #     print(characteristic)
                    # if characteristic.uuid == CHAR_NAME:
                    #     # print('write to ', service, characteristic)
                    #     # characteristic.write_value([0x00, 0x01, 0x02, 0x5D, 0x00])
                    #     characteristic.write_value([0x00, 0x01, 0x02, 0x5E, 0x00])
                    # if characteristic.uuid == ServiceInstanceId:
                    #     print('Servcie Instance ID', characteristic.uuid, int.from_bytes(characteristic.read_value(), byteorder='little'))
                    #     #characteristic.write_value('Hello\n'.encode('utf-8'))
                    #     pass

    # def characteristic_write_value_failed(self, characteristic, error):
    #     print('\t\tcharacteristic_write_value_failed', characteristic, error)
    #
    # def characteristic_write_value_succeeded(self, characteristic):
    #     print('\t\tcharacteristic_write_value_succeeded', characteristic)
    #     characteristic.read_value()
    #
    # def characteristic_read_value_failed(self, characteristic, error):
    #     print('\t\tcharacteristic_read_value_failed', characteristic, error)
    #
    # def characteristic_value_updated(self, characteristic, value):
    #     if characteristic.uuid == ServiceInstanceId:
    #         print('\t\tcharacteristic_value_updated', characteristic, value, int.from_bytes(value, byteorder='little'))
    #     else:
    #         print('\t\tcharacteristic_value_updated', characteristic, binascii.hexlify(value))
    #
    # def descriptor_read_value_failed(self, descriptor, error):
    #     print('descriptor_read_value_failed', descriptor, error)
    #     pass
    #
    # def descriptor_value_updated(self, descriptor, value):
    #     print('descriptor_value_updated', descriptor, value)
    #     pass

manager = gatt.DeviceManager(adapter_name='hci0')

device = AnyDevice(manager=manager, mac_address='DE:7C:84:60:71:5C')
device.connect()

try:
    manager.run()
except:
    device.disconnect()
