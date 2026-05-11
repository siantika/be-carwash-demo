import pytest

from app.modules.identity.application.dto.account_dto import RegisterAccountCmd
from app.modules.identity.application.use_cases.account_usecase import (
    ActivateAccountUseCase,
    DeleteAccountUseCase,
    ListAccountsUseCase,
    RegisterAccountUseCase,
)
from app.modules.identity.domain.entities.account import Account, RoleCode
from app.modules.identity.domain.value_objects.email import Email
from app.modules.identity.domain.value_objects.username import Username
from app.shared.domain.exceptions.exceptions import EntityAlreadyExists


class FakeAccountRepository:
    def __init__(self):
        self.accounts: dict[int, Account] = {}
        self.next_id = 1
        self.deleted_ids: list[int] = []

    async def find_by_id(self, account_id: int) -> Account | None:
        return self.accounts.get(account_id)

    async def find_by_username(self, username: Username) -> Account | None:
        return next(
            (
                account
                for account in self.accounts.values()
                if account.username == username
            ),
            None,
        )

    async def find_all(self) -> list[Account]:
        return list(self.accounts.values())

    async def find_all_by_role(self, role: RoleCode) -> list[Account]:
        return [
            account for account in self.accounts.values()
            if account.role == role
        ]

    async def find_all_by_status(self, is_active: bool) -> list[Account]:
        return [
            account for account in self.accounts.values()
            if account.is_active is is_active
        ]

    async def create(self, account: Account) -> Account:
        account.id = self.next_id
        self.next_id += 1
        self.accounts[account.id] = account
        return account

    async def save(self, account: Account) -> Account:
        self.accounts[account.id] = account
        return account

    async def delete(self, account_id: int) -> None:
        self.deleted_ids.append(account_id)
        self.accounts.pop(account_id, None)


class FakePasswordHasher:
    def hash(self, plain_password: str) -> str:
        return f"hashed:{plain_password}"

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return hashed_password == self.hash(plain_password)


@pytest.mark.anyio
async def test_register_account_hashes_password_and_saves_account() -> None:
    repo = FakeAccountRepository()
    usecase = RegisterAccountUseCase(repo, FakePasswordHasher())

    result = await usecase.execute(
        RegisterAccountCmd(
            username="Cashier_01",
            email="cashier@example.com",
            password="Password1",
            role=RoleCode.CASHIER,
        )
    )

    stored_account = repo.accounts[result.id]
    assert result.username == "cashier_01"
    assert result.email == "cashier@example.com"
    assert result.role == "CASHIER"
    assert stored_account.password_hash == "hashed:Password1"


@pytest.mark.anyio
async def test_register_account_rejects_duplicate_username() -> None:
    repo = FakeAccountRepository()
    usecase = RegisterAccountUseCase(repo, FakePasswordHasher())
    cmd = RegisterAccountCmd(
        username="cashier_01",
        email="cashier@example.com",
        password="Password1",
        role="CASHIER",
    )

    await usecase.execute(cmd)

    with pytest.raises(EntityAlreadyExists):
        await usecase.execute(cmd)


@pytest.mark.anyio
async def test_list_accounts_can_filter_by_role() -> None:
    repo = FakeAccountRepository()
    await repo.create(
        Account(
            username=Username("admin_01"),
            email=Email("admin@example.com"),
            password_hash="hash",
            role=RoleCode.ADMIN,
        )
    )
    await repo.create(
        Account(
            username=Username("cashier_01"),
            email=Email("cashier@example.com"),
            password_hash="hash",
            role=RoleCode.CASHIER,
        )
    )

    results = await ListAccountsUseCase(repo).execute(role="ADMIN")

    assert [account.username for account in results] == ["admin_01"]


@pytest.mark.anyio
async def test_activate_account_updates_status() -> None:
    repo = FakeAccountRepository()
    account = await repo.create(
        Account(
            username=Username("cashier_01"),
            email=Email("cashier@example.com"),
            password_hash="hash",
            role=RoleCode.CASHIER,
            is_active=False,
        )
    )

    result = await ActivateAccountUseCase(repo).execute(account.id)

    assert result.is_active is True
    assert repo.accounts[account.id].is_active is True


@pytest.mark.anyio
async def test_delete_account_removes_account() -> None:
    repo = FakeAccountRepository()
    account = await repo.create(
        Account(
            username=Username("cashier_01"),
            email=Email("cashier@example.com"),
            password_hash="hash",
            role=RoleCode.CASHIER,
        )
    )

    await DeleteAccountUseCase(repo).execute(account.id)

    assert repo.deleted_ids == [account.id]
    assert account.id not in repo.accounts

