"""Tests for AI Energy Scheduler services."""
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.ai_energy_scheduler.const import DOMAIN

@pytest.mark.asyncio
async def test_set_schedule_service(hass: HomeAssistant, entity_registry: er.EntityRegistry):
    """Test the set_schedule service registers sensors."""
    assert await hass.services.async_call(
        DOMAIN,
        "set_schedule",
        {
            "schedule_data": {
                "schedules": {
                    "test_device": {
                        "intervals": [
                            {
                                "start": "2025-06-02T00:00:00+02:00",
                                "end": "2025-06-02T01:00:00+02:00",
                                "command": "heat",
                                "power_kw": 2.5,
                                "energy_kwh": 1.1,
                                "source": "ai"
                            }
                        ]
                    }
                }
            }
        },
        blocking=True,
    )

    entity_id = "sensor.ai_energy_scheduler_test_device_command"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "heat"

@pytest.mark.asyncio
async def test_cleanup_entities_service(hass: HomeAssistant):
    """Test the cleanup_entities service runs without error."""
    await hass.services.async_call(
        DOMAIN,
        "cleanup_entities",
        {},
        blocking=True,
    )