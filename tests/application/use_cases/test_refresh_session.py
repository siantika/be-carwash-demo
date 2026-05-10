from datetime import timedelta

import pytest

from app.modules.identity.domain.entities.refresh_token import RefreshToken
from app.modules.identity.domain.entities.user import User, UserRoleEnum
from app.shared.domain.entities.base import _utcnow
from app.modules.identity.application.use_cases.logout_usecase import LogoutUseCase
from app.modules.identity.application.use_cases.refresh_session_usecase import (
    RefreshSessionUseCase,
)
from app.modules.identity.infra.security import hash_refresh_token


class FakeUserRepository:
    def __init__(self, user: User | None):
        self.user = user

    async def get_by_id(self, user_id: int) -> User | None:
        return self.user if self.user and self.user.id == user_id else None


class FakeRefreshTokenRepository:
    def __init__(self, refresh_token: RefreshToken | None):
        self.refresh_token = refresh_token
        self.saved: list[RefreshToken] = []
        self.revoked_ids: list[int] = []

    async def find_active_by_hash(
        self,
        token_hash: str,
        now,
    ) -> RefreshToken | None:
        if self.refresh_token is None:
            return None

        if self.refresh_token.token_hash != token_hash:
            return None

        if not self.refresh_token.is_active(now):
            return None

        return self.refresh_token

    async def save(self, refresh_token: RefreshToken) -> RefreshToken:
        refresh_token.id = 2
        self.saved.append(refresh_token)
        return refresh_token

    async def revoke(self, refresh_token_id: int, revoked_at) -> None:
        self.revoked_ids.append(refresh_token_id)

    async def mark_used(self, refresh_token_id: int, used_at) -> None:
        pass


@pytest.mark.anyio
async def test_refresh_session_rotates_refresh_token() -> None:
    raw_refresh_token = "refresh-token"
    now = _utcnow()
    stored_token = RefreshToken(
        id=1,
        user_id=1,
        token_hash=hash_refresh_token(raw_refresh_token),
        expires_at=now + timedelta(days=1),
    )
    user = User(
        id=1,
        username="cashier",
        role=UserRoleEnum.CASHIER,
        password_hash="hash",
    )
    refresh_token_repo = FakeRefreshTokenRepository(stored_token)
    usecase = RefreshSessionUseCase(
        user_repo=FakeUserRepository(user),
        refresh_token_repo=refresh_token_repo,
    )

    result = await usecase.execute(raw_refresh_token)

    assert result.access_token
    assert result.refresh_token != raw_refresh_token
    assert refresh_token_repo.revoked_ids == [1]
    assert len(refresh_token_repo.saved) == 1


@pytest.mark.anyio
async def test_logout_revokes_active_refresh_token() -> None:
    raw_refresh_token = "refresh-token"
    now = _utcnow()
    stored_token = RefreshToken(
        id=1,
        user_id=1,
        token_hash=hash_refresh_token(raw_refresh_token),
        expires_at=now + timedelta(days=1),
    )
    refresh_token_repo = FakeRefreshTokenRepository(stored_token)
    usecase = LogoutUseCase(refresh_token_repo)

    await usecase.execute(raw_refresh_token)

    assert refresh_token_repo.revoked_ids == [1]
