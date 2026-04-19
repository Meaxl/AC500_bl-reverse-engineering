"""DataUpdateCoordinator for Soehnle AC500 – handles reconnect loop."""
from __future__ import annotations

import asyncio
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .ble_client import AC500BleClient, AC500State

_LOGGER = logging.getLogger(__name__)

RECONNECT_INTERVAL = 5   # seconds between reconnect attempts
KEEPALIVE_TIMEOUT  = 15  # seconds without notify before reconnect


class AC500Coordinator(DataUpdateCoordinator):
    """Coordinates BLE connection, reconnects on drop, pushes state to entities."""

    def __init__(self, hass: HomeAssistant, client: AC500BleClient, name: str) -> None:
        super().__init__(hass, _LOGGER, name=name)
        self._client      = client
        self._last_notify = asyncio.get_event_loop().time()
        self._running     = False
        self._task: asyncio.Task | None = None

    @property
    def state(self) -> AC500State:
        return self._client.state

    @property
    def client(self) -> AC500BleClient:
        return self._client

    async def async_start(self) -> None:
        self._running = True
        self._client.register_callback(self._on_state_change)
        self._task = self.hass.async_create_task(self._connection_loop())

    async def async_stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
        await self._client.disconnect()

    def _on_state_change(self) -> None:
        self._last_notify = asyncio.get_event_loop().time()
        self.async_set_updated_data(self._client.state)

    async def _connection_loop(self) -> None:
        while self._running:
            if not self._client.is_connected:
                _LOGGER.info("AC500 connecting...")
                connected = await self._client.connect()
                if not connected:
                    await asyncio.sleep(RECONNECT_INTERVAL)
                    continue
                self._last_notify = asyncio.get_event_loop().time()

            # Monitor for keepalive timeout
            await asyncio.sleep(2)
            if asyncio.get_event_loop().time() - self._last_notify > KEEPALIVE_TIMEOUT:
                _LOGGER.warning("AC500 no notify for %ds – reconnecting", KEEPALIVE_TIMEOUT)
                await self._client.disconnect()
                await asyncio.sleep(RECONNECT_INTERVAL)
