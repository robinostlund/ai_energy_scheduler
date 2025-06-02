# AI Energy Scheduler Documentation

## JSON Schema

Each device has:
- name (e.g., heat_pump)
- intervals: list of 1h intervals with fields:
  - start (ISO8601)
  - end (ISO8601)
  - command (string)
  - power_kw (float)
  - energy_kwh (float)
  - source ("ai" or "manual")

## Sensors Created

- sensor.ai_energy_scheduler_last_update
- sensor.ai_energy_scheduler_total_power_kw
- sensor.ai_energy_scheduler_total_energy_kwh
- binary_sensor.ai_energy_scheduler_alert
- sensor.ai_energy_scheduler_<device>_command
- sensor.ai_energy_scheduler_<device>_power_kw
- sensor.ai_energy_scheduler_<device>_energy_kwh

## Event

Fires `ai_energy_scheduler_command_activated` when command changes per device.