DOMAIN = "ai_energy_scheduler"
LOGGER_NAME = "ai_energy_scheduler"

SERVICE_SET_SCHEDULE = "set_schedule"

STORAGE_KEY = f"{DOMAIN}_store"
STORAGE_VERSION = 1

SCHEMA_FILE = "schema.json"

SCHEDULE_UPDATED_EVENT = f"{DOMAIN}_schedule_updated"
# CALENDAR_OVERRIDE_EVENT = f"{DOMAIN}_calendar_override"

PLATFORMS = ["sensor", "calendar"]