import pytest
from fastapi import HTTPException, status

from app.api.dependencies.shared import get_current_user
from app.modules.identity.domain.entities.account import Account, RoleCode
from app.modules.identity.domain.value_objects.email import Email
from app.modules.identity.domain.value_objects.username import Username
from app.modules.identity.infra.security import create_access_token


class FakeAccountRepository:
    def __init__(self, account: Account | None):
        self.account = account

    async def find_by_id(self, account_id: int) -> Account | None:
        if self.account is None:
            return None

        if self.account.id != account_id:
            return None

        return self.account


def _account(is_active: bool = True) -> Account:
    return Account(
        id=1,
        username=Username("cashier_01"),
        email=Email("cashier@example.com"),
        role=RoleCode.CASHIER,
        password_hash="hash",
        is_active=is_active,
    )


@pytest.mark.anyio
async def test_get_current_user_loads_active_account_from_database() -> None:
    token = create_access_token("1", "stale_username", RoleCode.ADMIN, 1)

    user = await get_current_user(
        token=token,
        account_repo=FakeAccountRepository(_account()),
    )

    assert user.user_id == 1
    assert user.username == "cashier_01"
    assert user.role == "CASHIER"


@pytest.mark.anyio
async def test_get_current_user_rejects_inactive_account() -> None:
    token = create_access_token("1", "cashier_01", RoleCode.CASHIER, 1)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            token=token,
            account_repo=FakeAccountRepository(_account(is_active=False)),
        )

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "Account is inactive"


@pytest.mark.anyio
async def test_get_current_user_rejects_missing_account() -> None:
    token = create_access_token("1", "cashier_01", RoleCode.CASHIER, 1)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            token=token,
            account_repo=FakeAccountRepository(None),
        )

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Invalid token"
