from typing import List

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.dependencies.shared import RoleChecker
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
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RegisterAccountRequest,
    TokenResponse,
)
from app.modules.identity.application.dto.account_dto import RegisterAccountCmd
from app.modules.identity.application.use_cases.account_usecase import (
    ActivateAccountUseCase,
    DeactivateAccountUseCase,
    DeleteAccountUseCase,
    GetAccountUseCase,
    ListAccountsUseCase,
    RegisterAccountUseCase,
)
from app.modules.identity.application.use_cases.login_usecase import LoginUseCase
from app.modules.identity.application.use_cases.logout_usecase import LogoutUseCase
from app.modules.identity.application.use_cases.refresh_session_usecase import (
    RefreshSessionUseCase,
)
from app.modules.identity.domain.entities.account import RoleCode
from app.shared.middleware.limiter import limiter
from app.shared.response import BaseResponse

router = APIRouter()

ACCOUNT_MANAGER_ROLES = [RoleCode.ADMIN, RoleCode.OWNER]


@router.post(
    "/accounts",
    response_model=BaseResponse[AccountResponse],
    status_code=status.HTTP_201_CREATED,
)
async def register_account(
    payload: RegisterAccountRequest,
    user=Depends(RoleChecker(ACCOUNT_MANAGER_ROLES)),
    usecase: RegisterAccountUseCase = Depends(get_register_account_usecase),
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


@router.get("/accounts", response_model=BaseResponse[List[AccountResponse]])
async def list_accounts(
    role: RoleCode | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    user=Depends(RoleChecker(ACCOUNT_MANAGER_ROLES)),
    usecase: ListAccountsUseCase = Depends(get_list_accounts_usecase),
):
    accounts = await usecase.execute(role=role, is_active=is_active)
    return BaseResponse(data=accounts)


@router.get("/accounts/{account_id}", response_model=BaseResponse[AccountResponse])
async def get_account(
    account_id: int,
    user=Depends(RoleChecker(ACCOUNT_MANAGER_ROLES)),
    usecase: GetAccountUseCase = Depends(get_get_account_usecase),
):
    account = await usecase.execute(account_id)
    return BaseResponse(data=account)


@router.patch(
    "/accounts/{account_id}/activate",
    response_model=BaseResponse[AccountResponse],
)
async def activate_account(
    account_id: int,
    user=Depends(RoleChecker(ACCOUNT_MANAGER_ROLES)),
    usecase: ActivateAccountUseCase = Depends(get_activate_account_usecase),
):
    account = await usecase.execute(account_id)
    return BaseResponse(data=account)


@router.patch(
    "/accounts/{account_id}/deactivate",
    response_model=BaseResponse[AccountResponse],
)
async def deactivate_account(
    account_id: int,
    user=Depends(RoleChecker(ACCOUNT_MANAGER_ROLES)),
    usecase: DeactivateAccountUseCase = Depends(get_deactivate_account_usecase),
):
    account = await usecase.execute(account_id)
    return BaseResponse(data=account)


@router.delete("/accounts/{account_id}", response_model=BaseResponse[None])
async def delete_account(
    account_id: int,
    user=Depends(RoleChecker(ACCOUNT_MANAGER_ROLES)),
    usecase: DeleteAccountUseCase = Depends(get_delete_account_usecase),
):
    await usecase.execute(account_id)
    return BaseResponse(data=None)


@router.post("/login", response_model=BaseResponse[LoginResponse])
@limiter.limit("10/second")
async def login(
    request: Request,
    payload: LoginRequest,
    usecase: LoginUseCase = Depends(get_login_usecase),
):

    auth = await usecase.execute(payload.username, payload.password)
    
    return BaseResponse(
        data=auth
    )


@router.post("/refresh", response_model=BaseResponse[TokenResponse])
@limiter.limit("10/second")
async def refresh_session(
    request: Request,
    payload: RefreshTokenRequest,
    usecase: RefreshSessionUseCase = Depends(get_refresh_session_usecase),
):
    token_pair = await usecase.execute(payload.refresh_token)

    return BaseResponse(
        data=token_pair
    )


@router.post("/logout", response_model=BaseResponse[None])
@limiter.limit("10/second")
async def logout(
    request: Request,
    payload: RefreshTokenRequest,
    usecase: LogoutUseCase = Depends(get_logout_usecase),
):
    await usecase.execute(payload.refresh_token)

    return BaseResponse(
        data=None
    )
