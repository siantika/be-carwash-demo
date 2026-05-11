from app.modules.identity.domain.repositories.i_refresh_token_repo import (
    IRefreshTokenRepository,
)
from app.modules.identity.application.services.i_token_service import ITokenService
from app.shared.domain.entities.base import _utcnow
from app.shared.domain.exceptions.exceptions import BusinessRuleViolation


class LogoutUseCase:
    def __init__(
        self,
        refresh_token_repo: IRefreshTokenRepository,
        token_service: ITokenService,
    ):
        self.refresh_token_repo = refresh_token_repo
        self.token_service = token_service

    async def execute(self, refresh_token: str) -> None:
        now = _utcnow()
        stored_token = await self.refresh_token_repo.find_active_by_hash(
            self.token_service.hash_refresh_token(refresh_token),
            now,
        )

        if stored_token is None:
            return

        if stored_token.id is None:
            raise BusinessRuleViolation("Stored refresh token must have an id")

        revoked_token_id = await self.refresh_token_repo.revoke(stored_token.id, now)
        if revoked_token_id != stored_token.id:
            raise BusinessRuleViolation("Revoked refresh token id mismatch")
