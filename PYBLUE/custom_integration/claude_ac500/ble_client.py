"""BLE communication handler for Soehnle AC500."""
from __future__ import annotations

import asyncio
import logging

from bleak import BleakClient, BleakError

from .const import CHARACTERISTIC_UUID, COMMANDS

_LOGGER = logging.getLogger(__name__)


class AC500BleClient:
    """Manages the BLE connection and sends commands."""

    def __init__(self, address: str) -> None:
        self._address = address
        self._client: BleakClient | None = None
        self._lock = asyncio.Lock()

    async def _ensure_connected(self) -> bool:
        if self._client and self._client.is_connected:
            return True
        try:
            self._client = BleakClient(self._address)
            await self._client.connect()
            _LOGGER.debug("Connected to %s", self._address)
            return True
        except BleakError as err:
            _LOGGER.error("BLE connection failed: %s", err)
            self._client = None
            return False

    async def send_command(self, command_key: str) -> bool:
        """Send a named command from COMMANDS dict."""
        hex_cmd = COMMANDS.get(command_key)
        if not hex_cmd:
            _LOGGER.error("Unknown command: %s", command_key)
            return False

        async with self._lock:
            if not await self._ensure_connected():
                return False
            try:
                await self._client.write_gatt_char(
                    CHARACTERISTIC_UUID, bytearray.fromhex(hex_cmd)
                )
                _LOGGER.debug("Sent command %s (%s)", command_key, hex_cmd)
                return True
            except BleakError as err:
                _LOGGER.error("Failed to send command %s: %s", command_key, err)
                self._client = None
                return False

    async def disconnect(self) -> None:
        if self._client and self._client.is_connected:
            await self._client.disconnect()
            _LOGGER.debug("Disconnected from %s", self._address)
