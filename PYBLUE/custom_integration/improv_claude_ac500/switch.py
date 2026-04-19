"""Switch platform – UV-C, Night Mode (real state from EF02)."""
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


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    coordinator: AC500Coordinator = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get(CONF_NAME, "Soehnle AC500")
    async_add_entities([
        AC500Switch(coordinator, entry, "UV-C",       "uvc",   "uvc_on",   "uvc_off"),
        AC500Switch(coordinator, entry, "Night Mode",  "night", "night_on", "night_off"),
    ])


class AC500Switch(SwitchEntity):
    """Generic switch backed by EF02 state."""

    _attr_has_entity_name = True
    _attr_should_poll     = False

    def __init__(self, coordinator: AC500Coordinator, entry: ConfigEntry,
                 feature: str, state_attr: str, cmd_on: str, cmd_off: str) -> None:
        self._coordinator  = coordinator
        self._state_attr   = state_attr   # attribute name on AC500State
        self._cmd_on       = cmd_on
        self._cmd_off      = cmd_off
        device_name        = entry.data.get(CONF_NAME, "Soehnle AC500")
        self._attr_name    = f"{device_name} {feature}"
        self._attr_unique_id = f"{entry.entry_id}_{state_attr}"

    async def async_added_to_hass(self) -> None:
        self._coordinator.async_add_listener(self._handle_update)

    async def async_will_remove_from_hass(self) -> None:
        self._coordinator.async_remove_listener(self._handle_update)

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        return self._coordinator.state.available

    @property
    def is_on(self) -> bool:
        return bool(getattr(self._coordinator.state, self._state_attr, False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._coordinator.client.send_command(self._cmd_on)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._coordinator.client.send_command(self._cmd_off)
