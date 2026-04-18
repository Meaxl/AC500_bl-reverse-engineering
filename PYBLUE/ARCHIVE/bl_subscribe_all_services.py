import asyncio
from bleak import BleakClient

ble_address = "0CA7B1B5-927E-BF3D-5090-7488C2D34676"

UUID_WRITE = "0000EF01-0000-1000-8000-00805F9B34FB"
UUID_NOTIFY_EF02 = "0000EF02-0000-1000-8000-00805F9B34FB"
UUID_NOTIFY_EF03 = "0000EF03-0000-1000-8000-00805F9B34FB"
UUID_NOTIFY_EF04 = "0000EF04-0000-1000-8000-00805F9B34FB"

def notification_handler(sender, data):
    print(f"Notify von {sender}: {data.hex()}")

async def main():
    async with BleakClient(ble_address) as client:

        # 1. Notify abonnieren
        await client.start_notify(UUID_NOTIFY_EF02, notification_handler)
        print("Notify EF02 aktiviert - warte auf Daten...")

        await client.start_notify(UUID_NOTIFY_EF03, notification_handler)
        print("Notify EF03 aktiviert - warte auf Daten...")

        await client.start_notify(UUID_NOTIFY_EF04, notification_handler)
        print("Notify EF04 aktiviert - warte auf Daten...")

        # 2. WICHTIG: Script am Leben halten!
        await asyncio.sleep(30)

asyncio.run(main())

