from typing import Any, Dict, List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from application.dto.auth_context_dto import AuthContextDto
from application.dto.user_dto import UserResultDto
from application.i_unit_of_work import IUnitOfWork
from app.modules.identity.infra.security import decode_token
from app.shared.middleware.logger import StructlogLogger, setup_logger
from infra.db import get_db_pool
from infra.unit_of_work import AsyncpgUnitOfWork
from interfaces.i_logger import ILogger


async def get_uow(pool = Depends(get_db_pool), logger = Depends(setup_logger)) -> IUnitOfWork:
    return AsyncpgUnitOfWork(pool, logger)

# should be same as login path
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> AuthContextDto:
    try:
        payload = decode_token(token).model_dump() # convert from pydanctic object to dict
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user_id = payload.get("user_id")
    username = payload.get("username")
    role = payload.get("role")
    
    if user_id is None or role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return AuthContextDto (
        user_id,
        username,
        role,
    )


def RoleChecker(required_roles: List[str]):
    async def verify(user: UserResultDto = Depends(get_current_user)) -> UserResultDto:
        if user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission",
            )
        return user

    return verify


# dependencies for logger 

def get_logger() -> ILogger:
    return StructlogLogger("api")
