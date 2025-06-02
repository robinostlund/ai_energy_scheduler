"""JSON Schema validator for AI Energy Scheduler."""
import jsonschema
import json
import os

def validate_schedule_json(data, hass):
    """Validate schedule data against schema.json."""
    import_path = os.path.join(
        hass.config.path("custom_components/ai_energy_scheduler"), "schema.json"
    )
    with open(import_path, "r") as f:
        schema = json.load(f)
    jsonschema.validate(instance=data, schema=schema)
