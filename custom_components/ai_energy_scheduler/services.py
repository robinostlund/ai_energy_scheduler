"""Service handlers for ai_energy_scheduler."""

import json
import logging
import os
import re
from typing import Any, Dict, Union

import jsonschema
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er  # <-- Import entity_registry helper

from .const import (
    DOMAIN,
    SCHEMA_FILE,
    SERVICE_SET_SCHEDULE,
    SERVICE_CLEANUP_REMOVED,
    LOGGER_NAME,
)
# No import of AIDataUpdateCoordinator here to avoid circular references

_LOGGER = logging.getLogger(LOGGER_NAME)


def async_setup_services(hass: HomeAssistant) -> None:
    """Register services for this integration."""
    _LOGGER.debug("async_setup_services called")
    try:
        hass.services.async_register(
            DOMAIN, SERVICE_SET_SCHEDULE, handle_set_schedule
        )
        hass.services.async_register(
            DOMAIN, SERVICE_CLEANUP_REMOVED, handle_cleanup_removed
        )
        _LOGGER.debug(
            "Registered services %s.%s and %s.%s",
            DOMAIN,
            SERVICE_SET_SCHEDULE,
            DOMAIN,
            SERVICE_CLEANUP_REMOVED,
        )
    except Exception as err:
        _LOGGER.error("Error registering services: %s", err, exc_info=True)


def _load_schema(hass: HomeAssistant) -> Dict[str, Any]:
    """Load JSON schema from schema.json file."""
    _LOGGER.debug("_load_schema called")
    schema_path = os.path.join(os.path.dirname(__file__), SCHEMA_FILE)
    _LOGGER.debug("Loading schema from path: %s", schema_path)
    with open(schema_path, "r", encoding="utf-8") as file:
        data = json.load(file)
        _LOGGER.debug("Schema loaded successfully")
        return data


def validate_schedule_format(data: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validate the incoming schedule data against the JSON schema.
    Raise HomeAssistantError if invalid.
    """
    _LOGGER.debug("validate_schedule_format called with data: %s", data)
    try:
        jsonschema.validate(instance=data, schema=schema)
        _LOGGER.debug("JSON schema validation succeeded")
    except jsonschema.exceptions.ValidationError as err:
        _LOGGER.error("JSON schema validation failed: %s", err, exc_info=True)
        raise HomeAssistantError(f"Invalid schedule format: {err.message}")


async def handle_set_schedule(call: ServiceCall) -> None:
    """
    Service handler for ai_energy_scheduler.set_schedule.
    Expects either:
      - schedules as a dict (matching schema.json)
      - or schedules as a string containing JSON (possibly fenced with ```json ... ```)
    Strips any ``` fences, parses JSON if needed, validates schema, stores, and triggers coordinator update.
    """
    _LOGGER.debug("handle_set_schedule called with call.data: %s", call.data)
    hass: HomeAssistant = call.hass
    coordinator = hass.data.get(DOMAIN, {}).get("coordinator")
    if coordinator is None:
        _LOGGER.error("Coordinator not initialized in handle_set_schedule")
        raise HomeAssistantError("Coordinator not initialized")

    raw_schedules: Union[str, dict] = call.data.get("schedules")
    if raw_schedules is None:
        _LOGGER.error("No 'schedules' key provided in service data")
        raise HomeAssistantError("No 'schedules' key provided in service data")

    # Determine whether schedules is a string that needs parsing, or already a dict
    if isinstance(raw_schedules, str):
        _LOGGER.debug("Received schedules as string, attempting to strip fences and parse JSON")
        # Remove leading ```json or ``` (with optional whitespace)
        without_prefix = re.sub(r'^```(?:\s*json)?\s*', '', raw_schedules)
        # Remove trailing ```
        cleaned = re.sub(r'```\s*$', '', without_prefix)
        trimmed = cleaned.strip()
        _LOGGER.debug("Trimmed JSON string: %s", trimmed)
        try:
            parsed = json.loads(trimmed)
            _LOGGER.debug("Parsed JSON string into dict: %s", parsed)
        except json.JSONDecodeError as err:
            _LOGGER.error("JSON decoding failed: %s", err, exc_info=True)
            raise HomeAssistantError(f"Invalid JSON string: {err}") from err

        # Extract schedules dict
        if isinstance(parsed, dict) and "schedules" in parsed:
            schedules_dict = parsed["schedules"]
            _LOGGER.debug("Using parsed['schedules']: %s", schedules_dict)
        elif isinstance(parsed, dict):
            schedules_dict = parsed
            _LOGGER.debug("Using parsed as schedules dict: %s", schedules_dict)
        else:
            _LOGGER.error("Parsed JSON is not a dict: %s", type(parsed))
            raise HomeAssistantError("Parsed JSON must be an object containing 'schedules' or be the schedules dict")
    elif isinstance(raw_schedules, dict):
        _LOGGER.debug("Received schedules as dict: %s", raw_schedules)
        schedules_dict = raw_schedules
    else:
        _LOGGER.error("Unsupported type for schedules: %s", type(raw_schedules))
        raise HomeAssistantError("Schedules must be either a JSON string or a dict")

    payload = {"schedules": schedules_dict}
    _LOGGER.debug("Constructed payload for validation: %s", payload)

    try:
        schema = _load_schema(hass)
    except Exception as err:
        _LOGGER.error("Could not load schema.json: %s", err, exc_info=True)
        raise HomeAssistantError("Schema file not found or invalid") from err

    try:
        validate_schedule_format(payload, schema)
    except HomeAssistantError as err:
        _LOGGER.error("Schedule validation error: %s", err, exc_info=True)
        raise

    try:
        _LOGGER.debug("Calling coordinator.async_update_schedule with payload")
        await coordinator.async_update_schedule(payload)
        _LOGGER.info("Schedule successfully updated via service")
    except Exception as err:
        _LOGGER.error("Failed to set schedule: %s", err, exc_info=True)
        raise HomeAssistantError(f"Failed to update schedule: {err}") from err


async def handle_cleanup_removed(call: ServiceCall) -> None:
    """
    Service handler for ai_energy_scheduler.cleanup_removed.
    Removes entities for devices no longer present in the stored schedule.
    """
    _LOGGER.debug("handle_cleanup_removed called")
    hass: HomeAssistant = call.hass
    coordinator = hass.data.get(DOMAIN, {}).get("coordinator")
    if coordinator is None:
        _LOGGER.error("Coordinator not initialized in handle_cleanup_removed")
        raise HomeAssistantError("Coordinator not initialized")

    stored = coordinator.data.get("schedules", {})
    _LOGGER.debug("Stored schedules in coordinator: %s", stored)

    # Correct way to get the entity registry:
    registry = er.async_get(hass)
    to_remove = []

    for entity_id, entry in registry.entities.items():
        _LOGGER.debug("Inspecting entity: %s", entity_id)
        # Only consider our integration’s domains
        if entry.domain not in ("sensor", "calendar", "binary_sensor"):
            continue
        if not entity_id.startswith(f"{DOMAIN}."):
            continue

        parts = entity_id.split("_")
        if len(parts) < 3:
            continue

        device_id = parts[2]
        if device_id not in stored:
            _LOGGER.debug(
                "Scheduling removal for entity_id: %s (device_id=%s not in stored)",
                entity_id,
                device_id,
            )
            to_remove.append(entity_id)

    for entity_id in to_remove:
        _LOGGER.info("Removing entity not present in schedule: %s", entity_id)
        hass.states.async_set(entity_id, None)

    _LOGGER.info("Cleanup of removed devices complete")
