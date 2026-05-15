from typing import Annotated

from app.modules.identity.application.dto.auth_context_dto import AuthContextDto
from app.modules.identity.domain.entities.device import Device
from app.modules.identity.infra.repositories.account_repo import (
    AsyncPgAccountRepository,
)
from app.modules.identity.infra.repositories.device_repo import AsyncPgDeviceRepository
from app.modules.identity.infra.security import decode_token
from app.shared.domain.exceptions.exceptions import (
    InactiveUserError,
    InvalidTokenError,
    NotAuthenticatedError,
    PermissionDeniedError,
)
from app.shared.infra.database.db import get_db
from app.shared.interfaces.i_logger import ILogger
from app.shared.middleware.logger import StructlogLogger
from asyncpg import Pool
from fastapi import Depends, Header
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from pydantic import ValidationError

_logger = StructlogLogger("api")


def get_logger() -> ILogger:
    return _logger


def get_account_repo(
    db: Annotated[Pool, Depends(get_db)],
    logger: Annotated[ILogger, Depends(get_logger)],
) -> AsyncPgAccountRepository:
    return AsyncPgAccountRepository(db, logger)


def get_device_repo(
    db: Annotated[Pool, Depends(get_db)],
    logger: Annotated[ILogger, Depends(get_logger)],
) -> AsyncPgDeviceRepository:
    return AsyncPgDeviceRepository(db, logger)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)


async def get_required_token(
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> str:
    if token is None:
        raise NotAuthenticatedError("Not authenticated")

    return token


async def get_current_user(
    token: Annotated[str, Depends(get_required_token)],
    account_repo: Annotated[
        AsyncPgAccountRepository,
        Depends(get_account_repo),
    ],
) -> AuthContextDto:
    try:
        payload = decode_token(token)
    except (JWTError, ValidationError):
        raise InvalidTokenError("Invalid token")

    user_id = payload.user_id
    role = payload.role

    if user_id is None or role is None:
        raise InvalidTokenError("Invalid token payload")

    account = await account_repo.find_by_id(user_id)
    if account is None:
        raise InvalidTokenError("Invalid token")

    if not account.is_active:
        raise InactiveUserError("Account is inactive")

    return AuthContextDto(
        account.id,
        account.username.value,
        account.role.value,
    )


def RoleChecker(required_roles: list[str]):
    async def verify(
        user: Annotated[AuthContextDto, Depends(get_current_user)],
    ) -> AuthContextDto:
        allowed_roles = set(required_roles)

        if user.role not in allowed_roles:
            raise PermissionDeniedError("You don't have permission")

        return user

    return verify


async def get_current_device(
    device_repo: Annotated[
        AsyncPgDeviceRepository,
        Depends(get_device_repo),
    ],
    device_code:str = Header(default=None, alias="X-Device-Code"),
) -> Device:
    if device_code is None or device_code.strip() == "":
        raise PermissionDeniedError("Device code is required")

    device = await device_repo.find_by_code(device_code.strip())

    if device is None:
        raise PermissionDeniedError("Device is not registered")

    if not device.is_active:
        raise PermissionDeniedError("Device is inactive")

    await device_repo.touch_last_seen(device.id)

    return device