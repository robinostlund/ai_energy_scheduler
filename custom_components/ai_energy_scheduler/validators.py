"""Validation for AI Energy Scheduler JSON input."""

import voluptuous as vol
from typing import Any
from homeassistant.exceptions import HomeAssistantError

import re

# ISO 8601 datetime with timezone regex (e.g., 2025-06-02T00:00:00+02:00)
ISO8601_TZ_REGEX = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?([+-]\d{2}:\d{2}|Z)$"
)


def validate_iso8601_tz(value: str) -> str:
    """Validate that a string is an ISO 8601 datetime with timezone."""
    if not ISO8601_TZ_REGEX.match(value):
        raise vol.Invalid(f"Invalid datetime format: {value}")
    return value


SCHEDULE_ENTRY_SCHEMA = vol.Schema(
    {
        vol.Required("start"): validate_iso8601_tz,
        vol.Required("end"): validate_iso8601_tz,
        vol.Required("command"): vol.All(str, vol.Length(min=1)),
        vol.Optional("power_kw"): vol.Coerce(float),
        vol.Optional("energy_kwh"): vol.Coerce(float),
        vol.Optional("source", default="manual"): vol.In(["manual", "ai"]),
    }
)

DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required("schedule"): [SCHEDULE_ENTRY_SCHEMA]
    }
)

SCHEDULE_SCHEMA = vol.Schema(
    {
        vol.Match(r"^[a-zA-Z0-9_\-]+$"): DEVICE_SCHEMA  # device names as keys
    }
)


def validate_schedule_json(data: Any) -> None:
    """Validate the full JSON schedule structure."""
    try:
        SCHEDULE_SCHEMA(data)
    except vol.Invalid as err:
        raise HomeAssistantError(f"Invalid schedule format: {err}") from err
