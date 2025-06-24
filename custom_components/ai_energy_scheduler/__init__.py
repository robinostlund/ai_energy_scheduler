import os
import json
import logging
import aiofiles

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.storage import Store
from homeassistant.helpers.device_registry import DeviceEntry

from .const import (
    DOMAIN,
    LOGGER_NAME,
    STORAGE_KEY,
    STORAGE_VERSION,
    SCHEDULE_UPDATED_EVENT,
    SCHEMA_FILE,
    PLATFORMS,
)
from .services import async_setup_services
from .coordinator import AIEnergySchedulerCoordinator

_LOGGER = logging.getLogger(LOGGER_NAME)

async def _load_schema_file() -> dict:
    schema_path = os.path.join(os.path.dirname(__file__), SCHEMA_FILE)
    async with aiofiles.open(schema_path, "r", encoding="utf-8") as file:
        schema = await file.read()
    _LOGGER.debug(f"Loaded schema from {schema_path}")
    return json.loads(schema)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up integration from Config Entry."""
    hass.data.setdefault(DOMAIN, {})

    # load data from storage
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    try:
        initial_data = await store.async_load()
    except Exception as err:
        _LOGGER.error("Could not load stored data: %s", err, exc_info=True)
        raise ConfigEntryNotReady from err
    
    # load json schema file
    try:
        schema = await _load_schema_file()
        hass.data[DOMAIN]["schema"] = schema
    except Exception as err:
        _LOGGER.error("Could not load schema file: %s", err, exc_info=True)
        raise ConfigEntryNotReady from err

    # create coordinator
    coordinator = AIEnergySchedulerCoordinator(hass, store, initial_data, schema)
    hass.data[DOMAIN]["coordinator"] = coordinator

    # register the coordinator
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.error("Error during coordinator first refresh: %s", err, exc_info=True)
        raise ConfigEntryNotReady from err

    await async_setup_services(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry and cleanup."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    hass.data[DOMAIN].pop("coordinator", None)
    return True

async def async_remove_config_entry_device(hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry) -> bool:
    """Handle device removal."""
    coordinator = hass.data[DOMAIN]["coordinator"]
    device_id = device_entry.serial_number

    if device_id in coordinator.data.get("schedules", {}):
        _LOGGER.debug(f"Removed device {device_id} and its entities from registries.")
        # Remove the device from the coordinator's data
        coordinator.data["schedules"].pop(device_id, None)
        await coordinator.async_update_schedule(coordinator.data)

    return True
