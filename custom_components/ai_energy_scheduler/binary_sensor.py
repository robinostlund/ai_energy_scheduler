"""Binary sensor platform for ai_energy_scheduler."""

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, BINARY_ALERT
from .store import AIDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up the alert binary sensor via Config Entry."""
    _LOGGER.debug("async_setup_entry (binary_sensor) called for entry_id=%s", entry.entry_id)
    coordinator: AIDataUpdateCoordinator = hass.data[DOMAIN]["coordinator"]
    async_add_entities([AlertBinarySensor(coordinator)])
    _LOGGER.debug("AlertBinarySensor added to Home Assistant")


class AlertBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor that indicates schema validation errors."""

    def __init__(self, coordinator: AIDataUpdateCoordinator):
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_name = BINARY_ALERT
        self._attr_unique_id = f"{DOMAIN}_{BINARY_ALERT}"
        self._attr_entity_registry_enabled_default = True
        self._attr_device_class = None
        self._attr_icon = "mdi:alert-circle-outline"
        _LOGGER.debug("Initialized AlertBinarySensor")

    @property
    def device_info(self) -> DeviceInfo:
        """
        Return a DeviceInfo dict so that Home Assistant groups this binary sensor
        under the same device as the integration itself.
        """
        return DeviceInfo(
            identifiers={(DOMAIN, DOMAIN)},
            name="AI Energy Scheduler",
            manufacturer="AI Energy Scheduler",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def is_on(self) -> bool:
        """Return True if there was an error validating the schedule."""
        state = not getattr(self.coordinator, "_schema_valid", True)
        _LOGGER.debug("AlertBinarySensor.is_on returning: %s", state)
        return state

    async def async_update(self):
        """Request a refresh from the coordinator to update error status."""
        _LOGGER.debug("AlertBinarySensor.async_update called")
        await self.coordinator.async_request_refresh()
