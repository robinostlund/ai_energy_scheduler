"""Binary sensor platform for ai_energy_scheduler."""

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, BINARY_ALERT
from .store import AIDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the alert binary sensor."""
    coordinator: AIDataUpdateCoordinator = hass.data[DOMAIN]["coordinator"]
    async_add_entities([AlertBinarySensor(coordinator)])


class AlertBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor that indicates schema validation errors."""

    def __init__(self, coordinator: AIDataUpdateCoordinator):
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_name = BINARY_ALERT
        self._attr_unique_id = f"{DOMAIN}_{BINARY_ALERT}"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_class = None
        self._attr_icon = "mdi:alert-circle-outline"

    @property
    def is_on(self) -> bool:
        """Return true if there was an error in validating schema."""
        return not getattr(self.coordinator, "_schema_valid", True)

    async def async_update(self):
        """Vi behöver bara refresha coordinator för att få senaste felstatus."""
        await self.coordinator.async_request_refresh()

