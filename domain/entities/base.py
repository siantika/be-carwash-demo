from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from domain.exceptions import BusinessRuleViolation


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

@dataclass(kw_only=True) # `kw` mode abandons the args queue. No error for 'follow default args'
class BaseEntity:
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)
    id: Optional[int] = None  

    def __post_init__(self):
        self.ensure_timezone_aware(self.created_at, "created_at")
        self.ensure_timezone_aware(self.updated_at, "updated_at")

        if self.updated_at < self.created_at:
            raise BusinessRuleViolation(
                "updated_at time cannot be earlier than created_at time"
            )
    
    @staticmethod
    def ensure_timezone_aware(dt: datetime, field_name: str):
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            raise BusinessRuleViolation(f"{field_name} must be timezone-aware")
