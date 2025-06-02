"""Sensor platform for ai_energy_scheduler."""

from datetime import datetime, timezone
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.dt import parse_datetime

from .const import (
    DOMAIN,
    SUFFIX_COMMAND,
    SUFFIX_POWER,
    SUFFIX_ENERGY,
    SUFFIX_NEXT,
    SENSOR_TOTAL_POWER,
    SENSOR_TOTAL_ENERGY,
    SENSOR_LAST_UPDATE,
    ICON_SENSOR,
    ICON_SUMMARY_POWER,
    ICON_SUMMARY_ENERGY,
    EVENT_COMMAND_ACTIVATED,
)
from .store import AIDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """
    Set up sensor entities for ai_energy_scheduler via Config Entry.
    This is called by Home Assistant when the platform is loaded via async_forward_entry_setups.
    """
    _LOGGER.debug("async_setup_entry (sensor) called for entry_id=%s", entry.entry_id)
    coordinator: AIDataUpdateCoordinator = hass.data[DOMAIN]["coordinator"]
    entities: list[SensorEntity] = []

    # Create sensors for each device_id
    for device_id in coordinator.data.get("schedules", {}):
        _LOGGER.debug("Creating sensors for device_id=%s", device_id)
        entities.extend(_create_device_sensors(device_id, coordinator))

    # Add summary sensors
    _LOGGER.debug("Adding summary sensors (total_power, total_energy, last_update)")
    entities.append(TotalPowerSensor(coordinator))
    entities.append(TotalEnergySensor(coordinator))
    entities.append(LastUpdateSensor(coordinator))

    async_add_entities(entities)
    _LOGGER.debug("Initial sensor entities added: %s", [ent.entity_id for ent in entities])

    async def _async_schedule_updated(event: Event):
        _LOGGER.debug("Sensor platform received schedule_updated event: %s", event.data)
        new_entities: list[SensorEntity] = []
        existing_device_ids = {
            ent.device_id for ent in entities if isinstance(ent, DeviceSensor)
        }
        current_device_ids = set(coordinator.data.get("schedules", {}))

        # Create sensors for newly-added devices
        for device_id in current_device_ids - existing_device_ids:
            _LOGGER.debug("Detected new device_id=%s, creating sensors", device_id)
            new_entities.extend(_create_device_sensors(device_id, coordinator))

        if new_entities:
            async_add_entities(new_entities)
            _LOGGER.debug("Added new sensor entities: %s", [ent.entity_id for ent in new_entities])

    hass.bus.async_listen(f"{DOMAIN}_schedule_updated", _async_schedule_updated)


def _create_device_sensors(device_id: str, coordinator: AIDataUpdateCoordinator):
    """Helper: create four sensors (command, power, energy, next) per device."""
    return [
        DeviceSensor(coordinator, device_id, SUFFIX_COMMAND),
        DeviceSensor(coordinator, device_id, SUFFIX_POWER),
        DeviceSensor(coordinator, device_id, SUFFIX_ENERGY),
        DeviceSensor(coordinator, device_id, SUFFIX_NEXT),
    ]


