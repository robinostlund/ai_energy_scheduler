"""Constants for AI Energy Scheduler."""

DOMAIN = "ai_energy_scheduler"

ATTR_INTERVALS = "intervals"
ATTR_COMMAND = "command"
ATTR_POWER_KW = "power_kw"
ATTR_ENERGY_KWH = "energy_kwh"
ATTR_SOURCE = "source"
ATTR_START = "start"
ATTR_END = "end"

ATTR_SCHEDULES = "schedules"

SENSOR_COMMAND = "command"
SENSOR_POWER_KW = "power_kw"
SENSOR_ENERGY_KWH = "energy_kwh"
SENSOR_NEXT_COMMAND = "next_command"
SENSOR_TOTAL_POWER_KW = "total_power_kw"
SENSOR_TOTAL_ENERGY_KWH_TODAY = "total_energy_kwh_today"
SENSOR_LAST_UPDATE = "last_update"
SENSOR_ALERT = "alert"

EVENT_COMMAND_ACTIVATED = "ai_energy_scheduler_command_activated"

SERVICE_IMPORT_SCHEDULE = "import_schedule"
SERVICE_CLEANUP_REMOVED = "cleanup_removed"

STORAGE_VERSION = 1
STORAGE_KEY = "ai_energy_scheduler.cache"

DEVICE_CALENDAR_DOMAIN = "calendar"
DEVICE_SENSOR_DOMAIN = "sensor"
DEVICE_BINARY_SENSOR_DOMAIN = "binary_sensor"
DEVICE_BUTTON_DOMAIN = "button"

DEFAULT_NAME = "AI Energy Scheduler"
DEFAULT_ICON = "mdi:calendar-clock"
