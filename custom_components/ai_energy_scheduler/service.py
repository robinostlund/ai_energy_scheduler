"""Service handlers for AI Energy Scheduler."""
from homeassistant.core import HomeAssistant, ServiceCall
from .coordinator import AiEnergySchedulerCoordinator
from .helpers import load_schedule_from_data, cleanup_entities_by_schedule

DOMAIN = "ai_energy_scheduler"

async def async_register_services(hass: HomeAssistant, coordinator: AiEnergySchedulerCoordinator) -> None:
    """Register services for setting schedule and cleaning up entities."""

    async def handle_set_schedule(call: ServiceCall) -> None:
        """Handle the set_schedule service call."""
        schedule_data = call.data.get("schedule_data")
        if not schedule_data:
            raise ValueError("Missing schedule_data in service call")
        await load_schedule_from_data(hass, coordinator, schedule_data)

    async def handle_cleanup(call: ServiceCall) -> None:
        """Handle the cleanup_entities service call."""
        await cleanup_entities_by_schedule(hass, coordinator)

    hass.services.async_register(DOMAIN, "set_schedule", handle_set_schedule)
    hass.services.async_register(DOMAIN, "cleanup_entities", handle_cleanup)