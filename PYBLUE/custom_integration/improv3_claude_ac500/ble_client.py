"""BLE client + state parser for Soehnle AC500."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Callable

from bleak import BleakClient, BleakError

from .const import (
    UUID_WRITE, UUID_EF02, UUID_EF04,
    FLAG_POWER, FLAG_UVC, FLAG_TIMER, FLAG_AUTO, FLAG_NIGHT,
    SPEED_MAP, COMMANDS,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class AC500State:
    # ── Control state (from EF02) ────────────────────────────────────────
    power:      bool  = False
    uvc:        bool  = False
    night:      bool  = False
    auto:       bool  = False
    timer_on:   bool  = False
    speed:      int   = 0       # 0-3
    timer_val:  int   = 0       # 0 / 2 / 4 / 8  (hours)
    pm25_raw:   int   = 0       # raw; divide by 10 for µg/m³
    # ── Environmental sensors (from EF04 snapshot on connect) ───────────
    temperature: float | None = None   # °C
    humidity:    int   | None = None   # % RH (unconfirmed)
    # ── Availability ────────────────────────────────────────────────────
    available:  bool  = False

    @property
    def pm25(self) -> float:
        """PM2.5 in µg/m³ (one decimal place)."""
        return round(self.pm25_raw / 10, 1)

    @property
    def timer_hours(self) -> int:
        return self.timer_val if self.timer_on else 0

    def parse_ef02(self, data: bytes) -> bool:
        """Parse EF02 frame. Returns True if state changed."""
        if len(data) != 17 or data[0] != 0xAA or data[-1] != 0xEE:
            return False
        p = data[4:-1]
        expected = (p[0]+p[1]+p[2]+p[4]+p[6]+p[10]+0xC0) & 0xFF
        if expected != p[11]:
            _LOGGER.warning("EF02 checksum mismatch: expected 0x%02x got 0x%02x", expected, p[11])
            return False

        old = (self.power, self.uvc, self.night, self.auto,
               self.timer_on, self.timer_val, self.speed, self.pm25_raw)

        flags           = p[2]
        self.power      = bool(flags & FLAG_POWER)
        self.uvc        = bool(flags & FLAG_UVC)
        self.night      = bool(flags & FLAG_NIGHT)
        self.auto       = bool(flags & FLAG_AUTO)
        self.timer_on   = bool(flags & FLAG_TIMER)
        self.speed      = p[0]
        self.timer_val  = p[1]
        self.pm25_raw   = p[4]
        self.available  = True

        new = (self.power, self.uvc, self.night, self.auto,
               self.timer_on, self.timer_val, self.speed, self.pm25_raw)
        return old != new

    def parse_ef04(self, data: bytes) -> bool:
        """Parse EF04 snapshot. Returns True if temperature/humidity changed."""
        if len(data) < 4 or len(data) % 2 != 0:
            return False
        pairs = [int.from_bytes(data[i:i+2], "big") for i in range(0, len(data), 2)]

        old_temp = self.temperature
        old_hum  = self.humidity

        # pair[1] = Temperature ÷10 °C  (confirmed across multiple sessions)
        if len(pairs) >= 2 and pairs[1] != 0xFFFF:
            self.temperature = round(pairs[1] / 10, 1)

        # pair[4] = Humidity % RH  (unconfirmed – plausible 36% indoor)
        if len(pairs) >= 5 and pairs[4] != 0xFFFF and pairs[4] < 100:
            self.humidity = pairs[4]

        return self.temperature != old_temp or self.humidity != old_hum


class AC500BleClient:
    def __init__(self, address: str) -> None:
        self._address   = address
        self._client: BleakClient | None = None
        self._lock      = asyncio.Lock()
        self.state      = AC500State()
        self._callbacks: list[Callable] = []

    def register_callback(self, cb: Callable) -> None:
        self._callbacks.append(cb)

    def unregister_callback(self, cb: Callable) -> None:
        if cb in self._callbacks:
            self._callbacks.remove(cb)

    async def connect(self) -> bool:
        try:
            self._client = BleakClient(self._address)
            await self._client.connect()
            await self._client.start_notify(UUID_EF02, self._notify_ef02)
            await self._client.start_notify(UUID_EF04, self._notify_ef04)
            self.state.available = True
            _LOGGER.info("AC500 connected to %s", self._address)
            return True
        except BleakError as err:
            _LOGGER.error("AC500 connect failed: %s", err)
            self.state.available = False
            self._notify_ha()
            return False

    async def disconnect(self) -> None:
        if self._client:
            try:
                await self._client.disconnect()
            except BleakError:
                pass
        self.state.available = False
        self._notify_ha()

    @property
    def is_connected(self) -> bool:
        return bool(self._client and self._client.is_connected)

    async def send_command(self, command_key: str) -> bool:
        hex_cmd = COMMANDS.get(command_key)
        if not hex_cmd:
            _LOGGER.error("Unknown command: %s", command_key)
            return False
        async with self._lock:
            if not self.is_connected:
                _LOGGER.warning("Not connected, cannot send %s", command_key)
                return False
            try:
                await self._client.write_gatt_char(UUID_WRITE, bytearray.fromhex(hex_cmd))
                _LOGGER.debug("Sent %s (%s)", command_key, hex_cmd)
                return True
            except BleakError as err:
                _LOGGER.error("Write failed for %s: %s", command_key, err)
                self.state.available = False
                self._notify_ha()
                return False

    def _notify_ef02(self, _sender, raw: bytearray) -> None:
        if self.state.parse_ef02(bytes(raw)):
            self._notify_ha()

    def _notify_ef04(self, _sender, raw: bytearray) -> None:
        data = bytes(raw)
        # EF04 arrives as 3 sequential frames: 0x01 / actual data / 0xff
        # Only parse the real data frame (not the 1-byte delimiters)
        if len(data) > 2:
            if self.state.parse_ef04(data):
                self._notify_ha()

    def _notify_ha(self) -> None:
        for cb in self._callbacks:
            try:
                cb()
            except Exception as err:
                _LOGGER.error("Callback error: %s", err)