class DeviceSensor(CoordinatorEntity, SensorEntity):
    """Generic sensor for each device and attribute."""

    def __init__(self, coordinator: AIDataUpdateCoordinator, device_id: str, suffix: str):
        """Initialize sensor."""
        super().__init__(coordinator)
        self.device_id = device_id
        self.suffix = suffix
        self._attr_name = f"{device_id}_{suffix}"
        self._attr_unique_id = f"{DOMAIN}_{device_id}_{suffix}"
        self._attr_icon = ICON_SENSOR
        _LOGGER.debug("Initialized DeviceSensor for %s_%s", device_id, suffix)

    @property
    def device_info(self) -> DeviceInfo:
        """
        Return a DeviceInfo dict so that Home Assistant groups all sensors
        for this device_id under the same "device" in UI.
        """
        return DeviceInfo(
            identifiers={(DOMAIN, self.device_id)},
            name=self.device_id,
            manufacturer="AI Energy Scheduler",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def available(self) -> bool:
        """Available only if the device still exists in the schedule."""
        available = self.device_id in self.coordinator.data.get("schedules", {})
        _LOGGER.debug("DeviceSensor.available called for %s_%s: %s", self.device_id, self.suffix, available)
        return available

    @property
    def state(self) -> Any:
        """Return the current value based on suffix."""
        schedules = self.coordinator.data.get("schedules", {})
        device_data = schedules.get(self.device_id)
        if not device_data:
            _LOGGER.debug("DeviceSensor.state: no data found for device_id=%s", self.device_id)
            return None

        now = datetime.now(timezone.utc)
        intervals = device_data.get("intervals", [])
        current_command = None
        current_power = None
        current_energy = None
        next_command = None

        for interval in intervals:
            start = parse_datetime(interval["start"])
            end = parse_datetime(interval["end"])
            if start <= now < end:
                current_command = interval.get("command")
                current_power = interval.get("power_kw")
                current_energy = interval.get("energy_kwh")
                break

        sorted_intervals = sorted(intervals, key=lambda x: parse_datetime(x["start"]))
        for interval in sorted_intervals:
            st = parse_datetime(interval["start"])
            if st > now:
                next_command = interval.get("command")
                break

        if self.suffix == SUFFIX_COMMAND:
            value = current_command or "off"
        elif self.suffix == SUFFIX_POWER:
            value = current_power
        elif self.suffix == SUFFIX_ENERGY:
            value = current_energy
        elif self.suffix == SUFFIX_NEXT:
            value = next_command
        else:
            value = None

        _LOGGER.debug("DeviceSensor.state called for %s_%s, returning: %s", self.device_id, self.suffix, value)
        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose device_id for debugging."""
        return {"device_id": self.device_id}

    @property
    def unit_of_measurement(self) -> str | None:
        """Unit: kW for power, kWh for energy."""
        if self.suffix == SUFFIX_POWER:
            return "kW"
        if self.suffix == SUFFIX_ENERGY:
            return "kWh"
        return None

    async def async_update(self):
        """
        Called when the Coordinator updates data.
        If suffix == command and the value changes, fire an event.
        """
        old_state = self._attr_native_value
        await self.coordinator.async_request_refresh()
        new_state = self.state
        if self.suffix == SUFFIX_COMMAND and new_state != old_state:
            _LOGGER.debug(
                "Command changed for device_id=%s, old=%s, new=%s. Firing event.",
                self.device_id,
                old_state,
                new_state,
            )
            self.hass.bus.async_fire(
                f"{DOMAIN}_{EVENT_COMMAND_ACTIVATED}",
                {"device_id": self.device_id, "command": new_state},
            )


class TotalPowerSensor(CoordinatorEntity, SensorEntity):
    """Sensor that sums all power for the current hour."""

    def __init__(self, coordinator: AIDataUpdateCoordinator):
        """Initialize total power sensor."""
        super().__init__(coordinator)
        self._attr_name = SENSOR_TOTAL_POWER
        self._attr_unique_id = f"{DOMAIN}_{SENSOR_TOTAL_POWER}"
        self._attr_icon = ICON_SUMMARY_POWER
        _LOGGER.debug("Initialized TotalPowerSensor")

    @property
    def device_info(self) -> DeviceInfo:
        """
        Return a DeviceInfo dict so that Home Assistant groups this summary sensor
        under the integration’s device.
        """
        return DeviceInfo(
            identifiers={(DOMAIN, DOMAIN)},
            name="AI Energy Scheduler",
            manufacturer="AI Energy Scheduler",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def state(self) -> float:
        """Calculate total power (kW) by summing active intervals."""
        total = 0.0
        now = datetime.now(timezone.utc)
        for device_data in self.coordinator.data.get("schedules", {}).values():
            for interval in device_data.get("intervals", []):
                start = parse_datetime(interval["start"])
                end = parse_datetime(interval["end"])
                if start <= now < end:
                    pw = interval.get("power_kw") or 0.0
                    total += pw
        total_rounded = round(total, 2)
        _LOGGER.debug("TotalPowerSensor.state calculated: %s kW", total_rounded)
        return total_rounded

    @property
    def unit_of_measurement(self) -> str:
        return "kW"


class TotalEnergySensor(CoordinatorEntity, SensorEntity):
    """Sensor for accumulated energy consumed so far today."""

    def __init__(self, coordinator: AIDataUpdateCoordinator):
        """Initialize total energy sensor."""
        super().__init__(coordinator)
        self._attr_name = SENSOR_TOTAL_ENERGY
        self._attr_unique_id = f"{DOMAIN}_{SENSOR_TOTAL_ENERGY}"
        self._attr_icon = ICON_SUMMARY_ENERGY
        _LOGGER.debug("Initialized TotalEnergySensor")

    @property
    def device_info(self) -> DeviceInfo:
        """
        Return a DeviceInfo dict so that Home Assistant groups this summary sensor
        under the integration’s device.
        """
        return DeviceInfo(
            identifiers={(DOMAIN, DOMAIN)},
            name="AI Energy Scheduler",
            manufacturer="AI Energy Scheduler",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def state(self) -> float:
        """Calculate energy (kWh) for all completed intervals today."""
        total_energy = 0.0
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        for device_data in self.coordinator.data.get("schedules", {}).values():
            for interval in device_data.get("intervals", []):
                st = parse_datetime(interval["start"])
                en = parse_datetime(interval["end"])
                if st >= today_start and en <= now:
                    total_energy += interval.get("energy_kwh") or 0.0
        total_rounded = round(total_energy, 2)
        _LOGGER.debug("TotalEnergySensor.state calculated: %s kWh", total_rounded)
        return total_rounded

    @property
    def unit_of_measurement(self) -> str:
        return "kWh"


class LastUpdateSensor(CoordinatorEntity, SensorEntity):
    """Sensor that shows the timestamp of the last schedule update."""

    def __init__(self, coordinator: AIDataUpdateCoordinator):
        """Initialize last update sensor."""
        super().__init__(coordinator)
        self._attr_name = SENSOR_LAST_UPDATE
        self._attr_unique_id = f"{DOMAIN}_{SENSOR_LAST_UPDATE}"
        self._attr_icon = ICON_SENSOR
        _LOGGER.debug("Initialized LastUpdateSensor")

    @property
    def device_info(self) -> DeviceInfo:
        """
        Return a DeviceInfo dict so that Home Assistant groups this summary sensor
        under the integration’s device.
        """
        return DeviceInfo(
            identifiers={(DOMAIN, DOMAIN)},
            name="AI Energy Scheduler",
            manufacturer="AI Energy Scheduler",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def state(self) -> str:
        """Return last update in ISO format, or 'unknown' if none."""
        last = self.coordinator.data.get("last_update")
        state = last if last else "unknown"
        _LOGGER.debug("LastUpdateSensor.state returning: %s", state)
        return state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Show extra attribute: number of devices."""
        attrs = {"num_devices": len(self.coordinator.data.get("schedules", {}))}
        _LOGGER.debug("LastUpdateSensor.extra_state_attributes: %s", attrs)
        return attrs

    async def async_update(self):
        """Set last_update when Coordinator refreshes."""
        _LOGGER.debug("LastUpdateSensor.async_update called")
        await self.coordinator.async_request_refresh()
        now_iso = datetime.now(timezone.utc).isoformat()
        self.coordinator.data["last_update"] = now_iso
        try:
            await self.coordinator.store.async_save(self.coordinator.data)
            _LOGGER.debug("Last update timestamp saved to store: %s", now_iso)
        except Exception as err:
            _LOGGER.error("Error saving last_update to store: %s", err, exc_info=True)
