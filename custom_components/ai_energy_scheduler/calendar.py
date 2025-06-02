"""Calendar entities for AI Energy Scheduler."""

from homeassistant.components.calendar import CalendarEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Not used: entities created by service."""
    pass

def create_calendars_for_instance(hass, instance_id, instance_friendly_name, schedule):
    """Return a list of calendar entities for all devices in an instance."""
    calendars = []
    schedules = schedule.get("schedules", {})
    for device, info in schedules.items():
        calendars.append(AiEnergyDeviceCalendar(instance_id, instance_friendly_name, device, info))
    return calendars

class AiEnergyDeviceCalendar(CalendarEntity):
    """Calendar entity for a scheduled device."""

    def __init__(self, instance_id, instance_friendly_name, device, info):
        self._instance_id = instance_id
        self._instance_friendly_name = instance_friendly_name
        self._device = device
        self._info = info
        self._attr_unique_id = f"{DOMAIN}_{instance_id}_{device}_calendar"
        self._attr_name = f"{DOMAIN} {instance_friendly_name} {device} Schedule"

    async def async_get_events(self, hass, start_date, end_date):
        intervals = self._info.get("intervals", [])
        for interval in intervals:
            yield {
                "summary": interval.get("command", ""),
                "start": interval.get("start"),
                "end": interval.get("end")
            }
