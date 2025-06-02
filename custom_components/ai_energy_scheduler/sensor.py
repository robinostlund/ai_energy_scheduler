"""Sensors for AI Energy Scheduler."""

from homeassistant.components.sensor import SensorEntity
from .const import (
    DOMAIN, SENSOR_COMMAND, SENSOR_POWER_KW, SENSOR_ENERGY_KWH,
    SENSOR_NEXT_COMMAND, SENSOR_TOTAL_POWER, SENSOR_TOTAL_ENERGY, SENSOR_LAST_UPDATE,
    CONF_INSTANCE_ID, CONF_INSTANCE_FRIENDLY_NAME, EVENT_COMMAND_ACTIVATED
)
import datetime

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up AI Energy Scheduler sensors for all instances."""
    # Not used: All entity creation is triggered by the import_schedule service
    pass

def create_sensors_for_instance(hass, instance_id, instance_friendly_name, schedule):
    """Return a list of sensor entities for one instance."""
    sensors = []
    schedules = schedule.get("schedules", {})

    for device, info in schedules.items():
        sensors.extend([
            AiEnergyCommandSensor(hass, instance_id, instance_friendly_name, device, info),
            AiEnergyPowerKwSensor(hass, instance_id, instance_friendly_name, device, info),
            AiEnergyEnergyKwhSensor(hass, instance_id, instance_friendly_name, device, info),
            AiEnergyNextCommandSensor(hass, instance_id, instance_friendly_name, device, info),
        ])

    # Add summary sensors (per instance)
    sensors.append(AiEnergyTotalPowerSensor(hass, instance_id, instance_friendly_name, schedules))
    sensors.append(AiEnergyTotalEnergySensor(hass, instance_id, instance_friendly_name, schedules))
    sensors.append(AiEnergyLastUpdateSensor(hass, instance_id, instance_friendly_name, schedules))
    return sensors

def _get_active_interval(intervals):
    now = datetime.datetime.now(datetime.timezone.utc)
    for interval in intervals:
        start = datetime.datetime.fromisoformat(interval["start"])
        end = datetime.datetime.fromisoformat(interval["end"])
        if start <= now < end:
            return interval
    return None

class AiEnergyBaseSensor(SensorEntity):
    """Base class for AI Energy Scheduler sensors."""

    def __init__(self, hass, instance_id, instance_friendly_name, device, info):
        self._hass = hass
        self._instance_id = instance_id
        self._instance_friendly_name = instance_friendly_name
        self._device = device
        self._info = info

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._instance_id)},
            "name": f"{DOMAIN} {self._instance_friendly_name}"
        }

class AiEnergyCommandSensor(AiEnergyBaseSensor):
    """Sensor for current command."""

    def __init__(self, hass, instance_id, instance_friendly_name, device, info):
        super().__init__(hass, instance_id, instance_friendly_name, device, info)
        self._attr_name = f"{DOMAIN} {instance_friendly_name} {device} Command"
        self._attr_unique_id = f"{DOMAIN}_{instance_id}_{device}_{SENSOR_COMMAND}"
        self._last_state = None

    @property
    def state(self):
        intervals = self._info.get("intervals", [])
        active = _get_active_interval(intervals)
        new_state = active["command"] if active else None
        if new_state != self._last_state and new_state is not None:
            self._hass.bus.async_fire(
                EVENT_COMMAND_ACTIVATED,
                {"instance_id": self._instance_id, "device": self._device, "command": new_state}
            )
        self._last_state = new_state
        return new_state

class AiEnergyPowerKwSensor(AiEnergyBaseSensor):
    """Sensor for current power (kW)."""

    def __init__(self, hass, instance_id, instance_friendly_name, device, info):
        super().__init__(hass, instance_id, instance_friendly_name, device, info)
        self._attr_name = f"{DOMAIN} {instance_friendly_name} {device} Power kW"
        self._attr_unique_id = f"{DOMAIN}_{instance_id}_{device}_{SENSOR_POWER_KW}"

    @property
    def state(self):
        intervals = self._info.get("intervals", [])
        active = _get_active_interval(intervals)
        return active.get("power_kw") if active else None

class AiEnergyEnergyKwhSensor(AiEnergyBaseSensor):
    """Sensor for current energy (kWh)."""

    def __init__(self, hass, instance_id, instance_friendly_name, device, info):
        super().__init__(hass, instance_id, instance_friendly_name, device, info)
        self._attr_name = f"{DOMAIN} {instance_friendly_name} {device} Energy kWh"
        self._attr_unique_id = f"{DOMAIN}_{instance_id}_{device}_{SENSOR_ENERGY_KWH}"

    @property
    def state(self):
        intervals = self._info.get("intervals", [])
        active = _get_active_interval(intervals)
        return active.get("energy_kwh") if active else None

class AiEnergyNextCommandSensor(AiEnergyBaseSensor):
    """Sensor for next command."""

    def __init__(self, hass, instance_id, instance_friendly_name, device, info):
        super().__init__(hass, instance_id, instance_friendly_name, device, info)
        self._attr_name = f"{DOMAIN} {instance_friendly_name} {device} Next Command"
        self._attr_unique_id = f"{DOMAIN}_{instance_id}_{device}_{SENSOR_NEXT_COMMAND}"

    @property
    def state(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        intervals = self._info.get("intervals", [])
        future = [i for i in intervals if datetime.datetime.fromisoformat(i["start"]) > now]
        if not future:
            return None
        next_int = min(future, key=lambda x: x["start"])
        return next_int["command"]

class AiEnergyTotalPowerSensor(SensorEntity):
    """Sensor for total active power (kW)."""

    def __init__(self, hass, instance_id, instance_friendly_name, schedules):
        self._hass = hass
        self._instance_id = instance_id
        self._instance_friendly_name = instance_friendly_name
        self._schedules = schedules
        self._attr_name = f"{DOMAIN} {instance_friendly_name} Total Power kW"
        self._attr_unique_id = f"{DOMAIN}_{instance_id}_{SENSOR_TOTAL_POWER}"

    @property
    def state(self):
        total = 0.0
        for device, data in self._schedules.items():
            intervals = data.get("intervals", [])
            active = _get_active_interval(intervals)
            if active and "power_kw" in active:
                total += active["power_kw"]
        return total if total > 0 else None

class AiEnergyTotalEnergySensor(SensorEntity):
    """Sensor for total estimated energy (kWh) for today."""

    def __init__(self, hass, instance_id, instance_friendly_name, schedules):
        self._hass = hass
        self._instance_id = instance_id
        self._instance_friendly_name = instance_friendly_name
        self._schedules = schedules
        self._attr_name = f"{DOMAIN} {instance_friendly_name} Total Energy kWh Today"
        self._attr_unique_id = f"{DOMAIN}_{instance_id}_{SENSOR_TOTAL_ENERGY}"

    @property
    def state(self):
        today = datetime.datetime.now(datetime.timezone.utc).date()
        total = 0.0
        for device, data in self._schedules.items():
            for interval in data.get("intervals", []):
                start = datetime.datetime.fromisoformat(interval["start"])
                if start.date() == today and "energy_kwh" in interval:
                    total += interval["energy_kwh"]
        return total if total > 0 else None

class AiEnergyLastUpdateSensor(SensorEntity):
    """Sensor for last update timestamp."""

    def __init__(self, hass, instance_id, instance_friendly_name, schedules):
        self._hass = hass
        self._instance_id = instance_id
        self._instance_friendly_name = instance_friendly_name
        self._attr_name = f"{DOMAIN} {instance_friendly_name} Last Update"
        self._attr_unique_id = f"{DOMAIN}_{instance_id}_{SENSOR_LAST_UPDATE}"

    @property
    def state(self):
        return datetime.datetime.now(datetime.timezone.utc).isoformat()
