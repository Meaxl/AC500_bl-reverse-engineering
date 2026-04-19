"""Fan platform – reflects real device state via EF02 notify."""
from __future__ import annotations

import math
import logging
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, PRESET_MODES, SPEED_MAP
from .coordinator import AC500Coordinator

_LOGGER = logging.getLogger(__name__)

SPEED_TO_PCT = {0: 25, 1: 50, 2: 75, 3: 100}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    coordinator: AC500Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AC500Fan(coordinator, entry)])


class AC500Fan(FanEntity):
    """Fan entity with real-time state from EF02 notify."""

    _attr_has_entity_name    = True
    _attr_should_poll        = False
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.PRESET_MODE
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )

    def __init__(self, coordinator: AC500Coordinator, entry: ConfigEntry) -> None:
        self._coordinator    = coordinator
        self._attr_name      = entry.data.get(CONF_NAME, "Soehnle AC500")
        self._attr_unique_id = f"{entry.entry_id}_fan"

    async def async_added_to_hass(self) -> None:
        self._coordinator.async_add_listener(self._handle_update)

    async def async_will_remove_from_hass(self) -> None:
        self._coordinator.async_remove_listener(self._handle_update)

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()

    # ── State (from EF02) ────────────────────────────────────────────────

    @property
    def available(self) -> bool:
        return self._coordinator.state.available

    @property
    def is_on(self) -> bool:
        return self._coordinator.state.power

    @property
    def percentage(self) -> int | None:
        if not self._coordinator.state.power:
            return 0
        return SPEED_TO_PCT.get(self._coordinator.state.speed, 25)

    @property
    def speed_count(self) -> int:
        return 4

    @property
    def preset_mode(self) -> str | None:
        if not self._coordinator.state.power:
            return None
        if self._coordinator.state.auto:
            return "auto"
        return SPEED_MAP.get(self._coordinator.state.speed, "speed_1")

    @property
    def preset_modes(self) -> list[str]:
        return PRESET_MODES

    # ── Commands ─────────────────────────────────────────────────────────

    async def async_turn_on(self, percentage: int | None = None,
                            preset_mode: str | None = None, **kwargs: Any) -> None:
        await self._coordinator.client.send_command("power_on")
        if preset_mode:
            await self.async_set_preset_mode(preset_mode)
        elif percentage is not None:
            await self.async_set_percentage(percentage)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._coordinator.client.send_command("power_off")

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage == 0:
            await self.async_turn_off()
            return
        speed_idx = max(0, min(3, math.ceil(percentage / 25) - 1))
        cmd = ["speed_1", "speed_2", "speed_3", "speed_4"][speed_idx]
        await self._coordinator.client.send_command(cmd)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode == "auto":
            await self._coordinator.client.send_command("auto_on")
        elif preset_mode in ("speed_1", "speed_2", "speed_3", "speed_4"):
            await self._coordinator.client.send_command(preset_mode)
        else:
            _LOGGER.error("Unknown preset: %s", preset_mode)
