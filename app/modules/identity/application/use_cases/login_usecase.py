"""
Authentication login use case.

Handles user authentication and token generation.
"""
from datetime import timedelta

from app.modules.identity.domain.entities.refresh_token import RefreshToken
from app.modules.identity.domain.repositories.i_refresh_token_repo import (
    IRefreshTokenRepository,
)
from app.shared.domain.entities.base import _utcnow
from app.shared.domain.exceptions.exceptions import (
    BusinessRuleViolation,
    EntityNotFound,
    InactiveUserError,
    InvalidPasswordError,
)
from app.modules.identity.application.dto.login_dto import LoginResultDto
from app.modules.identity.application.constants import Consts
from app.modules.identity.infra.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    verify_password,
)
from app.shared.config.settings import settings
from domain.repositories.i_user_repo import IUserRepository


class LoginUseCase: 
    """Use case for authenticating a user and issuing an access token."""

    def __init__(
        self,
        user_repo: IUserRepository,
        refresh_token_repo: IRefreshTokenRepository,
    ):
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo

    async def execute(self, username: str, password: str) -> LoginResultDto:

        user = await self.user_repo.get_by_username(username)

        if user is None:
            raise EntityNotFound("Invalid username")

        if not verify_password(password, user.password_hash):
            raise InvalidPasswordError("Invalid password")

        if not user.is_active:
            raise InactiveUserError("User is inactive")

        if user.id is None:
            raise BusinessRuleViolation("Authenticated user must have an id")

        token = create_access_token(
            str(user.id),
            user.username,
            user.role,
        )
        refresh_token = generate_refresh_token()
        now = _utcnow()

        await self.refresh_token_repo.save(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_refresh_token(refresh_token),
                expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            )
        )

        return LoginResultDto(
            access_token=token,
            refresh_token=refresh_token,
            token_type=Consts.TOKEN_TYPE,
        )
