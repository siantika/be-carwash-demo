from typing import List

from fastapi import APIRouter, Depends

from api.dependencies.pagination import get_offset_pagination
from api.dependencies.shared import RoleChecker
from api.dependencies.user import (
    get_activate_user_usecase,
    get_deactivate_user_usecase,
    get_list_users_usecase,
    get_register_user_usecase,
)
from app.modules.identity.api.schemas import UserResponse
from api.schema.user_schema import CreateUserRequest
from app.modules.identity.domain.entities.user import UserRoleEnum
from application.dto.user_dto import RegisterUserCmd
from application.use_cases.user.list_users import ListUsersUseCase
from application.use_cases.user.manage_activation_user_usecase import (
    ActivateStatusUserUseCase,
    DeactivateStatusUserUseCase,
)
from application.use_cases.user.register_user_usecase import RegisterUserUseCase
from infra.repositories.response import BaseResponse

router = APIRouter()

@router.post("/users", response_model=BaseResponse[UserResponse])
async def create_user(
    payload:CreateUserRequest,
    user = Depends(RoleChecker([
        UserRoleEnum.ADMIN,
    ])),
    usecase:RegisterUserUseCase = Depends(get_register_user_usecase)
):    
    cmd = RegisterUserCmd(
            username= payload.username,
            plain_password= payload.plain_password,
            role= payload.role
        )

    created_user = await usecase.execute(cmd)
    
    return BaseResponse(
        status="success",
        message=f"Username: {created_user.username} with role: {created_user.role} is registered successfully",
        data=created_user
    )

@router.get("/users", response_model=BaseResponse[List[UserResponse]])
async def list_users(
    pagination = Depends(get_offset_pagination),
    usecase:ListUsersUseCase = Depends(get_list_users_usecase)
):    
    list_users = await usecase.execute(pagination.limit, pagination.offset)
    
    return BaseResponse(
        status="Success",
        message="Successfully",
        data=list_users
    )

    

@router.patch("/users/{user_id}/deactivate", 
              response_model=BaseResponse[UserResponse])
async def deactivate_user(
    user_id:int,
    user = Depends(RoleChecker([
    UserRoleEnum.ADMIN,
    ])),
    usecase: DeactivateStatusUserUseCase = Depends(get_deactivate_user_usecase)
):
    
    deactivated_user = await usecase.execute(user_id)
    
    return BaseResponse(
        status="success",
        message=f"User with id {deactivated_user.id} deactivated successfully",
        data= deactivated_user,
    )

@router.patch("/users/{user_id}/activate", 
              response_model=BaseResponse[UserResponse])
async def activate_user(
    user_id:int,
    user = Depends(RoleChecker([
    UserRoleEnum.ADMIN,
    ])),
    usecase: ActivateStatusUserUseCase = Depends(get_activate_user_usecase)
):

    activated_user = await usecase.execute(user_id)
    
    return BaseResponse(
        status="success",
        message=f"User with id {activated_user.id} is activated successfully",
        data= activated_user,
    )
      

    
