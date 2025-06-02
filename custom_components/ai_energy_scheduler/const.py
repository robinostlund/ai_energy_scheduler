"""
Constants for ai_energy_scheduler integration.
"""

DOMAIN = "ai_energy_scheduler"
VERSION = "1.0.0"

# Configuration options
CONF_SCHEDULES = "schedules"
CONF_INTERVALS = "intervals"

# Storage
STORAGE_KEY = f"{DOMAIN}_data"
STORAGE_VERSION = 1

# Service
SERVICE_SET_SCHEDULE = "set_schedule"
SERVICE_CLEANUP_REMOVED = "cleanup_removed"

# Events
EVENT_COMMAND_ACTIVATED = "ai_energy_scheduler_command_activated"

# Entity naming
SENSOR_ATTR_COMMAND = "command"
SENSOR_ATTR_POWER_KW = "power_kw"
SENSOR_ATTR_ENERGY_KWH = "energy_kwh"
SENSOR_ATTR_NEXT_COMMAND = "next_command"

# Sensor suffixes
SUFFIX_COMMAND = "command"
SUFFIX_POWER = "power_kw"
SUFFIX_ENERGY = "energy_kwh"
SUFFIX_NEXT = "next_command"

# Summary sensors
SENSOR_TOTAL_POWER = "total_power_kw"
SENSOR_TOTAL_ENERGY = "total_energy_kwh_today"
SENSOR_LAST_UPDATE = "last_update"

# Binary sensor
BINARY_ALERT = "alert"

# Calendar
CALENDAR_DOMAIN = "calendar"
# Each device will get ett kalenderobjekt med entity_id: calendar.<device>

# JSON Schema-fil
SCHEMA_FILE = "schema.json"

# Logging
LOGGER_NAME = DOMAIN

# JSON Schema validation errors
ERROR_INVALID_SCHEMA = "Invalid schedule schema"

# Defaults
DEFAULT_SCAN_INTERVAL = 60  # seconds för DataUpdateCoordinator

# Icons (enligt Material Design Icons)
ICON_SENSOR = "mdi:calendar-clock"
ICON_BINARY_ALERT = "mdi:alert-circle-outline"
ICON_SUMMARY_POWER = "mdi:flash"
ICON_SUMMARY_ENERGY = "mdi:factory"

