#!/usr/bin/env python3
"""
Soehnle AC500 – BLE Analyze Script v3
Fix: Keep-Alive + Reconnect-Loop für macOS/bleak Bug mit Python 3.10
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

def parse_ef02(data: bytes) -> dict | None:
    if len(data) < 6 or data[0] != 0xAA or data[-1] != 0xEE:
        return None
    payload = data[4:-1]
    return {
        "cmd":     data[2:4].hex(),
        "payload": payload.hex(),
        "bytes":   [f"[{i}]={b:02x}({b:3d})" for i, b in enumerate(payload)],
        "sum":     f"{sum(data[1:-1]) & 0xFF:02x}",
    }

previous: dict[str, bytes] = {"EF02": b"", "EF03": b"", "EF04": b""}
last_notify_time = [time.time()]  # mutable für closure

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
        p = parse_ef02(data)
        if p:
            log(f"  cmd={p['cmd']}  payload={p['payload']}  sum={p['sum']}")
            for b in p["bytes"]:
                log(f"    {b}")

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
    print("\n" + "=" * 52)
    print("  AC500 BLE Analyzer v3")
    print("=" * 52)
    for key, (label, cmd) in COMMANDS.items():
        print(f"  [{key:<2}]  {label:<22} {cmd}")
    print("-" * 52)
    print("  [l]  Log-Pfad  |  [q]  Quit")
    print("=" * 52)
    print("  Wahl: ", end="", flush=True)

async def connect_and_subscribe(client: BleakClient):
    """Verbindet und abonniert alle Notifies."""
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
        # ── Verbindung aufbauen ──────────────────────────────────────────────
        client = BleakClient(BLE_ADDRESS)
        try:
            await connect_and_subscribe(client)
        except BleakError as e:
            log(f"{ts()} Verbindungsfehler: {e} – retry in 3s")
            await asyncio.sleep(3)
            continue

        last_notify_time[0] = time.time()
        print_menu()

        # ── Haupt-Loop ───────────────────────────────────────────────────────
        while True:
            # Auf Input warten, aber maximal 2 Sekunden
            # → danach Verbindungscheck
            try:
                choice = await asyncio.wait_for(input_queue.get(), timeout=2.0)
            except asyncio.TimeoutError:
                # Keep-Alive Check: kein Notify seit >10s → Reconnect
                if time.time() - last_notify_time[0] > 10:
                    log(f"\n{ts()} ⚠ Kein Notify seit >10s – reconnecting...")
                    try:
                        await client.disconnect()
                    except Exception:
                        pass
                    break  # → äußere while-Schleife reconnectet
                continue

            # Verbindung nochmals prüfen vor Write
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
                log(f"\n{'─'*52}")
                log(f"{ts()} ► SEND: {label}  ({data})")
                log(f"{'─'*52}")
                try:
                    await client.write_gatt_char(UUID_WRITE, bytearray.fromhex(data))
                    last_notify_time[0] = time.time()  # Write zählt als Activity
                    await asyncio.sleep(1.5)
                except BleakError as e:
                    log(f"{ts()} ✗ Write fehlgeschlagen: {e} – reconnecting...")
                    break
                print_menu()
            else:
                print(f"  Ungültig: '{choice}'")
                print_menu()

        # Sauber trennen vor Reconnect
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
