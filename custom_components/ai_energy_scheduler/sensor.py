from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    SENSOR_COMMAND,
    SENSOR_POWER_KW,
    SENSOR_ENERGY_KWH,
    SENSOR_NEXT_COMMAND,
    SENSOR_TOTAL_POWER_KW,
    SENSOR_TOTAL_ENERGY_KWH_TODAY,
)
from .coordinator import AiEnergySchedulerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up AI Energy Scheduler sensors."""
    coordinator: AiEnergySchedulerCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = []

    for device_id, device_data in coordinator.schedule_data.items():
        entities.append(DeviceSensor(coordinator, device_id, SENSOR_COMMAND))
        entities.append(DeviceSensor(coordinator, device_id, SENSOR_POWER_KW))
        entities.append(DeviceSensor(coordinator, device_id, SENSOR_ENERGY_KWH))
        entities.append(DeviceSensor(coordinator, device_id, SENSOR_NEXT_COMMAND))

    # Global summary sensors
    entities.append(GlobalSensor(coordinator, SENSOR_TOTAL_POWER_KW))
    entities.append(GlobalSensor(coordinator, SENSOR_TOTAL_ENERGY_KWH_TODAY))

    async_add_entities(entities, update_before_add=True)


class DeviceSensor(CoordinatorEntity, SensorEntity):
    """Sensor for individual device state like command, power, energy."""

    def __init__(
        self,
        coordinator: AiEnergySchedulerCoordinator,
        device_id: str,
        sensor_type: str,
    ) -> None:
        super().__init__(coordinator)
        self.device_id = device_id
        self.sensor_type = sensor_type
        self._attr_unique_id = f"{DOMAIN}_{device_id}_{sensor_type}"
        self._attr_name = f"{device_id} {sensor_type.replace('_', ' ').title()}"

    @property
    def native_value(self):
        """Return the current value of the sensor."""
        data = self.coordinator.get_device_state(self.device_id)
        return data.get(self.sensor_type)

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        data = self.coordinator.get_device_state(self.device_id)
        return {
            "device": self.device_id,
            "last_updated": data.get("last_updated"),
            "source": data.get("source"),
        }


class GlobalSensor(CoordinatorEntity, SensorEntity):
    """Sensor for global summaries like total power and total energy."""

    def __init__(
        self,
        coordinator: AiEnergySchedulerCoordinator,
        sensor_type: str,
    ) -> None:
        super().__init__(coordinator)
        self.sensor_type = sensor_type
        self._attr_unique_id = f"{DOMAIN}_global_{sensor_type}"
        self._attr_name = f"AI Energy Scheduler {sensor_type.replace('_', ' ').title()}"

    @property
    def native_value(self):
        """Return the current aggregated value."""
        return self.coordinator.get_global_metric(self.sensor_type)

    @property
    def extra_state_attributes(self):
        """Return meta info."""
        return {
            "last_updated": datetime.now().isoformat(),
            "device_count": len(self.coordinator.schedule_data),
        }
