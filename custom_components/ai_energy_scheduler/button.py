from homeassistant.components.button import ButtonEntity
from homeassistant.core import callback
from .const import DOMAIN, BUTTON_CLEANUP

class CleanupRemovedButton(ButtonEntity):
    """Button to cleanup removed devices."""

    def __init__(self, hass, instance_id, instance_friendly_name):
        self._hass = hass
        self._instance_id = instance_id
        self._instance_friendly_name = instance_friendly_name
        self._attr_name = f"{DOMAIN} {instance_friendly_name} Cleanup Removed Devices"
        self._attr_unique_id = f"{DOMAIN}_{instance_id}_{BUTTON_CLEANUP}"

    async def async_press(self):
        """Call the cleanup_removed service for this instance."""
        await self._hass.services.async_call(
            DOMAIN,
            "cleanup_removed",
            {
                "instance_id": self._instance_id,
            },
            blocking=True,
        )
