from typing import Annotated, List

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.dependencies.shared import RoleChecker, get_current_user
from app.modules.identity.api.dependencies import (
    get_activate_account_usecase,
    get_deactivate_account_usecase,
    get_delete_account_usecase,
    get_get_account_usecase,
    get_list_accounts_usecase,
    get_login_usecase,
    get_logout_usecase,
    get_refresh_session_usecase,
    get_register_account_usecase,
)
from app.modules.identity.api.schemas import (
    AccountResponse,
    CurrentUserResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RegisterAccountRequest,
    TokenResponse,
)
from app.modules.identity.application.commands.account_command import (
    ActivateAccountUseCase,
    DeactivateAccountUseCase,
    DeleteAccountUseCase,
    RegisterAccountUseCase,
)
from app.modules.identity.application.commands.auth_command import (
    LoginUseCase,
    LogoutUseCase,
    RefreshSessionUseCase,
)
from app.modules.identity.application.dto.account_dto import RegisterAccountCmd
from app.modules.identity.application.dto.auth_context_dto import AuthContextDto
from app.modules.identity.application.queries.account_query import (
    GetAccountUseCase,
    ListAccountsUseCase,
)
from app.modules.identity.domain.entities.account import RoleCode
from app.shared.middleware.limiter import limiter
from app.shared.response import BaseResponse, Metadata

auth_router = APIRouter()
account_router = APIRouter()

ACCOUNT_MANAGER_ROLES = [RoleCode.ADMIN, RoleCode.OWNER]


@account_router.post(
    "",
    response_model=BaseResponse[AccountResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[],
)
async def register_account(
    payload: RegisterAccountRequest,
    usecase: Annotated[RegisterAccountUseCase, Depends(get_register_account_usecase)],
    user=Depends(RoleChecker(ACCOUNT_MANAGER_ROLES)),
):
    created_account = await usecase.execute(
        RegisterAccountCmd(
            username=payload.username,
            email=payload.email,
            password=payload.password,
            role=payload.role,
            is_active=payload.is_active,
        )
    )

    return BaseResponse(data=created_account)


@account_router.get("", response_model=BaseResponse[List[AccountResponse]])
async def list_accounts(
    role: Annotated[RoleCode | None, Query()] = None,
    is_active: Annotated[bool | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    user: Annotated[AuthContextDto, Depends(RoleChecker(ACCOUNT_MANAGER_ROLES))] = None,
    usecase: Annotated[
        ListAccountsUseCase,
        Depends(get_list_accounts_usecase),
    ] = None,
):
    result = await usecase.execute(
        role=role,
        is_active=is_active,
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


@account_router.get("/{account_id}", response_model=BaseResponse[AccountResponse])
async def get_account(
    account_id: int,
    user: Annotated[AuthContextDto, Depends(RoleChecker(ACCOUNT_MANAGER_ROLES))] = None,
    usecase: Annotated[
        GetAccountUseCase,
        Depends(get_get_account_usecase),
    ] = None,
):
    account = await usecase.execute(account_id)

    return BaseResponse(data=account)


@account_router.patch(
    "/{account_id}/activate",
    response_model=BaseResponse[AccountResponse],
)
async def activate_account(
    account_id: int,
    user: Annotated[AuthContextDto, Depends(RoleChecker(ACCOUNT_MANAGER_ROLES))] = None,
    usecase: Annotated[
        ActivateAccountUseCase,
        Depends(get_activate_account_usecase),
    ] = None,
):
    account = await usecase.execute(account_id)

    return BaseResponse(data=account)


@account_router.patch(
    "/{account_id}/deactivate",
    response_model=BaseResponse[AccountResponse],
)
async def deactivate_account(
    account_id: int,
    user: Annotated[AuthContextDto, Depends(RoleChecker(ACCOUNT_MANAGER_ROLES))] = None,
    usecase: Annotated[
        DeactivateAccountUseCase,
        Depends(get_deactivate_account_usecase),
    ] = None,
):
    account = await usecase.execute(account_id)

    return BaseResponse(data=account)


@account_router.delete("/{account_id}", response_model=BaseResponse[None])
async def delete_account(
    account_id: int,
    user: Annotated[AuthContextDto, Depends(RoleChecker(ACCOUNT_MANAGER_ROLES))] = None,
    usecase: Annotated[
        DeleteAccountUseCase,
        Depends(get_delete_account_usecase),
    ] = None,
):
    await usecase.execute(account_id)

    return BaseResponse(data=None)


@auth_router.post("/login", response_model=BaseResponse[LoginResponse])
@limiter.limit("10/second")
async def login(
    request: Request,
    payload: LoginRequest,
    usecase: Annotated[
        LoginUseCase,
        Depends(get_login_usecase),
    ] = None,
):
    auth = await usecase.execute(payload.username, payload.password)

    return BaseResponse(data=auth)


@auth_router.get("/me", response_model=BaseResponse[CurrentUserResponse])
async def me(
    user: Annotated[AuthContextDto, Depends(get_current_user)],
):
    return BaseResponse(
        data=CurrentUserResponse(
            user_id=user.user_id,
            username=user.username,
            role=user.role,
        )
    )


@auth_router.post("/refresh", response_model=BaseResponse[TokenResponse])
@limiter.limit("10/second")
async def refresh_session(
    request: Request,
    payload: RefreshTokenRequest,
    usecase: Annotated[
        RefreshSessionUseCase,
        Depends(get_refresh_session_usecase),
    ] = None,
):
    token_pair = await usecase.execute(payload.refresh_token)

    return BaseResponse(data=token_pair)


@auth_router.post("/logout", response_model=BaseResponse[None])
@limiter.limit("10/second")
async def logout(
    request: Request,
    payload: RefreshTokenRequest,
    usecase: Annotated[
        LogoutUseCase,
        Depends(get_logout_usecase),
    ] = None,
):
    await usecase.execute(payload.refresh_token)

    return BaseResponse(data=None)
