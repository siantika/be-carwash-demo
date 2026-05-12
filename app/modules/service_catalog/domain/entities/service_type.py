from dataclasses import dataclass
from datetime import datetime

from app.shared.domain.entities.base import BaseEntity
from app.shared.domain.exceptions.exceptions import (
    BusinessRuleViolation,
    InvalidValueObject,
)
from app.shared.domain.value_objects.money import Money


@dataclass(kw_only=True)
class ServiceType(BaseEntity):
    name: str
    desc: str
    price: Money
    is_active: bool = True
    is_primary: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()

        if not self.name.strip():
            raise InvalidValueObject("Service name must not be empty")

        if not self.desc.strip():
            raise InvalidValueObject("Service description must not be empty")

        if self.price is None:
            raise InvalidValueObject("Service price is required")

        self.name = self.name.strip()
        self.desc = self.desc.strip()

    def activate(self) -> None:
        self.is_active = True

    def deactivate(self) -> None:
        if self.is_primary:
            raise BusinessRuleViolation("Primary service cannot be deactivated")

        self.is_active = False

    def delete(self, deleted_at: datetime) -> None:
        self.ensure_timezone_aware(deleted_at, "deleted_at")

        if self.is_primary:
            raise BusinessRuleViolation("Primary service cannot be deleted")

        self.is_active = False
        self.deleted_at = deleted_at

    def mark_as_primary(self) -> None:
        self.is_primary = True
        self.is_active = True

    def update_details(
        self,
        *,
        name: str | None = None,
        desc: str | None = None,
        price: Money | None = None,
        is_active: bool | None = None,
        is_primary: bool | None = None,
    ) -> None:
        if name is not None:
            self.name = name.strip()

        if desc is not None:
            self.desc = desc.strip()

        if price is not None:
            self.price = price

        if is_active is not None:
            self.is_active = is_active

        if is_primary is not None:
            self.is_primary = is_primary

        self.__post_init__()
