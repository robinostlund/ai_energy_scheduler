"""Calendar platform for AI Energy Scheduler"""

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from datetime import datetime, timedelta
import voluptuous as vol

DOMAIN = "ai_energy_scheduler"
PLATFORMS = ["calendar"]

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities: AddEntitiesCallback) -> None:
    data = hass.data[DOMAIN][config_entry.entry_id]
    schedules = data.get("schedules", {})
    entities = []

    for device, info in schedules.items():
        name = f"{device.replace('_', ' ').title()} Schedule"
        entity = AIEnergySchedulerCalendar(device, name, info.get("intervals", []))
        entities.append(entity)

    async_add_entities(entities, update_before_add=True)


class AIEnergySchedulerCalendar(CalendarEntity):
    def __init__(self, device: str, name: str, intervals: list) -> None:
        self._attr_name = name
        self._device = device
        self._intervals = intervals
        self._event = None
        self._attr_unique_id = f"ai_energy_scheduler_{device}_calendar"

    @property
    def event(self) -> CalendarEvent | None:
        return self._event

    async def async_update(self) -> None:
        now = datetime.now().astimezone()
        for interval in self._intervals:
            start = datetime.fromisoformat(interval["start"])
            end = datetime.fromisoformat(interval["end"])
            if start <= now < end:
                self._event = CalendarEvent(
                    summary=interval["command"],
                    start=start,
                    end=end,
                    description=f"{interval['power_kw']} kW / {interval['energy_kwh']} kWh",
                )
                return
        self._event = None