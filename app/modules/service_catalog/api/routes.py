from typing import List

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies.shared import RoleChecker
from app.modules.identity.domain.entities.account import RoleCode
from app.modules.service_catalog.api.dependencies import (
    get_activate_service_type_usecase,
    get_change_service_type_usecase,
    get_create_service_type_usecase,
    get_deactivate_service_type_usecase,
    get_list_service_types_usecase,
)
from app.modules.service_catalog.api.schemas import (
    CreateServiceTypeRequest,
    ServiceTypeResponse,
    UpdateServiceTypeRequest,
)
from app.modules.service_catalog.application.dto.service_type_dto import (
    CreateServiceTypeCmd,
    UpdateServiceTypeCmd,
)
from app.modules.service_catalog.application.use_cases.service_type_usecase import (
    ActivateServiceTypeUseCase,
    ChangeServiceTypeDataUseCase,
    CreateServiceTypeUseCase,
    DeactivateServiceTypeUseCase,
    ListServiceTypesUseCase,
)
from app.shared.response import BaseResponse, Metadata

router = APIRouter()

SERVICE_CATALOG_MANAGER_ROLES = [RoleCode.ADMIN, RoleCode.OWNER]


@router.get("", response_model=BaseResponse[List[ServiceTypeResponse]])
async def list_service_types(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    user=Depends(RoleChecker(SERVICE_CATALOG_MANAGER_ROLES)),
    usecase: ListServiceTypesUseCase = Depends(get_list_service_types_usecase),
):
    result = await usecase.execute(page=page, limit=limit)
    return BaseResponse(
        data=result.items,
        metadata=Metadata(
            page=result.page,
            limit=result.limit,
            total=result.total,
        ),
    )


@router.post(
    "",
    response_model=BaseResponse[ServiceTypeResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_service_type(
    payload: CreateServiceTypeRequest,
    user=Depends(RoleChecker(SERVICE_CATALOG_MANAGER_ROLES)),
    usecase: CreateServiceTypeUseCase = Depends(get_create_service_type_usecase),
):
    service_type = await usecase.execute(
        CreateServiceTypeCmd(
            name=payload.name,
            desc=payload.desc,
            price=payload.price,
            is_active=payload.is_active,
            is_primary=payload.is_primary,
        )
    )
    return BaseResponse(data=service_type)


@router.patch(
    "/{service_type_id}",
    response_model=BaseResponse[ServiceTypeResponse],
)
async def update_service_type(
    service_type_id: int,
    payload: UpdateServiceTypeRequest,
    user=Depends(RoleChecker(SERVICE_CATALOG_MANAGER_ROLES)),
    usecase: ChangeServiceTypeDataUseCase = Depends(get_change_service_type_usecase),
):
    service_type = await usecase.execute(
        service_type_id,
        UpdateServiceTypeCmd(
            name=payload.name,
            desc=payload.desc,
            price=payload.price,
            is_active=payload.is_active,
            is_primary=payload.is_primary,
        ),
    )
    return BaseResponse(data=service_type)


@router.patch(
    "/{service_type_id}/activate",
    response_model=BaseResponse[ServiceTypeResponse],
)
async def activate_service_type(
    service_type_id: int,
    user=Depends(RoleChecker(SERVICE_CATALOG_MANAGER_ROLES)),
    usecase: ActivateServiceTypeUseCase = Depends(get_activate_service_type_usecase),
):
    service_type = await usecase.execute(service_type_id)
    return BaseResponse(data=service_type)


@router.patch(
    "/{service_type_id}/deactivate",
    response_model=BaseResponse[ServiceTypeResponse],
)
async def deactivate_service_type(
    service_type_id: int,
    user=Depends(RoleChecker(SERVICE_CATALOG_MANAGER_ROLES)),
    usecase: DeactivateServiceTypeUseCase = Depends(get_deactivate_service_type_usecase),
):
    service_type = await usecase.execute(service_type_id)
    return BaseResponse(data=service_type)
