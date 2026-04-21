"""Select platform – Timer (OFF / 2h / 4h / 8h)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import AC500Coordinator

_LOGGER = logging.getLogger(__name__)

TIMER_OPTIONS = ["off", "2h", "4h", "8h"]
TIMER_TO_CMD  = {"off": "timer_off", "2h": "timer_2h", "4h": "timer_4h", "8h": "timer_8h"}
VAL_TO_OPTION = {0: "off", 2: "2h", 4: "4h", 8: "8h"}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    coordinator: AC500Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AC500TimerSelect(coordinator, entry)])


class AC500TimerSelect(SelectEntity):
    """Timer select: OFF / 2h / 4h / 8h."""

    _attr_has_entity_name = True
    _attr_should_poll     = False
    _attr_options         = TIMER_OPTIONS
    _attr_icon            = "mdi:timer-outline"

    def __init__(self, coordinator: AC500Coordinator, entry: ConfigEntry) -> None:
        self._coordinator    = coordinator
        device_name          = entry.data.get(CONF_NAME, "Soehnle AC500")
        self._attr_name      = f"{device_name} Timer"
        self._attr_unique_id = f"{entry.entry_id}_timer"

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
    def current_option(self) -> str:
        return VAL_TO_OPTION.get(self._coordinator.state.timer_hours, "off")

    async def async_select_option(self, option: str) -> None:
        cmd = TIMER_TO_CMD.get(option)
        if cmd:
            await self._coordinator.client.send_command(cmd)
        else:
            _LOGGER.error("Unknown timer option: %s", option)
