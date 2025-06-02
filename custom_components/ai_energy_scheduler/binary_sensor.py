"""Binary sensor for AI Energy Scheduler alert."""

from homeassistant.components.binary_sensor import BinarySensorEntity
from .const import DOMAIN, BINARY_SENSOR_ALERT

async def async_setup_entry(hass, entry, async_add_entities):
    """Not used: entities created by service."""
    pass

def create_alert_binary_sensor_for_instance(hass, instance_id, instance_friendly_name, alert_state):
    return [AiEnergyAlertBinarySensor(instance_id, instance_friendly_name, alert_state)]

class AiEnergyAlertBinarySensor(BinarySensorEntity):
    """Binary sensor for schedule validation errors."""

    def __init__(self, instance_id, instance_friendly_name, alert_state):
        self._instance_id = instance_id
        self._instance_friendly_name = instance_friendly_name
        self._attr_name = f"{DOMAIN} {instance_friendly_name} Alert"
        self._attr_unique_id = f"{DOMAIN}_{instance_id}_{BINARY_SENSOR_ALERT}"
        self._alert_state = alert_state

    @property
    def is_on(self):
        return self._alert_state
