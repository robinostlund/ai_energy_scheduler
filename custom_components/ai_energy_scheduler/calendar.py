"""Calendar platform for ai_energy_scheduler."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.components.calendar import CalendarEntity
from homeassistant.components.calendar import CalendarEvent
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import Event

from .const import DOMAIN
from .store import AIDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up calendar entities."""
    coordinator: AIDataUpdateCoordinator = hass.data[DOMAIN]["coordinator"]
    entities = []

    for device_id in coordinator.data.get("schedules", {}):
        entities.append(AIEnergyCalendar(coordinator, device_id))

    async_add_entities(entities)

    # Lyssna på schema-uppdateringar för att hantera nya/avlägsna kalendrar
    async def _async_schedule_updated(event: Event):
        new_device_ids = set(coordinator.data.get("schedules", {}))
        existing = {ent.device_id for ent in entities}
        # Lägg till nya
        for dev in new_device_ids - existing:
            entities.append(AIEnergyCalendar(coordinator, dev))
            async_add_entities([entities[-1]])
        # Ta bort entiteter som inte längre finns (kanske sätt till unavailable)
        # För enkelhet: HA sätter till unavailable baserat på available()

    hass.bus.async_listen(f"{DOMAIN}_schedule_updated", _async_schedule_updated)


class AIEnergyCalendar(CoordinatorEntity, CalendarEntity):
    """Calendar entity for a single device."""

    def __init__(self, coordinator: AIDataUpdateCoordinator, device_id: str):
        """Initialize calendar."""
        super().__init__(coordinator)
        self.device_id = device_id
        self._attr_name = f"{device_id}"
        self._attr_unique_id = f"{DOMAIN}_{device_id}_calendar"
        self._attr_entity_registry_enabled_default = True
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def event_position(self) -> str:
        """Sortering av events i kalendern: earliest first."""
        return "start_time"

    @property
    def available(self) -> bool:
        """Tillgänglig om enheten finns i schemat."""
        return self.device_id in self.coordinator.data.get("schedules", {})

    async def async_get_events(self, hass, start_datetime, end_datetime) -> list[CalendarEvent]:
        """
        Returnerar en lista över CalendarEvent-objekt för perioden [start, end].
        Här mapper vi schemats intervall till CalendarEvent.
        """
        events = []
        device_data = self.coordinator.data.get("schedules", {}).get(self.device_id, {})
        for interval in device_data.get("intervals", []):
            start = datetime.fromisoformat(interval["start"])
            end = datetime.fromisoformat(interval["end"])
            # Endast inkludera events som ligger inom förfrågan
            if end < start_datetime or start > end_datetime:
                continue
            summary = interval.get("command", "")
            events.append(
                CalendarEvent(
                    start=start,
                    end=end,
                    summary=summary,
                    description=f"Power: {interval.get('power_kw')} kW, Energy: {interval.get('energy_kwh')} kWh, Source: {interval.get('source')}",
                    all_day=False,
                )
            )
        return events

    async def async_add_event(self, hass, event: CalendarEvent) -> str | None:
        """
        Hanterar när användaren skapar nytt event manuellt i kalender-UI.
        Vi tolkar inmatade tider/sammanfattning som ett nytt interval.
        Returnerar event_id (vi kan generera en slumpad).
        """
        try:
            new_interval = {
                "start": event.start.isoformat(),
                "end": event.end.isoformat(),
                "command": event.summary,
                "power_kw": None,
                "energy_kwh": None,
                "source": "manual",
            }
            # Hämta befintligt schema från coordinator
            schedules = self.coordinator.data.get("schedules", {})
            if self.device_id not in schedules:
                _LOGGER.error("Device %s not in schedules", self.device_id)
                return None
            schedules[self.device_id]["intervals"].append(new_interval)
            # Skicka ett internt event för att uppdatera Coordinator
            self.hass.bus.async_fire(f"{DOMAIN}_calendar_event", {
                "device_id": self.device_id,
                "intervals": schedules[self.device_id]["intervals"]
            })
            # Generera event_id (vi returnerar str)
            return f"{self.device_id}_{event.start.timestamp()}"
        except Exception as err:
            _LOGGER.error("Error adding event from calendar: %s", err)
            return None

    async def async_update_event(self, hass, event: CalendarEvent) -> bool:
        """
        Hanterar när användaren editerar ett befintligt event.
        Vi måste hitta motsvarande interval (baserat på unikt event_id eller starttid),
        uppdatera intervallet i schemat och spara.
        För enkelhet: vi itererar över alla intervall och matchar på starttid.
        """
        schedules = self.coordinator.data.get("schedules", {})
        device_data = schedules.get(self.device_id, {})
        updated = False
        for interval in device_data.get("intervals", []):
            if datetime.fromisoformat(interval["start"]) == event.start:
                # Uppdatera fält
                interval["start"] = event.start.isoformat()
                interval["end"] = event.end.isoformat()
                interval["command"] = event.summary
                interval["source"] = "manual"
                updated = True
                break
        if updated:
            self.hass.bus.async_fire(f"{DOMAIN}_calendar_event", {
                "device_id": self.device_id,
                "intervals": device_data.get("intervals", [])
            })
        return updated

    async def async_delete_event(self, hass, event_id: str) -> bool:
        """
        Hanterar när användaren tar bort ett event.
        Vi tar bort interval baserat på event_id-format (device_timestamp).
        """
        schedules = self.coordinator.data.get("schedules", {})
        device_data = schedules.get(self.device_id, {})
        removed = False
        for interval in list(device_data.get("intervals", [])):
            if f"{self.device_id}_{datetime.fromisoformat(interval['start']).timestamp()}" == event_id:
                device_data["intervals"].remove(interval)
                removed = True
                break
        if removed:
            self.hass.bus.async_fire(f"{DOMAIN}_calendar_event", {
                "device_id": self.device_id,
                "intervals": device_data.get("intervals", [])
            })
        return removed

