from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .coordinator import AiEnergySchedulerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up AI Energy Scheduler binary sensor."""
    coordinator: AiEnergySchedulerCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities(
        [ScheduleAlertBinarySensor(coordinator)],
        update_before_add=True,
    )


class ScheduleAlertBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor to indicate if the last JSON input failed."""

    def __init__(self, coordinator: AiEnergySchedulerCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        self._attr_name = f"{DOMAIN} alert"
        self._attr_unique_id = f"{DOMAIN}_alert"

    @property
    def is_on(self) -> bool:
        """Return True if the last schedule load failed or is invalid."""
        return getattr(self.coordinator, "has_validation_error", False)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "description": "True if the last schedule could not be processed or is invalid"
        }
