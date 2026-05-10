from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from app.shared.domain.entities.base import BaseEntity

from app.shared.domain.exceptions.exceptions import (
    BusinessRuleViolation,
    InvalidValueObject,
)
from domain.value_object.money import Money


@dataclass
class ServiceType(BaseEntity):
    name: str
    desc: str
    price: Money
    is_active: bool = True
    is_primary: bool = False

    def __post_init__(self):
        if not self.name.strip():
            raise InvalidValueObject("Service name must not be empty")

        if not self.desc.strip():
            raise InvalidValueObject("Service description must not be empty")

        if self.price is None:
            raise InvalidValueObject("Service price is required")

    # ---- domain behaviors ----

    def deactivate(self):
        if self.is_primary:
            raise BusinessRuleViolation(
                "Primary service cannot be deactivated"
            )
        self.is_active = False

    def activate(self):
        self.is_active = True

    def mark_as_primary(self):
        self.is_primary = True
        self.is_active = True

    def change_price(self, new_price: Money):
        self.price = new_price
        
    def update_details(
        self,
        *,
        name: Optional[str] = None,
        desc: Optional[str] = None,
        price: Optional[Decimal] = None,
        is_active: Optional[bool] = None,
        is_primary: Optional[bool] = None,
    ) -> None:
        # apply partial update
        if name is not None:
            self.name = name
        if desc is not None:
            self.desc = desc
        if price is not None:
            self.price = price
        if is_active is not None:
            self.is_active = is_active
        if is_primary is not None:
            self.is_primary = is_primary
