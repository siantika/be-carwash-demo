from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ServiceTypeListFilterDto:
    q: str | None = None
    is_active: bool | None = None
    is_primary: bool | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
