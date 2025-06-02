"""Storage and update coordinator for ai_energy_scheduler."""

import asyncio
import logging
from typing import Any, Dict

from homeassistant.core import HomeAssistant, callback, Event
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    STORAGE_KEY,
    STORAGE_VERSION,
    EVENT_COMMAND_ACTIVATED,
    BINARY_ALERT,
    ERROR_INVALID_SCHEMA,
)
from .services import validate_and_store_schedule

_LOGGER = logging.getLogger(__name__)


class AIDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to manage ai_energy_scheduler data."""

    def __init__(
        self, hass: HomeAssistant, store: Store, initial_data: dict[str, Any]
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=None,  # Vi kör inte periodisk uppdatering, vi triggar manuellt.
        )
        self.store = store
        self.data: dict[str, Any] = initial_data or {}
        # Början, inga fel:
        self._schema_valid = True

    async def _async_update_data(self) -> dict[str, Any]:
        """
        Denna metod körs om någon triggat async_refresh().
        Här kan vi validera schema och uppdatera self.data.
        """
        # Vi har redan kört validering i servicehanteraren, så om vi når hit
        # antar vi att data är OK. Returnera bara det som finns i self.data.
        return self.data

    async def async_update_schedule(self, new_data: dict[str, Any]) -> None:
        """
        Tar emot nytt schema-data, validerar och sparar.
        Om valideringen lyckas, uppdaterar vi self.data, sparar i Store
        och avfyrar update-signaler.
        Om valideringen misslyckas, sätter binär sensorn till alert.
        """
        try:
            validated = validate_and_store_schedule(self.hass, new_data)
        except Exception as err:
            _LOGGER.error("Schedule validation failed: %s", err)
            self._schema_valid = False
            # När valideringen misslyckas, avfyrar vi ett fel-event för att binärsensorn ska sättas.
            self.hass.bus.async_fire(f"{DOMAIN}_schedule_error", { "error": str(err) })
            raise UpdateFailed(ERROR_INVALID_SCHEMA) from err

        # Om validering lyckades, uppdatera intern data och spara
        self.data = validated
        await self.store.async_save(self.data)
        self._schema_valid = True

        # Avfyra en intern update så alla entiteter kan plocka nytt läge
        self.async_set_updated_data(self.data)

        # Skicka ett event med hela datan (för ex. loggning eller automationer)
        self.hass.bus.async_fire(f"{DOMAIN}_schedule_updated", { "data": self.data })

    @callback
    async def handle_calendar_event(self, event: Event) -> None:
        """
        Hanterar händelser från CalendarEntity (manuella ändringar).
        Payload innehåller: device_id, intervals (helt nya intervalldata).
        Vi uppdaterar vårt interna schema
        """
        device_id = event.data.get("device_id")
        new_intervals = event.data.get("intervals")
        if not device_id or new_intervals is None:
            return

        # Bygg om data-delen för device_id
        schedules = self.data.get("schedules", {})
        if device_id not in schedules:
            _LOGGER.warning("Received calendar event for unknown device: %s", device_id)
            return

        schedules[device_id]["intervals"] = new_intervals
        try:
            # Validera hela schemat innan vi sparar
            await self.async_update_schedule(self.data)
        except UpdateFailed:
            _LOGGER.error("Failed to update schedule after calendar edit for %s", device_id)

