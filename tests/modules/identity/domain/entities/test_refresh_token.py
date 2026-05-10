from datetime import timedelta

from app.modules.identity.domain.entities.refresh_token import RefreshToken
from app.shared.domain.entities.base import _utcnow


def test_refresh_token_is_active_before_expiry() -> None:
    now = _utcnow()
    refresh_token = RefreshToken(
        user_id=1,
        token_hash="hash",
        expires_at=now + timedelta(days=1),
    )

    assert refresh_token.is_active(now)


def test_refresh_token_is_inactive_after_revoke() -> None:
    now = _utcnow()
    refresh_token = RefreshToken(
        user_id=1,
        token_hash="hash",
        expires_at=now + timedelta(days=1),
    )

    refresh_token.revoke(now)

    assert not refresh_token.is_active(now)
