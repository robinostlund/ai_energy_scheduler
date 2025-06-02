SCHEDULE_SCHEMA = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "schedules": {
      "type": "object",
      "patternProperties": {
        "^[a-zA-Z0-9_]+$": {
          "type": "object",
          "properties": {
            "unit": {
              "type": "string"
            },
            "source": {
              "type": "string"
            },
            "schedule": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "start": {
                    "type": "string",
                    "format": "date-time"
                  },
                  "end": {
                    "type": "string",
                    "format": "date-time"
                  },
                  "command": {
                    "type": "string"
                  },
                  "power_kw": {
                    "type": "number"
                  },
                  "energy_kwh": {
                    "type": "number"
                  }
                },
                "required": [
                  "start",
                  "end",
                  "command"
                ]
              }
            }
          },
          "required": [
            "unit",
            "source",
            "schedule"
          ]
        }
      },
      "additionalProperties": false
    }
  },
  "required": [
    "schedules"
  ]
}