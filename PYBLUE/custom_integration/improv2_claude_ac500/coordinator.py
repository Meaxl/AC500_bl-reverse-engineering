"""Reconnect coordinator for AC500."""
from __future__ import annotations
import asyncio, logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .ble_client import AC500BleClient, AC500State
_LOGGER = logging.getLogger(__name__)
RECONNECT_INTERVAL = 5
KEEPALIVE_TIMEOUT  = 15

class AC500Coordinator(DataUpdateCoordinator):
    def __init__(self, hass, client: AC500BleClient, name: str):
        super().__init__(hass, _LOGGER, name=name)
        self._client = client
        self._last_notify = asyncio.get_event_loop().time()
        self._running = False
        self._task = None
    @property
    def state(self) -> AC500State: return self._client.state
    @property
    def client(self) -> AC500BleClient: return self._client
    async def async_start(self):
        self._running = True
        self._client.register_callback(self._on_state_change)
        self._task = self.hass.async_create_task(self._connection_loop())
    async def async_stop(self):
        self._running = False
        if self._task: self._task.cancel()
        await self._client.disconnect()
    def _on_state_change(self):
        self._last_notify = asyncio.get_event_loop().time()
        self.async_set_updated_data(self._client.state)
    async def _connection_loop(self):
        while self._running:
            if not self._client.is_connected:
                _LOGGER.info("AC500 connecting...")
                if not await self._client.connect():
                    await asyncio.sleep(RECONNECT_INTERVAL)
                    continue
                self._last_notify = asyncio.get_event_loop().time()
            await asyncio.sleep(2)
            if asyncio.get_event_loop().time() - self._last_notify > KEEPALIVE_TIMEOUT:
                _LOGGER.warning("No notify for %ds – reconnecting", KEEPALIVE_TIMEOUT)
                await self._client.disconnect()
                await asyncio.sleep(RECONNECT_INTERVAL)
