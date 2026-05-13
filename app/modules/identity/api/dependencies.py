from fastapi import Depends

from app.modules.identity.application.config.auth_config import AuthConfig
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
from app.modules.identity.infra.repositories.account_repo import (
    AsyncPgAccountRepository,
)
from app.modules.identity.infra.repositories.refresh_token_repo import (
    AsyncPgRefreshTokenRepository,
)
from app.modules.identity.infra.security import PasswordHasher, TokenService
from app.shared.config.settings import settings
from app.shared.infra.database.db import get_db
from app.shared.middleware.logger import StructlogLogger
from interfaces.i_logger import ILogger


def get_logger() -> ILogger:
    return StructlogLogger("identity")


def get_account_repo(db=Depends(get_db), logger=Depends(get_logger)):
    return AsyncPgAccountRepository(db, logger)


def get_refresh_token_repo(db=Depends(get_db), logger=Depends(get_logger)):
    return AsyncPgRefreshTokenRepository(db, logger)


def get_password_hasher():
    return PasswordHasher()


def get_token_service():
    return TokenService()


def get_auth_config():
    return AuthConfig(
        access_token_expire_hours=settings.ACCESS_TOKEN_EXPIRE_HOURS,
        refresh_token_expire_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )


def get_login_usecase(
    account_repo=Depends(get_account_repo),
    refresh_token_repo=Depends(get_refresh_token_repo),
    password_hasher=Depends(get_password_hasher),
    token_service=Depends(get_token_service),
    auth_config=Depends(get_auth_config),
):
    return LoginUseCase(
        account_repo,
        refresh_token_repo,
        password_hasher,
        token_service,
        auth_config,
    )


def get_refresh_session_usecase(
    account_repo=Depends(get_account_repo),
    refresh_token_repo=Depends(get_refresh_token_repo),
    token_service=Depends(get_token_service),
    auth_config=Depends(get_auth_config),
):
    return RefreshSessionUseCase(
        account_repo,
        refresh_token_repo,
        token_service,
        auth_config,
    )


def get_logout_usecase(
    refresh_token_repo=Depends(get_refresh_token_repo),
    token_service=Depends(get_token_service),
):
    return LogoutUseCase(refresh_token_repo, token_service)


def get_register_account_usecase(
    account_repo=Depends(get_account_repo),
    password_hasher=Depends(get_password_hasher),
):
    return RegisterAccountUseCase(account_repo, password_hasher)


def get_get_account_usecase(account_repo=Depends(get_account_repo)):
    return GetAccountUseCase(account_repo)


def get_list_accounts_usecase(account_repo=Depends(get_account_repo)):
    return ListAccountsUseCase(account_repo)


def get_activate_account_usecase(account_repo=Depends(get_account_repo)):
    return ActivateAccountUseCase(account_repo)


def get_deactivate_account_usecase(account_repo=Depends(get_account_repo)):
    return DeactivateAccountUseCase(account_repo)


def get_delete_account_usecase(account_repo=Depends(get_account_repo)):
    return DeleteAccountUseCase(account_repo)
