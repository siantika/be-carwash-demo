from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from domain.entities.base import _utcnow
from domain.exceptions import InvalidEntryTime


@dataclass(frozen=True)
class EntryTime:
    value: datetime
    def __init__(self, value: Optional[datetime] = None):
        object.__setattr__(
            self,
            "value",
            value or _utcnow()
        )
        
    def __post_init__(self):
        if self.value.tzinfo is None:
            raise InvalidEntryTime(
           "Entry time must be timezone-aware"
            )

        if self.value > datetime.now(timezone.utc):
            raise InvalidEntryTime(
              "Entry time cannot be in the future"
            )
