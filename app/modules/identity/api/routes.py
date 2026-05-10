from fastapi import APIRouter, Depends, Request

from app.modules.identity.api.dependencies import (
    get_login_usecase,
    get_logout_usecase,
    get_refresh_session_usecase,
)
from app.modules.identity.api.schemas import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    TokenResponse,
)
from app.modules.identity.application.use_cases.login_usecase import LoginUseCase
from app.modules.identity.application.use_cases.logout_usecase import LogoutUseCase
from app.modules.identity.application.use_cases.refresh_session_usecase import (
    RefreshSessionUseCase,
)
from core.middleware.limiter import limiter
from infra.repositories.response import BaseResponse

router = APIRouter()


@router.post("/login", response_model=BaseResponse[LoginResponse])
@limiter.limit("10/second")
async def login(
    request: Request,
    payload: LoginRequest,
    usecase: LoginUseCase = Depends(get_login_usecase),
):

    auth = await usecase.execute(payload.username, payload.password)
    
    return BaseResponse(
        status="success",
        message="login success",
        data=auth,
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
        status="success",
        message="session refreshed",
        data=token_pair,
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
        status="success",
        message="logout success",
        data=None,
    )
