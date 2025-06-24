import logging
from datetime import datetime, timezone

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
    SensorEntityDescription
)

from homeassistant.const import (
    EntityCategory,
    UnitOfPower,
    UnitOfEnergy
)
from homeassistant.helpers import (
    entity_registry,
    device_registry,
)
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, LOGGER_NAME, SCHEDULE_UPDATED_EVENT
from .entity import AIEnergySchedulerEntity

_LOGGER = logging.getLogger(LOGGER_NAME)


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN]["coordinator"]
    created_sensors_map = {}
    new_entities = []

    for device_id in coordinator.data.get("schedules", {}):
        _LOGGER.debug(f"Adding sensors for existing device: {device_id}")
        sensor_current_command = CurrentCommandSensor(coordinator, device_id)
        sensor_current_estimated_power = CurrentEstimatedPowerSensor(coordinator, device_id)
        sensor_current_estimated_energy = CurrentEstimatedEnergySensor(coordinator, device_id)
        new_entities.extend([sensor_current_command, sensor_current_estimated_power, sensor_current_estimated_energy])
        created_sensors_map[device_id] = [sensor_current_command, sensor_current_estimated_power, sensor_current_estimated_energy]
    async_add_entities(new_entities)

    @callback
    def async_schedule_update(event):
        nonlocal created_sensors_map
        current_devices = set(coordinator.data.get("schedules", {}).keys())
        managed_device_ids = set(created_sensors_map.keys())

        new_devices = current_devices - managed_device_ids

        if new_devices:
            new_entities = []
            for device_id in new_devices:
                _LOGGER.debug(f"Adding sensors for new device: {device_id}")
                sensor_current_command = CurrentCommandSensor(coordinator, device_id)
                sensor_current_estimated_power = CurrentEstimatedPowerSensor(coordinator, device_id)
                sensor_current_estimated_energy = CurrentEstimatedEnergySensor(coordinator, device_id)
                new_entities.extend([sensor_current_command, sensor_current_estimated_power, sensor_current_estimated_energy])
                created_sensors_map[device_id] = [sensor_current_command, sensor_current_estimated_power, sensor_current_estimated_energy]
            if new_entities:
                async_add_entities(new_entities) 

    config_entry.async_on_unload(
        hass.bus.async_listen(SCHEDULE_UPDATED_EVENT, async_schedule_update)
    )


class CurrentCommandSensor(AIEnergySchedulerEntity, SensorEntity):
    entity_description = SensorEntityDescription(
        key = "current_command",
        name = "Current Command",
        native_unit_of_measurement = None,
        device_class = SensorDeviceClass.ENUM,
        # entity_category=EntityCategory.DIAGNOSTIC,
        icon = "mdi:cog"
    )

    @property
    def native_value(self):
        if self._get_current_interval:
            if self._get_current_interval.command_override:
                return self._get_current_interval.command_override
            return self._get_current_interval.command
        return None
    
    @property
    def extra_state_attributes(self):
        """Return the raw intervals to be used for apex charts."""
        results = {"apex_charts": []}
        if self._get_intervals_apex_charts:
            results["apex_charts"] = self._get_intervals_apex_charts
        return results


class CurrentEstimatedPowerSensor(AIEnergySchedulerEntity, SensorEntity):
    entity_description = SensorEntityDescription(
        key = "estimated_power",
        name = "Estimated Power",
        native_unit_of_measurement = UnitOfPower.KILO_WATT,
        device_class = SensorDeviceClass.POWER,
        # entity_category=EntityCategory.DIAGNOSTIC,
        icon = "mdi:flash"
    )

    @property
    def native_value(self):
        return self._get_current_interval.power_kw if self._get_current_interval else None


class CurrentEstimatedEnergySensor(AIEnergySchedulerEntity, SensorEntity):
    entity_description = SensorEntityDescription(
        key = "estimated_energy",
        name = "Estimated Energy",
        native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR,
        device_class = SensorDeviceClass.ENERGY,
        # entity_category=EntityCategory.DIAGNOSTIC,
        icon = "mdi:lightning-bolt"
    )

    @property
    def native_value(self):
        return self._get_current_interval.energy_kwh if self._get_current_interval else None

