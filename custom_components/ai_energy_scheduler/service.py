"""Services for AI Energy Scheduler."""

import logging
import voluptuous as vol
import json

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, SERVICE_VALIDATE, SERVICE_UPDATE, SERVICE_CLEANUP
from .validators import validate_schedule_json

_LOGGER = logging.getLogger(__name__)


def register_services(hass: HomeAssistant, config: ConfigType) -> None:
    """Register AI Energy Scheduler custom services."""

    async def async_validate_schedule(call: ServiceCall) -> None:
        """Validate the provided JSON schedule without applying it."""
        json_input = call.data["schedule"]
        try:
            schedule_data = json.loads(json_input)
            validate_schedule_json(schedule_data)
            _LOGGER.info("Schedule JSON is valid.")
        except (ValueError, HomeAssistantError) as err:
            _LOGGER.error("Schedule validation failed: %s", err)
            raise HomeAssistantError(f"Schedule validation failed: {err}") from err

    async def async_update_schedule(call: ServiceCall) -> None:
        """Apply the provided JSON schedule to the system."""
        json_input = call.data["schedule"]
        try:
            schedule_data = json.loads(json_input)
            validate_schedule_json(schedule_data)
            _LOGGER.info("Schedule JSON passed validation. Applying update.")
        except (ValueError, HomeAssistantError) as err:
            _LOGGER.error("Failed to update schedule: %s", err)
            raise HomeAssistantError(f"Schedule update failed: {err}") from err

        for entry_id, entry_data in hass.data.get(DOMAIN, {}).items():
            coordinator = entry_data["coordinator"]
            await coordinator.async_update_schedule(schedule_data)

    async def async_cleanup_removed(call: ServiceCall) -> None:
        """Manually trigger cleanup of removed devices/entities."""
        for entry_id, entry_data in hass.data.get(DOMAIN, {}).items():
            coordinator = entry_data["coordinator"]
            await coordinator.async_cleanup_entities()

    hass.services.async_register(
        DOMAIN,
        SERVICE_VALIDATE,
        async_validate_schedule,
        vol.Schema({
            vol.Required("schedule"): cv.string,
        }),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE,
        async_update_schedule,
        vol.Schema({
            vol.Required("schedule"): cv.string,
        }),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEANUP,
        async_cleanup_removed,
        vol.Schema({}),
    )
