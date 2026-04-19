"""Sensor platform – AQI / PM2.5 from EF02 notify."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
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
    async_add_entities([AC500AQISensor(coordinator, entry)])


class AC500AQISensor(SensorEntity):
    """Air quality sensor from EF02 byte p[4]."""

    _attr_has_entity_name    = True
    _attr_should_poll        = False
    _attr_state_class        = SensorStateClass.MEASUREMENT
    # Unit unknown until confirmed – using raw index
    # Change to CONCENTRATION_MICROGRAMS_PER_CUBIC_METER once PM2.5 confirmed
    _attr_native_unit_of_measurement = "AQI"
    _attr_icon               = "mdi:air-filter"

    def __init__(self, coordinator: AC500Coordinator, entry: ConfigEntry) -> None:
        self._coordinator    = coordinator
        device_name          = entry.data.get(CONF_NAME, "Soehnle AC500")
        self._attr_name      = f"{device_name} Air Quality"
        self._attr_unique_id = f"{entry.entry_id}_aqi"

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
    def native_value(self) -> int | None:
        if not self._coordinator.state.available:
            return None
        return self._coordinator.state.aqi
