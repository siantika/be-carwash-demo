from datetime import datetime, timezone

import pytest

from app.modules.identity.domain.entities.account import Account, RoleCode
from app.modules.identity.domain.value_objects.email import Email
from app.modules.identity.domain.value_objects.username import Username
from app.shared.domain.exceptions.exceptions import BusinessRuleViolation


def test_account_accepts_username_value_object() -> None:
    account = Account(
        username=Username("cashier_01"),
        email=Email("cashier@example.com"),
        password_hash="hashed-password",
        role=RoleCode.CASHIER,
    )

    assert account.username.value == "cashier_01"
    assert account.email.value == "cashier@example.com"
    assert account.can_login(datetime.now(timezone.utc))


def test_account_rejects_negative_failed_login_attempts() -> None:
    with pytest.raises(BusinessRuleViolation):
        Account(
            username=Username("cashier_01"),
            email=Email("cashier@example.com"),
            password_hash="hashed-password",
            role=RoleCode.CASHIER,
            failed_login_attempts=-1,
        )


def test_account_locks_after_max_failed_login_attempts() -> None:
    now = datetime.now(timezone.utc)
    account = Account(
        username=Username("cashier_01"),
        email=Email("cashier@example.com"),
        password_hash="hashed-password",
        role=RoleCode.CASHIER,
    )

    account.record_failed_login(now)
    account.record_failed_login(now)
    account.record_failed_login(now)

    assert account.locked_until is not None
    assert not account.can_login(now)


def test_account_rejects_naive_login_timestamp() -> None:
    account = Account(
        username=Username("cashier_01"),
        email=Email("cashier@example.com"),
        password_hash="hashed-password",
        role=RoleCode.CASHIER,
    )

    with pytest.raises(BusinessRuleViolation):
        account.record_successful_login(datetime.now())
