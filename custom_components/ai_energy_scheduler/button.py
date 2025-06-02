from __future__ import annotations

import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .coordinator import AiEnergySchedulerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up button entities."""
    coordinator: AiEnergySchedulerCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([ScheduleCleanupButton(coordinator)], update_before_add=True)


class ScheduleCleanupButton(CoordinatorEntity, ButtonEntity):
    """Button to trigger manual cleanup of removed devices."""

    def __init__(self, coordinator: AiEnergySchedulerCoordinator) -> None:
        """Initialize the button entity."""
        super().__init__(coordinator)
        self._attr_name = f"{DOMAIN} cleanup"
        self._attr_unique_id = f"{DOMAIN}_cleanup"

    async def async_press(self) -> None:
        """Handle the button press to trigger cleanup."""
        _LOGGER.info("Manual cleanup button pressed.")
        await self.coordinator.async_cleanup_entities()
