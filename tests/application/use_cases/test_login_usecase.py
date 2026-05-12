import pytest

from app.modules.identity.application.config.auth_config import AuthConfig
from app.modules.identity.application.use_cases.login_usecase import LoginUseCase
from app.modules.identity.domain.entities.account import Account, RoleCode
from app.modules.identity.domain.value_objects.email import Email
from app.modules.identity.domain.value_objects.username import Username
from app.modules.identity.infra.security import TokenService
from app.shared.domain.exceptions.exceptions import (
    BusinessRuleViolation,
    InvalidPasswordError,
)


class FakeAccountRepository:
    def __init__(self, account: Account | None):
        self.account = account
        self.saved_accounts: list[Account] = []

    async def find_by_username(self, username: Username) -> Account | None:
        if self.account is None:
            return None

        if self.account.username != username:
            return None

        return self.account

    async def save(self, account: Account) -> Account:
        self.account = account
        self.saved_accounts.append(account)
        return account


class FakeRefreshTokenRepository:
    def __init__(self):
        self.saved_tokens = []

    async def save(self, refresh_token):
        self.saved_tokens.append(refresh_token)
        return refresh_token


class FakePasswordHasher:
    def hash(self, plain_password: str) -> str:
        return f"hashed:{plain_password}"

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return hashed_password == self.hash(plain_password)


def _active_account() -> Account:
    return Account(
        id=1,
        username=Username("cashier_01"),
        email=Email("cashier@example.com"),
        role=RoleCode.CASHIER,
        password_hash="hashed:correct-password",
    )


def _login_usecase(
    account_repo: FakeAccountRepository,
    refresh_token_repo: FakeRefreshTokenRepository | None = None,
) -> LoginUseCase:
    return LoginUseCase(
        account_repo=account_repo,
        refresh_token_repo=refresh_token_repo or FakeRefreshTokenRepository(),
        password_hasher=FakePasswordHasher(),
        token_service=TokenService(),
        auth_config=AuthConfig(
            access_token_expire_hours=1,
            refresh_token_expire_days=7,
        ),
    )


@pytest.mark.anyio
async def test_login_locks_account_after_three_failed_attempts() -> None:
    account_repo = FakeAccountRepository(_active_account())
    usecase = _login_usecase(account_repo)

    for _ in range(3):
        with pytest.raises(InvalidPasswordError):
            await usecase.execute("cashier_01", "wrong-password")

    assert account_repo.account.failed_login_attempts == 3
    assert account_repo.account.locked_until is not None
    assert len(account_repo.saved_accounts) == 3

    with pytest.raises(BusinessRuleViolation, match="temporarily locked"):
        await usecase.execute("cashier_01", "correct-password")


@pytest.mark.anyio
async def test_successful_login_resets_failed_attempts() -> None:
    account = _active_account()
    account.record_failed_login(account.created_at)
    account.record_failed_login(account.created_at)
    account_repo = FakeAccountRepository(account)
    refresh_token_repo = FakeRefreshTokenRepository()
    usecase = _login_usecase(account_repo, refresh_token_repo)

    result = await usecase.execute("cashier_01", "correct-password")

    assert result.access_token
    assert result.refresh_token
    assert account_repo.account.failed_login_attempts == 0
    assert account_repo.account.locked_until is None
    assert account_repo.account.last_login_at is not None
    assert len(refresh_token_repo.saved_tokens) == 1


@pytest.mark.anyio
async def test_login_rejects_unknown_username_as_invalid_credentials() -> None:
    account_repo = FakeAccountRepository(None)
    usecase = _login_usecase(account_repo)

    with pytest.raises(InvalidPasswordError, match="Invalid credentials"):
        await usecase.execute("missing_user", "wrong-password")


@pytest.mark.anyio
async def test_login_rejects_wrong_password_as_invalid_credentials() -> None:
    account_repo = FakeAccountRepository(_active_account())
    usecase = _login_usecase(account_repo)

    with pytest.raises(InvalidPasswordError, match="Invalid credentials"):
        await usecase.execute("cashier_01", "wrong-password")
