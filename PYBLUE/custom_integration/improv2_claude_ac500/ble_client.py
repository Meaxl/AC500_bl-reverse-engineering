"""BLE client + state parser for Soehnle AC500."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Callable

from bleak import BleakClient, BleakError

from .const import (
    UUID_WRITE, UUID_EF02,
    FLAG_POWER, FLAG_UVC, FLAG_TIMER, FLAG_AUTO, FLAG_NIGHT,
    SPEED_MAP, COMMANDS,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class AC500State:
    power:      bool = False
    uvc:        bool = False
    night:      bool = False
    auto:       bool = False
    timer_on:   bool = False
    speed:      int  = 0      # 0-3
    timer_val:  int  = 0      # raw: 0/2/4/8  (hours)
    aqi:        int  = 0
    available:  bool = False

    @property
    def timer_hours(self) -> int:
        """Timer hours as integer: 0, 2, 4, or 8."""
        return self.timer_val if self.timer_on else 0

    def parse(self, data: bytes) -> bool:
        """Parse EF02 frame. Returns True if state changed."""
        if len(data) != 17 or data[0] != 0xAA or data[-1] != 0xEE:
            return False
        p = data[4:-1]

        # Verify checksum
        expected = (p[0]+p[1]+p[2]+p[4]+p[6]+p[10]+0xC0) & 0xFF
        if expected != p[11]:
            _LOGGER.warning("EF02 checksum mismatch: expected 0x%02x got 0x%02x", expected, p[11])
            return False

        old = (self.power, self.uvc, self.night, self.auto,
               self.timer_on, self.timer_val, self.speed, self.aqi)

        flags          = p[2]
        self.power     = bool(flags & FLAG_POWER)
        self.uvc       = bool(flags & FLAG_UVC)
        self.night     = bool(flags & FLAG_NIGHT)
        self.auto      = bool(flags & FLAG_AUTO)
        self.timer_on  = bool(flags & FLAG_TIMER)
        self.speed     = p[0]
        self.timer_val = p[1]
        self.aqi       = p[4]
        self.available = True

        new = (self.power, self.uvc, self.night, self.auto,
               self.timer_on, self.timer_val, self.speed, self.aqi)
        return old != new


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
        if self.state.parse(bytes(raw)):
            self._notify_ha()

    def _notify_ha(self) -> None:
        for cb in self._callbacks:
            try:
                cb()
            except Exception as err:
                _LOGGER.error("Callback error: %s", err)
