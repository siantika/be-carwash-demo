from decimal import Decimal
from typing import Annotated, List

from fastapi import APIRouter, Depends, Path, Query, status

from app.api.dependencies.shared import RoleChecker
from app.modules.identity.domain.entities.account import RoleCode
from app.modules.service_catalog.api.dependencies import (
    get_activate_service_type_usecase,
    get_change_service_type_usecase,
    get_create_service_type_usecase,
    get_deactivate_service_type_usecase,
    get_delete_service_type_usecase,
    get_find_service_type_by_id,
    get_find_service_type_by_name,
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
from app.modules.service_catalog.application.queries.models import (
    ServiceTypeListFilterDto,
)
from app.modules.service_catalog.application.use_cases.service_type_usecase import (
    ActivateServiceTypeUseCase,
    ChangeServiceTypeDataUseCase,
    CreateServiceTypeUseCase,
    DeactivateServiceTypeUseCase,
    DeleteServiceTypeUseCase,
    FindServiceTypeByIdUseCase,
    FindServiceTypeByNameUseCase,
    ListServiceTypesUseCase,
)
from app.shared.response import BaseResponse, Metadata

router = APIRouter()

SERVICE_CATALOG_MANAGER_ROLES = [RoleCode.ADMIN, RoleCode.OWNER]


@router.get("", response_model=BaseResponse[List[ServiceTypeResponse]])
async def list_service_types(
    q: str | None = Query(default=None, min_length=1, max_length=100),
    is_active: bool | None = Query(default=None),
    is_primary: bool | None = Query(default=None),
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    user=Depends(RoleChecker(SERVICE_CATALOG_MANAGER_ROLES)),
    usecase: ListServiceTypesUseCase = Depends(get_list_service_types_usecase),
):
    result = await usecase.execute(
        filters=ServiceTypeListFilterDto(
            q=q,
            is_active=is_active,
            is_primary=is_primary,
            min_price=min_price,
            max_price=max_price,
        ),
        page=page,
        limit=limit,
    )
    return BaseResponse(
        data=result.items,
        metadata=Metadata(
            page=result.page,
            limit=result.limit,
            total=result.total,
        ),
    )


@router.get("/name/{service_name}", response_model=BaseResponse[ServiceTypeResponse])
async def find_service_type_by_name(
    service_name: Annotated[str, Path(min_length=3, max_length=50)],
    user=Depends(RoleChecker(SERVICE_CATALOG_MANAGER_ROLES)),
    usecase: FindServiceTypeByNameUseCase = Depends(get_find_service_type_by_name),
):
    service_type = await usecase.execute(service_name)
    return BaseResponse(data=service_type)


@router.get("/{service_type_id}", response_model=BaseResponse[ServiceTypeResponse])
async def find_service_type_by_id(
    service_type_id: Annotated[int, Path(ge=1)],
    user=Depends(RoleChecker(SERVICE_CATALOG_MANAGER_ROLES)),
    usecase: FindServiceTypeByIdUseCase = Depends(get_find_service_type_by_id),
):
    service_type = await usecase.execute(service_type_id)
    return BaseResponse(data=service_type)


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
    service_type_id: Annotated[int, Path(ge=1)],
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
    service_type_id: Annotated[int, Path(ge=1)],
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
    service_type_id: Annotated[int, Path(ge=1)],
    user=Depends(RoleChecker(SERVICE_CATALOG_MANAGER_ROLES)),
    usecase: DeactivateServiceTypeUseCase = Depends(get_deactivate_service_type_usecase),
):
    service_type = await usecase.execute(service_type_id)
    return BaseResponse(data=service_type)


@router.delete("/{service_type_id}", response_model=BaseResponse[None])
async def delete_service_type(
    service_type_id: Annotated[int, Path(ge=1)],
    user=Depends(RoleChecker(SERVICE_CATALOG_MANAGER_ROLES)),
    usecase: DeleteServiceTypeUseCase = Depends(get_delete_service_type_usecase),
):
    await usecase.execute(service_type_id)
    return BaseResponse(data=None)
