from dataclasses import dataclass
from datetime import datetime

from app.shared.domain.entities.base import BaseEntity
from app.shared.domain.exceptions.exceptions import BusinessRuleViolation


@dataclass(kw_only=True)
class Device(BaseEntity):
    device_code: str
    name: str
    location: str | None = None
    is_active: bool = True
    last_seen_at: datetime | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.device_code.strip():
            raise BusinessRuleViolation("Device code must not be empty")
        if not self.name.strip():
            raise BusinessRuleViolation("Device name must not be empty")
        if self.last_seen_at is not None:
            self.ensure_timezone_aware(self.last_seen_at, "last_seen_at")
