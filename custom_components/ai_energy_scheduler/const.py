"""Constants for AI Energy Scheduler."""

DOMAIN = "ai_energy_scheduler"
SCHEDULE_FILE_PREFIX = "ai_energy_scheduler_schedule_"
CONF_INSTANCE_ID = "instance_id"
CONF_INSTANCE_FRIENDLY_NAME = "instance_friendly_name"
CONF_JSON = "json"
CONF_SCHEDULES = "schedules"

# Entity suffixes
SENSOR_COMMAND = "command"
SENSOR_POWER_KW = "power_kw"
SENSOR_ENERGY_KWH = "energy_kwh"
SENSOR_NEXT_COMMAND = "next_command"
SENSOR_TOTAL_POWER = "total_power_kw"
SENSOR_TOTAL_ENERGY = "total_energy_kwh_today"
SENSOR_LAST_UPDATE = "last_update"
BINARY_SENSOR_ALERT = "alert"
BUTTON_CLEANUP = "cleanup_button"

# Events
EVENT_COMMAND_ACTIVATED = f"{DOMAIN}_command_activated"
EVENT_IMPORT_SCHEDULE = f"{DOMAIN}_import_schedule"
EVENT_VALIDATE_SCHEDULE = f"{DOMAIN}_validate_schedule"
EVENT_CLEANUP = f"{DOMAIN}_cleanup"
EVENT_ALERT_CHANGED = f"{DOMAIN}_alert_changed"
