"""BLE communication + state parsing for Soehnle AC500."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Callable

from bleak import BleakClient, BleakError

from .const import (
    UUID_WRITE, UUID_EF02,
    FLAG_POWER, FLAG_UVC, FLAG_NIGHT, FLAG_AUTO,
    SPEED_MAP, COMMANDS,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class AC500State:
    """Parsed device state from EF02 notify frame."""
    power:      bool  = False
    uvc:        bool  = False
    night:      bool  = False
    auto:       bool  = False
    speed:      int   = 0       # 0-3 (Speed1-4)
    aqi:        int   = 0       # Air Quality Index / PM2.5
    available:  bool  = False

    def parse(self, data: bytes) -> bool:
        """Parse EF02 frame. Returns True if any value changed."""
        if len(data) != 17:
            return False
        if data[0] != 0xAA or data[-1] != 0xEE:
            return False

        p = data[4:-1]   # 12 payload bytes

        # Verify checksum
        expected_chk = (p[0] + p[2] + p[4] + p[6] + p[10] + 0xC0) & 0xFF
        if expected_chk != p[11]:
            _LOGGER.warning("EF02 checksum mismatch: expected 0x%02x got 0x%02x", expected_chk, p[11])
            return False

        old = (self.power, self.uvc, self.night, self.auto, self.speed, self.aqi)

        flags       = p[2]
        self.power  = bool(flags & FLAG_POWER)
        self.uvc    = bool(flags & FLAG_UVC)
        self.night  = bool(flags & FLAG_NIGHT)
        self.auto   = bool(flags & FLAG_AUTO)
        self.speed  = p[0]          # 0x00–0x03
        self.aqi    = p[4]
        self.available = True

        new = (self.power, self.uvc, self.night, self.auto, self.speed, self.aqi)
        return old != new


class AC500BleClient:
    """Manages BLE connection, notify subscription, and write commands."""

    def __init__(self, address: str) -> None:
        self._address    = address
        self._client:    BleakClient | None = None
        self._lock       = asyncio.Lock()
        self.state       = AC500State()
        self._callbacks: list[Callable] = []

    # ── Public API ────────────────────────────────────────────────────────

    def register_callback(self, cb: Callable) -> None:
        self._callbacks.append(cb)

    def unregister_callback(self, cb: Callable) -> None:
        self._callbacks.discard(cb) if hasattr(self._callbacks, 'discard') \
            else self._callbacks.remove(cb) if cb in self._callbacks else None

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
                _LOGGER.warning("AC500 not connected, cannot send %s", command_key)
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

    # ── Internal ─────────────────────────────────────────────────────────

    def _notify_ef02(self, _sender, raw: bytearray) -> None:
        changed = self.state.parse(bytes(raw))
        if changed:
            _LOGGER.debug("State update: power=%s uvc=%s night=%s auto=%s speed=%s aqi=%s",
                          self.state.power, self.state.uvc, self.state.night,
                          self.state.auto, self.state.speed, self.state.aqi)
            self._notify_ha()

    def _notify_ha(self) -> None:
        for cb in self._callbacks:
            try:
                cb()
            except Exception as err:
                _LOGGER.error("Callback error: %s", err)
