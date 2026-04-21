"""Switch platform – UV-C, Night Mode."""
from __future__ import annotations
import logging
from typing import Any
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN
from .coordinator import AC500Coordinator
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get(CONF_NAME, "Soehnle AC500")
    async_add_entities([
        AC500Switch(coordinator, entry, "UV-C",      "uvc",   "uvc_on",   "uvc_off"),
        AC500Switch(coordinator, entry, "Night Mode", "night", "night_on", "night_off"),
    ])

class AC500Switch(SwitchEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False
    def __init__(self, coordinator, entry, feature, state_attr, cmd_on, cmd_off):
        self._coordinator = coordinator
        self._state_attr = state_attr
        self._cmd_on = cmd_on; self._cmd_off = cmd_off
        device_name = entry.data.get(CONF_NAME, "Soehnle AC500")
        self._attr_name = f"{device_name} {feature}"
        self._attr_unique_id = f"{entry.entry_id}_{state_attr}"
    async def async_added_to_hass(self):
        self._coordinator.async_add_listener(self._handle_update)
    async def async_will_remove_from_hass(self):
        self._coordinator.async_remove_listener(self._handle_update)
    @callback
    def _handle_update(self): self.async_write_ha_state()
    @property
    def available(self): return self._coordinator.state.available
    @property
    def is_on(self): return bool(getattr(self._coordinator.state, self._state_attr, False))
    async def async_turn_on(self, **kwargs): await self._coordinator.client.send_command(self._cmd_on)
    async def async_turn_off(self, **kwargs): await self._coordinator.client.send_command(self._cmd_off)
