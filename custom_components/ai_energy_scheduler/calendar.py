"""Calendar platform for ai_energy_scheduler."""

import logging
from datetime import datetime
from typing import Any, Optional

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util.dt import parse_datetime, utcnow

from .const import DOMAIN
from .store import AIDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """
    Set up calendar entries for ai_energy_scheduler via Config Entry.
    Detta anropas av Home Assistant när plattformen laddas via async_forward_entry_setups.
    """
    _LOGGER.debug("async_setup_entry (calendar) called for entry_id=%s", entry.entry_id)
    coordinator: AIDataUpdateCoordinator = hass.data[DOMAIN]["coordinator"]
    entities: list[AIEnergyCalendar] = []

    for device_id in coordinator.data.get("schedules", {}):
        _LOGGER.debug("Creating AIEnergyCalendar for device_id=%s", device_id)
        entities.append(AIEnergyCalendar(coordinator, device_id))

    async_add_entities(entities)
    _LOGGER.debug("Initial calendar entities added: %s", [ent.entity_id for ent in entities])

    async def _async_schedule_updated(event: Event) -> None:
        _LOGGER.debug("Calendar platform received schedule_updated event: %s", event.data)
        current_device_ids = set(coordinator.data.get("schedules", {}))
        existing_device_ids = {ent.device_id for ent in entities}

        # Lägg till nya kalendrar
        for device_id in current_device_ids - existing_device_ids:
            _LOGGER.debug("Detected new device_id=%s, creating calendar entity", device_id)
            new_entity = AIEnergyCalendar(coordinator, device_id)
            entities.append(new_entity)
            async_add_entities([new_entity])

        # Markera borttagna enheter som unavailable
        for ent in entities:
            if ent.device_id not in current_device_ids:
                _LOGGER.debug("Marking calendar entity unavailable for device_id=%s", ent.device_id)
                ent._attr_available = False

    hass.bus.async_listen(f"{DOMAIN}_schedule_updated", _async_schedule_updated)


