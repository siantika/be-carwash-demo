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
from app.modules.identity.application.dto.login_dto import TokenPairDto
from app.modules.identity.application.constants import Consts
from app.modules.identity.infra.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)
from app.shared.config.settings import settings
from domain.repositories.i_user_repo import IUserRepository


class RefreshSessionUseCase:
    def __init__(
        self,
        user_repo: IUserRepository,
        refresh_token_repo: IRefreshTokenRepository,
    ):
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo

    async def execute(self, refresh_token: str) -> TokenPairDto:
        now = _utcnow()
        stored_token = await self.refresh_token_repo.find_active_by_hash(
            hash_refresh_token(refresh_token),
            now,
        )

        if stored_token is None:
            raise InvalidPasswordError("Invalid refresh token")

        user = await self.user_repo.get_by_id(stored_token.user_id)
        if user is None:
            raise EntityNotFound("User not found")

        if not user.is_active:
            raise InactiveUserError("User is inactive")

        if stored_token.id is None:
            raise BusinessRuleViolation("Stored refresh token must have an id")

        if user.id is None:
            raise BusinessRuleViolation("Refresh token user must have an id")

        await self.refresh_token_repo.revoke(stored_token.id, now)

        new_refresh_token = generate_refresh_token()
        await self.refresh_token_repo.save(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_refresh_token(new_refresh_token),
                expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            )
        )

        access_token = create_access_token(
            str(user.id),
            user.username,
            user.role,
        )

        return TokenPairDto(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type=Consts.TOKEN_TYPE,
        )
