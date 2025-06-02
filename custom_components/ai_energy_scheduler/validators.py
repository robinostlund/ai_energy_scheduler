"""Schedule validators for AI Energy Scheduler."""

import json
from jsonschema import validate, ValidationError
import os

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.json")

def validate_schedule(schedule: dict):
    """Validate schedule against schema.json."""
    import jsonschema

    with open(SCHEMA_PATH, encoding="utf-8") as f:
        schema = json.load(f)
    try:
        jsonschema.validate(instance=schedule, schema=schema)
    except ValidationError as err:
        raise ValueError(f"Schedule does not match schema: {err.message}")