class AIEnergyCalendar(CoordinatorEntity, CalendarEntity):
    """Calendar entity for a single device."""

    def __init__(self, coordinator: AIDataUpdateCoordinator, device_id: str):
        """Initialize calendar."""
        super().__init__(coordinator)
        self.device_id = device_id
        self._attr_name = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_calendar"
        self._attr_entity_registry_enabled_default = True
        self._attr_available = True
        _LOGGER.debug("Initialized AIEnergyCalendar for device_id=%s", device_id)

    @property
    def device_info(self) -> DeviceInfo:
        """
        Return a DeviceInfo dict so that Home Assistant groups this calendar
        under the same device as the sensors for this device_id.
        """
        return DeviceInfo(
            identifiers={(DOMAIN, self.device_id)},
            name=self.device_id,
            manufacturer="AI Energy Scheduler",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def event_position(self) -> str:
        """Sort events by start_time."""
        return "start_time"

    @property
    def available(self) -> bool:
        """Return True if the device still exists in the schedule."""
        _LOGGER.debug("AIEnergyCalendar.available called for device_id=%s: %s", self.device_id, self._attr_available)
        return self._attr_available

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_datetime: datetime,
        end_datetime: datetime,
    ) -> list[CalendarEvent]:
        """
        Return a list of CalendarEvent objects for [start_datetime, end_datetime].
        Map schedule intervals to CalendarEvent.
        """
        _LOGGER.debug(
            "async_get_events called for device_id=%s, start=%s, end=%s",
            self.device_id,
            start_datetime,
            end_datetime,
        )
        events: list[CalendarEvent] = []
        device_data = self.coordinator.data.get("schedules", {}).get(self.device_id, {})
        for interval in device_data.get("intervals", []):
            # Parse timestamps as offset-aware
            start = parse_datetime(interval["start"])
            end = parse_datetime(interval["end"])
            if start is None or end is None:
                _LOGGER.warning("Skipping interval with invalid datetime format: %s", interval)
                continue
            if end < start_datetime or start > end_datetime:
                continue
            summary = interval.get("command", "")
            events.append(
                CalendarEvent(
                    start=start,
                    end=end,
                    summary=summary,
                    description=(
                        f"Power: {interval.get('power_kw')} kW, "
                        f"Energy: {interval.get('energy_kwh')} kWh, "
                        f"Source: {interval.get('source')}"
                    ),
                )
            )
        _LOGGER.debug("async_get_events returning %d events for device_id=%s", len(events), self.device_id)
        return events

    @property
    def event(self) -> Optional[CalendarEvent]:
        """
        Return the currently active CalendarEvent, if any.
        If none is active, return the next upcoming event.
        """
        now = utcnow()
        device_data = self.coordinator.data.get("schedules", {}).get(self.device_id, {})
        intervals = device_data.get("intervals", [])
        next_event: Optional[CalendarEvent] = None
        next_start: Optional[datetime] = None

        for interval in intervals:
            start = parse_datetime(interval["start"])
            end = parse_datetime(interval["end"])
            if start is None or end is None:
                continue
            # Om vi är mitt i ett intervall, returnera det direkt
            if start <= now < end:
                summary = interval.get("command", "")
                return CalendarEvent(
                    start=start,
                    end=end,
                    summary=summary,
                    description=(
                        f"Power: {interval.get('power_kw')} kW, "
                        f"Energy: {interval.get('energy_kwh')} kWh, "
                        f"Source: {interval.get('source')}"
                    ),
                )
            # Hitta nästa kommande event
            if start > now:
                if next_start is None or start < next_start:
                    next_start = start
                    next_event = CalendarEvent(
                        start=start,
                        end=end,
                        summary=interval.get("command", ""),
                        description=(
                            f"Power: {interval.get('power_kw')} kW, "
                            f"Energy: {interval.get('energy_kwh')} kWh, "
                            f"Source: {interval.get('source')}"
                        ),
                    )

        return next_event

    async def async_add_event(
        self, hass: HomeAssistant, event: CalendarEvent
    ) -> str | None:
        """
        Handle when a user creates a new event via the calendar UI.
        Build a new interval and fire a calendar_event so Coordinator updates data.
        """
        _LOGGER.debug("async_add_event called for device_id=%s with event: %s", self.device_id, event)
        try:
            new_interval = {
                "start": event.start.isoformat(),
                "end": event.end.isoformat(),
                "command": event.summary,
                "power_kw": None,
                "energy_kwh": None,
                "source": "manual",
            }
            schedules = self.coordinator.data.get("schedules", {})
            if self.device_id not in schedules:
                _LOGGER.error("Device %s not in schedules", self.device_id)
                return None
            schedules[self.device_id]["intervals"].append(new_interval)
            _LOGGER.debug("Added new interval: %s", new_interval)
            hass.bus.async_fire(
                f"{DOMAIN}_calendar_event",
                {"device_id": self.device_id, "intervals": schedules[self.device_id]["intervals"]},
            )
            event_id = f"{self.device_id}_{event.start.timestamp()}"
            _LOGGER.debug("Returning event_id: %s", event_id)
            return event_id
        except Exception as err:
            _LOGGER.error("Error adding event from calendar: %s", err, exc_info=True)
            return None

    async def async_update_event(
        self, hass: HomeAssistant, event: CalendarEvent
    ) -> bool:
        """
        Handle when a user edits an existing event.
        Match interval based on start time and update schedule.
        """
        _LOGGER.debug("async_update_event called for device_id=%s with event: %s", self.device_id, event)
        schedules = self.coordinator.data.get("schedules", {})
        device_data = schedules.get(self.device_id, {})
        updated = False
        for interval in device_data.get("intervals", []):
            if parse_datetime(interval["start"]) == event.start:
                _LOGGER.debug("Matching interval found, updating interval to: %s", event)
                interval["start"] = event.start.isoformat()
                interval["end"] = event.end.isoformat()
                interval["command"] = event.summary
                interval["source"] = "manual"
                updated = True
                break
        if updated:
            hass.bus.async_fire(
                f"{DOMAIN}_calendar_event",
                {"device_id": self.device_id, "intervals": device_data.get("intervals", [])},
            )
            _LOGGER.debug("Calendar event update fired for device_id=%s", self.device_id)
        else:
            _LOGGER.warning("No matching interval found for update on device_id=%s", self.device_id)
        return updated

    async def async_delete_event(self, hass: HomeAssistant, event_id: str) -> bool:
        """
        Handle when a user deletes an event.
        Remove the interval based on event_id (format: device_timestamp).
        """
        _LOGGER.debug("async_delete_event called for device_id=%s with event_id: %s", self.device_id, event_id)
        schedules = self.coordinator.data.get("schedules", {})
        device_data = schedules.get(self.device_id, {})
        removed = False
        for interval in list(device_data.get("intervals", [])):
            if f"{self.device_id}_{parse_datetime(interval['start']).timestamp()}" == event_id:
                _LOGGER.debug("Removing interval: %s", interval)
                device_data["intervals"].remove(interval)
                removed = True
                break
        if removed:
            hass.bus.async_fire(
                f"{DOMAIN}_calendar_event",
                {"device_id": self.device_id, "intervals": device_data.get("intervals", [])},
            )
            _LOGGER.debug("Calendar event delete fired for device_id=%s", self.device_id)
        else:
            _LOGGER.warning("No matching interval found for delete on device_id=%s", self.device_id)
        return removed
