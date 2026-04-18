"""Switch platform for Soehnle Airfresh Clean Connect 500 (UV-C, Night Mode)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .ble_client import AC500BleClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    address = entry.data[CONF_ADDRESS]
    name    = entry.data.get(CONF_NAME, "Soehnle AC500")
    client  = AC500BleClient(address)

    async_add_entities([
        SoehnleSwitch(client, name, entry.entry_id, "UV-C",       "uvc_on",   "uvc_off",   "uvc"),
        SoehnleSwitch(client, name, entry.entry_id, "Night Mode",  "night_on", "night_off", "night"),
    ])


class SoehnleSwitch(SwitchEntity):
    """Generic on/off switch for AC500 features."""

    _attr_has_entity_name = True

    def __init__(
        self,
        client: AC500BleClient,
        device_name: str,
        entry_id: str,
        feature_name: str,
        cmd_on: str,
        cmd_off: str,
        suffix: str,
    ) -> None:
        self._client       = client
        self._attr_name    = f"{device_name} {feature_name}"
        self._attr_unique_id = f"{entry_id}_{suffix}"
        self._cmd_on       = cmd_on
        self._cmd_off      = cmd_off
        self._is_on        = False

    @property
    def is_on(self) -> bool:
        return self._is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._client.send_command(self._cmd_on)
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._client.send_command(self._cmd_off)
        self._is_on = False
        self.async_write_ha_state()
