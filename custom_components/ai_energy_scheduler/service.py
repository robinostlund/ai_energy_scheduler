"""Services for AI Energy Scheduler."""

from homeassistant.core import HomeAssistant, ServiceCall
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_services(hass: HomeAssistant, coordinator):
    """Register custom services."""

    async def handle_import_schedule(call: ServiceCall):
        schedule_json = call.data.get("schedule_json")
        try:
            import json
            schedule = json.loads(schedule_json)
        except Exception as e:
            _LOGGER.error("Invalid JSON: %s", e)
            return
        try:
            await coordinator.async_import_schedule(schedule)
        except Exception as e:
            _LOGGER.error("Schedule validation failed: %s", e)

    async def handle_cleanup_removed(call: ServiceCall):
        await coordinator.async_cleanup_removed()
        _LOGGER.info("Cleanup of removed devices requested.")

    hass.services.async_register(DOMAIN, "import_schedule", handle_import_schedule)
    hass.services.async_register(DOMAIN, "cleanup_removed", handle_cleanup_removed)
