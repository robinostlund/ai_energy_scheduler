"""AI Energy Scheduler integration"""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

DOMAIN = "ai_energy_scheduler"
PLATFORMS = ["sensor", "calendar", "binary_sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"schedules": {}}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    hass.services.async_register(
        DOMAIN, "set_schedule", lambda call: None
    )
    hass.services.async_register(
        DOMAIN, "cleanup_entities", lambda call: None
    )
    return True