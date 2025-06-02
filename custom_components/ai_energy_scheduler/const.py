"""Constants for the AI Energy Scheduler integration."""

DOMAIN = "ai_energy_scheduler"

# Keys for storing data
DATA_COORDINATOR = "coordinator"

# Services
SERVICE_VALIDATE = "validate_schedule"
SERVICE_UPDATE = "update_schedule"
SERVICE_CLEANUP = "cleanup_removed"

# File for caching schedule
SCHEDULE_CACHE_FILENAME = "ai_energy_scheduler_schedule.json"

# Entity naming
SENSOR_COMMAND = "command"
SENSOR_POWER_KW = "power_kw"
SENSOR_ENERGY_KWH = "energy_kwh"
SENSOR_NEXT_COMMAND = "next_command"
SENSOR_TOTAL_POWER_KW = "total_power_kw"
SENSOR_TOTAL_ENERGY_KWH_TODAY = "total_energy_kwh_today"

# Binary sensor
BINARY_SENSOR_ALERT = "alert"

# Button
BUTTON_CLEANUP = "cleanup"

# Calendar event
CALENDAR_EVENT_SUMMARY = "Scheduled Command"

# Attribute keys
ATTR_COMMAND = "command"
ATTR_SOURCE = "source"
ATTR_START = "start"
ATTR_END = "end"
ATTR_POWER_KW = "power_kw"
ATTR_ENERGY_KWH = "energy_kwh"
ATTR_NEXT_EVENT = "next_event"

# Event
EVENT_COMMAND_ACTIVATED = "ai_energy_scheduler_command_activated"

# Config flow
CONF_NAME = "name"
CONF_JSON_DATA = "json_data"

# Other
DEFAULT_NAME = "AI Energy Scheduler"
