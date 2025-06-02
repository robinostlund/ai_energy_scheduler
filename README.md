# 🧠 AI Energy Scheduler

AI Energy Scheduler is a custom Home Assistant integration that schedules energy usage via JSON. It creates sensors, calendars, and triggers automations based on energy planning.

## ✅ Features
- JSON-based schedule via service
- Sensors per device (`command`, `power_kw`, `energy_kwh`, `next_command`)
- Total power/energy sensors
- Calendar per device
- Event trigger: `ai_energy_scheduler_command_activated`
- HACS compatible
- Visualize via ApexCharts
- Validate via JSON Schema

## 📊 Example ApexCharts
```yaml
type: custom:apexcharts-card
graph_span: 24h
series:
  - entity: sensor.ai_energy_scheduler_heat_pump_power_kw
    type: column
    name: Power (kW)
```

## 🔧 Automation Example
```yaml
alias: Notify on heat pump command change
trigger:
  platform: event
  event_type: ai_energy_scheduler_command_activated
condition:
  - condition: template
    value_template: "{{ trigger.event.data.device == 'heat_pump' }}"
action:
  - service: notify.notify
    data:
      message: "Heat pump changed command to {{ trigger.event.data.command }}"
```
