"""The ai_energy_scheduler integration."""

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.storage import Store

from .const import (
    DOMAIN,
    LOGGER_NAME,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .services import async_setup_services
from .store import AIDataUpdateCoordinator

_LOGGER = logging.getLogger(LOGGER_NAME)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the ai_energy_scheduler integration (via configuration.yaml)."""
    _LOGGER.debug("async_setup called with config: %s", config)
    # We only support Config Flow, so return True immediately.
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Set up ai_energy_scheduler from a config entry.
    Here we initialize stored data, services, and platform registration.
    """
    _LOGGER.debug("async_setup_entry called for entry_id=%s", entry.entry_id)
    hass.data.setdefault(DOMAIN, {})

    # Create a Store helper for persisting data
    _LOGGER.debug("Creating Store with key=%s, version=%s", STORAGE_KEY, STORAGE_VERSION)
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)

    try:
        data = await store.async_load()
        _LOGGER.debug("Loaded stored data: %s", data)
    except Exception as err:
        _LOGGER.error("Error loading stored schedule: %s", err, exc_info=True)
        raise ConfigEntryNotReady from err

    coordinator = AIDataUpdateCoordinator(hass, store, initial_data=data or {})
    hass.data[DOMAIN]["coordinator"] = coordinator
    _LOGGER.debug("Created AIDataUpdateCoordinator, now calling async_config_entry_first_refresh()")

    try:
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.debug("Coordinator first refresh completed.")
    except Exception as err:
        _LOGGER.error("Error during coordinator first refresh: %s", err, exc_info=True)
        raise ConfigEntryNotReady from err

    # Register our custom services
    _LOGGER.debug("Registering services")
    async_setup_services(hass)

    # Forward entry setup to sensor, binary_sensor, and calendar
    _LOGGER.debug("Forwarding entry setup to platforms: sensor, binary_sensor, calendar")
    try:
        await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor", "calendar"])
        _LOGGER.debug("Platform setups completed.")
    except Exception as err:
        _LOGGER.error("Error forwarding entry setup to platforms: %s", err, exc_info=True)
        raise

    # Listen for calendar events (manual edits)
    _LOGGER.debug("Registering calendar_event listener for %s_calendar_event", DOMAIN)
    remove_listener = hass.bus.async_listen(f"{DOMAIN}_calendar_event", coordinator.handle_calendar_event)
    hass.data[DOMAIN]["calendar_listener"] = remove_listener

    _LOGGER.debug("async_setup_entry successfully completed for entry_id=%s", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Unload a config entry.
    Returns True if all resources were successfully released.
    """
    _LOGGER.debug("async_unload_entry called for entry_id=%s", entry.entry_id)
    unload_tasks = [
        hass.config_entries.async_forward_entry_unload(entry, platform)
        for platform in ["sensor", "binary_sensor", "calendar"]
    ]
    _LOGGER.debug("Waiting for platform unload tasks to complete")
    try:
        unload_results = await asyncio.gather(*unload_tasks)
        _LOGGER.debug("Platform unload results: %s", unload_results)
    except Exception as err:
        _LOGGER.error("Error unloading platforms: %s", err, exc_info=True)
        return False

    if not all(unload_results):
        _LOGGER.warning("Not all platform unloads returned True: %s", unload_results)
        return False

    # Remove the calendar-event listener, if present
    _LOGGER.debug("Removing calendar_event listener if present")
    remove_listener = hass.data[DOMAIN].pop("calendar_listener", None)
    if callable(remove_listener):
        try:
            remove_listener()
            _LOGGER.debug("Calendar_event listener removed successfully")
        except Exception as err:
            _LOGGER.error("Error removing calendar_event listener: %s", err, exc_info=True)

    # Remove coordinator data
    hass.data[DOMAIN].pop("coordinator", None)
    _LOGGER.debug("Coordinator data removed from hass.data")

    return True


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """
    Remove the integration entirely (when the user uninstalls).
    Clears stored data.
    """
    _LOGGER.debug("async_remove_entry called for entry_id=%s", entry.entry_id)
    coordinator = hass.data.get(DOMAIN, {}).get("coordinator")
    if coordinator is None:
        _LOGGER.debug("Coordinator not found in hass.data; nothing to remove")
        return

    store: Store = coordinator.store
    try:
        await store.async_remove()
        _LOGGER.debug("Store removed successfully")
    except Exception as err:
        _LOGGER.error("Error removing store during async_remove_entry: %s", err, exc_info=True)


@callback
def async_schedule_updated(hass: HomeAssistant, schedule_data: dict[str, Any]) -> None:
    """
    Callback when a new schedule is installed. Fires an event so entities can refresh.
    """
    _LOGGER.debug("async_schedule_updated called with data: %s", schedule_data)
    hass.bus.async_fire(f"{DOMAIN}_schedule_updated", {"data": schedule_data})
