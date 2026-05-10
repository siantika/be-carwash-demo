from fastapi import Depends

from api.dependencies.shared import get_logger
from app.modules.identity.infra.repositories.refresh_token_repo import (
    AsyncPgRefreshTokenRepository,
)
from app.modules.identity.application.use_cases.login_usecase import LoginUseCase
from app.modules.identity.application.use_cases.logout_usecase import LogoutUseCase
from app.modules.identity.application.use_cases.refresh_session_usecase import (
    RefreshSessionUseCase,
)
from infra.db import get_db
from infra.repositories.user_repo import AsyncPgUserRepository


def get_user_repo(db=Depends(get_db), logger=Depends(get_logger)):
    return AsyncPgUserRepository(db, logger)


def get_refresh_token_repo(db=Depends(get_db), logger=Depends(get_logger)):
    return AsyncPgRefreshTokenRepository(db, logger)


def get_login_usecase(
    user_repo=Depends(get_user_repo),
    refresh_token_repo=Depends(get_refresh_token_repo),
):
    return LoginUseCase(user_repo, refresh_token_repo)


def get_refresh_session_usecase(
    user_repo=Depends(get_user_repo),
    refresh_token_repo=Depends(get_refresh_token_repo),
):
    return RefreshSessionUseCase(user_repo, refresh_token_repo)


def get_logout_usecase(refresh_token_repo=Depends(get_refresh_token_repo)):
    return LogoutUseCase(refresh_token_repo)
