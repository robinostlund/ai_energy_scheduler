import logging
import voluptuous as vol

from homeassistant import config_entries

from .const import DOMAIN, LOGGER_NAME

_LOGGER = logging.getLogger(LOGGER_NAME)


class EnergySchedulerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            # No user inputs expected yet
            return self.async_create_entry(title="AI Energy Scheduler", data={})

        data_schema = vol.Schema({})

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)