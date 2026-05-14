from logging import Logger
from typing import Annotated

from asyncpg import Pool
from fastapi import Depends

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
from app.modules.identity.application.config.auth_config import AuthConfig
from app.modules.identity.application.ports.i_account_query_repo import (
    IAccountQueryRepository,
)
from app.modules.identity.application.queries.account_query import (
    GetAccountUseCase,
    ListAccountsUseCase,
)
from app.modules.identity.domain.repositories.i_account_repo import IAccountRepository
from app.modules.identity.domain.repositories.i_refresh_token_repo import (
    IRefreshTokenRepository,
)
from app.modules.identity.infra.repositories.account_repo import (
    AsyncPgAccountRepository,
)
from app.modules.identity.infra.repositories.query.postgres_account_query_repository import (
    PostgresAccountQueryRepository,
)
from app.modules.identity.infra.repositories.refresh_token_repo import (
    AsyncPgRefreshTokenRepository,
)
from app.modules.identity.infra.security import PasswordHasher, TokenService
from app.shared.config.settings import settings
from app.shared.infra.database.db import get_db
from app.shared.interfaces.i_logger import ILogger
from app.shared.middleware.logger import StructlogLogger


def get_logger() -> ILogger:
    return StructlogLogger("identity")


def get_account_repo(
    db: Annotated[Pool, Depends(get_db)],
    logger: Annotated[ILogger, Depends(get_logger)],
) -> IAccountRepository:
    return AsyncPgAccountRepository(db, logger)


def get_account_query(
    db: Annotated[Pool, Depends(get_db)],
    logger: Annotated[ILogger, Depends(get_logger)],
) -> IAccountQueryRepository:
    return PostgresAccountQueryRepository(db, logger)


def get_refresh_token_repo(
    db: Annotated[Pool, Depends(get_db)],
    logger: Annotated[ILogger, Depends(get_logger)],
) -> IRefreshTokenRepository:
    return AsyncPgRefreshTokenRepository(db, logger)


def get_password_hasher() -> PasswordHasher:
    return PasswordHasher()


def get_token_service() -> TokenService:
    return TokenService()


def get_auth_config() -> AuthConfig:
    return AuthConfig(
        access_token_expire_hours=settings.ACCESS_TOKEN_EXPIRE_HOURS,
        refresh_token_expire_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )


def get_login_usecase(
    account_repo: Annotated[IAccountRepository, Depends(get_account_repo)],
    refresh_token_repo: Annotated[IRefreshTokenRepository, Depends(get_refresh_token_repo)],
    password_hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
    auth_config: Annotated[AuthConfig, Depends(get_auth_config)],
) -> LoginUseCase:
    return LoginUseCase(
        account_repo,
        refresh_token_repo,
        password_hasher,
        token_service,
        auth_config,
    )


def get_refresh_session_usecase(
    account_repo: Annotated[IAccountRepository, Depends(get_account_repo)],
    refresh_token_repo: Annotated[IRefreshTokenRepository, Depends(get_refresh_token_repo)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
    auth_config: Annotated[AuthConfig, Depends(get_auth_config)],
) -> RefreshSessionUseCase:
    return RefreshSessionUseCase(
        account_repo,
        refresh_token_repo,
        token_service,
        auth_config,
    )


def get_logout_usecase(
    refresh_token_repo: Annotated[IRefreshTokenRepository, Depends(get_refresh_token_repo)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> LogoutUseCase:
    return LogoutUseCase(refresh_token_repo, token_service)


def get_register_account_usecase(
    account_repo: Annotated[IAccountRepository, Depends(get_account_repo)],
    password_hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
) -> RegisterAccountUseCase:
    return RegisterAccountUseCase(account_repo, password_hasher)


def get_get_account_usecase(
    account_repo: Annotated[IAccountRepository, Depends(get_account_repo)],
) -> GetAccountUseCase:
    return GetAccountUseCase(account_repo)


def get_list_accounts_usecase(
    account_query: Annotated[IAccountQueryRepository, Depends(get_account_query)],
) -> ListAccountsUseCase:
    return ListAccountsUseCase(account_query)


def get_activate_account_usecase(
    account_repo: Annotated[IAccountRepository, Depends(get_account_repo)],
) -> ActivateAccountUseCase:
    return ActivateAccountUseCase(account_repo)


def get_deactivate_account_usecase(
    account_repo: Annotated[IAccountRepository, Depends(get_account_repo)],
) -> DeactivateAccountUseCase:
    return DeactivateAccountUseCase(account_repo)


def get_delete_account_usecase(
    account_repo: Annotated[IAccountRepository, Depends(get_account_repo)],
) -> DeleteAccountUseCase:
    return DeleteAccountUseCase(account_repo)