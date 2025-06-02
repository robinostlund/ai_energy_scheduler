from homeassistant import config_entries
from homeassistant.core import callback
import voluptuous as vol
import json
from .const import DOMAIN

@callback
def _get_data_schema():
    return vol.Schema({"json": str})

class AiEnergySchedulerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                json_data = json.loads(user_input["json"])
                return self.async_create_entry(title="AI Energy Scheduler", data=json_data)
            except Exception:
                errors["base"] = "invalid_json"

        return self.async_show_form(step_id="user", data_schema=_get_data_schema(), errors=errors)
