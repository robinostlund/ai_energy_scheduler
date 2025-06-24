import logging
from datetime import datetime, timezone

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN,LOGGER_NAME
from .helpers import Intervals

_LOGGER = logging.getLogger(LOGGER_NAME)

# @dataclass
# class Intervals:
#     """Intervals."""
#     start: str
#     end: str
#     command: str
#     power_kw: float
#     energy_kwh: float | None = None
#     source: str | None = "ai"

class AIEnergySchedulerEntity(CoordinatorEntity):
    """Base class for AI Energy Scheduler entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, device_id: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{self._device_id}_{self.entity_description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers = {(DOMAIN, self._device_id)},
            name = f"AI {self._device_id}",
            manufacturer = "AI Energy Scheduler",
            model = "Energy Scheduler Device",
            serial_number = self._device_id
        )

    @property
    def _get_intervals(self):
        """Return the intervals for the device."""
        schedules = self.coordinator.data.get("schedules", {}).get(self._device_id, {})
        if not schedules:
            _LOGGER.debug(f"No schedule found for device {self._device_id}")
        elif not schedules.get("intervals", []):
            _LOGGER.debug(f"No intervals found for device {self._device_id}")
        else:
            intervals = []
            for interval in schedules.get("intervals"):
                try:
                    start = datetime.fromisoformat(interval.get("start"))
                    end = datetime.fromisoformat(interval.get("end"))
                    cmd = interval.get("command")
                    cmd_override = interval.get("command_override", None)

                    intervals.append(Intervals(
                        start = start,
                        end = end,
                        command = cmd,
                        command_override = cmd_override,
                        power_kw = interval.get("power_kw", 0),
                        energy_kwh = interval.get("energy_kwh", 0),
                        source = interval.get("source", "ai")
                    ))
                except (ValueError) as e:
                    _LOGGER.error(f"Error parsing interval for device {self._device_id}: {e}")
                    continue
            return intervals
        # return empty list if no intervals found
        return []
    
    @property
    def _get_current_interval(self):
        """Return the current interval for the device."""
        now_utc = datetime.now(timezone.utc)
        intervals = self._get_intervals
        for interval in intervals:
            if interval.start <= now_utc < interval.end:
                return interval
        # If no current interval found, return None
        return None
    
    @property
    def _get_intervals_apex_charts(self):
        """Return the intervals for the device in apex charts format."""
        intervals = self._get_intervals
        if not intervals:
            _LOGGER.debug(f"No intervals found for device {self._device_id}")
            return None
        result = []
        for interval in intervals:
            result.append({
                "start": interval.start.isoformat(),
                "end": interval.end.isoformat(),
                "command": interval.command,
                "power_kw": interval.power_kw,
                "energy_kwh": interval.energy_kwh,
            })
        return result

    @callback
    def _handle_coordinator_update(self):
        self.async_write_ha_state()