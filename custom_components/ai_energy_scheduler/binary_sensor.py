"""Binary sensors for AI Energy Scheduler."""

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, SENSOR_ALERT

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AIESAlertSensor(coordinator)])

class AIESAlertSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for schedule processing errors."""

    @property
    def is_on(self):
        return self.coordinator.alert

    @property
    def name(self):
        return f"{DOMAIN}_{SENSOR_ALERT}"
