from __future__ import annotations

import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    text_selector,
)

from .const import DOMAIN
from .validators import validate_schedule_json

_LOGGER = logging.getLogger(__name__)


class AiEnergySchedulerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AI Energy Scheduler."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            name = user_input["name"]

            # Check for duplicates
            for entry in self._async_current_entries():
                if entry.data["name"] == name:
                    return self.async_abort(reason="already_configured")

            return self.async_create_entry(
                title=name,
                data={"name": name},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("name"): str,
            }),
        )


class AiEnergySchedulerOptionsFlow(config_entries.OptionsFlow):
    """Options flow for editing JSON directly."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry
        self._errors: dict[str, str] = {}

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Initial form for editing schedule JSON."""
        if user_input is not None:
            json_data = user_input.get("json_data", "")
            try:
                schedule = validate_schedule_json(json_data)
                _LOGGER.debug("Validated JSON: %s", schedule)

                # Store new data on config entry
                self.hass.data[DOMAIN][self.config_entry.entry_id]["coordinator"].schedule_data = schedule
                await self.hass.data[DOMAIN][self.config_entry.entry_id]["coordinator"].async_save_to_cache()
                return self.async_create_entry(title="", data={})
            except Exception as err:
                _LOGGER.warning("Invalid JSON input: %s", err)
                self._errors["base"] = "invalid_json"

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("json_data", default=""): text_selector(),
            }),
            errors=self._errors,
            description_placeholders={
                "example": '{"heat_pump": {"schedule": [{"start": "2025-06-02T00:00:00+02:00", "end": "2025-06-02T01:00:00+02:00", "command": "heat"}]}}'
            },
        )


@callback
def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
    return AiEnergySchedulerOptionsFlow(config_entry)
