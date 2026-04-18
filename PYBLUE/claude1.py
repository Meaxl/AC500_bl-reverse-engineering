#!/usr/bin/env python3
"""
Soehnle Airfresh Clean Connect 500 – BLE Control Script (macOS)
Device UUID (macOS): 0CA7B1B5-927E-BF3D-5090-7488C2D34676
Write Characteristic: 0000EF01-0000-1000-8000-00805F9B34FB
"""

import asyncio
from bleak import BleakClient

BLE_ADDRESS         = "0CA7B1B5-927E-BF3D-5090-7488C2D34676"
CHARACTERISTIC_UUID = "0000EF01-0000-1000-8000-00805F9B34FB"

COMMANDS = {
    # Power
    "1":  ("Power ON",       "aa0301000105ee"),
    "2":  ("Power OFF",      "aa0301000004ee"),
    # UV-C
    "3":  ("UV-C ON",        "aa0303000107ee"),
    "4":  ("UV-C OFF",       "aa0303000006ee"),
    # Night Mode
    "5":  ("Night Mode ON",  "aa030600010aee"),
    "6":  ("Night Mode OFF", "aa03af0001b3ee"),
    # Fan Speed
    "7":  ("Fan Speed 1",    "aa0302000005ee"),
    "8":  ("Fan Speed 2",    "aa0302000106ee"),
    "9":  ("Fan Speed 3",    "aa0302000207ee"),
    "10": ("Fan Speed 4",    "aa0302000308ee"),
    # Auto Mode
    "11": ("Auto Mode ON",   "aa0305000109ee"),
    "12": ("Auto Mode OFF",  "aa0305000008ee"),
}

def print_menu():
    print("\n" + "=" * 45)
    print("  Soehnle Airfresh Clean Connect 500")
    print("=" * 45)
    for key, (label, cmd) in COMMANDS.items():
        print(f"  [{key:<2}]  {label:<22} {cmd}")
    print("-" * 45)
    print("  [q]   Quit")
    print("=" * 45)

async def main():
    async with BleakClient(BLE_ADDRESS) as client:
        print("  Connected!")

        while True:
            print_menu()
            choice = input("  Enter choice: ").strip().lower()

            if choice == "q":
                print("  Bye!")
                break
            elif choice in COMMANDS:
                label, data = COMMANDS[choice]
                await client.write_gatt_char(CHARACTERISTIC_UUID, bytearray.fromhex(data))
                print(f"  Sent: {label}")
            else:
                print("  Invalid choice, try again.")

asyncio.run(main())
