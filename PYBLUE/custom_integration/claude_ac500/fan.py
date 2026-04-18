"""Fan platform for Soehnle Airfresh Clean Connect 500."""
from __future__ import annotations

import logging
import math
from typing import Any

from homeassistant.components.fan import (
    FanEntity,
    FanEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .ble_client import AC500BleClient
from .const import DOMAIN, PRESET_MODES, SPEED_AUTO, SPEED_1, SPEED_2, SPEED_3, SPEED_4

_LOGGER = logging.getLogger(__name__)

# Map preset name → command keys
PRESET_TO_CMD = {
    SPEED_1:   "speed_1",
    SPEED_2:   "speed_2",
    SPEED_3:   "speed_3",
    SPEED_4:   "speed_4",
    SPEED_AUTO: "auto_on",
}

# Percentage buckets for 4 speeds
SPEED_PERCENTAGES = {
    SPEED_1: 25,
    SPEED_2: 50,
    SPEED_3: 75,
    SPEED_4: 100,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    address = entry.data[CONF_ADDRESS]
    name    = entry.data.get(CONF_NAME, "Soehnle AC500")
    client  = AC500BleClient(address)
    async_add_entities([SoehnleAC500Fan(client, name, entry.entry_id)])


class SoehnleAC500Fan(FanEntity):
    """Representation of the Soehnle AC500 as a HA Fan entity."""

    _attr_has_entity_name = True
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.PRESET_MODE
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )

    def __init__(self, client: AC500BleClient, name: str, entry_id: str) -> None:
        self._client       = client
        self._attr_name    = name
        self._attr_unique_id = f"{entry_id}_fan"
        self._is_on        = False
        self._preset_mode  = SPEED_1
        self._percentage   = 25

    # ── State ──────────────────────────────────────────────────────────────────

    @property
    def is_on(self) -> bool:
        return self._is_on

    @property
    def percentage(self) -> int | None:
        return self._percentage if self._is_on else 0

    @property
    def speed_count(self) -> int:
        return 4

    @property
    def preset_mode(self) -> str | None:
        return self._preset_mode if self._is_on else None

    @property
    def preset_modes(self) -> list[str]:
        return PRESET_MODES

    # ── Commands ───────────────────────────────────────────────────────────────

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        await self._client.send_command("power_on")
        self._is_on = True

        if preset_mode:
            await self.async_set_preset_mode(preset_mode)
        elif percentage is not None:
            await self.async_set_percentage(percentage)
        else:
            # Default: restore last preset
            await self._client.send_command(PRESET_TO_CMD[self._preset_mode])

        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._client.send_command("power_off")
        self._is_on = False
        self.async_write_ha_state()

    async def async_set_percentage(self, percentage: int) -> None:
        """Map 0-100% to one of 4 speeds."""
        if percentage == 0:
            await self.async_turn_off()
            return

        # 1-25 → speed1, 26-50 → speed2, 51-75 → speed3, 76-100 → speed4
        speed_index = math.ceil(percentage / 25)
        speed_index = max(1, min(4, speed_index))
        preset = [SPEED_1, SPEED_2, SPEED_3, SPEED_4][speed_index - 1]

        await self._client.send_command(PRESET_TO_CMD[preset])
        self._preset_mode = preset
        self._percentage  = SPEED_PERCENTAGES[preset]
        self._is_on       = True
        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode not in PRESET_TO_CMD:
            _LOGGER.error("Unknown preset: %s", preset_mode)
            return

        await self._client.send_command(PRESET_TO_CMD[preset_mode])
        self._preset_mode = preset_mode
        self._percentage  = SPEED_PERCENTAGES.get(preset_mode, 50)
        self._is_on       = True
        self.async_write_ha_state()
