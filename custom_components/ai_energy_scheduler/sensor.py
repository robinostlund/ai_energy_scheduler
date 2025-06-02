"""Sensor platform for ai_energy_scheduler."""

from datetime import datetime, timezone, timedelta
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.dt import parse_datetime

from .const import (
    DOMAIN,
    SENSOR_ATTR_COMMAND,
    SENSOR_ATTR_POWER_KW,
    SENSOR_ATTR_ENERGY_KWH,
    SENSOR_ATTR_NEXT_COMMAND,
    SUFFIX_COMMAND,
    SUFFIX_POWER,
    SUFFIX_ENERGY,
    SUFFIX_NEXT,
    SENSOR_TOTAL_POWER,
    SENSOR_TOTAL_ENERGY,
    SENSOR_LAST_UPDATE,
    ICON_SENSOR,
    ICON_SUMMARY_POWER,
    ICON_SUMMARY_ENERGY,
)
from .store import AIDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up sensors when integration laddas (via discovery)."""
    coordinator: AIDataUpdateCoordinator = hass.data[DOMAIN]["coordinator"]

    entities: list[SensorEntity] = []
    # Initiala sensorer (en gång vid startup)
    for device_id in coordinator.data.get("schedules", {}):
        entities.extend(_create_device_sensors(device_id, coordinator))

    # Lägg till summary-sensorer
    entities.append(TotalPowerSensor(coordinator))
    entities.append(TotalEnergySensor(coordinator))
    entities.append(LastUpdateSensor(coordinator))

    async_add_entities(entities)

    # Lyssna på schedule_updates för att lägga till/ta bort sensorer dynamiskt
    async def _async_schedule_updated(event):
        new_entities = []
        existing_device_ids = {ent.device_id for ent in entities if isinstance(ent, DeviceSensor)}
        current_device_ids = set(coordinator.data.get("schedules", {}))

        # Lägg till för nya enheter
        for device_id in current_device_ids - existing_device_ids:
            new_entities.extend(_create_device_sensors(device_id, coordinator))

        async_add_entities(new_entities)

    hass.bus.async_listen(f"{DOMAIN}_schedule_updated", _async_schedule_updated)


def _create_device_sensors(device_id: str, coordinator: AIDataUpdateCoordinator):
    """Helper to skapa fyra sensorer per enhet."""
    return [
        DeviceSensor(coordinator, device_id, SUFFIX_COMMAND),
        DeviceSensor(coordinator, device_id, SUFFIX_POWER),
        DeviceSensor(coordinator, device_id, SUFFIX_ENERGY),
        DeviceSensor(coordinator, device_id, SUFFIX_NEXT),
    ]


class DeviceSensor(CoordinatorEntity, SensorEntity):
    """Generic sensor för varje device och attribut."""

    def __init__(self, coordinator: AIDataUpdateCoordinator, device_id: str, suffix: str):
        """Initialize sensor."""
        super().__init__(coordinator)
        self.device_id = device_id
        self.suffix = suffix
        self._attr_name = f"{device_id}_{suffix}"
        self._attr_unique_id = f"{DOMAIN}_{device_id}_{suffix}"
        self._attr_icon = ICON_SENSOR
        # Kategori “diagnostic” ej, för vi visar värde direkt
        self._attr_entity_category = None

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Show sensors by default."""
        return True

    @property
    def device_info(self) -> dict:
        """Associate sensorer med en virtuell “device” per device_id."""
        return {
            "identifiers": {(DOMAIN, self.device_id)},
            "name": self.device_id,
            "manufacturer": "AI Energy Scheduler",
        }

    @property
    def available(self) -> bool:
        """Tillgänglig bara om enheten fortfarande finns i schemat."""
        schedules = self.coordinator.data.get("schedules", {})
        return self.device_id in schedules

    @property
    def state(self) -> Any:
        """Returnerar aktuellt värde baserat på suffix."""
        schedules = self.coordinator.data.get("schedules", {})
        device_data = schedules.get(self.device_id)
        if not device_data:
            return None

        now = datetime.now(timezone.utc)
        intervals = device_data.get("intervals", [])
        current_command = None
        current_power = None
        current_energy = None
        next_command = None

        # Hitta aktuell interval
        for interval in intervals:
            start = parse_datetime(interval["start"])
            end = parse_datetime(interval["end"])
            if start <= now < end:
                current_command = interval.get("command")
                current_power = interval.get("power_kw")
                current_energy = interval.get("energy_kwh")
                break

        # Hitta nästa kommando
        sorted_intervals = sorted(intervals, key=lambda x: parse_datetime(x["start"]))
        for interval in sorted_intervals:
            st = parse_datetime(interval["start"])
            if st > now:
                next_command = interval.get("command")
                break

        if self.suffix == SUFFIX_COMMAND:
            return current_command or "off"
        if self.suffix == SUFFIX_POWER:
            return current_power
        if self.suffix == SUFFIX_ENERGY:
            return current_energy
        if self.suffix == SUFFIX_NEXT:
            return next_command

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Exempel: vi kan exponera alla intervall som attribut vid debug."""
        return {"device_id": self.device_id}

    @property
    def unit_of_measurement(self) -> str | None:
        """Enheter: power i kW, energy i kWh."""
        if self.suffix == SUFFIX_POWER:
            return "kW"
        if self.suffix == SUFFIX_ENERGY:
            return "kWh"
        return None

    async def async_update(self):
        """
        Called när Coordinator uppdaterar datan.
        Vi kan också kolla om vi byter kommando; om ja, avfyra event.
        """
        old_state = self._attr_native_value
        await self.coordinator.async_request_refresh()
        new_state = self.state
        if self.suffix == SUFFIX_COMMAND and new_state != old_state:
            # Avfyra event så att automationer kan lyssna på enskilda kommandobyten
            self.hass.bus.async_fire(
                f"{DOMAIN}_{EVENT_COMMAND_ACTIVATED}", {
                    "device_id": self.device_id,
                    "command": new_state
                }
            )


class TotalPowerSensor(CoordinatorEntity, SensorEntity):
    """Sensor som summerar all effekt för nuvarande timme."""

    def __init__(self, coordinator: AIDataUpdateCoordinator):
        """Initialize total power sensor."""
        super().__init__(coordinator)
        self._attr_name = SENSOR_TOTAL_POWER
        self._attr_unique_id = f"{DOMAIN}_{SENSOR_TOTAL_POWER}"
        self._attr_icon = ICON_SUMMARY_POWER
        self._attr_entity_registry_enabled_default = True
        self._attr_entity_category = None

    @property
    def state(self) -> float:
        """Beräkna total power (kW) genom att summera pågående intervaller."""
        total = 0.0
        now = datetime.now(timezone.utc)
        for device_id, device_data in self.coordinator.data.get("schedules", {}).items():
            for interval in device_data.get("intervals", []):
                start = parse_datetime(interval["start"])
                end = parse_datetime(interval["end"])
                if start <= now < end:
                    pw = interval.get("power_kw") or 0.0
                    total += pw
        return round(total, 2)

    @property
    def unit_of_measurement(self) -> str:
        return "kW"


class TotalEnergySensor(CoordinatorEntity, SensorEntity):
    """Sensor för ackumulerad energi som förbrukats hittills idag."""

    def __init__(self, coordinator: AIDataUpdateCoordinator):
        """Initialize total energy sensor."""
        super().__init__(coordinator)
        self._attr_name = SENSOR_TOTAL_ENERGY
        self._attr_unique_id = f"{DOMAIN}_{SENSOR_TOTAL_ENERGY}"
        self._attr_icon = ICON_SUMMARY_ENERGY
        self._attr_entity_registry_enabled_default = True

    @property
    def state(self) -> float:
        """Beräkna energiförbrukning (kWh) för alla avslutade intervaller under dagens datum."""
        total_energy = 0.0
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        for device_id, device_data in self.coordinator.data.get("schedules", {}).items():
            for interval in device_data.get("intervals", []):
                st = parse_datetime(interval["start"])
                en = parse_datetime(interval["end"])
                if st >= today_start and en <= now:
                    total_energy += interval.get("energy_kwh") or 0.0
        return round(total_energy, 2)

    @property
    def unit_of_measurement(self) -> str:
        return "kWh"


class LastUpdateSensor(CoordinatorEntity, SensorEntity):
    """Sensor som visar tidpunkt för senaste schema-uppdatering."""

    def __init__(self, coordinator: AIDataUpdateCoordinator):
        """Initialize last update sensor."""
        super().__init__(coordinator)
        self._attr_name = SENSOR_LAST_UPDATE
        self._attr_unique_id = f"{DOMAIN}_{SENSOR_LAST_UPDATE}"
        self._attr_icon = ICON_SENSOR
        self._attr_entity_registry_enabled_default = True

    @property
    def state(self) -> str:
        """Returnerar senaste uppdatering i ISO-format. Om ingen uppdatering: ’unknown’."""
        last = self.coordinator.data.get("last_update")
        if not last:
            return "unknown"
        return last

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Visa eventuella attribut, t.ex. totalt antal enheter."""
        return {"num_devices": len(self.coordinator.data.get("schedules", {}))}

    async def async_update(self):
        """Sätt last_update när Coordinator uppdateras."""
        await self.coordinator.async_request_refresh()
        now_iso = datetime.now(timezone.utc).isoformat()
        self.coordinator.data["last_update"] = now_iso
        await self.coordinator.store.async_save(self.coordinator.data)

