#!/usr/bin/env python3
"""
Soehnle AC500 – BLE Reverse Engineering Helper
Logs alle Notify-Pakete mit Timestamp + zeigt Diffs nach jedem Command.
Ziel: Korrelation zwischen Write-Commands und Notify-Responses finden.
"""

import asyncio
import time
from bleak import BleakClient

BLE_ADDRESS      = "0CA7B1B5-927E-BF3D-5090-7488C2D34676"
UUID_WRITE       = "0000EF01-0000-1000-8000-00805F9B34FB"
UUID_EF02        = "0000EF02-0000-1000-8000-00805F9B34FB"
UUID_EF03        = "0000EF03-0000-1000-8000-00805F9B34FB"
UUID_EF04        = "0000EF04-0000-1000-8000-00805F9B34FB"

COMMANDS = {
    "1":  ("Power ON",       "aa0301000105ee"),
    "2":  ("Power OFF",      "aa0301000004ee"),
    "3":  ("UV-C ON",        "aa0303000107ee"),
    "4":  ("UV-C OFF",       "aa0303000006ee"),
    "5":  ("Night Mode ON",  "aa030600010aee"),
    "6":  ("Night Mode OFF", "aa03af0001b3ee"),
    "7":  ("Fan Speed 1",    "aa0302000005ee"),
    "8":  ("Fan Speed 2",    "aa0302000106ee"),
    "9":  ("Fan Speed 3",    "aa0302000207ee"),
    "10": ("Fan Speed 4",    "aa0302000308ee"),
    "11": ("Auto Mode ON",   "aa0305000109ee"),
    "12": ("Auto Mode OFF",  "aa0305000008ee"),
}

# ── State für Diff-Tracking ─────────────────────────────────────────────────
last: dict[str, bytes] = {"EF02": b"", "EF03": b"", "EF04": b""}
log_file = open(f"./logs/ble_log_{int(time.time())}.txt", "w")

def ts():
    return time.strftime("%H:%M:%S")

def log(msg: str):
    print(msg)
    log_file.write(msg + "\n")
    log_file.flush()

# ── Byte-Diff Visualizer ────────────────────────────────────────────────────
def byte_diff(old: bytes, new: bytes) -> str:
    if not old:
        return "  (first packet)"
    result = []
    max_len = max(len(old), len(new))
    for i in range(max_len):
        o = old[i] if i < len(old) else None
        n = new[i] if i < len(new) else None
        if o != n:
            result.append(f"  byte[{i:02d}]: {f'{o:02x}' if o is not None else '--'} → {f'{n:02x}' if n is not None else '--'}")
    return "\n".join(result) if result else "  (no change)"

# ── EF02 Parser ─────────────────────────────────────────────────────────────
def parse_ef02(data: bytes) -> dict | None:
    if len(data) < 6:
        return None
    if data[0] != 0xAA or data[-1] != 0xEE:
        return None

    result = {
        "header":   f"{data[0]:02x}",
        "len":      data[1],
        "cmd":      data[2:4].hex(),
        "payload":  data[4:-1].hex(),
        "footer":   f"{data[-1]:02x}",
    }

    # Payload-Bytes einzeln aufdröseln
    payload = data[4:-1]
    result["payload_bytes"] = [f"{b:02x}" for b in payload]

    # Checksum-Versuch: XOR aller Bytes zwischen AA und EE
    xor = 0
    for b in data[1:-1]:
        xor ^= b
    result["xor_check"] = f"{xor:02x}"

    # Summen-Checksum-Versuch
    checksum = sum(data[1:-1]) & 0xFF
    result["sum_check"] = f"{checksum:02x}"

    return result

# ── EF04 Parser ─────────────────────────────────────────────────────────────
def parse_ef04(data: bytes) -> dict | None:
    if len(data) < 2:
        return None

    result = {"length": len(data), "raw": data.hex()}

    # Versuche als uint16 big-endian
    if len(data) % 2 == 0:
        values_be = [int.from_bytes(data[i:i+2], "big") for i in range(0, len(data), 2)]
        result["uint16_be"] = values_be

    # Versuche als uint16 little-endian
    if len(data) % 2 == 0:
        values_le = [int.from_bytes(data[i:i+2], "little") for i in range(0, len(data), 2)]
        result["uint16_le"] = values_le

    # Einzelbytes dezimal
    result["bytes_dec"] = list(data)

    return result

