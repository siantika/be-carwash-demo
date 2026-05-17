import pytest

from app.modules.identity.application.dto.account_dto import RegisterAccountCmd
from app.modules.identity.application.queries.models import AccountListFilterDto
from app.modules.identity.application.commands.account_command import (
    ActivateAccountUseCase,
    DeleteAccountUseCase,
    RegisterAccountUseCase,
)
from app.modules.identity.application.queries.account_query import (
    GetAccountUseCase,
    ListAccountsUseCase,
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

    async def list(
        self,
        *,
        filters: AccountListFilterDto,
        limit: int,
        offset: int,
    ) -> tuple[list[Account], int]:
        accounts = list(self.accounts.values())
        accounts.sort(key=lambda account: account.id or 0, reverse=True)

        if filters.role is not None:
            accounts = [account for account in accounts if account.role == filters.role]

        if filters.is_active is not None:
            accounts = [
                account
                for account in accounts
                if account.is_active is filters.is_active
            ]

        return accounts[offset : offset + limit], len(accounts)

    async def create(self, account: Account) -> Account:
        account.id = self.next_id
        self.next_id += 1
        self.accounts[account.id] = account
        return account

    async def save(self, account: Account) -> Account:
        self.accounts[account.id] = account
        return account

    async def delete(self, account_id: int) -> int:
        self.deleted_ids.append(account_id)
        self.accounts.pop(account_id, None)
        return account_id


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
async def test_registered_account_can_be_fetched_by_id() -> None:
    repo = FakeAccountRepository()
    register_usecase = RegisterAccountUseCase(repo, FakePasswordHasher())
    get_usecase = GetAccountUseCase(repo)

    created = await register_usecase.execute(
        RegisterAccountCmd(
            username="Owner_01",
            email="owner@example.com",
            password="Password1",
            role="OWNER",
            is_active=False,
        )
    )

    result = await get_usecase.execute(created.id)

    assert result.id == created.id
    assert result.username == "owner_01"
    assert result.email == "owner@example.com"
    assert result.role == "OWNER"
    assert result.is_active is False


@pytest.mark.anyio
async def test_registered_account_appears_in_account_list() -> None:
    repo = FakeAccountRepository()
    register_usecase = RegisterAccountUseCase(repo, FakePasswordHasher())
    list_usecase = ListAccountsUseCase(repo)

    created = await register_usecase.execute(
        RegisterAccountCmd(
            username="cashier_02",
            email="cashier02@example.com",
            password="Password1",
            role=RoleCode.CASHIER,
        )
    )

    result = await list_usecase.execute()

    assert result.items == [created]
    assert result.total == 1
    assert result.page == 1
    assert result.limit == 20


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

    result = await ListAccountsUseCase(repo).execute(role="ADMIN")

    assert [account.username for account in result.items] == ["admin_01"]
    assert result.total == 1


@pytest.mark.anyio
async def test_list_accounts_can_filter_by_role_and_status() -> None:
    repo = FakeAccountRepository()
    await repo.create(
        Account(
            username=Username("cashier_active"),
            email=Email("cashier-active@example.com"),
            password_hash="hash",
            role=RoleCode.CASHIER,
            is_active=True,
        )
    )
    await repo.create(
        Account(
            username=Username("cashier_inactive"),
            email=Email("cashier-inactive@example.com"),
            password_hash="hash",
            role=RoleCode.CASHIER,
            is_active=False,
        )
    )
    await repo.create(
        Account(
            username=Username("admin_inactive"),
            email=Email("admin-inactive@example.com"),
            password_hash="hash",
            role=RoleCode.ADMIN,
            is_active=False,
        )
    )

    result = await ListAccountsUseCase(repo).execute(
        role=RoleCode.CASHIER,
        is_active=False,
    )

    assert [account.username for account in result.items] == ["cashier_inactive"]
    assert result.total == 1


@pytest.mark.anyio
async def test_list_accounts_paginates_results() -> None:
    repo = FakeAccountRepository()
    for index in range(5):
        await repo.create(
            Account(
                username=Username(f"cashier_{index}"),
                email=Email(f"cashier-{index}@example.com"),
                password_hash="hash",
                role=RoleCode.CASHIER,
            )
        )

    result = await ListAccountsUseCase(repo).execute(page=2, limit=2)

    assert [account.username for account in result.items] == ["cashier_2", "cashier_1"]
    assert result.total == 5
    assert result.page == 2
    assert result.limit == 2


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
