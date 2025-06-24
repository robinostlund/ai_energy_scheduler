import logging
import os
import json
from typing import Any, Dict

import jsonschema
# import aiofiles
from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, STORAGE_KEY, STORAGE_VERSION, SCHEMA_FILE, SCHEDULE_UPDATED_EVENT

_LOGGER = logging.getLogger(__name__)


class AIEnergySchedulerCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, store: Store, initial_data: dict, schema: dict) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=None)
        self.store = store
        #self.data: dict = initial_data or {}
        self.data = initial_data
        self.schema = schema

    @property
    def device_ids(self):
        return list(self.data.get("schedules", {}).keys())
    
    async def _async_update_data(self) -> dict:
        return self.data

    async def async_update_schedule(self, new_data: dict) -> None:
        # validate schedule data against schema
        try:
            jsonschema.validate(instance=new_data, schema=self.schema)
        except jsonschema.exceptions.ValidationError as err:
            _LOGGER.error("Schema validation failed: %s", err, exc_info=True)
            raise UpdateFailed(f"Invalid schedule: {err}")

        self.data = new_data
        try:
            await self.store.async_save(self.data)
        except Exception:
            _LOGGER.exception("Failed to save schedule data")

        self.async_set_updated_data(self.data)
        self.hass.bus.async_fire(SCHEDULE_UPDATED_EVENT, {"data": self.data})

    async def async_override_device_interval(self, device_id: str, interval_id: int, interval_command: str) -> None:
        # update a specific interval for a device
        try:
            self.data["schedules"][device_id]["intervals"][interval_id]["command_override"] = interval_command
        except KeyError as err:
            _LOGGER.error(f"Invalid interval id: {err}", exc_info=True)
            raise UpdateFailed(f"Invalid interval id: {err}")

        # update the data in the store
        try:
            await self.store.async_save(self.data)
        except Exception:
            _LOGGER.exception("Failed to save schedule data")

        self.async_set_updated_data(self.data)
        self.hass.bus.async_fire(SCHEDULE_UPDATED_EVENT, {"data": self.data})
