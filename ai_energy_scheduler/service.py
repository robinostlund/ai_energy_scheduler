import json
from homeassistant.core import HomeAssistant, ServiceCall
from .const import DOMAIN

async def async_register_services(hass: HomeAssistant):
    async def handle_submit(call: ServiceCall):
        try:
            data = call.data.get("json")
            schedule = json.loads(data)
            # TODO: validate and process schedule
        except Exception as e:
            hass.components.persistent_notification.create(f"Failed to process schedule: {e}", title="AI Energy Scheduler")

    async def handle_validate(call: ServiceCall):
        try:
            data = call.data.get("json")
            # TODO: validate against schema
        except Exception as e:
            hass.components.persistent_notification.create(f"Validation failed: {e}", title="AI Energy Scheduler")

    async def handle_cleanup(call: ServiceCall):
        # TODO: remove unused sensors/calendars
        pass

    hass.services.async_register(DOMAIN, "submit_schedule", handle_submit)
    hass.services.async_register(DOMAIN, "validate_schedule", handle_validate)
    hass.services.async_register(DOMAIN, "cleanup_removed", handle_cleanup)
