from datetime import datetime, timezone
from decimal import Decimal

from app.modules.service_catalog.infra.repositories.service_type_repo import _mapper
from app.shared.domain.value_objects.money import Money


def test_service_type_mapper_loads_database_row() -> None:
    now = datetime.now(timezone.utc)

    service_type = _mapper(
        {
            "id": 1,
            "name": "Premium Wash",
            "desc": "Premium exterior wash",
            "price": Decimal("75000"),
            "is_active": True,
            "is_primary": False,
            "created_at": now,
            "updated_at": now,
        }
    )

    assert service_type.id == 1
    assert service_type.name == "Premium Wash"
    assert service_type.desc == "Premium exterior wash"
    assert service_type.price == Money(Decimal("75000"))
    assert service_type.is_active is True
    assert service_type.is_primary is False
