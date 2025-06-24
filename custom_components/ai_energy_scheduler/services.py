import json
import logging
from typing import Any, Dict, Union

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, SERVICE_SET_SCHEDULE, LOGGER_NAME

_LOGGER = logging.getLogger(LOGGER_NAME)


async def handle_set_schedule(call: ServiceCall) -> None:
    hass: HomeAssistant = call.hass
    coordinator = hass.data.get(DOMAIN, {}).get("coordinator")
    if coordinator is None:
        raise HomeAssistantError("Coordinator not found")

    raw_schedules: Union[str, dict, None] = call.data.get("schedules")
    if raw_schedules is None:
        raise HomeAssistantError("Missing 'schedules' key")

    schedules_dict: dict
    if isinstance(raw_schedules, str):
        try:
            schedules_dict = json.loads(raw_schedules)
        except json.JSONDecodeError as err:
            raise HomeAssistantError(f"Invalid JSON string: {err}") from err
    elif isinstance(raw_schedules, dict):
        schedules_dict = raw_schedules
    else:
        raise HomeAssistantError("'schedules' must be dict or JSON string")

    # Wrap in 'schedules' key if needed
    if "schedules" not in schedules_dict:
        payload = {"schedules": schedules_dict}
    else:
        payload = schedules_dict

    _LOGGER.debug(f"Setting schedule from payload: {payload}")
    try:
        await coordinator.async_update_schedule(payload)
    except Exception as err:
        _LOGGER.error("Failed to update schedule: %s", err)
        raise HomeAssistantError(f"Failed to update schedule: {err}") from err

async def async_setup_services(hass: HomeAssistant) -> None:
    """Register custom services."""
    hass.services.async_register(DOMAIN, SERVICE_SET_SCHEDULE, handle_set_schedule)
