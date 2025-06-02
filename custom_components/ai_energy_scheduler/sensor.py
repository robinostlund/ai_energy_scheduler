"""Sensors for AI Energy Scheduler."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, SENSOR_TOTAL_POWER_KW, SENSOR_TOTAL_ENERGY_KWH_TODAY
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    # Device sensors
    if coordinator.schedule:
        for device, obj in coordinator.schedule["schedules"].items():
            entities.append(AIESSensor(coordinator, device, "command"))
            entities.append(AIESSensor(coordinator, device, "power_kw"))
            entities.append(AIESSensor(coordinator, device, "energy_kwh"))
            entities.append(AIESSensor(coordinator, device, "next_command"))

    # Summary sensors
    entities.append(AIESSummarySensor(coordinator, SENSOR_TOTAL_POWER_KW))
    entities.append(AIESSummarySensor(coordinator, SENSOR_TOTAL_ENERGY_KWH_TODAY))
    async_add_entities(entities)

class AIESSensor(CoordinatorEntity, SensorEntity):
    """Sensor for device state/power/energy."""

    def __init__(self, coordinator, device, sensor_type):
        super().__init__(coordinator)
        self._attr_name = f"{DOMAIN}_{device}_{sensor_type}"
        self._attr_unique_id = f"{DOMAIN}_{device}_{sensor_type}"
        self.device = device
        self.sensor_type = sensor_type

    @property
    def state(self):
        # Return the current state for the sensor_type
        schedule = self.coordinator.schedule
        if not schedule:
            return None
        intervals = schedule["schedules"][self.device]["intervals"]
        # Simplified: return first value, production code would return correct interval for now
        if self.sensor_type == "command":
            return intervals[0].get("command")
        elif self.sensor_type == "power_kw":
            return intervals[0].get("power_kw", 0)
        elif self.sensor_type == "energy_kwh":
            return intervals[0].get("energy_kwh", 0)
        elif self.sensor_type == "next_command":
            return intervals[1].get("command") if len(intervals) > 1 else None

    @property
    def available(self):
        return bool(self.coordinator.schedule)

class AIESSummarySensor(CoordinatorEntity, SensorEntity):
    """Sensor for total power/energy."""

    def __init__(self, coordinator, sensor_type):
        super().__init__(coordinator)
        self._attr_name = f"{DOMAIN}_{sensor_type}"
        self._attr_unique_id = f"{DOMAIN}_{sensor_type}"
        self.sensor_type = sensor_type

    @property
    def state(self):
        # Example: sum all devices' values
        schedule = self.coordinator.schedule
        if not schedule:
            return None
        total = 0
        for obj in schedule["schedules"].values():
            for interval in obj["intervals"]:
                if self.sensor_type == SENSOR_TOTAL_POWER_KW:
                    total += interval.get("power_kw", 0)
                elif self.sensor_type == SENSOR_TOTAL_ENERGY_KWH_TODAY:
                    total += interval.get("energy_kwh", 0)
        return round(total, 2)
