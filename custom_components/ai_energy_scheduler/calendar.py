"""Calendar for AI Energy Scheduler."""

from homeassistant.components.calendar import CalendarEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    if coordinator.schedule:
        for device in coordinator.schedule["schedules"]:
            entities.append(AIESDeviceCalendar(coordinator, device))
    async_add_entities(entities)

class AIESDeviceCalendar(CoordinatorEntity, CalendarEntity):
    """Calendar entity per device."""

    def __init__(self, coordinator, device):
        super().__init__(coordinator)
        self.device = device
        self._attr_name = f"{DOMAIN}_{device}_calendar"

    async def async_get_events(self, hass, start_date, end_date):
        # Return intervals as calendar events
        schedule = self.coordinator.schedule
        if not schedule:
            return []
        events = []
        for interval in schedule["schedules"][self.device]["intervals"]:
            events.append({
                "start": interval["start"],
                "end": interval["end"],
                "summary": interval["command"],
            })
        return events
