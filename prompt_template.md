# Prompt Template for AI Generated Schedule JSON

Use this prompt with any AI assistant (such as ChatGPT or Claude) to generate a valid schedule for the ai_energy_scheduler component:

---

🔧 **Prompt:**

Generate a valid JSON schedule for Home Assistant's ai_energy_scheduler integration. Use the following format:

- The root key must be "schedules".
- Each key under "schedules" represents a device name (e.g., "heat_pump").
- Each device has an "intervals" list.
- Each interval contains:
  - "start": ISO 8601 timestamp (e.g., "2025-06-02T00:00:00+02:00")
  - "end": ISO 8601 timestamp
  - "command": a string like "heat", "cool", "off", "sleep"
  - Optional: "power_kw": float, "energy_kwh": float
  - Optional: "source": either "ai" or "manual"

Create 24 intervals of 1 hour each for a device called "heat_pump", using the "heat" command throughout.

Respond only with JSON.

---

💡 Example Output:

```json
{
  "schedules": {
    "heat_pump": {
      "intervals": [
        {
          "start": "2025-06-02T00:00:00+02:00",
          "end": "2025-06-02T01:00:00+02:00",
          "command": "heat",
          "power_kw": 2.0,
          "energy_kwh": 1.9,
          "source": "ai"
        }
        // ... 23 more intervals
      ]
    }
  }
}
```

You can copy this prompt directly into your AI tool of choice.