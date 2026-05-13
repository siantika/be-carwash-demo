from typing import List

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from pydantic import ValidationError

from app.modules.identity.application.dto.auth_context_dto import AuthContextDto
from app.modules.identity.infra.repositories.account_repo import (
    AsyncPgAccountRepository,
)
from app.modules.identity.infra.security import decode_token
from app.shared.domain.exceptions.exceptions import (
    InactiveUserError,
    InvalidTokenError,
    NotAuthenticatedError,
    PermissionDeniedError,
)
from app.shared.infra.database.db import get_db, get_db_pool
from app.shared.interfaces.i_logger import ILogger
from app.shared.middleware.logger import StructlogLogger, setup_logger


def get_logger() -> ILogger:
    return StructlogLogger("api")


def get_account_repo(db=Depends(get_db), logger=Depends(get_logger)):
    return AsyncPgAccountRepository(db, logger)

# should be same as login path
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    account_repo=Depends(get_account_repo),
) -> AuthContextDto:
    if token is None:
        raise NotAuthenticatedError("Not authenticated")

    try:
        payload = decode_token(token).model_dump() # convert from pydanctic object to dict
    except (JWTError, ValidationError):
        raise InvalidTokenError("Invalid token")

    user_id = payload.get("user_id")
    role = payload.get("role")
    
    if user_id is None or role is None:
        raise InvalidTokenError("Invalid token payload")

    account = await account_repo.find_by_id(user_id)
    if account is None:
        raise InvalidTokenError("Invalid token")

    if not account.is_active:
        raise InactiveUserError("Account is inactive")

    return AuthContextDto (
        account.id,
        account.username.value,
        account.role.value,
    )


def RoleChecker(required_roles: List[str]):
    async def verify(user: AuthContextDto = Depends(get_current_user)) -> AuthContextDto:
        allowed_roles = {
            role.value if hasattr(role, "value") else role
            for role in required_roles
        }
        if user.role not in allowed_roles:
            raise PermissionDeniedError("You don't have permission")
        return user

    return verify
