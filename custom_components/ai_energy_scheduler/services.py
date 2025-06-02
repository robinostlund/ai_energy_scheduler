"""Service handlers for ai_energy_scheduler."""

import asyncio
import json
import logging
import os
from typing import Any, Dict

import jsonschema
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN,
    SCHEMA_FILE,
    SERVICE_SET_SCHEDULE,
    SERVICE_CLEANUP_REMOVED,
    LOGGER_NAME,
    EVENT_COMMAND_ACTIVATED,
    BINARY_ALERT,
)
from .store import AIDataUpdateCoordinator

_LOGGER = logging.getLogger(LOGGER_NAME)


def async_setup_services(hass: HomeAssistant) -> None:
    """Register services for this integration."""
    hass.services.async_register(DOMAIN, SERVICE_SET_SCHEDULE, handle_set_schedule)
    hass.services.async_register(DOMAIN, SERVICE_CLEANUP_REMOVED, handle_cleanup_removed)


def _load_schema(hass: HomeAssistant) -> Dict[str, Any]:
    """Load JSON schema from schema.json file."""
    schema_path = os.path.join(
        os.path.dirname(__file__), SCHEMA_FILE
    )
    with open(schema_path, "r", encoding="utf-8") as file:
        return json.load(file)


def validate_and_store_schedule(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the incoming schedule data against the JSON schema.
    Return clean data if valid, or raise HomeAssistantError on failure.
    """
    schema = _load_schema(hass)
    try:
        jsonschema.validate(instance=data, schema=schema)
        return data
    except jsonschema.exceptions.ValidationError as err:
        _LOGGER.error("Schedule validation error: %s", err)
        raise HomeAssistantError(f"Invalid schedule format: {err.message}")


async def handle_set_schedule(call: ServiceCall) -> None:
    """
    Service handler for ai_energy_scheduler.set_schedule.
    Förväntar sig en parameter: schedules: {...} (helt JSON-objekt).
    Validerar, sparar, uppdaterar Coordinator.
    """
    hass: HomeAssistant = call.hass
    coordinator: AIDataUpdateCoordinator = hass.data[DOMAIN]["coordinator"]

    schedule_data = call.data
    if not schedule_data:
        raise HomeAssistantError("No schedule data provided")

    try:
        # Kör validering + spara i Coordinator
        await coordinator.async_update_schedule(schedule_data)
    except Exception as err:
        _LOGGER.error("Failed to set schedule: %s", err)
        raise

    _LOGGER.info("Schedule successfully updated via service")


async def handle_cleanup_removed(call: ServiceCall) -> None:
    """
    Service handler for ai_energy_scheduler.cleanup_removed.
    Rensar entiteter som inte längre finns i schemat.
    """
    hass: HomeAssistant = call.hass
    coordinator: AIDataUpdateCoordinator = hass.data[DOMAIN]["coordinator"]
    stored = coordinator.data.get("schedules", {})

    # Hämta alla exist­erande enheter genom entity_registry
    entity_registry = hass.helpers.entity_registry.async_get(hass)
    to_remove = []

    for entity in entity_registry.entities.values():
        if entity.domain not in ("sensor", "calendar", "binary_sensor"):
            continue
        # Vi letar efter enheter som har prefix DOMAIN_…
        if not entity.entity_id.startswith(f"{DOMAIN}."):
            continue
        # Format: <domain>.<entity_name>. Sensorer heter e.g. sensor.ai_energy_scheduler_<device>_<suffix>
        parts = entity.entity_id.split("_")
        if len(parts) < 3:
            continue
        device_id = parts[2]
        if device_id not in stored:
            to_remove.append(entity.entity_id)

    # Registrera borttagna enheter
    for entity_id in to_remove:
        _LOGGER.info("Removing entity not in schedule: %s", entity_id)
        hass.states.async_set(entity_id, None)
        # Note: för kalendrar kan vi behöva extra hantering, men HA brukar ta bort state automatiskt.

    _LOGGER.info("Cleanup of removed devices complete")

