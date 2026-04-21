"""Fan platform for Soehnle AC500."""
from __future__ import annotations
import math, logging
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

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AC500Fan(coordinator, entry)])

class AC500Fan(FanEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_supported_features = (FanEntityFeature.SET_SPEED | FanEntityFeature.PRESET_MODE
                                 | FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF)
    def __init__(self, coordinator, entry):
        self._coordinator = coordinator
        self._attr_name = entry.data.get(CONF_NAME, "Soehnle AC500")
        self._attr_unique_id = f"{entry.entry_id}_fan"
    async def async_added_to_hass(self):
        self._coordinator.async_add_listener(self._handle_update)
    async def async_will_remove_from_hass(self):
        self._coordinator.async_remove_listener(self._handle_update)
    @callback
    def _handle_update(self): self.async_write_ha_state()
    @property
    def available(self): return self._coordinator.state.available
    @property
    def is_on(self): return self._coordinator.state.power
    @property
    def percentage(self): return SPEED_TO_PCT.get(self._coordinator.state.speed, 25) if self._coordinator.state.power else 0
    @property
    def speed_count(self): return 4
    @property
    def preset_mode(self):
        if not self._coordinator.state.power: return None
        if self._coordinator.state.auto: return "auto"
        return SPEED_MAP.get(self._coordinator.state.speed, "speed_1")
    @property
    def preset_modes(self): return PRESET_MODES
    async def async_turn_on(self, percentage=None, preset_mode=None, **kwargs):
        await self._coordinator.client.send_command("power_on")
        if preset_mode: await self.async_set_preset_mode(preset_mode)
        elif percentage is not None: await self.async_set_percentage(percentage)
    async def async_turn_off(self, **kwargs):
        await self._coordinator.client.send_command("power_off")
    async def async_set_percentage(self, percentage):
        if percentage == 0: return await self.async_turn_off()
        idx = max(0, min(3, math.ceil(percentage/25)-1))
        await self._coordinator.client.send_command(["speed_1","speed_2","speed_3","speed_4"][idx])
    async def async_set_preset_mode(self, preset_mode):
        if preset_mode == "auto": await self._coordinator.client.send_command("auto_on")
        elif preset_mode in ("speed_1","speed_2","speed_3","speed_4"):
            await self._coordinator.client.send_command(preset_mode)
