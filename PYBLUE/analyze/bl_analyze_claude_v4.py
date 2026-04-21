#!/usr/bin/env python3
"""
Soehnle AC500 – BLE Analyze Script v3
Vollständig dekodiertes Protokoll inkl. Timer-Funktion.
"""

import asyncio
import threading
import time
import os
from bleak import BleakClient, BleakError

BLE_ADDRESS = "0CA7B1B5-927E-BF3D-5090-7488C2D34676"
UUID_WRITE  = "0000EF01-0000-1000-8000-00805F9B34FB"
UUID_EF02   = "0000EF02-0000-1000-8000-00805F9B34FB"
UUID_EF03   = "0000EF03-0000-1000-8000-00805F9B34FB"
UUID_EF04   = "0000EF04-0000-1000-8000-00805F9B34FB"

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
    # Timer
    "13": ("Timer OFF",      "aa0304000007ee"),
    "14": ("Timer 2h",       "aa0304000209ee"),
    "15": ("Timer 4h",       "aa030400040bee"),
    "16": ("Timer 8h",       "aa030400080fee"),
}

# ── EF02 Frame Layout ───────────────────────────────────────────────────────
# aa 0d a0 21 | p0   p1   p2   p3   p4   p5   p6   p7   p8   p9   p10  p11 | ee
#               spd  tmr  flg  00   aqi  00   adc  10   e0   02   d5   chk
#
# p[0]  fan speed:  0x00=Spd1 0x01=Spd2 0x02=Spd3 0x03=Spd4
# p[1]  timer hrs:  0x00=off  0x02=2h   0x04=4h   0x08=8h
# p[2]  flags:      bit0=Power bit1=UVC bit2=Timer bit5=Auto bit6+7=Night
# p[4]  AQI sensor: 0–255
# p[11] checksum:   (p0+p1+p2+p4+p6+p10+0xC0) & 0xFF

FLAG_POWER = 0x01
FLAG_UVC   = 0x02
FLAG_TIMER = 0x04
FLAG_AUTO  = 0x20
FLAG_NIGHT = 0xC0

TIMER_LABELS = {0x00: "OFF", 0x02: "2h", 0x04: "4h", 0x08: "8h"}
SPEED_LABELS = {0: "Spd1", 1: "Spd2", 2: "Spd3", 3: "Spd4"}

os.makedirs("./logs", exist_ok=True)
log_path = f"./logs/ble_log_{int(time.time())}.txt"
log_file = open(log_path, "w")

def ts():
    return time.strftime("%H:%M:%S")

def log(msg: str):
    print(msg)
    log_file.write(msg + "\n")
    log_file.flush()

def byte_diff(old: bytes, new: bytes) -> str:
    if not old:
        return "  (first packet)"
    result = []
    for i in range(max(len(old), len(new))):
        o = old[i] if i < len(old) else None
        n = new[i] if i < len(new) else None
        if o != n:
            o_s = f"{o:02x}" if o is not None else "--"
            n_s = f"{n:02x}" if n is not None else "--"
            result.append(f"  byte[{i:02d}]: {o_s} → {n_s}")
    return "\n".join(result) if result else "  (no change)"

def parse_ef02(data: bytes) -> str | None:
    if len(data) != 17 or data[0] != 0xAA or data[-1] != 0xEE:
        return None
    p = data[4:-1]

    # Checksum verify
    expected = (p[0]+p[1]+p[2]+p[4]+p[6]+p[10]+0xC0) & 0xFF
    chk_ok = "✓" if expected == p[11] else f"✗(exp {expected:02x})"

    flags = p[2]
    power = "ON " if flags & FLAG_POWER else "OFF"
    uvc   = "ON " if flags & FLAG_UVC   else "OFF"
    timer_on = bool(flags & FLAG_TIMER)
    auto  = "ON " if flags & FLAG_AUTO  else "OFF"
    night = "ON " if flags & FLAG_NIGHT else "OFF"
    speed = SPEED_LABELS.get(p[0], f"0x{p[0]:02x}")
    timer = TIMER_LABELS.get(p[1], f"0x{p[1]:02x}") if timer_on else "OFF"
    aqi   = p[4]

    return (f"  Power={power}  Speed={speed}  UVC={uvc}  "
            f"Night={night}  Auto={auto}  Timer={timer}  "
            f"AQI={aqi}  chk={chk_ok}")

previous: dict[str, bytes] = {"EF02": b"", "EF03": b"", "EF04": b""}
last_notify_time = [time.time()]

def notify_ef02(sender, raw: bytearray):
    last_notify_time[0] = time.time()
    data = bytes(raw)
    changed = data != previous["EF02"]
    diff = byte_diff(previous["EF02"], data)
    previous["EF02"] = data
    m = "△ CHANGE" if changed else "· same  "
    log(f"{ts()} [EF02] {m}  {data.hex()}  ({len(data)}B)")
    if changed:
        log(diff)
        decoded = parse_ef02(data)
        if decoded:
            log(decoded)

