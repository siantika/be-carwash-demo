from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

@dataclass(frozen=True)
class CreateServiceTypeCmd:
    name: str
    desc: str
    price: Decimal
    is_active: bool = True
    is_primary: bool = False


@dataclass(frozen=True)
class UpdateServiceTypeCmd:
    name: str | None = None
    desc: str | None = None
    price: Decimal | None = None
    is_active: bool | None = None
    is_primary: bool | None = None


@dataclass(frozen=True)
class ServiceTypeResultDto:
    id: int | None
    name: str
    desc: str
    price: Decimal
    is_active: bool
    is_primary: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ServiceTypeListResultDto:
    items: list[ServiceTypeResultDto]
    total: int
    page: int
    limit: int
