"""Coordinator for AI Energy Scheduler."""

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.storage import Store
from .const import DOMAIN, STORAGE_KEY, STORAGE_VERSION
from .validators import validate_schedule
import logging

_LOGGER = logging.getLogger(__name__)

class AIESDataCoordinator(DataUpdateCoordinator):
    """Data coordinator for AI Energy Scheduler."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=None,  # Manual update only on schedule import
        )
        self.entry = entry
        self.schedule = None
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.alert = False

    async def async_init(self):
        """Restore schedule from cache."""
        cached = await self._store.async_load()
        if cached:
            try:
                validate_schedule(cached)
                self.schedule = cached
                _LOGGER.info("Loaded schedule from cache.")
            except Exception as err:
                _LOGGER.error("Cached schedule invalid: %s", err)
                self.alert = True

    async def async_import_schedule(self, schedule: dict):
        """Import and validate new schedule."""
        try:
            validate_schedule(schedule)
            self.schedule = schedule
            await self._store.async_save(schedule)
            self.alert = False
            await self.async_request_refresh()
            _LOGGER.info("Schedule imported and validated.")
        except Exception as err:
            self.alert = True
            _LOGGER.error("Failed to import schedule: %s", err)
            raise

    async def async_cleanup_removed(self):
        """Cleanup entities/devices not in current schedule."""
        # This is a stub; actual entity removal is managed in setup/unload.
        pass
