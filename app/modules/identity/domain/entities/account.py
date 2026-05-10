from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from app.modules.identity.domain.value_objects.email import Email
from app.modules.identity.domain.value_objects.username import Username
from app.shared.domain.entities.base import BaseEntity
from app.shared.domain.exceptions.exceptions import BusinessRuleViolation

MAX_LOGIN_ATTEMPTS = 3
LOCK_DURATION = timedelta(minutes=15)


class RoleCode(str, Enum):
    CASHIER = "CASHIER"
    ADMIN = "ADMIN"
    OWNER = "OWNER"


@dataclass(kw_only=True)
class Account(BaseEntity):
    username: Username
    email: Email
    password_hash: str
    role: RoleCode
    failed_login_attempts: int = 0
    locked_until: datetime | None = None
    last_login_at: datetime | None = None
    is_active: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()

        if not self.password_hash.strip():
            raise BusinessRuleViolation("Password hash must not be empty")

        if self.failed_login_attempts < 0:
            raise BusinessRuleViolation("Failed login attempts must not be negative")

        if self.locked_until is not None:
            self.ensure_timezone_aware(self.locked_until, "locked_until")

        if self.last_login_at is not None:
            self.ensure_timezone_aware(self.last_login_at, "last_login_at")

    # --- Domain behaviours ---
    def has_role(self, role: RoleCode) -> bool:
        return self.role == role

    def is_admin(self) -> bool:
        return self.role == RoleCode.ADMIN

    def is_cashier(self) -> bool:
        return self.role == RoleCode.CASHIER

    def is_owner(self) -> bool:
        return self.role == RoleCode.OWNER

    def can_login(self, now: datetime) -> bool:
        self.ensure_timezone_aware(now, "now")

        if not self.is_active:
            return False

        if self.locked_until is not None and self.locked_until > now:
            return False

        return True

    def activate(self) -> None:
        self.is_active = True

    def deactivate(self) -> None:
        self.is_active = False

    def record_successful_login(self, now: datetime) -> None:
        self.ensure_timezone_aware(now, "now")
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login_at = now

    def record_failed_login(self, now: datetime) -> None:
        self.ensure_timezone_aware(now, "now")
        self.failed_login_attempts += 1

        if self.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
            self.locked_until = now + LOCK_DURATION
