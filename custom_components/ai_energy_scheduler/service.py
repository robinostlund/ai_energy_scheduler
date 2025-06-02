"""Service handlers for AI Energy Scheduler."""
from homeassistant.core import ServiceCall
from homeassistant.helpers import config_validation as cv
import voluptuous as vol
import json
import hashlib

from .const import (
    DOMAIN, CONF_INSTANCE_ID, CONF_INSTANCE_FRIENDLY_NAME, SCHEDULE_FILE_PREFIX,
    EVENT_IMPORT_SCHEDULE, EVENT_VALIDATE_SCHEDULE, EVENT_CLEANUP, EVENT_ALERT_CHANGED,
)
from .coordinator import AiEnergySchedulerCoordinator
from .validators import validate_schedule_json

SCHEMA_IMPORT_SCHEDULE = vol.Schema({
    vol.Required("instance_id"): cv.string,
    vol.Optional("instance_friendly_name"): cv.string,
    vol.Required("schedule"): cv.string,  # JSON string
})

async def async_setup_services(hass):
    """Register custom services for AI Energy Scheduler."""

    if not hasattr(hass.data, DOMAIN):
        hass.data[DOMAIN] = {}
    instance_states = hass.data[DOMAIN]

    async def handle_import_schedule(call: ServiceCall):
        instance_id = call.data["instance_id"]
        instance_friendly_name = call.data.get("instance_friendly_name", instance_id)
        schedule_json = call.data["schedule"]
        try:
            schedule = json.loads(schedule_json)
        except Exception as ex:
            raise ValueError(f"Invalid JSON: {ex}")

        # Schema-caching: check previous hash
        coordinator = instance_states.get(instance_id)
        if not coordinator:
            coordinator = AiEnergySchedulerCoordinator(hass, instance_id, instance_friendly_name)
            instance_states[instance_id] = coordinator
        prev_hash = coordinator.schema_hash() if coordinator.schedule else None

        # Validate new schedule
        validate_schedule_json(schedule, hass)

        new_hash = hashlib.sha256(json.dumps(schedule, sort_keys=True).encode("utf-8")).hexdigest()
        if new_hash == prev_hash:
            hass.bus.async_fire(EVENT_IMPORT_SCHEDULE, {"instance_id": instance_id, "status": "no_change"})
            return

        # Update state
        coordinator.schedule = schedule
        coordinator.instance_friendly_name = instance_friendly_name
        coordinator._schema_hash = new_hash
        coordinator.save_schedule()

        # (Re)create all entities etc (not shown: see main sensor/calendar.py)
        hass.bus.async_fire(EVENT_IMPORT_SCHEDULE, {"instance_id": instance_id, "status": "imported", "hash": new_hash})

        # TODO: Dynamically load/unload entity platforms per instance

    async def handle_validate_schedule(call: ServiceCall):
        instance_id = call.data.get("instance_id")
        if not instance_id or instance_id not in instance_states:
            raise ValueError("Instance ID required and must be imported first.")
        coordinator = instance_states[instance_id]
        validate_schedule_json(coordinator.schedule, hass)
        hass.bus.async_fire(EVENT_VALIDATE_SCHEDULE, {"instance_id": instance_id, "status": "validated"})

    async def handle_cleanup_removed(call: ServiceCall):
        instance_id = call.data.get("instance_id")
        if not instance_id or instance_id not in instance_states:
            raise ValueError("Instance ID required and must be imported first.")
        # Remove the file and clear in-memory state
        coordinator = instance_states[instance_id]
        import os
        path = hass.config.path(f"{SCHEDULE_FILE_PREFIX}{instance_id}.json")
        if os.path.exists(path):
            os.remove(path)
        del instance_states[instance_id]
        hass.bus.async_fire(EVENT_CLEANUP, {"instance_id": instance_id, "status": "cleaned"})

    hass.services.async_register(
        DOMAIN, "import_schedule", handle_import_schedule, schema=SCHEMA_IMPORT_SCHEDULE
    )
    hass.services.async_register(
        DOMAIN, "validate_schedule", handle_validate_schedule,
        schema=vol.Schema({vol.Required("instance_id"): cv.string})
    )
    hass.services.async_register(
        DOMAIN, "cleanup_removed", handle_cleanup_removed,
        schema=vol.Schema({vol.Required("instance_id"): cv.string})
    )
