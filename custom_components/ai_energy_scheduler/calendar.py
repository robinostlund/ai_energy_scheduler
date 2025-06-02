from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional, List

from homeassistant.components.calendar import (
    CalendarEntity,
    CalendarEvent,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .coordinator import AiEnergySchedulerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up AI Energy Scheduler calendars."""
    coordinator: AiEnergySchedulerCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = []
    for device_id in coordinator.schedule_data.keys():
        entities.append(SchedulerCalendarEntity(coordinator, device_id))

    async_add_entities(entities, update_before_add=True)


class SchedulerCalendarEntity(CalendarEntity):
    """Calendar entity to represent scheduled command intervals."""

    def __init__(self, coordinator: AiEnergySchedulerCoordinator, device_id: str) -> None:
        self._coordinator = coordinator
        self._device_id = device_id
        self._attr_name = f"{device_id} Schedule"
        self._attr_unique_id = f"{DOMAIN}_{device_id}_calendar"
        self._events: List[CalendarEvent] = []

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events (commands) for the specified time range."""
        events = []
        device_schedule = self._coordinator.schedule_data.get(self._device_id, {}).get("schedule", [])

        for item in device_schedule:
            try:
                start = datetime.fromisoformat(item["start"])
                end = datetime.fromisoformat(item["end"])
                if start < end_date and end > start_date:
                    events.append(
                        CalendarEvent(
                            summary=item.get("command", "Unknown"),
                            start=start,
                            end=end,
                        )
                    )
            except Exception as e:
                _LOGGER.warning(f"Invalid schedule item for {self._device_id}: {e}")

        return events

    @property
    def event(self) -> Optional[CalendarEvent]:
        """Return the next upcoming event."""
        now = datetime.now()
        future_events = [
            e for e in self._events if e.start >= now
        ]
        return min(future_events, default=None, key=lambda e: e.start)

    async def async_update(self) -> None:
        """Refresh the list of upcoming events."""
        now = datetime.now()
        future = now + timedelta(days=7)
        self._events = await self.async_get_events(self._coordinator.hass, now, future)
