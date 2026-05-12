from dataclasses import dataclass
from datetime import datetime, timezone

from app.shared.domain.entities.base import _utcnow
from app.shared.domain.exceptions.exceptions import InvalidEntryTime


@dataclass(frozen=True)
class EntryTime:
    value: datetime

    def __init__(self, value: datetime | None = None):
        object.__setattr__(self, "value", value or _utcnow())
        self.__post_init__()

    def __post_init__(self):
        if self.value.tzinfo is None or self.value.tzinfo.utcoffset(self.value) is None:
            raise InvalidEntryTime("Entry time must be timezone-aware")

        if self.value > datetime.now(timezone.utc):
            raise InvalidEntryTime("Entry time cannot be in the future")
