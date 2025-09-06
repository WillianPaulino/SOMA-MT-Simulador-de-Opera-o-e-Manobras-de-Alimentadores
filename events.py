from dataclasses import dataclass
from typing import Optional, Literal

EventType = Literal["fault_permanent", "fault_temporary", "device_out"]

@dataclass
class Event:
    type: EventType
    target: str          # ex.: "line:RCL-02" ou "line:R3B-B3"
    t0_min: float = 0.0
    duration_min: float = 0.0
    note: Optional[str] = None

def parse_target(target: str):
    kind, name = target.split(":", 1)
    return kind, name
