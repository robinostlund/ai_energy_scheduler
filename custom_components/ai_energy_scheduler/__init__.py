"""The ai_energy_scheduler integration."""

import asyncio
import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, callback, Event
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import entity_platform
from homeassistant.helpers.storage import Store
from homeassistant.helpers.event import async_call_later

from .const import (
    DOMAIN,
    LOGGER_NAME,
    STORAGE_KEY,
    STORAGE_VERSION,
    SERVICE_SET_SCHEDULE,
    SERVICE_CLEANUP_REMOVED,
    EVENT_COMMAND_ACTIVATED,
    ERROR_INVALID_SCHEMA,
)
from .services import async_setup_services, validate_and_store_schedule
from .store import AIDataUpdateCoordinator

_LOGGER = logging.getLogger(LOGGER_NAME)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the ai_energy_scheduler integration from configuration.yaml (not used)."""
    # Vi stödjer endast Config Flow, så vi returnerar True.
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Set up ai_energy_scheduler from a config entry.
    Här initieras lagrad data och services.
    """
    hass.data.setdefault(DOMAIN, {})

    # Skapa en Store för att läsa/inital data
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)

    try:
        data = await store.async_load()
    except Exception as err:
        _LOGGER.error("Error loading stored schedule: %s", err)
        raise ConfigEntryNotReady from err

    coordinator = AIDataUpdateCoordinator(hass, store, initial_data=data or {})
    hass.data[DOMAIN]["coordinator"] = coordinator

    # Starta coordinator
    await coordinator.async_config_entry_first_refresh()

    # Sätt upp services (set_schedule & cleanup_removed)
    async_setup_services(hass)

    # Registrera entitetsplattformar
    hass.async_create_task(
        hass.helpers.discovery.async_load_platform(hass, "sensor", DOMAIN, {}, entry)
    )
    hass.async_create_task(
        hass.helpers.discovery.async_load_platform(hass, "binary_sensor", DOMAIN, {}, entry)
    )
    hass.async_create_task(
        hass.helpers.discovery.async_load_platform(hass, "calendar", DOMAIN, {}, entry)
    )

    # Lyssna på event från kalendrar (för manuella ändringar)
    hass.bus.async_listen(f"{DOMAIN}_calendar_event", coordinator.handle_calendar_event)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Unload a config entry.
    Returnerar True om alla resurser har släppts.
    """
    unload_ok = all(
        await asyncio.gather(
            hass.config_entries.async_forward_entry_unload(entry, platform)
            for platform in ["sensor", "binary_sensor", "calendar"]
        )
    )
    if not unload_ok:
        return False

    # Ta bort lyssnare
    hass.bus.async_remove_listeners(f"{DOMAIN}_calendar_event")

    hass.data[DOMAIN].pop("coordinator")
    return True


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """
    Ta bort integrationen helt (om användaren avinstallerar).
    Rensar lagrad data.
    """
    store: Store = hass.data[DOMAIN]["coordinator"].store
    await store.async_remove()


@callback
def async_schedule_updated(hass: HomeAssistant, schedule_data: dict[str, Any]) -> None:
    """
    Callback när ett nytt schema är installerat. Publicerar update-signaler så
    att alla entiteter kan uppdatera sig själva.
    """
    hass.bus.async_fire(f"{DOMAIN}_schedule_updated", {"data": schedule_data})

