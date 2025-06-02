from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, DATA_COORDINATOR
from .coordinator import AiEnergySchedulerCoordinator
from .service import register_services

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the AI Energy Scheduler integration from yaml (not used)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AI Energy Scheduler from a config entry."""
    coordinator = AiEnergySchedulerCoordinator(hass, entry.entry_id)
    await coordinator.async_load_from_cache()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
    }

    # Register services once (only once globally, not per entry)
    if not hasattr(hass.data[DOMAIN], "services_registered"):
        register_services(hass, coordinator)
        hass.data[DOMAIN].services_registered = True

    await coordinator.async_config_entry_first_refresh()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:  # No more entries left
            hass.data.pop(DOMAIN)

    return True
