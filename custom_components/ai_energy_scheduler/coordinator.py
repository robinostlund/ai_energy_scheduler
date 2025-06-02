"""Coordinator for AI Energy Scheduler."""
import json
import os
import hashlib
from .const import SCHEDULE_FILE_PREFIX

def _schema_hash(data):
    """Generate a hash of the schedule dict."""
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()

class AiEnergySchedulerCoordinator:
    """Manages per-instance state, schedule cache, hash, and friendly name."""

    def __init__(self, hass, instance_id, instance_friendly_name):
        self.hass = hass
        self.instance_id = instance_id
        self.instance_friendly_name = instance_friendly_name
        self.schedule = {}
        self.alert = False
        self._schema_hash = None

    def load_schedule(self):
        """Load the schedule from file (per instance)."""
        path = self.hass.config.path(f"{SCHEDULE_FILE_PREFIX}{self.instance_id}.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                self.schedule = json.load(f)
        else:
            self.schedule = {}
        self._schema_hash = _schema_hash(self.schedule)

    def save_schedule(self):
        """Save the schedule to file (per instance)."""
        path = self.hass.config.path(f"{SCHEDULE_FILE_PREFIX}{self.instance_id}.json")
        with open(path, "w") as f:
            json.dump(self.schedule, f, indent=2)

    def schema_hash(self):
        return self._schema_hash
