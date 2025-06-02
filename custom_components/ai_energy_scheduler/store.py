"""Storage and update coordinator for ai_energy_scheduler."""

import logging
import json
import os
from typing import Any, Dict

import jsonschema
from homeassistant.core import HomeAssistant, callback, Event
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util.async_ import run_callback_threadsafe

from .const import (
    DOMAIN,
    STORAGE_KEY,
    STORAGE_VERSION,
    EVENT_COMMAND_ACTIVATED,
    BINARY_ALERT,
    SCHEMA_FILE,
)

_LOGGER = logging.getLogger(__name__)


def _read_schema_file(schema_path: str) -> Dict[str, Any]:
    """Blocking read of schema.json file."""
    with open(schema_path, "r", encoding="utf-8") as file:
        return json.load(file)


class AIDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to manage ai_energy_scheduler data."""

    def __init__(
        self, hass: HomeAssistant, store: Store, initial_data: dict[str, Any]
    ) -> None:
        """Initialize coordinator."""
        _LOGGER.debug("Initializing AIDataUpdateCoordinator with initial_data: %s", initial_data)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=None,  # We trigger updates manually
        )
        self.store = store
        self.data: dict[str, Any] = initial_data or {}
        self._schema_valid = True

    async def _async_update_data(self) -> dict[str, Any]:
        """
        Called whenever Coordinator.refresh() is triggered.
        Since validation already happened in async_update_schedule, simply return self.data.
        """
        _LOGGER.debug("_async_update_data returning current data: %s", self.data)
        return self.data

    async def async_update_schedule(self, new_data: dict[str, Any]) -> None:
        """
        Receive new schedule data, validate against JSON schema, and save.
        If validation fails, set _schema_valid=False and raise UpdateFailed.
        """
        _LOGGER.debug("async_update_schedule called with new_data: %s", new_data)

        # Load schema in executor to avoid blocking event loop
        schema_path = os.path.join(os.path.dirname(__file__), SCHEMA_FILE)
        try:
            schema = await self.hass.async_add_executor_job(_read_schema_file, schema_path)
            _LOGGER.debug("Schema loaded successfully from %s", schema_path)
        except Exception as err:
            _LOGGER.error("Error loading schema.json: %s", err, exc_info=True)
            self._schema_valid = False
            self.hass.bus.async_fire(f"{DOMAIN}_schedule_error", {"error": str(err)})
            raise UpdateFailed(f"Could not load schema: {err}") from err

        # Validate schema
        try:
            jsonschema.validate(instance=new_data, schema=schema)
            _LOGGER.debug("Schema validation passed")
        except Exception as err:
            _LOGGER.error("Schedule validation failed: %s", err, exc_info=True)
            self._schema_valid = False
            self.hass.bus.async_fire(f"{DOMAIN}_schedule_error", {"error": str(err)})
            raise UpdateFailed(f"Invalid schedule: {err}") from err

        # Validation succeeded
        self.data = new_data
        try:
            await self.store.async_save(self.data)
            _LOGGER.debug("Data saved to store successfully: %s", self.data)
        except Exception as err:
            _LOGGER.error("Error saving data to store: %s", err, exc_info=True)
            # Not fatal; continue

        self._schema_valid = True
        _LOGGER.debug("Triggering Coordinator update with new data")
        self.async_set_updated_data(self.data)

        _LOGGER.debug("Firing schedule_updated event with data: %s", self.data)
        self.hass.bus.async_fire(f"{DOMAIN}_schedule_updated", {"data": self.data})

    @callback
    async def handle_calendar_event(self, event: Event) -> None:
        """
        Handle events from CalendarEntity (manual edits).
        Payload contains: device_id, intervals (new intervals list).
        Update the internal data and re-validate/save.
        """
        _LOGGER.debug("handle_calendar_event called with event.data: %s", event.data)
        device_id = event.data.get("device_id")
        new_intervals = event.data.get("intervals")
        if not device_id or new_intervals is None:
            _LOGGER.debug("Invalid calendar event payload: %s", event.data)
            return

        schedules = self.data.get("schedules", {})
        if device_id not in schedules:
            _LOGGER.warning("Received calendar event for unknown device: %s", device_id)
            return

        schedules[device_id]["intervals"] = new_intervals
        _LOGGER.debug("Updated intervals for device_id=%s to %s", device_id, new_intervals)
        try:
            _LOGGER.debug("Calling async_update_schedule after calendar event")
            await self.async_update_schedule(self.data)
            _LOGGER.debug("async_update_schedule succeeded after calendar event")
        except UpdateFailed:
            _LOGGER.error("Failed to update schedule after calendar edit for %s", device_id, exc_info=True)
