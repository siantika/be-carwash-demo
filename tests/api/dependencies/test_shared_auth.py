import pytest

from app.api.dependencies.shared import get_current_device, get_current_user
from app.modules.identity.domain.entities.device import Device
from app.modules.identity.domain.entities.account import Account, RoleCode
from app.modules.identity.domain.value_objects.email import Email
from app.modules.identity.domain.value_objects.username import Username
from app.modules.identity.infra.security import create_access_token
from app.shared.domain.exceptions.exceptions import (
    InactiveUserError,
    InvalidTokenError,
    PermissionDeniedError,
)


class FakeAccountRepository:
    def __init__(self, account: Account | None):
        self.account = account

    async def find_by_id(self, account_id: int) -> Account | None:
        if self.account is None:
            return None

        if self.account.id != account_id:
            return None

        return self.account


class FakeDeviceRepository:
    def __init__(self, device: Device | None):
        self.device = device
        self.touched_device_ids: list[int] = []

    async def find_by_code(self, device_code: str) -> Device | None:
        if self.device is None:
            return None
        if self.device.device_code != device_code:
            return None
        return self.device

    async def touch_last_seen(self, device_id: int) -> None:
        self.touched_device_ids.append(device_id)


def _account(is_active: bool = True) -> Account:
    return Account(
        id=1,
        username=Username("cashier_01"),
        email=Email("cashier@example.com"),
        role=RoleCode.CASHIER,
        password_hash="hash",
        is_active=is_active,
    )


def _device(is_active: bool = True) -> Device:
    return Device(
        id=1,
        device_code="PI-ENTRANCE-01",
        name="Entrance Pi",
        location="Gate A",
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

    with pytest.raises(InactiveUserError) as exc_info:
        await get_current_user(
            token=token,
            account_repo=FakeAccountRepository(_account(is_active=False)),
        )

    assert str(exc_info.value) == "Account is inactive"


@pytest.mark.anyio
async def test_get_current_user_rejects_missing_account() -> None:
    token = create_access_token("1", "cashier_01", RoleCode.CASHIER, 1)

    with pytest.raises(InvalidTokenError) as exc_info:
        await get_current_user(
            token=token,
            account_repo=FakeAccountRepository(None),
        )

    assert str(exc_info.value) == "Invalid token"


@pytest.mark.anyio
async def test_get_current_device_loads_active_device() -> None:
    repo = FakeDeviceRepository(_device())
    device = await get_current_device(
        device_code="PI-ENTRANCE-01",
        device_repo=repo,
    )
    assert device.device_code == "PI-ENTRANCE-01"
    assert repo.touched_device_ids == [1]


@pytest.mark.anyio
async def test_get_current_device_rejects_inactive_device() -> None:
    repo = FakeDeviceRepository(_device(is_active=False))
    with pytest.raises(PermissionDeniedError) as exc_info:
        await get_current_device(
            device_code="PI-ENTRANCE-01",
            device_repo=repo,
        )
    assert str(exc_info.value) == "Device is inactive"


@pytest.mark.anyio
async def test_get_current_device_rejects_unknown_device() -> None:
    repo = FakeDeviceRepository(None)
    with pytest.raises(PermissionDeniedError) as exc_info:
        await get_current_device(
            device_code="PI-ENTRANCE-01",
            device_repo=repo,
        )
    assert str(exc_info.value) == "Device is not registered"
