# AI Energy Scheduler

AI-driven energy scheduling for Home Assistant, supporting multiple buildings or zones with unique instance identifiers and friendly names.

## Features

- JSON-based scheduling per device
- Support for multiple instances (`instance_id`, `instance_friendly_name`)
- Per-device sensors and calendars (with clear prefix)
- Total and summary sensors
- Manual import of schedule via service (not config flow)
- Schema validation and error reporting
- Full HACS support
- Automatic Home Assistant events for all status changes

## Installation

1. Copy `ai_energy_scheduler` into your `custom_components` directory.
2. Restart Home Assistant.
3. Use the `ai_energy_scheduler.import_schedule` service to import your JSON schedule for each instance/building.
4. Use entities such as `sensor.ai_energy_scheduler_<instance_id>_<device>_command` in your dashboards.

## Example service call

```yaml
service: ai_energy_scheduler.import_schedule
data:
  instance_id: mainhouse
  instance_friendly_name: "Main House"
  schedule: >
    {
      "schedules": {
        "heat_pump": {
          "intervals": [
            {
              "start": "2025-06-02T00:00:00+02:00",
              "end": "2025-06-02T01:00:00+02:00",
              "command": "heat",
              "power_kw": 1.2,
              "energy_kwh": 1.2,
              "source": "ai"
            }
          ]
        }
      }
    }
