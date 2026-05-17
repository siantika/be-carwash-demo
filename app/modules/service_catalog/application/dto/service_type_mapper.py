from app.modules.service_catalog.application.dto.service_type_dto import (
    ServiceTypeResultDto,
)
from app.modules.service_catalog.domain.entities.service_type import ServiceType


def to_service_type_result(service_type: ServiceType) -> ServiceTypeResultDto:
    return ServiceTypeResultDto(
        id=service_type.id,
        name=service_type.name,
        desc=service_type.desc,
        price=service_type.price.amount,
        is_active=service_type.is_active,
        is_primary=service_type.is_primary,
        created_at=service_type.created_at,
        updated_at=service_type.updated_at,
    )
