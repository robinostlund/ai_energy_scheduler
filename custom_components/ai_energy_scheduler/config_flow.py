"""Config flow for AI Energy Scheduler."""
from __future__ import annotations

import logging
import voluptuous as vol
import json
import jsonschema
from typing import Any

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from .validators import SCHEDULE_SCHEMA

_LOGGER = logging.getLogger(__name__)

class AiEnergySchedulerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AI Energy Scheduler."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step where JSON can be pasted."""
        errors = {}

        if user_input is not None:
            raw_json = user_input.get("schedule_json", "")
            try:
                parsed_json = json.loads(raw_json)
                jsonschema.validate(instance=parsed_json, schema=SCHEDULE_SCHEMA)
            except json.JSONDecodeError as e:
                errors["schedule_json"] = f"Invalid JSON: {str(e)}"
            except jsonschema.ValidationError as e:
                errors["schedule_json"] = f"Invalid schema: {str(e)}"

            if not errors:
                return self.async_create_entry(
                    title="AI Energy Scheduler",
                    data={"schedule_json": raw_json}
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("schedule_json"): str
            }),
            errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        from .options_flow import AiEnergySchedulerOptionsFlowHandler
        return AiEnergySchedulerOptionsFlowHandler(config_entry)
