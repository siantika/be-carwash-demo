from dataclasses import dataclass
from datetime import datetime

from app.shared.domain.entities.base import BaseEntity
from app.shared.domain.exceptions.exceptions import BusinessRuleViolation


@dataclass(kw_only=True)
class RefreshToken(BaseEntity):
    account_id: int
    token_hash: str
    expires_at: datetime
    revoked_at: datetime | None = None
    last_used_at: datetime | None = None

    def __post_init__(self) -> None:
        super().__post_init__()

        if self.account_id <= 0:
            raise BusinessRuleViolation("Refresh token account_id must be positive")

        if not self.token_hash.strip():
            raise BusinessRuleViolation("Refresh token hash must not be empty")

        self.ensure_timezone_aware(self.expires_at, "expires_at")

        if self.revoked_at is not None:
            self.ensure_timezone_aware(self.revoked_at, "revoked_at")

        if self.last_used_at is not None:
            self.ensure_timezone_aware(self.last_used_at, "last_used_at")

    def is_active(self, now: datetime) -> bool:
        self.ensure_timezone_aware(now, "now")
        return self.revoked_at is None and self.expires_at > now

    def mark_used(self, now: datetime) -> None:
        self.ensure_timezone_aware(now, "now")
        self.last_used_at = now
        self.updated_at = now

    def revoke(self, now: datetime) -> None:
        self.ensure_timezone_aware(now, "now")
        self.revoked_at = now
        self.updated_at = now
