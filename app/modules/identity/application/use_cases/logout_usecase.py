from app.modules.identity.domain.repositories.i_refresh_token_repo import (
    IRefreshTokenRepository,
)
from app.shared.domain.entities.base import _utcnow
from app.shared.domain.exceptions.exceptions import BusinessRuleViolation
from core.security import hash_refresh_token


class LogoutUseCase:
    def __init__(self, refresh_token_repo: IRefreshTokenRepository):
        self.refresh_token_repo = refresh_token_repo

    async def execute(self, refresh_token: str) -> None:
        now = _utcnow()
        stored_token = await self.refresh_token_repo.find_active_by_hash(
            hash_refresh_token(refresh_token),
            now,
        )

        if stored_token is None:
            return

        if stored_token.id is None:
            raise BusinessRuleViolation("Stored refresh token must have an id")

        await self.refresh_token_repo.revoke(stored_token.id, now)
