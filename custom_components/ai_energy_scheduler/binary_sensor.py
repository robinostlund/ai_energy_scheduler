from homeassistant.components.binary_sensor import BinarySensorEntity

async def async_setup_entry(hass, config_entry, async_add_entities):
    async_add_entities([AIEnergySchedulerAlertSensor()])

class AIEnergySchedulerAlertSensor(BinarySensorEntity):
    _attr_name = "AI Energy Scheduler Alert"
    _attr_unique_id = "ai_energy_scheduler_alert"
    _attr_device_class = "problem"

    def __init__(self):
        self._attr_is_on = False

    async def async_update(self):
        self._attr_is_on = False  # Will be managed by core logic