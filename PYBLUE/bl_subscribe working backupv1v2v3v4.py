import asyncio
from bleak import BleakClient

ble_address = "0CA7B1B5-927E-BF3D-5090-7488C2D34676"

UUID_WRITE = "0000EF01-0000-1000-8000-00805F9B34FB"
UUID_NOTIFY_EF02 = "0000EF02-0000-1000-8000-00805F9B34FB"
UUID_NOTIFY_EF03 = "0000EF03-0000-1000-8000-00805F9B34FB"
UUID_NOTIFY_EF04 = "0000EF04-0000-1000-8000-00805F9B34FB"

def parse_ef02(data: bytes):
    # Mindestlänge prüfen
    if len(data) < 12:
        return None

    # Header/Footer prüfen
    if data[0] != 0xAA or data[-1] != 0xEE:
        return None

    return {
        "length": data[1],
        "cmd": data[2:4].hex(),
        "mode": int.from_bytes(data[4:6], "little"),
        "flags": int.from_bytes(data[6:8], "little"),
        "value": int.from_bytes(data[8:10], "little"),
    }

def parse_ef04(data: bytes):
    if len(data) < 8:
        return None

    return {
        "v1": int.from_bytes(data[0:2], "big"),
        "v2": int.from_bytes(data[2:4], "big"),
        "v3": int.from_bytes(data[4:6], "big"),
        "v4": int.from_bytes(data[6:8], "big"),
    }

def notification_handler_ef02(sender, data):
    print(f"\n[EF02] Raw: {data.hex()}")

    parsed_ef02 = parse_ef02(data)
    if parsed_ef02:
        print(f"[EF02] Parsed: {parsed_ef02}")

def notification_handler_ef03(sender, data):
    print(f"\n[EF03] Raw: {data.hex()}")

def notification_handler_ef04(sender, data):
    print(f"\n[EF04] Raw: {data.hex()}")

    parsed_ef04 = parse_ef04(data)
    if parsed_ef04:
        print(f"[EF04] Parsed: {parsed_ef04}")
        print(f"[EF04] Wert v1: {parsed_ef04['v1']}")
        print(f"[EF04] Wert v2: {parsed_ef04['v2']}")
        print(f"[EF04] Wert v3: {parsed_ef04['v3']}")
        print(f"[EF04] Wert v4: {parsed_ef04['v4']}")
        #print({"raw": data.hex(), "bytes": list(data)})


async def main():
    async with BleakClient(ble_address) as client:

        # 1. Notify abonnieren
        await client.start_notify(UUID_NOTIFY_EF02, notification_handler_ef02)
        print("Notify EF02 aktiviert - warte auf Daten...")

        await client.start_notify(UUID_NOTIFY_EF03, notification_handler_ef03)
        print("Notify EF03 aktiviert - warte auf Daten...")

        await client.start_notify(UUID_NOTIFY_EF04, notification_handler_ef04)
        print("Notify EF04 aktiviert - warte auf Daten...")

        # 2. WICHTIG: Script am Leben halten!
        await asyncio.sleep(30)

asyncio.run(main())

