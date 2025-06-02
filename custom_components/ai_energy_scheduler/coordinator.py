from __future__ import annotations

import logging
from datetime import datetime, timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import STORAGE_DIR, Store

from .const import DOMAIN
from typing import Any

_LOGGER = logging.getLogger(__name__)


class AiEnergySchedulerCoordinator(DataUpdateCoordinator):
    """Coordinator to manage state and caching of the AI Energy Scheduler."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_coordinator",
            update_interval=timedelta(minutes=5),
        )
        self.hass = hass
        self.entry_id = entry_id
        self.schedule_data: dict[str, Any] = {}
        self.storage = Store(hass, 1, f"{DOMAIN}/{entry_id}.json")

    async def async_update_data(self):
        """Fetch data for periodic update (not heavily used here)."""
        return self.schedule_data

    async def async_load_from_cache(self):
        """Load schedule data from persistent cache."""
        cached = await self.storage.async_load()
        if cached:
            self.schedule_data = cached
            _LOGGER.debug("Loaded schedule data from cache.")
        else:
            _LOGGER.info("No cached schedule found.")

    async def async_save_to_cache(self):
        """Save schedule data to persistent cache."""
        await self.storage.async_save(self.schedule_data)
        _LOGGER.debug("Saved schedule data to cache.")

    async def async_update_schedule(self, schedule_data: dict[str, Any]):
        """Apply new schedule data and update entities."""
        self.schedule_data = schedule_data
        await self.async_save_to_cache()
        self.async_set_updated_data(schedule_data)

    async def async_cleanup_entities(self):
        """Remove unavailable entities (if applicable)."""
        # In a full integration, this would deregister/remove missing entities.
        _LOGGER.info("Cleanup is not fully implemented yet.")

    @callback
    def get_command(self, device_id: str) -> str | None:
        return self._get_device_state(device_id).get("command")

    @callback
    def get_power_kw(self, device_id: str) -> float | None:
        return self._get_device_state(device_id).get("power_kw")

    @callback
    def get_energy_kwh(self, device_id: str) -> float | None:
        return self._get_device_state(device_id).get("energy_kwh")

    @callback
    def get_next_command(self, device_id: str) -> str | None:
        return self._get_device_state(device_id).get("next_command")

    @callback
    def get_interval_attributes(self, device_id: str) -> dict[str, Any]:
        return self._get_device_state(device_id).get("interval", {})

    @callback
    def get_next_command_attributes(self, device_id: str) -> dict[str, Any]:
        return self._get_device_state(device_id).get("next", {})

    @callback
    def get_total_power_kw(self) -> float:
        return sum(self.get_power_kw(dev) or 0.0 for dev in self.schedule_data)

    @callback
    def get_total_energy_kwh_today(self) -> float:
        return sum(self.get_energy_kwh(dev) or 0.0 for dev in self.schedule_data)

    @callback
    def _get_device_state(self, device_id: str) -> dict[str, Any]:
        return self.schedule_data.get(device_id, {})