def notify_ef03(sender, raw: bytearray):
    last_notify_time[0] = time.time()
    data = bytes(raw)
    changed = data != previous["EF03"]
    diff = byte_diff(previous["EF03"], data)
    previous["EF03"] = data
    m = "△ CHANGE" if changed else "· same  "
    log(f"{ts()} [EF03] {m}  {data.hex()}  ({len(data)}B)")
    if changed:
        log(diff)

def notify_ef04(sender, raw: bytearray):
    last_notify_time[0] = time.time()
    data = bytes(raw)
    changed = data != previous["EF04"]
    diff = byte_diff(previous["EF04"], data)
    previous["EF04"] = data
    m = "△ CHANGE" if changed else "· same  "
    log(f"{ts()} [EF04] {m}  {data.hex()}  ({len(data)}B)")
    if changed:
        log(diff)
        if len(data) >= 4 and len(data) % 2 == 0:
            be = [int.from_bytes(data[i:i+2], "big") for i in range(0, len(data), 2)]
            le = [int.from_bytes(data[i:i+2], "little") for i in range(0, len(data), 2)]
            log(f"  uint16_be: {be}")
            log(f"  uint16_le: {le}")
            log(f"  bytes_dec: {list(data)}")

# ── Input via Thread + Queue ─────────────────────────────────────────────────
input_queue: asyncio.Queue = asyncio.Queue()

def input_thread(loop: asyncio.AbstractEventLoop):
    while True:
        try:
            line = input()
            asyncio.run_coroutine_threadsafe(input_queue.put(line.strip().lower()), loop)
        except EOFError:
            asyncio.run_coroutine_threadsafe(input_queue.put("q"), loop)
            break

def print_menu():
    print("\n" + "=" * 56)
    print("  AC500 BLE Analyzer v3  –  vollständiges Protokoll")
    print("=" * 56)
    for key, (label, cmd) in COMMANDS.items():
        print(f"  [{key:<2}]  {label:<22} {cmd}")
    print("-" * 56)
    print("  [l]  Log-Pfad  |  [q]  Quit")
    print("=" * 56)
    print("  Wahl: ", end="", flush=True)

async def connect_and_subscribe(client: BleakClient):
    await client.connect()
    await client.start_notify(UUID_EF02, notify_ef02)
    await client.start_notify(UUID_EF03, notify_ef03)
    await client.start_notify(UUID_EF04, notify_ef04)
    log(f"{ts()} Verbunden & Notify aktiv.")

async def main():
    log(f"=== BLE Analyze Session {time.strftime('%Y-%m-%d %H:%M:%S')} ===")
    loop = asyncio.get_event_loop()
    threading.Thread(target=input_thread, args=(loop,), daemon=True).start()
    quit_flag = False

    while not quit_flag:
        client = BleakClient(BLE_ADDRESS)
        try:
            await connect_and_subscribe(client)
        except BleakError as e:
            log(f"{ts()} Verbindungsfehler: {e} – retry in 3s")
            await asyncio.sleep(3)
            continue

        last_notify_time[0] = time.time()
        print_menu()

        while True:
            try:
                choice = await asyncio.wait_for(input_queue.get(), timeout=2.0)
            except asyncio.TimeoutError:
                if time.time() - last_notify_time[0] > 10:
                    log(f"\n{ts()} ⚠ Kein Notify seit >10s – reconnecting...")
                    try:
                        await client.disconnect()
                    except Exception:
                        pass
                    break
                continue

            if not client.is_connected:
                log(f"\n{ts()} ⚠ Verbindung verloren – reconnecting...")
                break

            if choice == "q":
                quit_flag = True
                log("Beende Session.")
                break
            elif choice == "l":
                print(f"\n  Log: {log_path}")
                print_menu()
            elif choice in COMMANDS:
                label, data = COMMANDS[choice]
                log(f"\n{'─'*56}")
                log(f"{ts()} ► SEND: {label}  ({data})")
                log(f"{'─'*56}")
                try:
                    await client.write_gatt_char(UUID_WRITE, bytearray.fromhex(data))
                    last_notify_time[0] = time.time()
                    await asyncio.sleep(1.5)
                except BleakError as e:
                    log(f"{ts()} ✗ Write fehlgeschlagen: {e} – reconnecting...")
                    break
                print_menu()
            else:
                print(f"  Ungültig: '{choice}'")
                print_menu()

        if not quit_flag:
            try:
                await client.disconnect()
            except Exception:
                pass
            log(f"{ts()} Reconnect in 2s...")
            await asyncio.sleep(2)

    try:
        await client.disconnect()
    except Exception:
        pass
    log_file.close()
    print(f"\nLog gespeichert: {log_path}")

asyncio.run(main())
