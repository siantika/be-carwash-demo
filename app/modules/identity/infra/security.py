import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import jwt
from passlib.context import CryptContext

from app.modules.identity.application.dto.token_data import TokenData
from app.modules.identity.domain.entities.account import RoleCode
from app.modules.identity.domain.value_objects.username import Username
from app.shared.config.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, username: str, role: str, expires:int) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=expires)

    payload: Dict[str, Any] = {
        "sub": user_id,
        "username": username,
        "role": role.value if hasattr(role, "value") else role,
        "exp": expire, 
    }

    encoded_jwt = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def decode_token(token: str) -> TokenData:
    """Raise JWTError if token is invalid/expired"""
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    return TokenData(**payload)


class PasswordHasher:
    def hash(self, plain_password: str) -> str:
        return hash_password(plain_password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return verify_password(plain_password, hashed_password)


class TokenService:
    def create_access_token(
        self,
        account_id: str,
        username: Username,
        role: RoleCode,
        expires: int,
    ) -> str:
        return create_access_token(account_id, username.value, role, expires)

    def generate_refresh_token(self) -> str:
        return generate_refresh_token()

    def hash_refresh_token(self, token: str) -> str:
        return hash_refresh_token(token)
