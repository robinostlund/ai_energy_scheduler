"""Config flow for ai_energy_scheduler integration."""

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_NAME

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class AIEnergySchedulerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for AI Energy Scheduler."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Step when user adds integration via UI."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({vol.Optional(CONF_NAME, default="AI Energy Scheduler"): str}),
            )

        # Vi accepterar bara installation; inga extra parametrar behövs
        return self.async_create_entry(title=user_input.get(CONF_NAME), data={})


    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return options flow handler."""
        return AIEnergySchedulerOptionsFlow(config_entry)


class AIEnergySchedulerOptionsFlow(config_entries.OptionsFlow):
    """Options flow for AI Energy Scheduler."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Grab options - just visa en tom sida för framtida utbyggnader."""
        if user_input is None:
            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema({}),
            )
        return self.async_create_entry(title="", data=user_input)

