"""Config flow for AI Energy Scheduler."""
from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
import json
import jsonschema

from .const import DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required("name"): str,
    vol.Optional("schedule_json", default=""): str,
})

class AiEnergySchedulerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AI Energy Scheduler."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
                        if user_input.get("schedule_json"):
                try:
                    json_data = json.loads(user_input["schedule_json"])
                    jsonschema.validate(instance=json_data, schema={"$schema": "http://json-schema.org/draft-07/schema#", "type": "object", "properties": {"schedules": {"type": "object", "patternProperties": {"^.*$": {"type": "object", "properties": {"intervals": {"type": "array", "items": {"type": "object", "properties": {"start": {"type": "string", "format": "date-time"}, "end": {"type": "string", "format": "date-time"}, "command": {"type": "string"}, "power_kw": {"type": "number"}, "energy_kwh": {"type": "number"}, "source": {"type": "string", "enum": ["ai", "manual"]}}, "required": ["start", "end", "command"]}}}, "required": ["intervals"]}}, "additionalProperties": false}}, "required": ["schedules"], "additionalProperties": false})
                except (json.JSONDecodeError, jsonschema.ValidationError) as err:
                    errors["schedule_json"] = "Invalid JSON or schema"
                    return self.async_show_form(
                        step_id="user",
                        data_schema=STEP_USER_DATA_SCHEMA,
                        errors=errors,
                    )
            return self.async_create_entry(title=user_input["name"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return AiEnergySchedulerOptionsFlowHandler(config_entry)

class AiEnergySchedulerOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for AI Energy Scheduler."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("manual_schedule_override", default=False): bool,
            }),
        )