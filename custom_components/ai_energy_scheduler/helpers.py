from dataclasses import dataclass
from typing import Optional

@dataclass
class Intervals:
    """Intervals."""
    start: str
    end: str
    command: str
    power_kw:  float
    energy_kwh: float | None = None
    source: str | None = "ai"
    command_override: Optional[str] = None
