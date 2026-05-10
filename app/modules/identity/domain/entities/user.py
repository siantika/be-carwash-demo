from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.shared.domain.entities.base import BaseEntity
from app.shared.domain.exceptions.exceptions import BusinessRuleViolation


class UserRoleEnum(str, Enum):
    CASHIER = "CASHIER"
    ADMIN = "ADMIN"


@dataclass(kw_only=True)
class User(BaseEntity):
    username: str
    role: UserRoleEnum | str
    password_hash: Optional[str] = None
    is_active: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()

        if not self.username.strip():
            raise BusinessRuleViolation("Username must not be empty")

        if not isinstance(self.role, UserRoleEnum):
            try:
                self.role = UserRoleEnum(self.role)
            except ValueError as exc:
                raise BusinessRuleViolation(f"Invalid user role: {self.role}") from exc

    # --- Domain behaviours ---
    def has_role(self, role: UserRoleEnum) -> bool:
        return self.role == role

    def is_admin(self) -> bool:
        return self.role == UserRoleEnum.ADMIN

    def is_cashier(self) -> bool:
        return self.role == UserRoleEnum.CASHIER

    def activate(self) -> None:
        self.is_active = True

    def deactivate(self) -> None:
        self.is_active = False
