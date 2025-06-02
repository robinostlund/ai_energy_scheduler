"""AI Energy Scheduler integration setup."""
from homeassistant.core import HomeAssistant
from .const import DOMAIN

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up AI Energy Scheduler integration."""
    # All logic is handled via service calls; nothing to do here
    return True
