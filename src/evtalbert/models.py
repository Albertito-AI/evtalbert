from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime

class PreStartState(str, Enum):
    ALERT = "alertness"  # operational alertness
    FEVER = "fever"
    APATHY = "apathy"

class Outcome(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"

@dataclass
class SessionEntry:
    ts: str  # ISO 8601 UTC time
    athlete: str
    sport: str
    task: str
    pre_state: PreStartState
    regulation: str
    sec_to_target: Optional[float]
    obstacle: str
    outcome: Outcome
    rpe: Optional[int]
    volition: Dict[str, int]  # e.g., purposefulness, persistence, self_control, decisiveness
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["pre_state"] = self.pre_state.value
        d["outcome"] = self.outcome.value
        return d

def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"