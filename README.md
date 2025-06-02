# AI Energy Scheduler

[![hassfest](https://github.com/robinostlund/ai_energy_scheduler/actions/workflows/test_integration.yaml/badge.svg)](https://github.com/robinostlund/ai_energy_scheduler/actions/workflows/test_integration.yaml)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AI Energy Scheduler is a Home Assistant custom integration that schedules energy-consuming devices using AI-generated JSON.

## 🧠 [Prompt Template](https://github.com/robinostlund/ai_energy_scheduler/blob/main/prompt_template.md)

## 📘 [Documentation](https://github.com/robinostlund/ai_energy_scheduler/blob/main/docs/README.md)

## 🛠️ HACS Custom Repository Setup

1. Go to HACS → Integrations → ⋮ → Custom repositories
2. Add: `https://github.com/robinostlund/ai_energy_scheduler`
3. Set category: Integration
4. Search for AI Energy Scheduler
5. Install and restart Home Assistant

## 🛠️ Services

### `ai_energy_scheduler.set_schedule`

Submit schedule JSON to the integration.

```yaml
service: ai_energy_scheduler.set_schedule
data:
  schedule_data: !include example_schedule.json
```

### `ai_energy_scheduler.cleanup_entities`

Removes any `unavailable` sensors and associated calendars for devices no longer in the current schedule.
You can trigger this manually via automation or the UI button.

## 📯 Entities

- `sensor.ai_energy_scheduler_last_update` — timestamp of last schedule update
- `sensor.ai_energy_scheduler_total_power_kw` — current summed kW
- `sensor.ai_energy_scheduler_total_energy_kwh` — today's estimated kWh
- `binary_sensor.ai_energy_scheduler_alert` — alert if latest schedule input failed
- `button.ai_energy_scheduler_cleanup` — triggers cleanup_entities service manually

## 🧩 Entities Created

### Global Sensors

| Entity ID | Type | Description |
|-----------|------|-------------|
| `sensor.ai_energy_scheduler_last_update` | Sensor | Timestamp of last schedule update |
| `sensor.ai_energy_scheduler_total_power_kw` | Sensor | Sum of all current kW load |
| `sensor.ai_energy_scheduler_total_energy_kwh` | Sensor | Estimated total energy consumption today |
| `binary_sensor.ai_energy_scheduler_alert` | Binary Sensor | Active if schedule JSON input failed |
| `button.ai_energy_scheduler_cleanup` | Button | Triggers manual cleanup of stale entities |

### Per Device (e.g., `heat_pump`)

| Entity ID | Type | Description |
|-----------|------|-------------|
| `sensor.ai_energy_scheduler_heat_pump_command` | Sensor | Current command for the device |
| `sensor.ai_energy_scheduler_heat_pump_power_kw` | Sensor | Power load for current period |
| `sensor.ai_energy_scheduler_heat_pump_energy_kwh` | Sensor | Energy use for current period |
| `calendar.ai_energy_scheduler_heat_pump_schedule` | Calendar | Calendar view of command schedule |