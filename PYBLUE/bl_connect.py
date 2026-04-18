import asyncio
from bleak import BleakClient

async def main():
    ble_address = "0CA7B1B5-927E-BF3D-5090-7488C2D34676"

    async with BleakClient(ble_address) as client:
        # we’ll do the read/write operations here
        print("Connected to BLE device")
        print(client.is_connected)

asyncio.run(main())
