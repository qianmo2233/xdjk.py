import warnings
warnings.filterwarnings('ignore')
import asyncio
import requests
import sys
from bleak import BleakScanner, BleakClient

SERVICE_UUID = '0000ffe0-0000-1000-8000-00805f9b34fb'
CHARACTERISTIC_UUID = '0000ffe1-0000-1000-8000-00805f9b34fb'

async def scan_devices():
    scanner = BleakScanner()
    try:
        devices = await scanner.discover()
        for device in devices:
            if device.name == device_name:
                print('搜索到设备 ', device.name, '\n')
                print('信号强度:', device.rssi, '\n')
                return device.address
        print('\n未搜索到设备，请重试！！！\n')
        return None
    except Exception as e:
        print('\n未扫描到设备，请打开蓝牙并重试！！！\n')
        return None

async def connect_and_write(address, data):
    byte_array = bytearray.fromhex(data)
    try:
        async with BleakClient(address) as client:
            print('连接成功:', client.is_connected, '\n')
            await client.write_gatt_char(CHARACTERISTIC_UUID, byte_array)
            print('电源启动成功！', '\n')
    except Exception as e:
        print('连接设备出错，请重试！！！\n')

async def read_characteristic(address):
    try:
        async with BleakClient(address) as client:
            services = await client.get_services()
            target_service = next((s for s in services if s.uuid == SERVICE_UUID), None)
            if not target_service:
                print('未搜索到服务！\n')
                return (None, None)

            target_char = next((c for c in target_service.characteristics if c.uuid == CHARACTERISTIC_UUID), None)
            if not target_char:
                print('未搜索到特征值！\n')
                return (None, None)

            if 'read' not in target_char.properties:
                print('该特征值不可读！\n')
                return (None, None)

            value = await client.read_gatt_char(target_char.uuid)
            raw_data = value.decode('ascii')
            print('获取到设备信息：', raw_data, '\n')

            data_list = raw_data.split(',')
            if len(data_list) != 13:
                print('获取设备信息错误，请重试！\n')
                return (None, None)

            result = []
            for item in data_list:
                key_value = item.split(':')
                if len(key_value) == 2:
                    result.append(key_value[1])
                else:
                    print('获取设备信息错误，请重试！\n')
                    return (None, None)

            print('获取到设备信息！\n')
            return (result, raw_data)

    except Exception as e:
        print('连接设备出错，请重试！\n')
        return (None, None)

def get_data(data, device_name, info):
    try:
        # TODO: DO IT YOURSELF
        url = 'https://11.451.419.1:9810/apigetdata'
        headers = {'Content-Type': 'application/json'}
        data = {'data': data, 'name': device_name, 'info': info}
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 403:
            print('你不是订阅用户，请联系管理员！！！\n')
            return None
        if response.status_code == 200:
            print('数据获取成功！\n')
            return response.text
        print('获取数据失败！\n')
        return None
    except Exception as e:
        print('获取数据失败！\n')
        return None

# 主流程
print('\n')
device_name = input('请输入设备名称(通常为二维码下面的字符)：')
if not device_name:
    print('设备名称不能为空！\n')
    input('任意键退出...')
    sys.exit()

loop = asyncio.get_event_loop()
print('\n正在搜索蓝牙设备...\n')
device_address = loop.run_until_complete(scan_devices())
if device_address is None:
    input('任意键退出...')
    sys.exit()

print('正在获取设备数据...\n')
data, info = loop.run_until_complete(read_characteristic(device_address))
if data is None or info is None:
    input('任意键退出...')
    sys.exit()

print('正在获取复电数据...\n')
result = get_data(data, device_name, info)
if result is None:
    input('任意键退出...')
    sys.exit()

print('正在启动电源...\n')
loop.run_until_complete(connect_and_write(device_address, result))
input('任意键退出...')