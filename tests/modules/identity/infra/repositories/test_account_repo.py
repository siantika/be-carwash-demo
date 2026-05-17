from datetime import datetime, timedelta, timezone

from app.modules.identity.infra.repositories.account_repo import _mapper


def test_account_mapper_loads_login_lockout_fields() -> None:
    now = datetime.now(timezone.utc)
    locked_until = now + timedelta(minutes=15)

    account = _mapper(
        {
            "id": 1,
            "username": "cashier_01",
            "email": "cashier@example.com",
            "role": "CASHIER",
            "password_hash": "hash",
            "is_active": True,
            "failed_login_attempts": 3,
            "locked_until": locked_until,
            "last_login_at": now,
            "created_at": now,
            "updated_at": now,
        }
    )

    assert account.failed_login_attempts == 3
    assert account.locked_until == locked_until
    assert account.last_login_at == now
