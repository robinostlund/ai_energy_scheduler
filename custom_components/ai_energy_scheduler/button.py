from homeassistant.components.button import ButtonEntity

async def async_setup_entry(hass, config_entry, async_add_entities):
    async_add_entities([AIEnergySchedulerCleanupButton(hass)])

class AIEnergySchedulerCleanupButton(ButtonEntity):
    def __init__(self, hass):
        self.hass = hass
        self._attr_name = "AI Energy Scheduler Cleanup"
        self._attr_unique_id = "ai_energy_scheduler_cleanup"

    async def async_press(self):
        await self.hass.services.async_call(
            "ai_energy_scheduler", "cleanup_entities", {}
        )