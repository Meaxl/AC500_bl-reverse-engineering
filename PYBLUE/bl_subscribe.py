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
    if len(data) % 2 != 0:
        return None

    values = [
        int.from_bytes(data[i:i+2], "big")
        for i in range(0, len(data), 2)
    ]

    # Paare bilden
    pairs = [
        (values[i], values[i+1])
        for i in range(0, len(values)-1, 2)
    ]

    return {
        "raw_values": values,
        "pairs": pairs,
        "count": len(pairs)
    }
    ####### WORKINGGGG!!
    # if len(data) % 2 != 0:
    #     return None

    # values =[]

    # for i in range(0, len(data), 2):
    #     values.append(int.from_bytes(data[i:i+2], "big"))

    # return values

def OLD_notification_handler_ef02(sender, data):
    print(f"\n[EF02] Raw: {data.hex()}")

    parsed_ef02 = parse_ef02(data)
    if parsed_ef02:
        print(f"[EF02] Parsed: {parsed_ef02}")

last_ef02 = None

def notification_handler_ef02(sender,data):
    global last_ef02

    parsed_ef02 = parse_ef02(data)
    if not parsed_ef02:
        return

    if parsed_ef02 != last_ef02:
        print(f"\n[EF02] CHANGE: {parsed_ef02}")
        last_ef02 = parse_ef02

def notification_handler_ef03(sender, data):
    print(f"\n[EF03] Raw: {data.hex()}")

def notification_handler_ef04(sender, data):
    print(f"\n[EF04] Raw: {data.hex()}")

    if len(data) <= 2:
        print("[EF04] Event Frame:", data.hex())
        return

    parsed_ef04 = parse_ef04(data)

    if parsed_ef04:
        print(f"[EF04] Anzahl Sensoren: {parsed_ef04['count']}")
        for i, (v, r) in enumerate(parsed_ef04["pairs"]):
            print(f"  Sensor {i}: value={v}, ref={r}")
    ########## WWOOOOOOOrRRKING
    # print(f"\n[EF04] Raw: {data.hex()}")

    # # Kurze Pakete ignorieren
    # if len(data) <= 2:
    #     return

    # parsed_ef04 = parse_ef04(data)

    # if parsed_ef04:
    #     print(f"[EF04] Values: {parsed_ef04}")

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

