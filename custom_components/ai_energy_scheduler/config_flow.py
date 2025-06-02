"""Config flow for AI Energy Scheduler."""

from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, DEFAULT_NAME

class AIESSchedulerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow."""

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            # For now, no options – integration is added
            return self.async_create_entry(title=DEFAULT_NAME, data={})

        return self.async_show_form(
            step_id="user",
            data_schema=None,
            description_placeholders={"name": DEFAULT_NAME},
        )
