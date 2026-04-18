import asyncio
from bleak import BleakClient

async def main():
    ble_address = "0CA7B1B5-927E-BF3D-5090-7488C2D34676"
    characteristic_uuid = "0000EF01-0000-1000-8000-00805F9B34FB"

    async with BleakClient(ble_address) as client:
        data = "aa03af0001b3ee"

        await client.write_gatt_char(characteristic_uuid, bytearray.fromhex(data))

asyncio.run(main())

