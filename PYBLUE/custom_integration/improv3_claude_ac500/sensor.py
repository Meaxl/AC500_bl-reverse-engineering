"""Sensor platform – PM2.5, Temperature, Humidity."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
    UnitOfTemperature,
    PERCENTAGE,
)
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
        AC500PM25Sensor(coordinator, entry, name),
        AC500TempSensor(coordinator, entry, name),
        AC500HumSensor(coordinator, entry, name),
    ])


class _AC500SensorBase(SensorEntity):
    _attr_has_entity_name = True
    _attr_should_poll     = False
    _attr_state_class     = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: AC500Coordinator, entry: ConfigEntry,
                 device_name: str, suffix: str) -> None:
        self._coordinator    = coordinator
        self._attr_unique_id = f"{entry.entry_id}_{suffix}"

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


class AC500PM25Sensor(_AC500SensorBase):
    """PM2.5 sensor from EF02 p[4] ÷ 10."""
    _attr_device_class                = SensorDeviceClass.PM25
    _attr_native_unit_of_measurement  = "µg/m³"
    _attr_icon                        = "mdi:air-filter"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, entry, device_name):
        super().__init__(coordinator, entry, device_name, "pm25")
        self._attr_name = f"{device_name} PM2.5"

    @property
    def native_value(self) -> float | None:
        return self._coordinator.state.pm25 if self._coordinator.state.available else None


class AC500TempSensor(_AC500SensorBase):
    """Temperature from EF04 pair[1] ÷ 10."""
    _attr_device_class                = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement  = UnitOfTemperature.CELSIUS
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, entry, device_name):
        super().__init__(coordinator, entry, device_name, "temperature")
        self._attr_name = f"{device_name} Temperature"

    @property
    def native_value(self) -> float | None:
        return self._coordinator.state.temperature


class AC500HumSensor(_AC500SensorBase):
    """Humidity from EF04 pair[4] – unconfirmed, shown as sensor."""
    _attr_device_class                = SensorDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement  = PERCENTAGE
    _attr_icon                        = "mdi:water-percent"

    def __init__(self, coordinator, entry, device_name):
        super().__init__(coordinator, entry, device_name, "humidity")
        self._attr_name = f"{device_name} Humidity"

    @property
    def available(self) -> bool:
        # Only available if we actually received humidity data
        return (self._coordinator.state.available
                and self._coordinator.state.humidity is not None)

    @property
    def native_value(self) -> int | None:
        return self._coordinator.state.humidity