# ── Notification Handlers ───────────────────────────────────────────────────
def make_handler(name: str, parser):
    def handler(sender, raw_data: bytearray):
        data = bytes(raw_data)
        changed = data != last[name]
        last[name] = data

        marker = "△ CHANGE" if changed else "  same  "
        log(f"\n{ts()} [{name}] {marker}  raw: {data.hex()}  ({len(data)} bytes)")

        if changed and parser:
            parsed = parser(data)
            if parsed:
                for k, v in parsed.items():
                    log(f"  {k}: {v}")
            diff = byte_diff(last[name], data)  # Note: last already updated above
            # Show diff against previous (we need to track separately)

    return handler

# Better handler with proper previous tracking
previous: dict[str, bytes] = {"EF02": b"", "EF03": b"", "EF04": b""}

def notify_ef02(sender, raw_data: bytearray):
    data = bytes(raw_data)
    changed = data != previous["EF02"]
    diff = byte_diff(previous["EF02"], data)
    previous["EF02"] = data

    marker = "△ CHANGE" if changed else "· same"
    log(f"\n{ts()} [EF02] {marker}  {data.hex()}  ({len(data)}B)")
    if changed:
        log(diff)
        parsed = parse_ef02(data)
        if parsed:
            log(f"  cmd={parsed['cmd']}  payload={parsed['payload']}  xor={parsed['xor_check']}  sum={parsed['sum_check']}")

def notify_ef03(sender, raw_data: bytearray):
    data = bytes(raw_data)
    changed = data != previous["EF03"]
    diff = byte_diff(previous["EF03"], data)
    previous["EF03"] = data

    marker = "△ CHANGE" if changed else "· same"
    log(f"\n{ts()} [EF03] {marker}  {data.hex()}  ({len(data)}B)")
    if changed:
        log(diff)

def notify_ef04(sender, raw_data: bytearray):
    data = bytes(raw_data)
    changed = data != previous["EF04"]
    diff = byte_diff(previous["EF04"], data)
    previous["EF04"] = data

    marker = "△ CHANGE" if changed else "· same"
    log(f"\n{ts()} [EF04] {marker}  {data.hex()}  ({len(data)}B)")
    if changed:
        log(diff)
        parsed = parse_ef04(data)
        if parsed:
            log(f"  uint16_be: {parsed.get('uint16_be')}")
            log(f"  uint16_le: {parsed.get('uint16_le')}")
            log(f"  bytes_dec: {parsed.get('bytes_dec')}")

# ── Menu & Main ─────────────────────────────────────────────────────────────
def print_menu():
    print("\n" + "=" * 50)
    print("  AC500 BLE Analyzer – sende Command, beobachte Notify")
    print("=" * 50)
    for key, (label, cmd) in COMMANDS.items():
        print(f"  [{key:<2}]  {label:<22} {cmd}")
    print("-" * 50)
    print("  [l]   Log-Datei Pfad anzeigen")
    print("  [q]   Quit")
    print("=" * 50)

async def main():
    log(f"=== BLE Analyze Session {time.strftime('%Y-%m-%d %H:%M:%S')} ===")

    async with BleakClient(BLE_ADDRESS) as client:
        log("Verbunden!")

        await client.start_notify(UUID_EF02, notify_ef02)
        await client.start_notify(UUID_EF03, notify_ef03)
        await client.start_notify(UUID_EF04, notify_ef04)
        log("Notify EF02 + EF03 + EF04 aktiv. Warte auf Pakete...\n")

        # Kurz warten um initiale Pakete zu sehen
        await asyncio.sleep(2)

        loop = asyncio.get_event_loop()

        while True:
            print_menu()
            choice = await loop.run_in_executor(None, lambda: input("  Wahl: ").strip().lower())

            if choice == "q":
                break
            elif choice == "l":
                print(f"  → {log_file.name}")
            elif choice in COMMANDS:
                label, data = COMMANDS[choice]
                log(f"\n{'─'*50}")
                log(f"{ts()} ► SEND: {label} ({data})")
                log(f"{'─'*50}")
                await client.write_gatt_char(UUID_WRITE, bytearray.fromhex(data))
                # Kurz warten damit Notify-Antworten ankommen
                await asyncio.sleep(1)
            else:
                print("  Ungültige Eingabe.")

    log_file.close()
    print(f"\nLog gespeichert: {log_file.name}")

asyncio.run(main())
