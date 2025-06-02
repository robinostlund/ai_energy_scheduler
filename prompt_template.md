# Prompt Template – AI Energy Scheduler

Use this prompt to generate valid JSON schedule input for Home Assistant.

> Generate JSON matching this format:
> https://github.com/robinostlund/ai_energy_scheduler/blob/main/custom_components/ai_energy_scheduler/example_schedule.json

Requirements:
- 24 intervals per day
- start/end in ISO 8601 with timezone
- fields: start, end, command, power_kw, energy_kwh, source
- use "ai" as source