from datetime import datetime
from typing import Protocol

from app.modules.identity.domain.entities.refresh_token import RefreshToken


class IRefreshTokenRepository(Protocol):
    async def save(self, refresh_token: RefreshToken) -> RefreshToken: ...

    async def find_active_by_hash(
        self,
        token_hash: str,
        now: datetime,
    ) -> RefreshToken | None: ...

    async def revoke(self, refresh_token_id: int, revoked_at: datetime) -> None: ...

    async def mark_used(self, refresh_token_id: int, used_at: datetime) -> None: ...
