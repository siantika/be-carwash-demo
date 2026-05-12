from datetime import timedelta

import pytest

from app.modules.identity.application.config.auth_config import AuthConfig
from app.modules.identity.domain.entities.refresh_token import RefreshToken
from app.modules.identity.domain.entities.account import Account, RoleCode
from app.modules.identity.domain.value_objects.email import Email
from app.modules.identity.domain.value_objects.username import Username
from app.shared.domain.entities.base import _utcnow
from app.modules.identity.application.use_cases.logout_usecase import LogoutUseCase
from app.modules.identity.application.use_cases.refresh_session_usecase import (
    RefreshSessionUseCase,
)
from app.modules.identity.infra.security import TokenService, hash_refresh_token
from app.shared.domain.exceptions.exceptions import InvalidTokenError


class FakeAccountRepository:
    def __init__(self, account: Account | None):
        self.account = account

    async def find_by_id(self, account_id: int) -> Account | None:
        return self.account if self.account and self.account.id == account_id else None


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

    async def revoke(self, refresh_token_id: int, revoked_at) -> int:
        self.revoked_ids.append(refresh_token_id)
        return refresh_token_id

    async def mark_used(self, refresh_token_id: int, used_at) -> int:
        return refresh_token_id


@pytest.mark.anyio
async def test_refresh_session_rotates_refresh_token() -> None:
    raw_refresh_token = "refresh-token"
    now = _utcnow()
    stored_token = RefreshToken(
        id=1,
        account_id=1,
        token_hash=hash_refresh_token(raw_refresh_token),
        expires_at=now + timedelta(days=1),
    )
    account = Account(
        id=1,
        username=Username("cashier"),
        email=Email("cashier@example.com"),
        role=RoleCode.CASHIER,
        password_hash="hash",
    )
    refresh_token_repo = FakeRefreshTokenRepository(stored_token)
    usecase = RefreshSessionUseCase(
        account_repo=FakeAccountRepository(account),
        refresh_token_repo=refresh_token_repo,
        token_service=TokenService(),
        auth_config=AuthConfig(
            access_token_expire_hours=1,
            refresh_token_expire_days=7,
        ),
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
        account_id=1,
        token_hash=hash_refresh_token(raw_refresh_token),
        expires_at=now + timedelta(days=1),
    )
    refresh_token_repo = FakeRefreshTokenRepository(stored_token)
    usecase = LogoutUseCase(refresh_token_repo, TokenService())

    await usecase.execute(raw_refresh_token)

    assert refresh_token_repo.revoked_ids == [1]


@pytest.mark.anyio
async def test_logout_rejects_invalid_refresh_token() -> None:
    refresh_token_repo = FakeRefreshTokenRepository(None)
    usecase = LogoutUseCase(refresh_token_repo, TokenService())

    with pytest.raises(InvalidTokenError, match="Invalid refresh token"):
        await usecase.execute("wrong-refresh-token")

    assert refresh_token_repo.revoked_ids == []


@pytest.mark.anyio
async def test_refresh_session_rejects_invalid_refresh_token() -> None:
    refresh_token_repo = FakeRefreshTokenRepository(None)
    usecase = RefreshSessionUseCase(
        account_repo=FakeAccountRepository(None),
        refresh_token_repo=refresh_token_repo,
        token_service=TokenService(),
        auth_config=AuthConfig(
            access_token_expire_hours=1,
            refresh_token_expire_days=7,
        ),
    )

    with pytest.raises(InvalidTokenError, match="Invalid refresh token"):
        await usecase.execute("wrong-refresh-token")
