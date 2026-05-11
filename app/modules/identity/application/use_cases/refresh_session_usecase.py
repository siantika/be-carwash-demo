from datetime import timedelta

from app.modules.identity.application.config.auth_config import AuthConfig
from app.modules.identity.application.constants import Consts
from app.modules.identity.application.dto.login_dto import TokenPairDto
from app.modules.identity.application.services.i_token_service import ITokenService
from app.modules.identity.domain.entities.refresh_token import RefreshToken
from app.modules.identity.domain.repositories.i_account_repo import IAccountRepository
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


class RefreshSessionUseCase:
    def __init__(
        self,
        account_repo: IAccountRepository,
        refresh_token_repo: IRefreshTokenRepository,
        token_service: ITokenService,
        auth_config: AuthConfig,
    ):
        self.account_repo = account_repo
        self.refresh_token_repo = refresh_token_repo
        self.token_service = token_service
        self.auth_config = auth_config

    async def execute(self, refresh_token: str) -> TokenPairDto:
        now = _utcnow()
        stored_token = await self.refresh_token_repo.find_active_by_hash(
            self.token_service.hash_refresh_token(refresh_token),
            now,
        )

        if stored_token is None:
            raise InvalidPasswordError("Invalid refresh token")

        account = await self.account_repo.find_by_id(stored_token.user_id)
        if account is None:
            raise EntityNotFound("Account not found")

        if not account.is_active:
            raise InactiveUserError("Account is inactive")

        if stored_token.id is None:
            raise BusinessRuleViolation("Stored refresh token must have an id")

        if account.id is None:
            raise BusinessRuleViolation("Refresh token user must have an id")

        await self.refresh_token_repo.revoke(stored_token.id, now)

        new_refresh_token = self.token_service.generate_refresh_token()
        await self.refresh_token_repo.save(
            RefreshToken(
                user_id=account.id,
                token_hash=self.token_service.hash_refresh_token(new_refresh_token),
                expires_at=now + timedelta(days=self.auth_config.refresh_token_expire_days),
            )
        )

        access_token = self.token_service.create_access_token(
            str(account.id),
            account.username,
            account.role,
            self.auth_config.access_token_expire_hours,
        )

        return TokenPairDto(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type=Consts.TOKEN_TYPE,
        )
