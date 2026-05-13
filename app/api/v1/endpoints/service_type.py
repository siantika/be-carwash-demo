from typing import List

from fastapi import APIRouter, Depends, Request

from app.api.dependencies.pagination import get_offset_pagination
from app.api.dependencies.service_type import (
    get_activate_service_type_usercase,
    get_create_service_type_usecase,
    get_deactivate_service_type_usercase,
    get_list_service_types_usecase,
)
from app.api.dependencies.shared import RoleChecker
from app.api.schema.pagination_schema import OffsetPagination
from app.api.schema.service_type_schema import CreateServiceTypeRequest, ServiceTypeResponse
from application.dto.service_type_dto import CreateServiceTypeCmd
from application.use_cases.service_type.create_service_type_usecase import (
    CreateServiceTypeUseCase,
)
from application.use_cases.service_type.manage_activation_status_usecase import (
    ActivateStatusServiceTypeUseCase,
    DeactivateStatusServiceTypeUseCase,
)
from app.modules.identity.domain.entities.account import RoleCode
from app.shared.response import BaseResponse
from app.shared.interfaces.i_usecase import IUseCase

router = APIRouter()


@router.get("/service-types", response_model=BaseResponse[List[ServiceTypeResponse]])
async def list_service_types(
    pagination:OffsetPagination = Depends(get_offset_pagination),
    user = Depends(RoleChecker([
        RoleCode.ADMIN,
        ])),
    usecase:IUseCase = Depends(get_list_service_types_usecase)
):
    service_types = await usecase.execute(pagination.limit,
                                          pagination.offset)
    
    return BaseResponse(
        status="success",
        message="List all service types successfully!",
        data=service_types,
    )
    
    
@router.post("/service-types", response_model=BaseResponse[ServiceTypeResponse])
async def post_service_types(
    payload: CreateServiceTypeRequest,
    user = Depends(RoleChecker([
        RoleCode.ADMIN,
        ])),
    usecase:CreateServiceTypeUseCase = Depends(get_create_service_type_usecase)
):
    cmd = CreateServiceTypeCmd(
        name= payload.name,
        desc= payload.desc,
        price= payload.price,
        is_active= payload.is_active,
        is_primary= payload.is_primary
    )
    created_service_type = await usecase.execute(cmd)
    
    return BaseResponse(
        status="success",
        message=f"Service type with id {created_service_type.id} created successfully!",
        data=created_service_type,
    )

@router.patch(
    "/service-types/{service_type_id}/activate",
    response_model=BaseResponse[ServiceTypeResponse],
)
async def activate_service_type(
    service_type_id: int,
    user = Depends(RoleChecker([
        RoleCode.ADMIN,
        ])),
    usecase:IUseCase=Depends(get_activate_service_type_usercase),
):
    activated_service_type = await usecase.execute(service_type_id)
    
    return BaseResponse(
        status="success",
        message=f"Service type with id {activated_service_type.id} is activated",
        data=activated_service_type,
    )


@router.patch(
    "/service-types/{service_type_id}/deactivate",
    response_model=BaseResponse[ServiceTypeResponse],
)
async def deactivate_service_type(
    service_type_id: int,
    user = Depends(RoleChecker([
        RoleCode.ADMIN,
        ])),
    usecase:IUseCase=Depends(get_deactivate_service_type_usercase),
):
    deactivated_service_type = await usecase.execute(service_type_id)

    return BaseResponse(
        status="success",
        message=f"Service type with id {deactivated_service_type.id} is deactivated",
        data=deactivated_service_type,
    )
