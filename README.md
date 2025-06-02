# AI Energy Scheduler

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square)](https://hacs.xyz/)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/robinostlund/ai_energy_scheduler/test_and_validate.yaml?branch=main)](https://github.com/robinostlund/ai_energy_scheduler/actions)

**AI-driven energy scheduling for Home Assistant.**  
Import a JSON schedule for your devices (heat pump, battery, EV, etc.), visualize and automate, all powered by AI or manual plans.

---

## Features

- **JSON-based scheduling:** Plan your devices per interval, including command, power (kW), energy (kWh), and source (ai/manual).
- **Automatic entities:** Sensors, binary sensors, calendars, and buttons for every device.
- **Summary sensors:** Total power (kW), total energy (kWh) for today, last update.
- **Calendar integration:** Each device gets its own calendar, visible and overrideable.
- **Event support:** Emits `ai_energy_scheduler_command_activated` every time a new command is activated (perfect for automations).
- **Error indication:** Binary sensor alerts you if your schedule fails validation or parsing.
- **HACS compatible:** Easy to install and update.
- **Full logging:** English log output, clear error messages.
- **UI config flow:** Add/remove the integration via the Home Assistant UI, with preview of entities.

---

## Example JSON Schema

```json
{
  "schedules": {
    "heat_pump": {
      "intervals": [
        {
          "start": "2025-06-02T00:00:00+02:00",
          "end": "2025-06-02T06:00:00+02:00",
          "command": "off",
          "power_kw": 0,
          "energy_kwh": 0,
          "source": "ai"
        },
        {
          "start": "2025-06-02T06:00:00+02:00",
          "end": "2025-06-02T22:00:00+02:00",
          "command": "heat",
          "power_kw": 2.5,
          "energy_kwh": 40,
          "source": "ai"
        },
        {
          "start": "2025-06-02T22:00:00+02:00",
          "end": "2025-06-03T00:00:00+02:00",
          "command": "standby",
          "power_kw": 0.3,
          "energy_kwh": 0.6,
          "source": "manual"
        }
      ]
    }
  }
}
