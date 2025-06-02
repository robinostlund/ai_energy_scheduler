"""Button for manual schedule refresh."""

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AIESRefreshButton(coordinator)])

class AIESRefreshButton(CoordinatorEntity, ButtonEntity):
    """Button to refresh the schedule."""

    @property
    def name(self):
        return f"{DOMAIN}_refresh"

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()
